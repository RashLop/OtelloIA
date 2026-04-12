import argparse
from ga.genetic_algorithm import OthelloGA

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenamiento de Pesos Heurísticos usando Algoritmo Genético")
    parser.add_argument('--generations', type=int, default=10, help="Número de generaciones")
    parser.add_argument('--population', type=int, default=10, help="Tamaño de la población")
    parser.add_argument('--depth', type=int, default=1, help="Profundidad de búsqueda en los simulacros")
    parser.add_argument('--games', type=int, default=2, help="Juegos por individuo")
    args = parser.parse_args()

    print("=== OTHELLO: INICIANDO ENTRENAMIENTO GENÉTICO ===")
    
    ga = OthelloGA(
        population_size=args.population,
        generations=args.generations,
        search_depth=args.depth,
        games_per_individual=args.games
    )
    ga.run()
