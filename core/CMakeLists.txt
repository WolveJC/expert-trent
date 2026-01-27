cmake_minimum_required(VERSION 3.10)
project(DiskSchedulerEngine VERSION 2.0)

# 1. Configuración del estándar C++
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 2. Flags de compilación para máxima eficiencia metabólica del CPU
# -O3: Optimización agresiva.
# -march=native: Utiliza instrucciones específicas de tu procesador actual.
if(MSVC)
    add_compile_options(/W4 /Ox /Ot)
else()
    add_compile_options(-Wall -Wextra -O3 -march=native -pthread)
endif()

# 3. Localizar librerías de sistema para IPC y Multihilo
find_package(Threads REQUIRED)
set(RT_LIB rt) # Necesaria para shm_open y shm_unlink en sistemas POSIX

# 4. Definir fuentes del motor (Estructura Modular Fase 2)
# Hemos separado las responsabilidades para evitar colisiones de nombres.
set(ENGINE_SOURCES
    src/main.cpp
    src/shm_layer.cpp
    src/scheduler_core.cpp
    src/api_server.cpp
    src/utils.cpp
)

# 5. Definir el ejecutable
add_executable(scheduler_engine ${ENGINE_SOURCES})

# 6. Directorios de inclusión
# Incluimos 'include/' para los headers locales y '../common/' para el protocolo binario.
target_include_directories(scheduler_engine PRIVATE 
    include
    ../common
)

# 7. Vincular librerías
# Threads::Threads gestiona automáticamente -pthread según el OS.
target_link_libraries(scheduler_engine 
    PRIVATE 
    Threads::Threads
    ${RT_LIB}
)

# 8. Mensajes de diagnóstico
message(STATUS "-------------------------------------------------------")
message(STATUS "Configuración del Motor (Multihilo/EventFD) lista.")
message(STATUS "Fuentes detectadas: ${ENGINE_SOURCES}")
message(STATUS "-------------------------------------------------------")