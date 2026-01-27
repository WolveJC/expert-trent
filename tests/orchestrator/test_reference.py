import pytest
from orchestrator.reference import ScanReference

@pytest.fixture
def ref():
    return ScanReference()

# Casos para SCAN (Bidireccional)
@pytest.mark.parametrize("head, requests, expected_mov, expected_final_pos", [
    (50, [
        {"cylinder": 100, "id": 1},
        {"cylinder": 20, "id": 2},
        {"cylinder": 180, "id": 3}
    ], 290, 20), # (180-50) + (180-20) = 130 + 160 = 290. Final en 20.
    (100, [
        {"cylinder": 150, "id": 1},
        {"cylinder": 50, "id": 2}
    ], 150, 50), # (150-100) + (150-50) = 50 + 100 = 150. Final en 50.
])
def test_scan_reference_logic(ref, head, requests, expected_mov, expected_final_pos):
    """Verifica movimiento total y posición final del cabezal."""
    mov, final_pos = ref.calculate_scan(requests, head)
    
    assert mov == expected_mov
    assert final_pos == expected_final_pos

# Casos para C-SCAN (Circular)
@pytest.mark.parametrize("head, requests, max_cyl, expected_mov, expected_final_pos", [
    (400, [
        {"cylinder": 450},
        {"cylinder": 10}
    ], 500, 110, 10), # (450-400) + (500-450) + 10 = 50 + 50 + 10 = 110. Final en 10.
])
def test_cscan_reference_logic(ref, head, requests, max_cyl, expected_mov, expected_final_pos):
    """Verifica el cálculo de C-SCAN con flyback."""
    mov, final_pos = ref.calculate_cscan(requests, head, max_cyl=max_cyl)
    
    assert mov == expected_mov
    assert final_pos == expected_final_pos

def test_empty_requests(ref):
    """Asegura manejo de listas vacías."""
    mov, final_pos = ref.calculate_scan([], 100)
    assert mov == 0
    assert final_pos == 100