#ifndef SCHEDULER_CORE_H
#define SCHEDULER_CORE_H

#include "../../common/protocol.h"
#include <vector>
#include <cstdint>

/**
 * @enum SchedulerMode
 * @brief Modos de operación para la lógica de barrido.
 */
enum class SchedulerMode {
    SCAN,
    CSCAN
};

/**
 * @struct SchedulerMetrics
 * @brief Contenedor de métricas para análisis de rendimiento metabólico del disco.
 */
struct SchedulerMetrics {
    uint32_t total_requests_served = 0;
    uint32_t total_head_movement = 0;
    double average_wait_time = 0.0;
};

/**
 * @class SchedulerCore
 * @brief Núcleo de ejecución optimizado para algoritmos de planificación de disco.
 */
class SchedulerCore {
public:
    explicit SchedulerCore(uint32_t initial_head = 0, uint32_t max_cylinders = 500);
    ~SchedulerCore() = default;

    /**
     * @brief Procesa un lote de solicitudes directamente desde la SHM.
     * @param batch Referencia al vector de solicitudes pre-alocado.
     * @param mode Algoritmo a aplicar (SCAN o C-SCAN).
     * @return Movimiento total generado en este lote.
     */
    uint32_t execute_batch(std::vector<DiskRequest>& batch, SchedulerMode mode);

    // Getters para instrumentación
    uint32_t get_head_position() const { return current_head_; }
    const SchedulerMetrics& get_metrics() const { return metrics_; }
    
    /**
     * @brief Reinicia las métricas sin detener el motor.
     */
    void reset_metrics();

private:
    uint32_t current_head_;
    uint32_t max_cylinders_;
    bool moving_up_; // Dirección actual para el algoritmo SCAN
    SchedulerMetrics metrics_;

    // Métodos internos de cálculo cinemático
    uint32_t run_scan(std::vector<DiskRequest>& batch);
    uint32_t run_cscan(std::vector<DiskRequest>& batch);
    
    /**
     * @brief Actualiza métricas temporales (latencia y turnaround).
     */
    void update_metrics(uint32_t movement, size_t batch_size);
};

#endif // SCHEDULER_CORE_H