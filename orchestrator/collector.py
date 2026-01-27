import mmap
import struct
import posix_ipc
import time
import pandas as pd
from datetime import datetime

# Alineación con protocol.h y producer.py
SHM_NAME = "/disk_scheduler_shm"
HEADER_SIZE = 24
# Offset de consumer_index: Magic(4) + Version(2) + Pad(2) + Capacity(4) + ProdIdx(4) = 16
CONS_IDX_OFFSET = 16

class ShmCollector:
    def __init__(self, log_file="results/metrics.csv"):
        try:
            self.shm_obj = posix_ipc.SharedMemory(SHM_NAME)
            # CAMBIO: Mapeo automático de tamaño
            self.map_file = mmap.mmap(self.shm_obj.fd, 0)
            self.log_file = log_file
            self.history = []
            print(f"[Collector] Conectado a SHM. Resultados se guardarán en {log_file}")
        except posix_ipc.ExistentialError:
            print("[Error] No se encontró SHM. El motor C++ debe estar activo.")
            raise

    def wait_for_completion(self, target_idx, timeout=5):
        """
        Bloquea el proceso hasta que el motor C++ alcance el índice de producción objetivo.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Leer consumer_index desde SHM
            current_cons_idx = struct.unpack("<I", self.map_file[CONS_IDX_OFFSET:CONS_IDX_OFFSET+4])[0]
            
            if current_cons_idx >= target_idx:
                return True
            time.sleep(0.01) # Pequeña pausa para no saturar el bus de memoria
        
        return False

    def collect_metrics(self, batch_id, algorithm, elapsed_ms):
        """
        Extrae las métricas actuales del motor y las guarda en el historial.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "batch_id": batch_id,
            "algorithm": algorithm,
            "processing_time_ms": elapsed_ms,
            "status": "completed"
        }
        self.history.append(entry)
        return entry

    def save_to_csv(self):
        """
        Persiste los datos recolectados en un archivo CSV para el módulo de análisis.
        """
        if not self.history:
            return
            
        df = pd.DataFrame(self.history)
        # Si el archivo ya existe, añade sin escribir cabecera
        header = not pd.io.common.file_exists(self.log_file)
        df.to_csv(self.log_file, mode='a', index=False, header=header)
        print(f"[Collector] {len(self.history)} registros guardados en {self.log_file}")
        self.history.clear()

    def close(self):
        self.map_file.close()
        self.shm_obj.close_fd()