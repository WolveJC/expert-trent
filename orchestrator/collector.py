import mmap
import struct
import time
import platform
import os
import pandas as pd
from datetime import datetime

# Configuración de nombres alineada con C++ y producer.py
SHM_NAME = "disk_scheduler_shm"  # Sin '/' para compatibilidad con Windows tagname
CONS_IDX_OFFSET = 16            # Magic(4) + Ver(2) + Pad(2) + Cap(4) + ProdIdx(4)

class ShmCollector:
    def __init__(self, log_file="results/metrics.csv"):
        self.os_type = platform.system()
        self.log_file = log_file
        self.history = []
        self.map_file = None
        self.shm_obj = None

        try:
            if self.os_type == "Windows":
                # En Windows, mmap.mmap con tagname accede a la memoria nombrada
                # 0 indica que el motor C++ ya definió el tamaño
                self.map_file = mmap.mmap(-1, 0, tagname=SHM_NAME, access=mmap.ACCESS_READ)
            else:
                import posix_ipc
                # En Linux, posix_ipc requiere el '/' inicial
                self.shm_obj = posix_ipc.SharedMemory("/" + SHM_NAME)
                self.map_file = mmap.mmap(self.shm_obj.fd, 0, prot=mmap.PROT_READ)
            
            # Asegurar que el directorio de resultados existe
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            print(f"[Collector] Conectado en {self.os_type}. Guardando en {self.log_file}")
        except Exception as e:
            print(f"[Error Collector] No se pudo conectar a la SHM: {e}")
            print("Asegúrese de que el motor C++ esté corriendo.")
            raise

    def wait_for_completion(self, target_idx, timeout=5):
        """
        Bloquea el proceso hasta que el motor C++ procese las peticiones.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Leer consumer_index (uint32_t) desde el offset 16
            current_cons_idx = struct.unpack("<I", self.map_file[CONS_IDX_OFFSET:CONS_IDX_OFFSET+4])[0]
            
            if current_cons_idx >= target_idx:
                return True
            time.sleep(0.01)  # Evita saturar el bus de memoria
        
        return False

    def collect_metrics(self, batch_id, algorithm, elapsed_ms):
        """
        Registra los resultados de un lote en la memoria temporal.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "batch_id": batch_id,
            "algorithm": algorithm.upper(),
            "processing_time_ms": round(elapsed_ms, 4),
            "os": self.os_type,
            "status": "completed"
        }
        self.history.append(entry)
        return entry

    def save_to_csv(self):
        """
        Persiste el historial en el archivo CSV.
        """
        if not self.history:
            return
            
        df = pd.DataFrame(self.history)
        # Escribir cabecera solo si el archivo no existe
        file_exists = os.path.isfile(self.log_file)
        df.to_csv(self.log_file, mode='a', index=False, header=not file_exists)
        
        print(f"[Collector] {len(self.history)} registros guardados.")
        self.history.clear()

    def close(self):
        """Libera los recursos de memoria."""
        if self.map_file:
            self.map_file.close()
        if self.shm_obj:
            # close_fd solo existe en el objeto posix_ipc
            self.shm_obj.close_fd()