#ifndef SCHEDULER_CORE_H
#define SCHEDULER_CORE_H

#include "../../common/protocol.h"
#include <vector>
#include <cstdint>

enum class SchedulerMode {
    SCAN,
    CSCAN
};

struct SchedulerMetrics {
    uint32_t total_requests_served = 0;
    uint32_t total_head_movement = 0;
    double average_wait_time = 0.0;
};

class SchedulerCore {
public:
    explicit SchedulerCore(uint32_t initial_head = 0, uint32_t max_cylinders = 500);
    ~SchedulerCore() = default;

    /**
     * @brief Procesa un lote y MODIFICA el vector original para reflejar el orden servido.
     * Esto permite que el Test verifique el orden después de la llamada.
     */
    uint32_t execute_batch(std::vector<DiskRequest>& batch, SchedulerMode mode);

    // --- Métodos expuestos para Unit Testing ---
    
    /**
     * @brief Permite forzar la dirección en SCAN para pruebas deterministas.
     */
    void set_direction(bool moving_up) { moving_up_ = moving_up; }
    
    /**
     * @brief Permite forzar la posición del cabezal para tests unitarios.
     */
    void set_head_position(uint32_t head) { current_head_ = head; }

    uint32_t get_head_position() const { return current_head_; }
    const SchedulerMetrics& get_metrics() const { return metrics_; }
    void reset_metrics();

private:
    uint32_t current_head_;
    uint32_t max_cylinders_;
    bool moving_up_; 
    SchedulerMetrics metrics_;

    // El Test podrá validar estos algoritmos a través de execute_batch
    uint32_t run_scan(std::vector<DiskRequest>& batch);
    uint32_t run_cscan(std::vector<DiskRequest>& batch);
    
    void update_metrics(uint32_t movement, size_t batch_size);
};

#endif