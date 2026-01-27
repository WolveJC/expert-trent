class ScanReference:
    """
    Implementación de referencia en Python para validar la precisión 
    del motor de alto rendimiento C++.
    """

    @staticmethod
    def calculate_scan(requests: list, initial_head: int, direction_up: bool = True):
        """
        Calcula el movimiento total usando el algoritmo del elevador (SCAN).
        """
        if not requests:
            return 0, initial_head
        
        # Separar solicitudes en dos grupos respecto a la posición actual
        left = sorted([r['cylinder'] for r in requests if r['cylinder'] < initial_head], reverse=True)
        right = sorted([r['cylinder'] for r in requests if r['cylinder'] >= initial_head])
        
        movement = 0
        current_pos = initial_head

        # Lógica de barrido bidireccional
        if direction_up:
            # Primero hacia arriba, luego hacia abajo
            for cyl in right:
                movement += abs(cyl - current_pos)
                current_pos = cyl
            for cyl in left:
                movement += abs(cyl - current_pos)
                current_pos = cyl
        else:
            # Primero hacia abajo, luego hacia arriba
            for cyl in left:
                movement += abs(cyl - current_pos)
                current_pos = cyl
            for cyl in right:
                movement += abs(cyl - current_pos)
                current_pos = cyl
                
        return movement, current_pos

    @staticmethod
    def calculate_cscan(requests: list, initial_head: int, max_cyl: int):
        """
        Calcula el movimiento total usando C-SCAN (Circular SCAN).
        Este algoritmo solo sirve en una dirección y salta al inicio.
        """
        if not requests:
            return 0, initial_head

        sorted_reqs = sorted([r['cylinder'] for r in requests])
        
        # Encontrar punto de corte (primer cilindro >= cabezal)
        right = [cyl for cyl in sorted_reqs if cyl >= initial_head]
        left = [cyl for cyl in sorted_reqs if cyl < initial_head]
        
        movement = 0
        current_pos = initial_head

        # 1. Servir hacia el final del disco
        for cyl in right:
            movement += abs(cyl - current_pos)
            current_pos = cyl

        # 2. Salto circular (si hay peticiones pendientes al inicio)
        if left:
            # El salto cuenta como movimiento: del final al cilindro 0 + hasta la primera petición
            movement += (max_cyl - current_pos) + left[0]
            current_pos = left[0]
            
            # 3. Servir el resto de las peticiones desde el inicio
            for cyl in left[1:]:
                movement += abs(cyl - current_pos)
                current_pos = cyl

        return movement, current_pos