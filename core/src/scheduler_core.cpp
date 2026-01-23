#include "../include/scheduler_core.h"
#include <algorithm>
#include <cmath>

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
    
    // Separar en sub-lotes para evitar saltos bruscos
    std::vector<DiskRequest> lower, upper;
    for (const auto& req : batch) {
        if (req.cylinder < current_head_) lower.push_back(req);
        else upper.push_back(req);
    }

    // Ordenar in-place para minimizar el overhead metabólico
    std::sort(lower.begin(), lower.end(), [](const DiskRequest& a, const DiskRequest& b) {
        return a.cylinder > b.cylinder; // Hacia abajo
    });
    std::sort(upper.begin(), upper.end(), [](const DiskRequest& a, const DiskRequest& b) {
        return a.cylinder < b.cylinder; // Hacia arriba
    });

    auto process_list = [&](std::vector<DiskRequest>& list) {
        for (const auto& req : list) {
            batch_movement += std::abs((int32_t)req.cylinder - (int32_t)current_head_);
            current_head_ = req.cylinder;
        }
    };

    if (moving_up_) {
        process_list(upper);
        moving_up_ = false; // Cambio de tensión mecánica
        process_list(lower);
    } else {
        process_list(lower);
        moving_up_ = true;
        process_list(upper);
    }

    return batch_movement;
}

uint32_t SchedulerCore::run_cscan(std::vector<DiskRequest>& batch) {
    uint32_t batch_movement = 0;

    // C-SCAN siempre ordena en una sola dirección ascendente
    std::sort(batch.begin(), batch.end(), [](const DiskRequest& a, const DiskRequest& b) {
        return a.cylinder < b.cylinder;
    });

    // Encontrar el punto de corte para el cabezal actual
    auto it = std::lower_bound(batch.begin(), batch.end(), current_head_, 
        [](const DiskRequest& a, uint32_t val) {
            return a.cylinder < val;
        });

    // 1. Servir desde el cabezal hasta el final (derecha)
    for (auto i = it; i != batch.end(); ++i) {
        batch_movement += std::abs((int32_t)i->cylinder - (int32_t)current_head_);
        current_head_ = i->cylinder;
    }

    // 2. Salto circular al inicio (Reset cinemático)
    if (it != batch.begin()) {
        // El salto al inicio cuenta como movimiento mecánico si así se parametriza
        batch_movement += (max_cylinders_ - current_head_) + batch.begin()->cylinder;
        current_head_ = 0; // Reset a base

        // 3. Servir el resto desde el inicio
        for (auto i = batch.begin(); i != it; ++i) {
            batch_movement += std::abs((int32_t)i->cylinder - (int32_t)current_head_);
            current_head_ = i->cylinder;
        }
    }

    return batch_movement;
}

void SchedulerCore::update_metrics(uint32_t movement, size_t batch_size) {
    metrics_.total_head_movement += movement;
    metrics_.total_requests_served += batch_size;
    // Cálculo de media móvil simple para la espera
    metrics_.average_wait_time = (double)metrics_.total_head_movement / metrics_.total_requests_served;
}