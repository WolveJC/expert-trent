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
    uint32_t request_id;   // Identificador único [cite: 27]
    uint32_t cylinder;     // Posición en el disco [cite: 27]
    double arrival_time;   // Tiempo de llegada (señalización química/temporal) [cite: 28]
    uint32_t batch_id;     // ID del lote para procesamiento agrupado [cite: 28]
    uint32_t status;       // 0: Vacío, 1: Listo, 2: Procesado [cite: 28]
};

/**
 * Header de la Memoria Compartida
 * Contiene los metadatos y los índices atómicos de control [cite: 23, 24]
 */
struct ShmHeader {
    uint32_t magic;            // Identificador [cite: 24]
    uint16_t version;          // Versión del protocolo [cite: 24]
    uint32_t capacity;         // Número de slots [cite: 24]
    
    // Índices atómicos para sincronización Lockless (SPSC) [cite: 25, 40]
    // Usamos std::atomic para garantizar visibilidad entre hilos/procesos
    std::atomic<uint32_t> producer_index; 
    std::atomic<uint32_t> consumer_index;
    
    uint32_t flags;            // Banderas de estado (ej: modo debug) [cite: 25]
};

/**
 * Estructura Completa de la Región SHM
 */
struct ShmRegion {
    ShmHeader header;
    DiskRequest buffer[RING_BUFFER_CAPACITY]; // Ring Buffer de entradas [cite: 26]
};

#pragma pack(pop)

#endif // DISK_SCHEDULER_PROTOCOL_H