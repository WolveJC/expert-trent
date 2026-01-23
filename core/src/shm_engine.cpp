#include "../../common/protocol.h"
#include <iostream>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/eventfd.h>

class ShmEngine {
private:
    int shm_fd;
    int efd; // File descriptor para eventfd (notificaciones eficientes)
    ShmRegion* region;
    const char* shm_name = "/disk_scheduler_shm";

public:
    ShmEngine() : shm_fd(-1), efd(-1), region(nullptr) {}

    bool init() {
        // 1. Crear o abrir el objeto de memoria compartida [cite: 6, 48]
        shm_fd = shm_open(shm_name, O_CREAT | O_RDWR, 0666);
        if (shm_fd == -1) return false;

        // 2. Definir el tamaño de la región según el protocolo [cite: 24, 81]
        if (ftruncate(shm_fd, sizeof(ShmRegion)) == -1) return false;

        // 3. Mapear la memoria al espacio de direcciones del proceso [cite: 16]
        region = (ShmRegion*)mmap(nullptr, sizeof(ShmRegion), 
                                 PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
        
        if (region == MAP_FAILED) return false;

        // 4. Inicializar el Header si es necesario [cite: 23, 25]
        region->header.magic = SHM_MAGIC;
        region->header.version = SHM_VERSION;
        region->header.capacity = RING_BUFFER_CAPACITY;
        
        // Inicializar índices atómicos [cite: 40, 88]
        region->header.producer_index.store(0);
        region->header.consumer_index.store(0);

        std::cout << "[C++ Engine] SHM Initialized. Magic: " << std::hex << region->header.magic << std::endl;
        return true;
    }

    void wait_for_data() {
        // Aquí implementaríamos el bloqueo eficiente (eventfd o polling controlado) [cite: 41, 96]
        // Para el prototipo inicial, usaremos un spin-lock ligero con backoff
        while (region->header.producer_index.load() == region->header.consumer_index.load()) {
            usleep(100); // Evitar consumo de CPU innecesario en el prototipo [cite: 41]
        }
    }

    ShmRegion* get_region() { return region; }

    ~ShmEngine() {
        if (region) munmap(region, sizeof(ShmRegion));
        if (shm_fd != -1) close(shm_fd);
        // shm_unlink(shm_name); // Se suele dejar al Orquestador Python la limpieza final [cite: 49, 127]
    }
};