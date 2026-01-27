import pytest
from orchestrator.generators.scenarios import ScenarioGenerator

@pytest.fixture
def generator():
    # Inicializamos con 500 cilindros como límite estándar
    return ScenarioGenerator(max_cylinders=500)

def test_random_requests_limits(generator):
    """Verifica que las peticiones aleatorias estén dentro del rango del disco."""
    count = 100
    requests = generator.random_requests(count=count)
    
    assert len(requests) == count
    for r in requests:
        assert 0 <= r['cylinder'] < 500
        assert 'batch_id' in r
        assert 'id' in r

def test_locality_burst_concentration(generator):
    """Verifica que el escenario de localidad concentre peticiones en un rango."""
    count = 50
    requests = generator.locality_burst(count=count)
    
    # Extraemos cilindros para analizar la dispersión
    cylinders = [r['cylinder'] for r in requests]
    
    # En un patrón de localidad, la diferencia entre el max y min 
    # suele ser mucho menor que el rango total del disco (500)
    spread = max(cylinders) - min(cylinders)
    assert spread <= 100  # Definimos que una 'ráfaga' no debe exceder 100 cilindros

def test_scan_killer_alternation(generator):
    """Verifica que el SCAN-killer genere extremos opuestos."""
    # El killer suele poner peticiones en los bordes para forzar al cabezal
    requests = generator.scan_killer(count=10)
    cylinders = [r['cylinder'] for r in requests]
    
    # Verificamos que existan peticiones cerca del 0 y cerca del 499
    assert any(c < 50 for c in cylinders)
    assert any(c > 450 for c in cylinders)

def test_unique_ids(generator):
    """Asegura que cada petición tenga un ID único para evitar colisiones en la SHM."""
    requests = generator.random_requests(count=100)
    ids = [r['id'] for r in requests]
    
    assert len(set(ids)) == len(ids)