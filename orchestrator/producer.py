import mmap
import struct
import posix_ipc
import os
import time
from typing import List

# Configuración alineada con include/protocol.h
SHM_NAME = "/disk_scheduler_shm"
RING_BUFFER_CAPACITY = 1024
SLOT_SIZE = 24
HEADER_SIZE = 24 

# Formatos de empaquetado (Little-endian)
SLOT_FORMAT = "<I I d I I"

class ShmProducer:
    def __init__(self, event_fd_path="/tmp/scheduler_eventfd"):
        try:
            # Conexión a SHM
            self.shm_obj = posix_ipc.SharedMemory(SHM_NAME)
            self.map_file = mmap.mmap(self.shm_obj.fd, 0) 
            self.efd_path = event_fd_path
            
            print(f"[Producer] Conectado. Tamaño SHM: {self.map_file.size()} bytes")
        except posix_ipc.ExistentialError:
            print("[Error] SHM no encontrada. Inicie el motor C++ primero.")
            raise

    def _notify_engine(self):
        """
        Envía la señal física al motor. 
        Si el motor usa un eventfd puro, aquí escribimos en el path del FIFO/Named Pipe.
        """
        try:
            # Simulamos el incremento del contador eventfd escribiendo 8 bytes (uint64)
            # El motor C++ debe estar escuchando este path específico si no es un FD heredado.
            if os.path.exists(self.efd_path):
                with open(self.efd_path, "wb") as f:
                    # 'Q' es unsigned long long (8 bytes) para eventfd
                    f.write(struct.pack("Q", 1))
        except Exception as e:
            # En modo prototipo, si falla el archivo, el motor detectará el cambio por polling
            pass

    def write_batch(self, requests: List[dict]):
        """
        Escribe un lote y retorna el target_idx para el collector.
        """
        # Offset 12: Magic(4) + Version(2) + Pad(2) + Capacity(4)
        prod_idx_offset = 12
        
        # Leemos el índice actual directamente de la SHM
        prod_idx = struct.unpack("<I", self.map_file[prod_idx_offset:prod_idx_offset+4])[0]

        for req in requests:
            slot_idx = prod_idx % RING_BUFFER_CAPACITY
            offset = HEADER_SIZE + (slot_idx * SLOT_SIZE)
            
            data = struct.pack(
                SLOT_FORMAT,
                req['id'],
                req['cylinder'],
                float(req['time']),
                req['batch_id'],
                1 # Status: Ready (enviado)
            )
            
            self.map_file[offset:offset + SLOT_SIZE] = data
            prod_idx += 1

        # 1. Actualizar el producer_index en SHM (Atómico para C++)
        self.map_file[prod_idx_offset:prod_idx_offset+4] = struct.pack("<I", prod_idx)
        
        # 2. Notificar al motor para que salga del estado wait()
        self._notify_engine()
        
        # RETORNO CRÍTICO para evitar TypeError en main.py
        return prod_idx

    def close(self):
        if hasattr(self, 'map_file') and self.map_file:
            self.map_file.close()
        if hasattr(self, 'shm_obj') and self.shm_obj:
            self.shm_obj.close_fd()