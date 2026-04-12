from AgenteIA.Agente import Agente
from collections import namedtuple
import time
import numpy as np

ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')

class AgenteJugador(Agente):
    def __init__(self, altura=3, jugador_ia=2):
        """
        Args:
            altura: Profundidad del árbol de búsqueda para Alpha-Beta
            jugador_ia: El ID del jugador que representa la IA (1=Negro, 2=Blanco)
                        Por convención, 2=Blanco (recomendado)
        """
        Agente.__init__(self)
        self.estado = None
        self.altura = altura
        self.tecnica = "podaalfabeta"  # Por defecto
        self.jugador_ia = jugador_ia   # IMPORTANTE: Asignado una sola vez en __init__
        
        # Importar y configurar la heurística aquí para evitar imports circulares
        from heuristica_evaluacion_othello import FuncionEvaluacionOthello
        self._evaluador = FuncionEvaluacionOthello(player_ia=jugador_ia)

    def jugadas(self, estado):
        return estado.movidas

    def get_utilidad(self, estado, jugador):
        return self.funcion_evaluacion(estado)

    def testTerminal(self, estado):
        return len(estado.movidas) == 0

    def getResultado(self, estado, m):
        import copy
        tablero_nuevo = copy.deepcopy(estado.tablero)
        row, col = m
        jugador = estado.jugador
        tablero_nuevo[row][col] = jugador
        
        # Voltear fichas
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent = 3 - jugador
        for dr, dc in directions:
            r, c = row + dr, col + dc
            to_flip = []
            while 0 <= r < 8 and 0 <= c < 8 and tablero_nuevo[r][c] == opponent:
                to_flip.append((r, c))
                r += dr
                c += dc
            if 0 <= r < 8 and 0 <= c < 8 and tablero_nuevo[r][c] == jugador:
                for flip_row, flip_col in to_flip:
                    tablero_nuevo[flip_row][flip_col] = jugador
        
        # Calcular movidas para el siguiente jugador
        siguiente_jugador = 3 - jugador
        movidas_siguientes = self._obtener_movidas(tablero_nuevo, siguiente_jugador)
        
        # Si el siguiente no tiene movidas, le toca al mismo (pase de turno)
        if not movidas_siguientes:
            siguiente_jugador = jugador
            movidas_siguientes = self._obtener_movidas(tablero_nuevo, siguiente_jugador)
            
        return ElEstado(jugador=siguiente_jugador, get_utilidad=None, tablero=tablero_nuevo, movidas=movidas_siguientes)
        
    def _obtener_movidas(self, tablero, player):
        movidas = []
        opponent = 3 - player
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for r in range(8):
            for c in range(8):
                if tablero[r][c] != 0: continue
                es_valido = False
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    tiene_contrario = False
                    while 0 <= nr < 8 and 0 <= nc < 8 and tablero[nr][nc] == opponent:
                        tiene_contrario = True
                        nr += dr
                        nc += dc
                    if tiene_contrario and 0 <= nr < 8 and 0 <= nc < 8 and tablero[nr][nc] == player:
                        es_valido = True
                        break
                if es_valido:
                    movidas.append((r, c))
        return movidas

    def funcion_evaluacion(self, estado):
        return self._evaluador.evaluar(estado)

    def podaAlphaBeta_eval(self, estado):
        mejor_score = -float('inf')
        beta = float('inf')
        self.nodos_explorados = 0
        self.podas_realizadas = 0
        
        def max_value(e, alpha, beta, profundidad):
            self.nodos_explorados += 1
            if self.testTerminal(e) or profundidad >= self.altura:
                return self.funcion_evaluacion(e)
            v = -float('inf')
            for accion in self.jugadas(e):
                v = max(v, min_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v >= beta: 
                    self.podas_realizadas += 1
                    return v
                alpha = max(alpha, v)
            return v

        def min_value(e, alpha, beta, profundidad):
            self.nodos_explorados += 1
            if self.testTerminal(e) or profundidad >= self.altura:
                return self.funcion_evaluacion(e)
            v = float('inf')
            for accion in self.jugadas(e):
                v = min(v, max_value(self.getResultado(e, accion), alpha, beta, profundidad + 1))
                if v <= alpha:
                    self.podas_realizadas += 1
                    return v
                beta = min(beta, v)
            return v

        mejor_accion = None
        
        # Si no hay movidas para este jugador pero el juego no ha terminado
        # (se maneja fuera de aquí, pero por seguridad)
        if not self.jugadas(estado):
            return None
            
        for accion in self.jugadas(estado):
            # Envolver en try-except por si falla internamente
            try:
                v = min_value(self.getResultado(estado, accion), mejor_score, beta, 1)
                if v > mejor_score:
                    mejor_score = v
                    mejor_accion = accion
            except Exception as e:
                print(f"[DEBUG MINIMAX] Ocurrió un error min_value con accion {accion}: {e}")
        
        self.valor_minimax = mejor_score
        return mejor_accion

    def mide_tiempo(funcion):
        def funcion_medida(self, *args, **kwargs):
            inicio = time.time()
            c = funcion(self, *args, **kwargs)
            self.tiempo_decision = time.time() - inicio
            return c
        return funcion_medida

    @mide_tiempo
    def programa(self):
        if not self.estado.movidas:
            self.set_acciones(None)
            return
        
        accion = self.podaAlphaBeta_eval(self.estado)
        self.set_acciones(accion)
        
    def obtener_metricas_busqueda(self):
        return {
            "nodos_explorados": getattr(self, "nodos_explorados", 0),
            "podas_realizadas": getattr(self, "podas_realizadas", 0),
            "tiempo_decision": getattr(self, "tiempo_decision", 0.0),
            "valor_minimax": getattr(self, "valor_minimax", 0.0)
        }