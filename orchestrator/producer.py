import mmap
import struct
import os
import platform
import time
from typing import List

# Configuración compartida
SHM_NAME = "disk_scheduler_shm"  # En Win no lleva '/' inicial necesariamente
RING_BUFFER_CAPACITY = 1024
SLOT_SIZE = 24
HEADER_SIZE = 24
SLOT_FORMAT = "<I I d I I"

class ShmProducer:
    def __init__(self, event_fd_path="/tmp/scheduler_eventfd"):
        self.os_type = platform.system()
        self.shm_name = SHM_NAME
        
        try:
            if self.os_type == "Windows":
                # En Windows, mmap.mmap con tagname abre la SHM existente
                # 0 significa que el motor C++ ya la creó con el tamaño correcto
                self.map_file = mmap.mmap(-1, 0, tagname=self.shm_name, access=mmap.ACCESS_WRITE)
                import ctypes
                self.set_event = ctypes.windll.kernel32.SetEvent
                self.open_event = ctypes.windll.kernel32.OpenEventA
                self.EVENT_MODIFY_STATE = 0x0002
                # Abrir el evento creado por C++
                self.h_event = self.open_event(self.EVENT_MODIFY_STATE, False, (self.shm_name + "_event").encode())
            else:
                import posix_ipc
                self.shm_obj = posix_ipc.SharedMemory("/" + self.shm_name)
                self.map_file = mmap.mmap(self.shm_obj.fd, 0)
                self.efd_path = event_fd_path

            print(f"[Producer] Conectado en {self.os_type}. SHM Size: {self.map_file.size()} bytes")
        except Exception as e:
            print(f"[Error] No se pudo conectar a la SHM: {e}")
            raise

    def _notify_engine(self):
        """Notifica al motor C++ dependiendo del OS."""
        if self.os_type == "Windows":
            if self.h_event:
                self.set_event(self.h_event)
        else:
            try:
                if os.path.exists(self.efd_path):
                    with open(self.efd_path, "wb") as f:
                        f.write(struct.pack("Q", 1))
            except:
                pass

    def write_batch(self, requests: List[dict]):
        # Offset 12: Magic(4) + Version(2) + Pad(2) + Capacity(4) -> Producer Index
        prod_idx_offset = 12
        
        # Leer producer_index actual
        prod_idx = struct.unpack("<I", self.map_file[prod_idx_offset:prod_idx_offset+4])[0]

        for req in requests:
            slot_idx = prod_idx % RING_BUFFER_CAPACITY
            offset = HEADER_SIZE + (slot_idx * SLOT_SIZE)
            
            data = struct.pack(
                SLOT_FORMAT,
                req['id'],
                req['cylinder'],
                float(req.get('time', time.time())),
                req['batch_id'],
                1 # Status: Ready
            )
            
            self.map_file[offset:offset + SLOT_SIZE] = data
            prod_idx += 1

        # Actualizar índice y notificar
        self.map_file[prod_idx_offset:prod_idx_offset+4] = struct.pack("<I", prod_idx)
        self._notify_engine()
        return prod_idx

    def close(self):
        if self.map_file:
            self.map_file.close()
        if self.os_type == "Windows" and hasattr(self, 'h_event'):
            import ctypes
            ctypes.windll.kernel32.CloseHandle(self.h_event)