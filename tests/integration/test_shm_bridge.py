import pytest
import posix_ipc
import mmap
import struct
import os
from orchestrator.producer import ShmProducer, SHM_NAME, HEADER_SIZE, SLOT_SIZE, SLOT_FORMAT

@pytest.fixture
def shm_setup():
    """Prepara la SHM con la estructura de Ring Buffer que el productor espera."""
    # Tamaño: Header (24) + Buffer (1024 * 24)
    total_size = HEADER_SIZE + (1024 * SLOT_SIZE)
    try:
        posix_ipc.unlink_shared_memory(SHM_NAME)
    except posix_ipc.ExistentialError:
        pass

    shm = posix_ipc.SharedMemory(SHM_NAME, posix_ipc.O_CREAT, size=total_size)
    region = mmap.mmap(shm.fd, shm.size)
    
    # Inicializar Header: Magic(4) 'DSCH', Version(2), Pad(2), Capacity(4)=1024, ProdIdx(4)=0, ConsIdx(4)=0...
    region[0:4] = b"DSCH"
    region[8:12] = struct.pack("<I", 1024) # Capacity
    region[12:16] = struct.pack("<I", 0)    # Producer Index
    
    yield region
    
    region.close()
    shm.close_fd()
    posix_ipc.unlink_shared_memory(SHM_NAME)

def test_binary_compatibility_ring_buffer(shm_setup):
    """Valida que el productor escriba en el Slot correcto después del Header."""
    # Usamos el path por defecto o uno temporal para el test
    producer = ShmProducer(event_fd_path="/tmp/test_efd")
    
    test_req = {
        'id': 99,
        'cylinder': 250,
        'time': 555.5,
        'batch_id': 1
    }
    
    # Escribir el lote
    new_idx = producer.write_batch([test_req])
    
    # El primer slot debe estar en offset 24 (HEADER_SIZE)
    data = shm_setup[24 : 24 + SLOT_SIZE]
    unpacked = struct.unpack(SLOT_FORMAT, data)
    
    assert unpacked[0] == 99          # id
    assert unpacked[1] == 250         # cylinder
    assert unpacked[2] == pytest.approx(555.5)
    assert unpacked[4] == 1           # Status: Ready (tu código pone 1)
    assert new_idx == 1               # Producer Index incrementado