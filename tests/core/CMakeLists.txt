cmake_minimum_required(VERSION 3.10)
project(DiskSchedulerTests)

# 1. Buscar Threads ANTES de usarlo en target_link_libraries
find_package(Threads REQUIRED)

# 2. Configuración de GTest (Descarga automática)
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/heads/main.zip
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

# 3. Inclusión de directorios (Core y Common)
# Usamos target_include_directories para que sea específico al ejecutable de test
include_directories(
    ../../core/include 
    ../../common
)

# 4. Definición del ejecutable de pruebas
add_executable(unit_tests
    test_scheduler.cpp
    ../../core/src/scheduler_core.cpp
    ../../core/src/utils.cpp
)

# 5. Vinculación de librerías corregida
# GTest ya incluye internamente dependencias, pero el core necesita rt y pthreads
target_link_libraries(unit_tests 
    PRIVATE
    gtest_main 
    Threads::Threads 
    rt
)

# 6. Habilitar descubrimiento de tests
include(GoogleTest)
gtest_discover_tests(unit_tests)