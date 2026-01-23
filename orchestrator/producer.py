import mmap
import struct
import posix_ipc
import time
from typing import List

# Basado en protocol.h (Alineación con #pragma pack(1))
SHM_NAME = "/disk_scheduler_shm"
# ShmRegion size = Header (22 bytes aprox) + (1024 * 24 bytes de slots)
# Usamos un tamaño generoso para el mapa inicial
SHM_SIZE = 32768 

# Formatos de struct para empaquetado binario
# Header: magic(I), version(H), capacity(I), prod_idx(I), cons_idx(I), flags(I)
HEADER_FORMAT = "I H I I I I"
HEADER_SIZE = 22 # Ajustado por alineación atómica en C++

# Slot: req_id(I), cylinder(I), arrival_time(d), batch_id(I), status(I)
SLOT_FORMAT = "I I d I I"
SLOT_SIZE = 24

class ShmProducer:
    def __init__(self):
        try:
            self.shm_obj = posix_ipc.SharedMemory(SHM_NAME)
            self.map_file = mmap.mmap(self.shm_obj.fd, SHM_SIZE)
        except posix_ipc.PermissionsError:
            print("[Error] No hay permisos para acceder a SHM. ¿El motor C++ está corriendo?")
            raise

    def write_batch(self, requests: List[dict]):
        # Obtener el índice actual del productor (Offset 10 en nuestro layout)
        prod_idx_bytes = self.map_file[10:14]
        prod_idx = struct.unpack("I", prod_idx_bytes)[0]

        for req in requests:
            offset = HEADER_SIZE + (prod_idx % 1024) * SLOT_SIZE
            
            # Empaquetar a binario puro
            data = struct.pack(
                SLOT_FORMAT,
                req['id'],
                req['cylinder'],
                req['time'],
                req['batch_id'],
                1 # Status: Ready
            )
            
            self.map_file[offset:offset + SLOT_SIZE] = data
            prod_idx += 1

        # Actualizar índice atómico (Notificación al motor)
        self.map_file[10:14] = struct.pack("I", prod_idx)

    def close(self):
        self.map_file.close()
        self.shm_obj.close_fd()