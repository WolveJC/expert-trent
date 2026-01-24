import random
import time

class ScenarioGenerator:
    """
    Generador de escenarios de carga para evaluar el rendimiento
    mecánico y la latencia del motor de planificación de disco.
    """
    
    def __init__(self, max_cylinders=500):
        self.max_cylinders = max_cylinders
        self.current_batch_id = 0

    def _create_request(self, cylinder, request_id):
        """Estructura base para una petición compatible con el orquestador."""
        return {
            'id': request_id,
            'cylinder': cylinder,
            'time': time.time(),
            'batch_id': self.current_batch_id
        }

    def random_requests(self, count=20):
        """
        Escenario Base: Distribución uniforme.
        Útil para medir el rendimiento promedio.
        """
        self.current_batch_id += 1
        return [self._create_request(random.randint(0, self.max_cylinders - 1), i) 
                for i in range(count)]

    def locality_burst(self, count=20):
        """
        Escenario de Localidad: Peticiones concentradas en un rango estrecho.
        Simula la lectura de un archivo grande o base de datos.
        """
        self.current_batch_id += 1
        center = random.randint(50, self.max_cylinders - 50)
        # 80% de las peticiones en un rango de 40 cilindros
        requests = []
        for i in range(count):
            if random.random() < 0.8:
                cyl = random.randint(max(0, center - 20), min(self.max_cylinders - 1, center + 20))
            else:
                cyl = random.randint(0, self.max_cylinders - 1)
            requests.append(self._create_request(cyl, i))
        return requests

    def scan_killer(self, count=20):
        """
        Escenario Adverso: Peticiones en extremos opuestos.
        Diseñado para maximizar el 'Seek Time' y exponer debilidades de SCAN.
        """
        self.current_batch_id += 1
        requests = []
        for i in range(count):
            # Alterna entre los primeros y últimos 10 cilindros
            if i % 2 == 0:
                cyl = random.randint(0, 10)
            else:
                cyl = random.randint(self.max_cylinders - 11, self.max_cylinders - 1)
            requests.append(self._create_request(cyl, i))
        return requests

    def sequential_stream(self, count=20, step=5):
        """
        Escenario Secuencial: Simula un streaming de datos.
        """
        self.current_batch_id += 1
        start = random.randint(0, self.max_cylinders // 2)
        return [self._create_request(min(self.max_cylinders - 1, start + (i * step)), i) 
                for i in range(count)]