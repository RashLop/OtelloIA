import os
import sys
import json
import numpy as np
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from servidor import GameServer
from AgenteIA.AgenteJugador import AgenteJugador, ElEstado
from heuristica_evaluacion_othello import FuncionEvaluacionOthello

def run_local_match(agent_black, agent_white):
    """
    Ejecuta una partida sin red usando el GameServer como motor local puro.
    Extremadamente rápido. Retorna (ganador, puntos_negro, puntos_blanco).
    """
    game = GameServer()  # Inicia tablero
    agents = {1: agent_black, 2: agent_white}
    
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
            
        estado = ElEstado(jugador=player, get_utilidad=None, tablero=game.board.copy(), movidas=valid_moves)
        agent.estado = estado
        agent.programa()
        move = agent.get_acciones()
        
        if move:
            game.make_move(move[0], move[1], player)
        else:
            game.make_move(valid_moves[0][0], valid_moves[0][1], player)

    black_score = np.sum(game.board == 1)
    white_score = np.sum(game.board == 2)
    return game.winner, black_score, white_score, game.board

class RandomAgent:
    def __init__(self, jugador_ia):
        self.jugador_ia = jugador_ia
        self.estado = None
        self.acciones_elegidas = None
    
    def programa(self):
        movidas = self.estado.movidas
        if movidas:
            import random
            self.acciones_elegidas = random.choice(movidas)
        else:
            self.acciones_elegidas = None
            
    def get_acciones(self):
        return self.acciones_elegidas

