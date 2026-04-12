import numpy as np
from typing import Tuple

# MATRIZ DE PESOS POSICIONALES ESTÁNDAR PARA OTHELLO 8x8
POSITION_WEIGHTS = np.array([
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,   5,   1,   1,   5,  -2,  10],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [  5,  -2,   1,   0,   0,   1,  -2,   5],
    [ 10,  -2,   5,   1,   1,   5,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100],
], dtype=np.float32)

# Posiciones especiales
CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
CORNER_ADJACENT = [(0, 1), (1, 0), (1, 1),  
                   (0, 6), (1, 6), (1, 7),  
                   (6, 0), (6, 1), (7, 1),  
                   (6, 6), (6, 7), (7, 6)]  


class FuncionEvaluacionOthello:
    
    WEIGHTS = {
        'fichas': 10,           
        'movilidad': 45,        
        'esquinas': 200,        
        'adyacentes': -50,      
        'estabilidad': 20,     
        'posicional': 15,       
    }
    

    PHASE_FACTORS = {
        'apertura': {'fichas': 0.3, 'movilidad': 1.3, 'posicional': 1.5},   # Movidas 1-15
        'medio': {'fichas': 0.7, 'movilidad': 1.0, 'posicional': 1.0},      # Movidas 15-50
        'final': {'fichas': 2.0, 'movilidad': 0.5, 'posicional': 0.3},      # Movidas 50-60
    }
    
    def __init__(self, player_ia: int = 2):
        self.jugador_ia = player_ia
        self.opponent_id = 3 - player_ia  # 1 si IA es 2, 2 si IA es 1
    
    def evaluar(self, estado) -> float:
        tablero = estado.tablero
        
        # Si es estado terminal, retorna la utilidad final
        if not estado.movidas:
            return self._utilidad_final(tablero)
        
        # Calcular fase de juego
        fase = self._calcular_fase(tablero)
        
        # Inicializar score
        evaluacion = 0
        
        score_fichas = self._evaluar_fichas(tablero)
        factor = self.PHASE_FACTORS[fase]['fichas']
        evaluacion += score_fichas * factor * self.WEIGHTS['fichas']
        
        score_movilidad = self._evaluar_movilidad(estado)
        factor = self.PHASE_FACTORS[fase]['movilidad']
        evaluacion += score_movilidad * factor * self.WEIGHTS['movilidad']
        
        score_esquinas = self._evaluar_esquinas(tablero)
        evaluacion += score_esquinas * self.WEIGHTS['esquinas']
        
        score_adyacentes = self._evaluar_adyacentes(tablero)
        evaluacion += score_adyacentes * self.WEIGHTS['adyacentes']
        
        score_estabilidad = self._evaluar_estabilidad(tablero)
        evaluacion += score_estabilidad * self.WEIGHTS['estabilidad']
        
        score_posicional = self._evaluar_posicional(tablero)
        factor = self.PHASE_FACTORS[fase]['posicional']
        evaluacion += score_posicional * factor * self.WEIGHTS['posicional']
        
        return evaluacion
    
    
    def _evaluar_fichas(self, tablero: np.ndarray) -> float:
        fichas_ia = np.sum(tablero == self.jugador_ia)
        fichas_rival = np.sum(tablero == self.opponent_id)
        
        total_fichas = fichas_ia + fichas_rival
        if total_fichas == 0:
            return 0
        
        # Normalizar: resultado entre -1 y +1
        diferencia = (fichas_ia - fichas_rival) / total_fichas
        return diferencia
    
    def _evaluar_movilidad(self, estado) -> float:
        mis_movidas = len(estado.movidas)
        
        # Calcular movidas del rival sin modificar el estado
        rival_id = 3 - estado.jugador
        tablero = estado.tablero
        
        # Opciones del rival: simular cambio de turno
        tus_movidas = len(self._obtener_movidas_validas(tablero, rival_id))
        
        total_movidas = mis_movidas + tus_movidas
        if total_movidas == 0:
            return 0
        
        # Diferencia normalizada
        diferencia = (mis_movidas - tus_movidas) / total_movidas
        return diferencia
    
    def _evaluar_esquinas(self, tablero: np.ndarray) -> float:
        score = 0
        for r, c in CORNERS:
            celda = tablero[r, c]
            if celda == self.jugador_ia:
                score += 1
            elif celda == self.opponent_id:
                score -= 1
        return float(score)
    
    def _evaluar_adyacentes(self, tablero: np.ndarray) -> float:
        penalizacion = 0
        
        # Para cada esquina vacía, penalizar las fichas adyacentes
        for r, c in CORNERS:
            if tablero[r, c] == 0:  # Esquina vacía
                # Penalizar fichas adyacentes de la IA
                for adj_r, adj_c in CORNER_ADJACENT:
                    if (0 <= adj_r < 8 and 0 <= adj_c < 8 and
                        tablero[adj_r, adj_c] == self.jugador_ia):
                        penalizacion -= 1  # negativo porque es malo
        
        return float(penalizacion)
    
    def _evaluar_estabilidad(self, tablero: np.ndarray) -> float:

        fichas_ia_borde = 0
        fichas_rival_borde = 0
        
        # Borde = fila 0, fila 7, col 0, col 7
        for i in range(8):
            for j in range(8):
                if i == 0 or i == 7 or j == 0 or j == 7:
                    if tablero[i, j] == self.jugador_ia:
                        fichas_ia_borde += 1
                    elif tablero[i, j] == self.opponent_id:
                        fichas_rival_borde += 1
        
        diferencia = fichas_ia_borde - fichas_rival_borde
        return float(diferencia)
    
    def _evaluar_posicional(self, tablero: np.ndarray) -> float:

        score = 0
        for i in range(8):
            for j in range(8):
                if tablero[i, j] == self.jugador_ia:
                    score += POSITION_WEIGHTS[i, j]
                elif tablero[i, j] == self.opponent_id:
                    score -= POSITION_WEIGHTS[i, j]
        
        return float(score)
    
    # ========================= AUXILIARES =========================
    
    def _calcular_fase(self, tablero: np.ndarray) -> str:

        fichas_totales = np.sum(tablero != 0)
        
        if fichas_totales <= 20:
            return 'apertura'
        elif fichas_totales <= 52:
            return 'medio'
        else:
            return 'final'
    
    def _utilidad_final(self, tablero: np.ndarray) -> float:

        fichas_ia = np.sum(tablero == self.jugador_ia)
        fichas_rival = np.sum(tablero == self.opponent_id)
        
        diferencia = fichas_ia - fichas_rival
        
        if diferencia > 0:
            return 10000 + diferencia  # IA gana
        elif diferencia < 0:
            return -10000 + diferencia  # IA pierde
        else:
            return 0  # Empate
    
    def _obtener_movidas_validas(self, tablero: np.ndarray, player: int):
        movidas = []
        opponent = 3 - player
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for r in range(8):
            for c in range(8):
                if tablero[r, c] != 0:
                    continue
                
                # Buscar en 8 direcciones
                es_valido = False
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    tiene_contrario = False
                    
                    while 0 <= nr < 8 and 0 <= nc < 8 and tablero[nr, nc] == opponent:
                        tiene_contrario = True
                        nr += dr
                        nc += dc
                    
                    if (tiene_contrario and 0 <= nr < 8 and 0 <= nc < 8 and
                        tablero[nr, nc] == player):
                        es_valido = True
                        break
                
                if es_valido:
                    movidas.append((r, c))
        
        return movidas


