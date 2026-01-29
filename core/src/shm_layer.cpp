#include "../include/shm_layer.h"
#include <iostream>
#include <cstring>
#include <thread>
#include <chrono>

#ifdef _WIN32
    #include <windows.h>
#else
    #include <sys/mman.h>
    #include <sys/stat.h>
    #include <fcntl.h>
    #include <unistd.h>
    #include <sys/eventfd.h>
#endif

ShmLayer::ShmLayer(const std::string& shm_name) 
    : name_(shm_name), region_(nullptr) {
    #ifdef _WIN32
        hMapFile_ = NULL;
        hEvent_ = NULL;
    #else
        shm_fd_ = -1;
        event_fd_ = -1;
    #endif
}

bool ShmLayer::initialize() {
#ifdef _WIN32
    // --- Implementación para Windows ---
    // 1. Memoria Compartida (File Mapping)
    hMapFile_ = CreateFileMappingA(
        INVALID_HANDLE_VALUE,    // Usar swap file
        NULL,                    // Seguridad por defecto
        PAGE_READWRITE,          // Acceso lectura/escritura
        0,                       // Tamaño high
        sizeof(ShmRegion),       // Tamaño low
        name_.c_str()            // Nombre del objeto
    );

    if (hMapFile_ == NULL) {
        std::cerr << "[shm_layer] Error CreateFileMapping: " << GetLastError() << std::endl;
        return false;
    }

    region_ = (ShmRegion*)MapViewOfFile(hMapFile_, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(ShmRegion));
    
    // 2. Evento de sincronización
    hEvent_ = CreateEventA(NULL, FALSE, FALSE, (name_ + "_event").c_str());

#else
    // --- Implementación para Linux ---
    shm_unlink(name_.c_str());
    shm_fd_ = shm_open(name_.c_str(), O_CREAT | O_RDWR, 0666);
    if (shm_fd_ == -1) return false;

    if (ftruncate(shm_fd_, sizeof(ShmRegion)) == -1) {
        close(shm_fd_);
        return false;
    }
    region_ = (ShmRegion*)mmap(nullptr, sizeof(ShmRegion), PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd_, 0);

    if (region_ == MAP_FAILED) {
        region_ = nullptr;
        return false;
    }
    
    event_fd_ = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK);
#endif

    if (!region_) return false;

    // Inicialización del Header
    region_->header.magic = SHM_MAGIC;
    region_->header.version = SHM_VERSION;
    region_->header.capacity = RING_BUFFER_CAPACITY;
    region_->header.producer_index.store(0, std::memory_order_release);
    region_->header.consumer_index.store(0, std::memory_order_release);

    std::cout << "[shm_layer] Sinapsis establecida en " << (
#ifdef _WIN32 
        "Windows"
#else
        "Linux"
#endif
    ) << std::endl;
    return true;
}

void ShmLayer::wait_for_signal() {
    if (!region_) return;

    // 1. Polling de alta velocidad (Común)
    if (region_->header.producer_index.load(std::memory_order_acquire) > 
        region_->header.consumer_index.load(std::memory_order_acquire)) {
        return;
    }

    // 2. Espera pasiva (Específica de OS)
#ifdef _WIN32
    WaitForSingleObject(hEvent_, 10); // Espera 10ms o señal
#else
    eventfd_t counter;
    if (event_fd_ != -1) {
        if (eventfd_read(event_fd_, &counter) < 0) {
            std::this_thread::sleep_for(std::chrono::microseconds(500));
        }
    }
#endif
}

void ShmLayer::unlink() {
#ifdef _WIN32
    if (region_) UnmapViewOfFile(region_);
    if (hMapFile_) CloseHandle(hMapFile_);
    if (hEvent_) CloseHandle(hEvent_);
#else
    if (region_) munmap(region_, sizeof(ShmRegion));
    if (shm_fd_ != -1) close(shm_fd_);
    if (event_fd_ != -1) close(event_fd_);
    shm_unlink(name_.c_str());
#endif
    region_ = nullptr;
}

ShmLayer::~ShmLayer() { unlink(); }