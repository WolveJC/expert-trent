import mmap
import posix_ipc
import struct
import time
import random
from reference import ScanReference

# Configuración estricta según protocol.h
SHM_NAME = "/disk_scheduler_shm"
# Header: I(4) + H(2) + I(4) + I(4) + I(4) + I(4) = 22 bytes
# Pero C++ suele alinear el primer atomic a 4 o 8 bytes. 
# Con #pragma pack(1), el offset de producer_index es exactamente 10.
HEADER_FORMAT = "=I H I I I I" 
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

SLOT_FORMAT = "=I I d I I" # I(4), I(4), d(8), I(4), I(4) = 24 bytes
SLOT_SIZE = struct.calcsize(SLOT_FORMAT)
RING_BUFFER_CAPACITY = 1024

class ShmProducer:
    def __init__(self):
        try:
            # Intentamos conectar a la memoria existente
            self.shm_obj = posix_ipc.SharedMemory(SHM_NAME)
            self.map_file = mmap.mmap(self.shm_obj.fd, 0)
            print("[Python] Conexión establecida con el motor")
        except posix_ipc.NoSuchEntityError:
            print("[Error] La memoria compartida no existe. ¿Iniciaste el motor C++?")
            raise SystemExit(1)

    def _get_producer_idx(self):
        # Offset 10: magic(4)+version(2)+capacity(4)
        return struct.unpack("=I", self.map_file[10:14])[0]

    def _set_producer_idx(self, val):
        self.map_file[10:14] = struct.pack("=I", val)

    def _get_consumer_idx(self):
        # Offset 14: producer_idx(4) tras los anteriores
        return struct.unpack("=I", self.map_file[14:18])[0]

    def send_batch(self, requests):
        p_idx = self._get_producer_idx()
        
        for req in requests:
            offset = HEADER_SIZE + (p_idx % RING_BUFFER_CAPACITY) * SLOT_SIZE
            data = struct.pack(
                SLOT_FORMAT,
                req['id'], req['cylinder'], req['time'], req['batch_id'], 1
            )
            self.map_file[offset:offset + SLOT_SIZE] = data
            p_idx += 1
        
        # Actualización atómica: despierta al motor C++
        self._set_producer_idx(p_idx)
        return p_idx

def run_experiment():
    producer = ShmProducer()
    reference = ScanReference()
    
    # 1. Generar datos (Escenario de prueba analítico)
    test_requests = [
        {'id': i, 'cylinder': random.randint(0, 499), 'time': time.time(), 'batch_id': 1}
        for i in range(10)
    ]
    
    print(f"[Orquestador] Enviando lote de {len(test_requests)} solicitudes...")
    
    # 2. Inyectar en SHM
    initial_head = 0
    target_idx = producer.send_batch(test_requests)
    
    # 3. Esperar a que el motor C++ procese (Sincronización)
    print("[Orquestador] Esperando respuesta del motor C++...")
    while True:
        c_idx = producer._get_consumer_idx()
        if c_idx >= target_idx:
            break
        time.sleep(0.1)
    
    # 4. Validación de resultados
    ref_movement, _ = reference.calculate_scan(test_requests, initial_head)
    print(f"\n[Resultado] Motor C++ finalizó el lote.")
    print(f"[Validación] Movimiento esperado (Python Ref): {ref_movement}")
    print(f"[Validación] Verifique el log del Motor C++ para contrastar.")

if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        print(f"[Error] {e}")