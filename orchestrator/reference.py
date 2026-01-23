class ScanReference:
    """Implementación de referencia para validar el motor C++"""
    
    @staticmethod
    def calculate_scan(requests: list, initial_head: int):
        if not requests:
            return 0, initial_head
        
        # Ordenar solicitudes por cilindro
        sorted_reqs = sorted(requests, key=lambda x: x['cylinder'])
        
        movement = 0
        current_pos = initial_head
        
        # Simulación de un barrido simple (One-way para validación Fase 1)
        for req in sorted_reqs:
            movement += abs(req['cylinder'] - current_pos)
            current_pos = req['cylinder']
            
        return movement, current_pos