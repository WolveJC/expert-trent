#include "../../common/protocol.h"
#include "shm_engine.cpp"
#include "scheduler.cpp" // Incluimos el músculo algorítmico
#include <iostream>
#include <vector>
#include <unistd.h>

int main() {
    // 1. Inicialización de componentes
    ShmEngine engine;
    DiskScheduler scheduler(0); // Iniciamos el cabezal en el cilindro 0

    if (!engine.init()) {
        std::cerr << "Error crítico: Fallo en la sinapsis de memoria compartida." << std::endl;
        return 1;
    }

    ShmRegion* region = engine.get_region();
    uint32_t total_movement = 0;

    std::cout << "[Motor C++] Sistema listo. Monitoreando señales de entrada..." << std::endl;

    // Bucle principal de ejecución (Hot Path)
    while (true) {
        // 2. Espera pasiva de datos (eficiencia energética/CPU)
        engine.wait_for_data();

        uint32_t p_idx = region->header.producer_index.load(std::memory_order_acquire);
        uint32_t c_idx = region->header.consumer_index.load(std::memory_order_relaxed);

        if (c_idx < p_idx) {
            std::vector<DiskRequest> current_batch;
            current_batch.reserve(p_idx - c_idx); // Optimización de memoria previa

            // 3. Extracción de señales del Ring Buffer
            while (c_idx < p_idx) {
                uint32_t slot_idx = c_idx % RING_BUFFER_CAPACITY;
                current_batch.push_back(region->buffer[slot_idx]);
                c_idx++;
            }

            // 4. Ejecución del algoritmo (Delegación al Scheduler)
            uint32_t batch_movement = scheduler.execute_scan(current_batch);
            total_movement += batch_movement;

            std::cout << "[Motor C++] SCAN completado. Movimiento lote: " << batch_movement 
                      << " | Posición actual: " << scheduler.get_head_position()
                      << " | Total acumulado: " << total_movement << std::endl;

            // 5. Retroalimentación: Notificar al productor que el consumo finalizó
            region->header.consumer_index.store(c_idx, std::memory_order_release);
        }

        // Delay mínimo para el prototipo (en producción se usa eventfd para latencia cero)
        usleep(1000);
    }

    return 0;
}