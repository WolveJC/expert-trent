cmake_minimum_required(VERSION 3.10)
project(DiskSchedulerEngine VERSION 1.0)

# 1. Configuración del estándar C++ (C++17 para soporte de std::atomic y mejores headers)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 2. Flags de compilación para alto rendimiento
if(MSVC)
    add_compile_options(/W4 /OX)
else()
    add_compile_options(-Wall -Wextra -O3 -march=native)
endif()

# 3. Localizar librerías necesarias para Shared Memory y Threads en Linux
find_package(Threads REQUIRED)
set(RT_LIB rt) # Librería de tiempo real para shm_open

# 4. Definir el ejecutable y sus fuentes
# Nota: shm_engine.cpp y scheduler.cpp se incluyen vía header o se compilan aquí
add_executable(scheduler_engine 
    src/main.cpp 
    src/scheduler.cpp
)

# 5. Vincular librerías
target_link_libraries(scheduler_engine 
    PRIVATE 
    Threads::Threads
    ${RT_LIB}
)

# 6. Directorios de inclusión (para que encuentre protocol.h)
target_include_directories(scheduler_engine PRIVATE ../common)

# Mensaje de éxito al configurar
message(STATUS "Configuración lista para el motor de alto rendimiento.")