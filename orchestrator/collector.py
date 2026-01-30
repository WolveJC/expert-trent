import mmap
import struct
import time
import platform
import os
import pandas as pd
from datetime import datetime

# Configuración de nombres alineada con protocol.h
SHM_NAME = "disk_scheduler_shm"
# Offset corregido para Consumer Index (ahora es 14 según la estructura C++)
CONS_IDX_OFFSET = 14 
# Nuevo offset para el tiempo (justo después de flags)
DURATION_OFFSET = 22 

class ShmCollector:
    def __init__(self, log_file="results/metrics.csv"):
        self.os_type = platform.system()
        self.log_file = log_file
        self.history = []
        self.map_file = None
        self.shm_obj = None

        try:
            if self.os_type == "Windows":
                self.map_file = mmap.mmap(-1, 0, tagname=SHM_NAME, access=mmap.ACCESS_READ)
            else:
                import posix_ipc
                self.shm_obj = posix_ipc.SharedMemory("/" + SHM_NAME)
                self.map_file = mmap.mmap(self.shm_obj.fd, 0, prot=mmap.PROT_READ)
            
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            print(f"[Collector] Conectado. Escuchando telemetría en offset {DURATION_OFFSET}")
        except Exception as e:
            print(f"[Error Collector] {e}")
            raise

    def wait_for_completion(self, target_idx, timeout=5):
        """Bloquea hasta que el motor procese las peticiones."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Leemos 4 bytes (I = uint32)
            current_cons_idx = struct.unpack("<I", self.map_file[CONS_IDX_OFFSET:CONS_IDX_OFFSET+4])[0]
            if current_cons_idx >= target_idx:
                return True
            time.sleep(0.01)
        return False

    def get_last_duration(self):
        """
        Extrae el tiempo real de procesamiento (double = 8 bytes) desde la SHM.
        """
        try:
            # "d" es el formato para double (8 bytes) en struct.unpack
            raw_duration = struct.unpack("<d", self.map_file[DURATION_OFFSET:DURATION_OFFSET+8])[0]
            # Convertimos segundos a milisegundos para el reporte
            return raw_duration * 1000.0
        except Exception as e:
            print(f"[Collector] Error leyendo duración: {e}")
            return 0.0

    def collect_metrics(self, batch_id, algorithm, elapsed_ms=None):
        """
        Registra los resultados. Si elapsed_ms es None, lo lee de la SHM.
        """
        # Si no nos pasan el tiempo, lo buscamos en el "buzón" de la SHM
        if elapsed_ms is None:
            elapsed_ms = self.get_last_duration()

        entry = {
            "timestamp": datetime.now().isoformat(),
            "batch_id": batch_id,
            "algorithm": algorithm.upper(),
            "processing_time_ms": round(elapsed_ms, 6), # Más precisión para ver los picos
            "os": self.os_type,
            "status": "completed"
        }
        self.history.append(entry)
        return entry

    def save_to_csv(self):
        if not self.history: return
        df = pd.DataFrame(self.history)
        file_exists = os.path.isfile(self.log_file)
        df.to_csv(self.log_file, mode='a', index=False, header=not file_exists)
        self.history.clear()

    def close(self):
        if self.map_file: self.map_file.close()
        if self.shm_obj: self.shm_obj.close_fd()