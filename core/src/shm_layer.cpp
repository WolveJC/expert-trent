#include "../include/shm_layer.h"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/eventfd.h>
#include <iostream>
#include <cstring>
#include <cerrno>
#include <thread>
#include <chrono>

ShmLayer::ShmLayer(const std::string& shm_name) 
    : name_(shm_name), shm_fd_(-1), event_fd_(-1), region_(nullptr) {}

bool ShmLayer::initialize() {
    // 1. Asegurar limpieza previa para evitar conflictos de tamaño (mmap length error)
    shm_unlink(name_.c_str());

    // 2. Apertura de Memoria Compartida
    shm_fd_ = shm_open(name_.c_str(), O_CREAT | O_RDWR, 0666);
    if (shm_fd_ == -1) {
        std::cerr << "[shm_layer] Error shm_open: " << strerror(errno) << std::endl;
        return false;
    }

    // 3. Dimensionamiento estricto
    if (ftruncate(shm_fd_, sizeof(ShmRegion)) == -1) {
        std::cerr << "[shm_layer] Error ftruncate: " << strerror(errno) << std::endl;
        return false;
    }

    // 4. Mapeo en el espacio de direcciones
    region_ = (ShmRegion*)mmap(nullptr, sizeof(ShmRegion), 
                               PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd_, 0);
    
    if (region_ == MAP_FAILED) {
        std::cerr << "[shm_layer] Error mmap: " << strerror(errno) << std::endl;
        return false;
    }

    // 5. Inicialización del Contrato Binario (Header)
    region_->header.magic = SHM_MAGIC;
    region_->header.version = SHM_VERSION;
    region_->header.capacity = RING_BUFFER_CAPACITY;
    region_->header.producer_index.store(0, std::memory_order_release);
    region_->header.consumer_index.store(0, std::memory_order_release);

    // 6. Configuración de eventfd
    // Para que Python pueda escribir aquí, en un entorno real usaríamos un FIFO.
    // Aquí inicializamos para permitir Active Waiting si no hay señal.
    event_fd_ = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK);
    
    std::cout << "[shm_layer] Sinapsis establecida. SHM_SIZE: " << sizeof(ShmRegion) 
              << " | ADDR: " << region_ << std::endl;
    return true;
}

void ShmLayer::wait_for_signal() {
    if (!region_) return;

    // --- Mecanismo de Resiliencia Híbrido ---
    // 1. Revisión rápida de índices (Polling de baja latencia)
    // Si Python ya escribió, no necesitamos esperar al eventfd.
    if (region_->header.producer_index.load(std::memory_order_acquire) > 
        region_->header.consumer_index.load(std::memory_order_acquire)) {
        return;
    }

    // 2. Espera pasiva (Reducción de consumo de CPU)
    // Intentamos leer el eventfd. Si falla (EAGAIN), dormimos un poco.
    eventfd_t counter;
    if (event_fd_ != -1) {
        if (eventfd_read(event_fd_, &counter) < 0) {
            if (errno == EAGAIN || errno == EINTR) {
                // Pequeña pausa para no saturar el bus de memoria si no hay señal física
                std::this_thread::sleep_for(std::chrono::microseconds(500));
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
    shm_unlink(name_.c_str());
}

ShmLayer::~ShmLayer() {
    unlink();
}