#include <gtest/gtest.h>
#include "scheduler_core.h"
#include "protocol.h"
#include <vector>

class SchedulerTest : public ::testing::Test {
protected:
    SchedulerCore scheduler;

    DiskRequest create_req(uint32_t id, uint32_t cyl) {
        return {id, cyl, 0.0, 1, 1}; // id, cyl, time, batch, status
    }
};

// 1. Probar SCAN Ascendente
TEST_F(SchedulerTest, ScanAscendingOrder) {
    scheduler.set_head_position(50);
    scheduler.set_direction(true); // Subiendo

    std::vector<DiskRequest> reqs = {
        create_req(1, 100),
        create_req(2, 20),
        create_req(3, 180)
    };

    // Usamos la función real del motor
    uint32_t movement = scheduler.execute_batch(reqs, SchedulerMode::SCAN);

    ASSERT_EQ(reqs.size(), 3);
    // Orden esperado: 100 -> 180 -> 20
    EXPECT_EQ(reqs[0].cylinder, 100);
    EXPECT_EQ(reqs[1].cylinder, 180);
    EXPECT_EQ(reqs[2].cylinder, 20);
    
    // Verificamos que el cabezal terminó en la última petición
    EXPECT_EQ(scheduler.get_head_position(), 20);
}

// 2. Probar C-SCAN (Salto circular)
TEST_F(SchedulerTest, CScanCircularJump) {
    scheduler.set_head_position(400);
    
    std::vector<DiskRequest> reqs = {
        create_req(1, 450),
        create_req(2, 10),
        create_req(3, 50)
    };

    uint32_t movement = scheduler.execute_batch(reqs, SchedulerMode::CSCAN);

    ASSERT_EQ(reqs.size(), 3);
    // Orden esperado: 450 -> (salto) -> 10 -> 50
    EXPECT_EQ(reqs[0].cylinder, 450);
    EXPECT_EQ(reqs[1].cylinder, 10);
    EXPECT_EQ(reqs[2].cylinder, 50);
}

// 3. Probar manejo de lotes vacíos (Robustez)
TEST_F(SchedulerTest, EmptyBatchHandling) {
    std::vector<DiskRequest> empty_reqs;
    EXPECT_NO_THROW({
        uint32_t movement = scheduler.execute_batch(empty_reqs, SchedulerMode::SCAN);
        EXPECT_EQ(movement, 0);
    });
}

// 4. Probar reinicio de métricas
TEST_F(SchedulerTest, MetricsReset) {
    std::vector<DiskRequest> reqs = { create_req(1, 100) };
    scheduler.execute_batch(reqs, SchedulerMode::SCAN);
    
    EXPECT_GT(scheduler.get_metrics().total_head_movement, 0);
    
    scheduler.reset_metrics();
    EXPECT_EQ(scheduler.get_metrics().total_head_movement, 0);
    EXPECT_EQ(scheduler.get_metrics().total_requests_served, 0);
}