#ifndef SHM_LAYER_H
#define SHM_LAYER_H

#include "../../common/protocol.h"
#include <string>
#include <atomic>
#include <cstdint>

/**
 * @class ShmLayer
 * @brief Gestiona la sinapsis de memoria compartida y la sincronización por eventos.
 * * Esta capa encapsula el acceso al Ring Buffer y la señalización de baja latencia.
 */
class ShmLayer {
public:
    explicit ShmLayer(const std::string& shm_name);
    ~ShmLayer();

    // Prohibir copia para evitar duplicidad de descriptores de memoria
    ShmLayer(const ShmLayer&) = delete;
    ShmLayer& operator=(const ShmLayer&) = delete;

    /**
     * @brief Inicializa la región SHM y configura eventfd.
     * @return true si la sinapsis fue exitosa.
     */
    bool initialize();

    /**
     * @brief Bloquea el hilo actual hasta que el productor envíe nuevos datos.
     * Utiliza eventfd para un consumo de CPU del 0% durante la espera.
     */
    void wait_for_signal();

    /**
     * @brief Obtiene acceso directo a la región de memoria compartida.
     */
    ShmRegion* get_region() const { return region_; }

    /**
     * @brief Limpia y desvincula la memoria del sistema (Watchdog).
     */
    void unlink();

private:
    std::string name_;
    int shm_fd_;
    int event_fd_; // Descriptor para notificaciones de baja latencia (eventfd)
    ShmRegion* region_;

    bool map_memory();
    void setup_event_signal();
};

#endif // SHM_LAYER_H