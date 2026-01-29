cmake_minimum_required(VERSION 3.10)
project(DiskSchedulerEngine VERSION 2.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 1. COMPILACIÓN ESTÁTICA: El secreto del "Zero-Setup"
if(MSVC)
    # En Windows, vincula estáticamente el runtime de C++ (/MT)
    # Evita el error "VCRUNTIME140.dll not found" en otras PCs.
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    add_compile_options(/W4 /Ox /Ot /D_CRT_SECURE_NO_WARNINGS)
else()
    # En Linux, forzamos a que incluya libstdc++ y libgcc dentro del binario
    add_compile_options(-Wall -Wextra -O3 -march=native)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static-libgcc -static-libstdc++")
endif()

# 2. Localizar librerías de sistema
find_package(Threads REQUIRED)

# 3. Fuentes del motor
set(ENGINE_SOURCES
    src/main.cpp
    src/shm_layer.cpp
    src/scheduler_core.cpp
    src/api_server.cpp
    src/utils.cpp
)

# 4. Definir el ejecutable
add_executable(scheduler_engine ${ENGINE_SOURCES})

# 5. Directorios de inclusión
target_include_directories(scheduler_engine PRIVATE 
    include
    ../common
)

# 6. Vinculación inteligente según el OS
target_link_libraries(scheduler_engine PRIVATE Threads::Threads)

if(UNIX AND NOT APPLE)
    # La librería 'rt' es vital para shm_open en Linux
    target_link_libraries(scheduler_engine PRIVATE rt)
endif()

# 7. Configuración de Instalación (Para el empaquetado posterior)
# Esto facilita que nuestro script de Python sepa dónde buscar el binario final.
install(TARGETS scheduler_engine DESTINATION bin)

message(STATUS "-------------------------------------------------------")
message(STATUS "Motor configurado para distribución ESTÁTICA.")
message(STATUS "Configuración del Motor (Multihilo/EventFD) lista.")
message(STATUS "Fuentes detectadas: ${ENGINE_SOURCES}")
message(STATUS "Sistema operativo detectado: ${CMAKE_SYSTEM_NAME}")
message(STATUS "-------------------------------------------------------")