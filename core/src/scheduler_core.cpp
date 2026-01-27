#include "../include/scheduler_core.h"
#include <algorithm>
#include <cmath>
#include <vector>

SchedulerCore::SchedulerCore(uint32_t initial_head, uint32_t max_cylinders)
    : current_head_(initial_head), 
      max_cylinders_(max_cylinders), 
      moving_up_(true) {
    reset_metrics();
}

void SchedulerCore::reset_metrics() {
    metrics_ = {0, 0, 0.0};
}

uint32_t SchedulerCore::execute_batch(std::vector<DiskRequest>& batch, SchedulerMode mode) {
    if (batch.empty()) return 0;

    uint32_t movement = 0;
    if (mode == SchedulerMode::SCAN) {
        movement = run_scan(batch);
    } else {
        movement = run_cscan(batch);
    }

    update_metrics(movement, batch.size());
    return movement;
}

uint32_t SchedulerCore::run_scan(std::vector<DiskRequest>& batch) {
    uint32_t batch_movement = 0;
    std::vector<DiskRequest> lower, upper;

    // Clasificación por cercanía cinemática
    for (const auto& req : batch) {
        if (req.cylinder < current_head_) lower.push_back(req);
        else upper.push_back(req);
    }

    // Ordenar para barrido bidireccional
    std::sort(lower.begin(), lower.end(), [](const DiskRequest& a, const DiskRequest& b) {
        return a.cylinder > b.cylinder; // Descendente para barrido hacia abajo
    });
    std::sort(upper.begin(), upper.end(), [](const DiskRequest& a, const DiskRequest& b) {
        return a.cylinder < b.cylinder; // Ascendente para barrido hacia arriba
    });

    std::vector<DiskRequest> ordered_result;
    auto process_list = [&](std::vector<DiskRequest>& list) {
        for (auto& req : list) {
            batch_movement += std::abs((int32_t)req.cylinder - (int32_t)current_head_);
            current_head_ = req.cylinder;
            ordered_result.push_back(req);
        }
    };

    if (moving_up_) {
        process_list(upper);
        moving_up_ = false; // Cambio de sentido al llegar al extremo del lote
        process_list(lower);
    } else {
        process_list(lower);
        moving_up_ = true;
        process_list(upper);
    }

    // CRÍTICO: Sincronizar el vector original con el orden de servicio
    batch = std::move(ordered_result);
    return batch_movement;
}

uint32_t SchedulerCore::run_cscan(std::vector<DiskRequest>& batch) {
    uint32_t batch_movement = 0;
    std::vector<DiskRequest> ordered_result;

    // C-SCAN requiere una base ordenada
    std::sort(batch.begin(), batch.end(), [](const DiskRequest& a, const DiskRequest& b) {
        return a.cylinder < b.cylinder;
    });

    // Buscar el punto de entrada (lower_bound)
    auto it = std::lower_bound(batch.begin(), batch.end(), current_head_, 
        [](const DiskRequest& a, uint32_t val) {
            return a.cylinder < val;
        });

    // 1. Fase Ascendente (Derecha)
    for (auto i = it; i != batch.end(); ++i) {
        batch_movement += std::abs((int32_t)i->cylinder - (int32_t)current_head_);
        current_head_ = i->cylinder;
        ordered_result.push_back(*i);
    }

    // 2. Salto Circular (Flyback mecánico)
    if (it != batch.begin()) {
        // Penalización por flyback: hasta el final y vuelta al inicio
        batch_movement += (max_cylinders_ - current_head_) + batch.begin()->cylinder;
        current_head_ = batch.begin()->cylinder; // El salto termina en la primera petición
        
        // 3. Fase de reinicio desde el inicio del disco
        for (auto i = batch.begin(); i != it; ++i) {
            // Nota: El primer elemento después del salto ya sumó su movimiento en el flyback
            if (i != batch.begin()) {
                batch_movement += std::abs((int32_t)i->cylinder - (int32_t)current_head_);
                current_head_ = i->cylinder;
            }
            ordered_result.push_back(*i);
        }
    }

    batch = std::move(ordered_result);
    return batch_movement;
}

void SchedulerCore::update_metrics(uint32_t movement, size_t batch_size) {
    metrics_.total_head_movement += movement;
    metrics_.total_requests_served += batch_size;
    metrics_.average_wait_time = (double)metrics_.total_head_movement / metrics_.total_requests_served;
}