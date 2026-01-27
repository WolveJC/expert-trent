#include "../include/utils.h"
#include <iostream>
#include <chrono>
#include <iomanip>
#include <ctime>
#include <numeric>
#include <algorithm>

namespace utils {

    double get_timestamp_now() {
        auto now = std::chrono::high_resolution_clock::now();
        auto duration = now.time_since_epoch();
        return std::chrono::duration<double>(duration).count();
    }

    void log_info(const std::string& module, const std::string& message) {
        auto now_system = std::chrono::system_clock::now();
        auto now_c = std::chrono::system_clock::to_time_t(now_system);
        
        std::cout << "[" << std::put_time(std::localtime(&now_c), "%H:%M:%S") << "] "
                  << "[" << module << "] " << message << std::endl;
    }

    Stats calculate_stats(const std::vector<double>& latencies) {
        if (latencies.empty()) return {0.0, 0.0, 0.0};

        double sum = std::accumulate(latencies.begin(), latencies.end(), 0.0);
        auto [min_it, max_it] = std::minmax_element(latencies.begin(), latencies.end());

        return {
            sum / static_cast<double>(latencies.size()),
            *min_it,
            *max_it
        };
    }

} // namespace utils