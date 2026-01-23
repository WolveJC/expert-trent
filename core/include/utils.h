#ifndef UTILS_H
#define UTILS_H

#include <string>
#include <vector>

namespace utils {

    /**
     * @brief Estructura para el perfil metabólico de latencias.
     */
    struct Stats {
        double mean;
        double min;
        double max;
    };

    /**
     * @brief Obtiene la marca de tiempo actual con precisión de nanosegundos.
     */
    double get_timestamp_now();

    /**
     * @brief Formatea logs con marca de tiempo para análisis de rendimiento.
     */
    void log_info(const std::string& module, const std::string& message);

    /**
     * @brief Calcula estadísticas de dispersión sobre latencias.
     */
    Stats calculate_stats(const std::vector<double>& latencies);

} // namespace utils

#endif // UTILS_H