#include "../../common/protocol.h"
#include <vector>
#include <algorithm>
#include <cmath>

class DiskScheduler {
public:
    enum class Direction { UP, DOWN };

private:
    uint32_t current_head;
    Direction current_direction;

public:
    DiskScheduler(uint32_t start_cylinder = 0) 
        : current_head(start_cylinder), current_direction(Direction::UP) {}

    /**
     * Implementación del algoritmo SCAN optimizado para el lote actual.
     * El objetivo es minimizar el movimiento total del cabezal[cite: 11, 64].
     */
    uint32_t execute_scan(std::vector<DiskRequest>& batch) {
        if (batch.empty()) return 0;

        uint32_t batch_movement = 0;

        // 1. Separar y ordenar solicitudes según la dirección actual
        std::vector<DiskRequest> left, right;
        for (const auto& req : batch) {
            if (req.cylinder < current_head) left.push_back(req);
            else right.push_back(req);
        }

        // Ordenar ambos vectores para un barrido eficiente
        std::sort(left.begin(), left.end(), [](const DiskRequest& a, const DiskRequest& b) {
            return a.cylinder > b.cylinder; // Descendente para el regreso
        });
        std::sort(right.begin(), right.end(), [](const DiskRequest& a, const DiskRequest& b) {
            return a.cylinder < b.cylinder; // Ascendente para el avance
        });

        // 2. Lógica de barrido SCAN (Elevator Algorithm)
        if (current_direction == Direction::UP) {
            // Procesar hacia arriba
            for (const auto& req : right) {
                batch_movement += std::abs((int32_t)req.cylinder - (int32_t)current_head);
                current_head = req.cylinder;
            }
            current_direction = Direction::DOWN; // Cambiar sentido al llegar al final del lote
            // Procesar las que quedaron atrás (hacia abajo)
            for (const auto& req : left) {
                batch_movement += std::abs((int32_t)req.cylinder - (int32_t)current_head);
                current_head = req.cylinder;
            }
        } else {
            // Procesar hacia abajo primero
            for (const auto& req : left) {
                batch_movement += std::abs((int32_t)req.cylinder - (int32_t)current_head);
                current_head = req.cylinder;
            }
            current_direction = Direction::UP;
            for (const auto& req : right) {
                batch_movement += std::abs((int32_t)req.cylinder - (int32_t)current_head);
                current_head = req.cylinder;
            }
        }

        return batch_movement;
    }

    uint32_t get_head_position() const { return current_head; }
};