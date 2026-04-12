import os
import sys

# Permite cargar el módulo de AgenteIA fácilmente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from AgenteIA.AgenteJugador import ElEstado

def game_state_to_el_estado(game_state, player_color):
    """
    Convierte el game_state JSON que envía el servidor a un objeto ElEstado
    que puede ser leído por el AgenteJugador para el Minimax.
    """
    tablero = np.array(game_state['board'])
    valid_moves = game_state['valid_moves']
    
    # Valid_moves se recibe del JSON como listas de listas ej: [[1,2], [3,4]], 
    # necesitamos que sean tuplas para el Agente: [(1,2), (3,4)]
    valid_moves_tuples = [(int(m[0]), int(m[1])) for m in valid_moves]
    
    return ElEstado(
        jugador=player_color,
        get_utilidad=None,
        tablero=tablero,
        movidas=valid_moves_tuples
    )
