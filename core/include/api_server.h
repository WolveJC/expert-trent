#ifndef API_SERVER_H
#define API_SERVER_H

#include <thread>
#include <atomic>
#include "scheduler_core.h"

/**
 * @class ApiServer
 * @brief Orquestador asíncrono para la gestión de comandos y estados del motor.
 */
class ApiServer {
public:
    ApiServer(std::atomic<bool>& run_flag, SchedulerMode& mode_flag);
    ~ApiServer();

    void start();
    void stop();

private:
    void listen_commands();

    std::atomic<bool>& running_;
    SchedulerMode& current_mode_;
    std::thread server_thread_;
};

#endif // API_SERVER_H