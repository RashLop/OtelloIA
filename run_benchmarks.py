import os
import sys
import copy
import random
import time
import numpy as np

# Asegurar importes del proyecto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from servidor import GameServer
from AgenteIA.AgenteJugador import AgenteJugador, ElEstado

class RandomAgentLocal:
    """Agente sin heurística que escoge movimientos al azar rápidamente."""
    def __init__(self, jugador_ia):
        self.jugador_ia = jugador_ia
        self.estado = None
        self.acciones_elegidas = None
    
    def programa(self):
        movidas = self.estado.movidas
        if movidas:
            self.acciones_elegidas = random.choice(movidas)
        else:
            self.acciones_elegidas = None
            
    def get_acciones(self):
        return self.acciones_elegidas

def run_local_match_bench(agent_black, agent_white):
    """
    Ejecuta una partida local en memoria (sin red/sockets) usando el motor de GameServer.
    Retorna: winner (1, 2 o 0), margin (diferencia abs de fichas), tiempo_total.
    """
    game = GameServer()  
    agents = {1: agent_black, 2: agent_white}
    start_time = time.time()
    
    while not game.game_over:
        player = game.current_player
        agent = agents[player]
        
        valid_moves = game.get_valid_moves(player)
        if not valid_moves:
            game.current_player = 3 - player
            if not game.get_valid_moves(game.current_player):
                game.game_over = True
                game.determine_winner()
            continue
            
        estado = ElEstado(jugador=player, get_utilidad=None, tablero=copy.deepcopy(game.board), movidas=valid_moves)
        agent.estado = estado
        
        agent.programa()
        move = agent.get_acciones()
        
        if move:
            game.make_move(move[0], move[1], player)
        else:
            # Fallback a un movimiento válido
            game.make_move(valid_moves[0][0], valid_moves[0][1], player)

    end_time = time.time()
    b_score = np.sum(game.board == 1)
    w_score = np.sum(game.board == 2)
    
    return game.winner, abs(b_score - w_score), (end_time - start_time)

def get_agents(exp_type, is_black, depth=1):
    """Factory de agentes según el experimento."""
    if exp_type == 'random':
        return RandomAgentLocal(jugador_ia=1 if is_black else 2)
    elif exp_type == 'manual':
        return AgenteJugador(altura=depth, jugador_ia=1 if is_black else 2, use_optimized_weights=False)
    elif exp_type == 'genetica':
        return AgenteJugador(altura=depth, jugador_ia=1 if is_black else 2, use_optimized_weights=True)

def run_experiment(name, type_a, type_b, num_games=10, depth=1):
    print(f"\n" + "="*55)
    print(f" EXPERIMENTO: {name} ({num_games} partidas)")
    print(f" Agente A: {type_a.upper()} | Agente B: {type_b.upper()} | Profundidad: {depth}")
    print("="*55)
    
    wins_a = 0
    wins_b = 0
    draws = 0
    total_margin_a = 0
    total_time = 0
    
    for i in range(num_games):
        a_is_black = (i % 2 == 0)
        
        agent_a = get_agents(type_a, is_black=a_is_black, depth=depth)
        agent_b = get_agents(type_b, is_black=not a_is_black, depth=depth)
        
        agent_black = agent_a if a_is_black else agent_b
        agent_white = agent_b if a_is_black else agent_a
        
        try:
            winner, margin, time_spent = run_local_match_bench(agent_black, agent_white)
        except Exception as e:
            print(f"  ⚠️ Error aislando partida {i+1}: {e}. Saltando...")
            continue
            
        total_time += time_spent
        
        if (winner == 1 and a_is_black) or (winner == 2 and not a_is_black):
            wins_a += 1
            total_margin_a += margin
            color_a = "Negro" if a_is_black else "Blanco"
            print(f"  Partida {i+1}: Gana A ({color_a}) [Margen: +{margin} fichas]")
        elif (winner == 2 and a_is_black) or (winner == 1 and not a_is_black):
            wins_b += 1
            total_margin_a -= margin
            color_b = "Negro" if not a_is_black else "Blanco"
            print(f"  Partida {i+1}: Gana B ({color_b}) [Margen: +{margin} fichas]")
        else:
            draws += 1
            print(f"  Partida {i+1}: Empate")

    winrate_a = (wins_a / num_games) * 100 if num_games > 0 else 0
    avg_time = total_time / num_games if num_games > 0 else 0
    margin_a_wins = (total_margin_a / wins_a) if wins_a > 0 else 0
    
    print("\n  --- RESULTADOS ---")
    print(f"  Victorias A ({type_a}): {wins_a}")
    print(f"  Victorias B ({type_b}): {wins_b}")
    print(f"  Empates: {draws}")
    print(f"  Winrate A: {winrate_a:.1f}%")
    print(f"  Tiempo promedio por partida: {avg_time:.2f} s")
    print("="*55)
    
    return {
        "experiment": f"{name} (D{depth})",
        "agent_a": type_a,
        "agent_b": type_b,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "draws": draws,
        "winrate_a": winrate_a,
        "avg_time": avg_time,
        "margin_a": margin_a_wins
    }

if __name__ == '__main__':
    genetic_weights_path = os.path.join(os.path.dirname(__file__), 'ga', 'best_weights.json')
    if not os.path.exists(genetic_weights_path):
        print(f"⚠️ AVISO: No se encontró '{genetic_weights_path}'.")
        print("   La 'IA genética' usará sus pesos default como escudo protector automático.")
        print("   Para hacer la comparativa real completa, corre 'train_ga.py' antes.\n")
        
    games_per_depth = {
        2: 8,
        3: 8,
        4: 6,
        5: 4
    }
    
    print("\n🚀 INICIANDO BENCHMARK OTHELLO (Simulación Local Múltiples Profundidades) 🚀")
    
    results = []
    
    for prof, partidas in games_per_depth.items():
        print(f"\n====================== TESTEANDO PROFUNDIDAD {prof} ======================")
        results.append(run_experiment("Manual vs Random", "manual", "random", num_games=partidas, depth=prof))
        results.append(run_experiment("Genética vs Random", "genetica", "random", num_games=partidas, depth=prof))
        results.append(run_experiment("Genética vs Manual", "genetica", "manual", num_games=partidas, depth=prof))

    import json
    os.makedirs('ga', exist_ok=True)
    report_path = os.path.join(os.path.dirname(__file__), 'ga', 'benchmark_results.json')
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"\n✅ Resultados completos de los benchmarks guardados en '{report_path}' para graficado.")