class OthelloGA:
    def __init__(self,
                 population_size=10, 
                 generations=10, 
                 mutation_rate=0.15, 
                 mutation_sigma=0.2, 
                 tournament_size=3,
                 elite_count=1,
                 games_per_individual=2,
                 search_depth=1): # Profundidad 1 para que el GA sea rápido en local
        
        self.pop_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.mutation_sigma = mutation_sigma
        self.tournament_size = tournament_size
        self.elite_count = elite_count
        self.games_per_individual = games_per_individual
        self.depth = search_depth
        
        self.keys = ['fichas', 'movilidad', 'esquinas', 'adyacentes', 'estabilidad', 'posicional']
        self.baseline_weights = {
            'fichas': 10.0,           
            'movilidad': 45.0,        
            'esquinas': 200.0,        
            'adyacentes': -50.0,      
            'estabilidad': 20.0,     
            'posicional': 15.0
        }
        
    def _create_individual(self):
        ind = {}
        for k, v in self.baseline_weights.items():
            ind[k] = v + np.random.normal(0, abs(v) * 0.5) 
            if k == 'adyacentes' and ind[k] > 0: ind[k] = -ind[k]
        return ind
        
    def _crossover(self, p1, p2):
        child = {}
        for k in self.keys:
            alpha = np.random.random()
            child[k] = alpha * p1[k] + (1 - alpha) * p2[k]  
        return child
        
    def _mutate(self, ind):
        mutated = ind.copy()
        for k in self.keys:
            if np.random.random() < self.mutation_rate:
                mutated[k] += np.random.normal(0, abs(self.baseline_weights[k]) * self.mutation_sigma)
                if k == 'adyacentes' and mutated[k] > 0: mutated[k] = -mutated[k]
        return mutated
        
    def evaluate_fitness(self, individual_weights):
        fitness = 0.0
        
        # 1. REGULARIZACIÓN (F): Castigo por desviaciones excesivas que producen pesos absurdos.
        # Evitamos que la IA abandone conceptos básicos del Othello matemático.
        reg_penalty = 0.0
        for k in self.keys:
            ind_val = individual_weights[k]
            base_val = self.baseline_weights[k]
            
            # Castigo severo si las esquinas dejan de ser lo más valioso
            if k == 'esquinas' and ind_val < 80:
                reg_penalty -= (80 - ind_val) * 10
            # Castigo severo si adyacentes pasa a ser positivo (regalar esquinas)
            if k == 'adyacentes' and ind_val > -10:
                reg_penalty -= (ind_val + 10) * 10
            # Regularización suave L2 hacia los baselines para frenar la inflación de números
            diff = abs(ind_val - base_val)
            reg_penalty -= (diff / max(abs(base_val), 1.0)) * 0.5
            
        fitness += reg_penalty
        
        wins = 0
        total_margin = 0
        total_corner_diff = 0
        total_danger = 0
        
        for i in range(self.games_per_individual):
            is_black = (i % 2 == 0)
            # Jugar contra Default la mitad de veces, contra Random la otra mitad
            against_random = (i >= self.games_per_individual / 2)
            
            evaluador_ind = FuncionEvaluacionOthello(player_ia=1 if is_black else 2, custom_weights=individual_weights)
            agente_ind = AgenteJugador(altura=self.depth, jugador_ia=1 if is_black else 2)
            agente_ind._evaluador = evaluador_ind
            
            if against_random:
                agente_rival = RandomAgent(jugador_ia=2 if is_black else 1)
            else:
                evaluador_rival = FuncionEvaluacionOthello(player_ia=2 if is_black else 1)
                agente_rival = AgenteJugador(altura=self.depth, jugador_ia=2 if is_black else 1)
                agente_rival._evaluador = evaluador_rival
            
            if is_black:
                winner, pts_black, pts_white, final_board = run_local_match(agente_ind, agente_rival)
                margin = pts_black - pts_white
                gane = (winner == 1)
                my_p = 1
            else:
                winner, pts_black, pts_white, final_board = run_local_match(agente_rival, agente_ind)
                margin = pts_white - pts_black
                gane = (winner == 2)
                my_p = 2
                
            # Extraer métricas de esquinas del tablero final
            my_corners = 0
            opp_corners = 0
            my_danger = 0
            corners = [(0,0), (0,7), (7,0), (7,7)]
            adjacents = {
                (0,0): [(0,1), (1,0), (1,1)],
                (0,7): [(0,6), (1,7), (1,6)],
                (7,0): [(6,0), (7,1), (6,1)],
                (7,7): [(7,6), (6,7), (6,6)]
            }
            opp_p = 3 - my_p
            for r, c in corners:
                if final_board[r][c] == my_p:
                    my_corners += 1
                elif final_board[r][c] == opp_p:
                    opp_corners += 1
                elif final_board[r][c] == 0:
                    for ar, ac in adjacents[(r,c)]:
                        if final_board[ar][ac] == my_p:
                            my_danger += 1
            
            total_corner_diff += (my_corners - opp_corners)
            total_danger += my_danger
                
            if gane:
                wins += 1
                total_margin += margin 
            elif winner == 0:
                wins += 0.5  # Empate
            else:
                total_margin += margin # Es negativo
                
        # 2. CÁLCULO DE FITNESS
        # A (Dominante): Tasa de victoria
        # B (Secundario): Margen final promedio de fichas
        # C (Muy importante): Diferencia de esquinas tomadas al final de la partida
        # D (Importante): Posiciones peligrosas retenidas (adyacentes a esquinas vacías)
        
        win_rate = wins / self.games_per_individual
        avg_margin = total_margin / self.games_per_individual
        avg_corner_diff = total_corner_diff / self.games_per_individual
        avg_danger = total_danger / self.games_per_individual
        
        A = 1000.0
        B = 2.0
        C = 50.0
        D = 30.0
        
        score_partidas = (A * win_rate) + (B * avg_margin) + (C * avg_corner_diff) - (D * avg_danger)
        fitness += score_partidas
        
        return fitness

    def run(self):
        print("🧬 Iniciando Algoritmo Genético (Modo Local Seguro)...")
        population = [self._create_individual() for _ in range(self.pop_size)]
        
        history = {
            "generations": [],
            "best_fitness": [],
            "avg_fitness": []
        }
        
        for gen in range(self.generations):
            print(f"\n--- Generación {gen+1}/{self.generations} ---")
            fitness_scores = []
            
            for i, ind in enumerate(population):
                fit = self.evaluate_fitness(ind)
                fitness_scores.append(fit)
                print(f"Ind. {i+1} -> Fitness: {fit:.2f}")
                
            sorted_indices = np.argsort(fitness_scores)[::-1]
            best_fitness = fitness_scores[sorted_indices[0]]
            avg_fitness = np.mean(fitness_scores)
            
            print(f"🏆 Mejor Fitness de Gen {gen+1}: {best_fitness:.2f} (Promedio: {avg_fitness:.2f})")
            
            history["generations"].append(gen + 1)
            history["best_fitness"].append(float(best_fitness))
            history["avg_fitness"].append(float(avg_fitness))
            
            new_population = [population[i] for i in sorted_indices[:self.elite_count]]
            
            while len(new_population) < self.pop_size:
                t1 = np.random.choice(self.pop_size, self.tournament_size, replace=False)
                p1_idx = t1[np.argmax([fitness_scores[i] for i in t1])]
                
                t2 = np.random.choice(self.pop_size, self.tournament_size, replace=False)
                p2_idx = t2[np.argmax([fitness_scores[i] for i in t2])]
                
                child = self._crossover(population[p1_idx], population[p2_idx])
                child = self._mutate(child)
                new_population.append(child)
                
            population = new_population

        best_ind = population[0] 
        print("\n✅ Entrenamiento terminado.")
        
        os.makedirs('ga', exist_ok=True)
        with open('ga/best_weights.json', 'w') as f:
            json.dump(best_ind, f, indent=4)
            
        with open('ga/ga_history.json', 'w') as f:
            json.dump(history, f, indent=4)
            
        print("💾 Mejores pesos guardados en 'ga/best_weights.json'")
        print("📊 Historial de entrenamiento guardado en 'ga/ga_history.json'")

if __name__ == "__main__":
    ga = OthelloGA()
    ga.run()
