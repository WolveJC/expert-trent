#include "../include/api_server.h"
#include <iostream>
#include <string>

ApiServer::ApiServer(std::atomic<bool>& run_flag, SchedulerMode& mode_flag) 
    : running_(run_flag), current_mode_(mode_flag) {}

void ApiServer::start() {
    server_thread_ = std::thread(&ApiServer::listen_commands, this);
}

void ApiServer::listen_commands() {
    std::string command;
    while (running_.load()) {
        
        if (!(std::cin >> command)) break;

        if (command == "scan") {
            current_mode_ = SchedulerMode::SCAN;
            std::cout << "[API] Señalización cambiada a modo SCAN." << std::endl;
        } 
        else if (command == "cscan") {
            current_mode_ = SchedulerMode::CSCAN;
            std::cout << "[API] Señalización cambiada a modo C-SCAN." << std::endl;
        } 
        else if (command == "stop") {
            running_.store(false);
            std::cout << "[API] Comando de parada detectado. Desactivando motor..." << std::endl;
            break;
        }
    }
}

void ApiServer::stop() {
    if (server_thread_.joinable()) {
        server_thread_.join();
    }
}

ApiServer::~ApiServer() {
    stop();
}