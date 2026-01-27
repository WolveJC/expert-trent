import random
import time

class ScenarioGenerator:
    """
    Generador de carga de trabajo para simular diferentes comportamientos de acceso a disco.
    """
    def __init__(self, max_cylinders=500):
        self.max_cylinders = max_cylinders
        self.request_count = 0      # Contador global de IDs únicos
        self.current_batch_id = 0    # Contador de lotes

    def _create_request(self, cylinder):
        """
        Estructura base para una petición compatible con el orquestador y el motor C++.
        """
        self.request_count += 1
        return {
            'id': self.request_count,
            'cylinder': cylinder,
            'time': time.time(),
            'batch_id': self.current_batch_id,
            'status': 0  # Requerido por el protocolo binario
        }

    def random_requests(self, count=20):
        """Escenario Base: Distribución uniforme."""
        self.current_batch_id += 1
        return [self._create_request(random.randint(0, self.max_cylinders - 1)) 
                for _ in range(count)]

    def locality_burst(self, count=50, window=80):
        """Escenario de Localidad: Concentración en una zona específica (clúster)."""
        self.current_batch_id += 1
        anchor = random.randint(0, self.max_cylinders - window)
        return [self._create_request(anchor + random.randint(0, window)) 
                for _ in range(count)]

    def scan_killer(self, count=20):
        """Escenario Adverso: Alternancia entre extremos (0 y max) para forzar saltos."""
        self.current_batch_id += 1
        requests = []
        for i in range(count):
            if i % 2 == 0:
                cyl = random.randint(0, 10)
            else:
                cyl = random.randint(self.max_cylinders - 11, self.max_cylinders - 1)
            requests.append(self._create_request(cyl))
        return requests

    def sequential_stream(self, count=20, step=5):
        """Escenario Secuencial: Simula lectura/escritura de archivos contiguos."""
        self.current_batch_id += 1
        start = random.randint(0, self.max_cylinders // 2)
        return [self._create_request(min(self.max_cylinders - 1, start + (i * step))) 
                for i in range(count)]