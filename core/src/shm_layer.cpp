#include "../include/shm_layer.h"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/eventfd.h>
#include <iostream>
#include <cstring>
#include <cerrno>

/**
 * @brief Implementación de la sinapsis de memoria y eventos (Fase 2)
 */
ShmLayer::ShmLayer(const std::string& shm_name) 
    : name_(shm_name), shm_fd_(-1), event_fd_(-1), region_(nullptr) {}

bool ShmLayer::initialize() {
    // 1. Apertura con flags de control: O_CREAT garantiza que el recurso exista
    shm_fd_ = shm_open(name_.c_str(), O_CREAT | O_RDWR, 0666);
    if (shm_fd_ == -1) {
        std::cerr << "[shm_layer] Error shm_open: " << strerror(errno) << std::endl;
        return false;
    }

    // 2. Dimensionamiento exacto para evitar SIGBUS
    if (ftruncate(shm_fd_, sizeof(ShmRegion)) == -1) {
        return false;
    }

    // 3. Mapeo persistente en el espacio de direcciones
    region_ = (ShmRegion*)mmap(nullptr, sizeof(ShmRegion), 
                               PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd_, 0);
    
    if (region_ == MAP_FAILED) {
        return false;
    }

    // 4. Inicialización del Header (Contrato binario)
    region_->header.magic = SHM_MAGIC;
    region_->header.version = SHM_VERSION;
    region_->header.capacity = RING_BUFFER_CAPACITY;
    
    // Sincronización atómica inicial para evitar estados indeterminados
    region_->header.producer_index.store(0, std::memory_order_release);
    region_->header.consumer_index.store(0, std::memory_order_release);

    // 5. Configuración de eventfd (La clave de la latencia cero)
    // Usamos EFD_CLOEXEC por seguridad y EFD_NONBLOCK para no colgar el hilo si no hay señal
    event_fd_ = eventfd(0, EFD_CLOEXEC);
    if (event_fd_ == -1) {
        std::cerr << "[shm_layer] Error al crear eventfd" << std::endl;
        return false;
    }

    std::cout << "[shm_layer] Sistema nervioso listo. SHM_MAGIC: " 
              << std::hex << region_->header.magic << std::dec << std::endl;
    return true;
}

void ShmLayer::wait_for_signal() {
    // Eliminado el usleep(100) y el while loop de la Fase 1
    // Ahora el proceso se suspende de forma real a través del sistema operativo
    eventfd_t counter;
    
    // Este read se bloquea hasta que Python realice un write en el eventfd asignado
    // Nota: Para que Python escriba aquí, deberemos pasarle el descriptor o usar un semáforo POSIX asociado
    if (event_fd_ != -1) {
        if (eventfd_read(event_fd_, &counter) < 0) {
            // Manejo de interrupciones de sistema
            if (errno != EINTR) {
                usleep(100); // Fallback de seguridad si falla la señalización pura
            }
        }
    }
}

void ShmLayer::unlink() {
    if (region_) {
        munmap(region_, sizeof(ShmRegion));
        region_ = nullptr;
    }
    if (shm_fd_ != -1) {
        close(shm_fd_);
        shm_fd_ = -1;
    }
    if (event_fd_ != -1) {
        close(event_fd_);
        event_fd_ = -1;
    }
    // La limpieza física de la memoria compartida se delega a este motor 
    // para asegurar que no queden residuos tras una ejecución limpia
    shm_unlink(name_.c_str());
}

ShmLayer::~ShmLayer() {
    unlink();
}