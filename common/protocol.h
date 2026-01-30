#ifndef DISK_SCHEDULER_PROTOCOL_H
#define DISK_SCHEDULER_PROTOCOL_H

#include <stdint.h>
#include <atomic>

// Magic number para validar la integridad de la SHM (0x53484D44 = "SHMD" en ASCII)
#define SHM_MAGIC 0x53484D44
#define SHM_VERSION 1
#define RING_BUFFER_CAPACITY 1024

#pragma pack(push, 1) // Aseguramos que no haya padding extra entre campos

/**
 * Estructura de una solicitud individual (Slot)
 * Tamaño: 24 bytes (Alineación natural para tipos de 64 y 32 bits)
 */
struct DiskRequest {
    uint32_t request_id;   // Identificador único
    uint32_t cylinder;     // Posición en el disco
    double arrival_time;   // Tiempo de llegada (señalización química/temporal)
    uint32_t batch_id;     // ID del lote para procesamiento agrupado
    uint32_t status;       // 0: Vacío, 1: Listo, 2: Procesado
};

/**
 * Header de la Memoria Compartida
 * Contiene los metadatos, índices de control y canal de métricas.
 */
struct ShmHeader {
    uint32_t magic;            // Identificador
    uint16_t version;          // Versión del protocolo
    uint32_t capacity;         // Número de slots
    
    // Índices atómicos para sincronización Lockless (SPSC)
    std::atomic<uint32_t> producer_index; 
    std::atomic<uint32_t> consumer_index;
    
    uint32_t flags;            // Banderas de estado (ej: modo debug)

    /**
     * CANAL DE TELEMETRÍA:
     * El motor C++ escribirá aquí el tiempo de ejecución del último lote.
     * Al estar antes del buffer y dentro de la estructura empaquetada,
     * Python podrá leerlo con el mismo offset.
     */
    double last_batch_duration; 
};

/**
 * Estructura Completa de la Región SHM
 */
struct ShmRegion {
    ShmHeader header;
    DiskRequest buffer[RING_BUFFER_CAPACITY]; // Ring Buffer de entradas
};

#pragma pack(pop)

#endif // DISK_SCHEDULER_PROTOCOL_H