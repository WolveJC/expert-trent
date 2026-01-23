#include "../include/shm_layer.h"
#include "../include/scheduler_core.h"
#include "../include/api_server.h" // Incluimos la lógica de control asíncrono
#include "../include/utils.h"      // Herramientas
#include <iostream>
#include <vector>
#include <atomic>
#include <signal.h>

// Bandera global para manejo de señales de terminación (SIGINT, SIGTERM)
std::atomic<bool> g_running(true);

void signal_handler(int) {
    g_running.store(false);
}

int main() {
    // 1. Configuración de señales para un cierre limpio (Graceful Shutdown)
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, nullptr);

    // 2. Inicialización de Componentes (Fase 2)
    ShmLayer shm("/disk_scheduler_shm");
    SchedulerCore scheduler(0, 500); // Cabezal en 0, 500 cilindros
    SchedulerMode current_mode = SchedulerMode::SCAN;

    if (!shm.initialize()) {
        utils::log_info("CRITICAL", "Fallo en la sinapsis SHM. Abortando motor.");
        return 1;
    }

    // 3. Lanzar Servidor de Control (API)
    ApiServer api(g_running, current_mode);
    api.start();

    ShmRegion* region = shm.get_region();
    utils::log_info("SYSTEM", "Motor C++ Fase 2 Activo. Esperando señales eventfd...");

    // Vector pre-alocado para evitar mallocs en el Hot Path (Zero-Allocation)
    std::vector<DiskRequest> batch_buffer;
    batch_buffer.reserve(RING_BUFFER_CAPACITY);

    // 4. Bucle de Procesamiento de Alta Tensión
    while (g_running.load(std::memory_order_relaxed)) {
        
        // Bloqueo eficiente mediante eventfd (Latencia cero vs usleep)
        shm.wait_for_signal();

        uint32_t p_idx = region->header.producer_index.load(std::memory_order_acquire);
        uint32_t c_idx = region->header.consumer_index.load(std::memory_order_relaxed);

        if (c_idx < p_idx) {
            batch_buffer.clear(); // Mantiene la capacidad reservada

            // 5. Extracción In-Place del Ring Buffer
            while (c_idx < p_idx) {
                uint32_t slot_idx = c_idx % RING_BUFFER_CAPACITY;
                batch_buffer.push_back(region->buffer[slot_idx]);
                c_idx++;
            }

            // 6. Ejecución y Medición
            double start_time = utils::get_timestamp_now();
            
            uint32_t batch_movement = scheduler.execute_batch(batch_buffer, current_mode);
            
            double end_time = utils::get_timestamp_now();

            // 7. Registro de Resultados y Retroalimentación
            region->header.consumer_index.store(c_idx, std::memory_order_release);

            // Logging 
            std::string log_msg = "Batch procesado [" + std::to_string(batch_buffer.size()) + 
                                  " reqs] Mov: " + std::to_string(batch_movement) + 
                                  " Tiempo: " + std::to_string(end_time - start_time) + "s";
            utils::log_info("ENGINE", log_msg);
        }
    }

    // 8. Cierre de Ciclo
    utils::log_info("SYSTEM", "Cerrando motor y liberando recursos...");
    api.stop();
    shm.unlink(); 

    return 0;
}