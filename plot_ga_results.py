import json
import os
import matplotlib.pyplot as plt

def plot_history():
    history_file = os.path.join(os.path.dirname(__file__), 'ga', 'ga_history.json')
    
    if not os.path.exists(history_file):
        print(f"❌ No se encontró el archivo de historial en: {history_file}")
        print("👉 Asegúrate de ejecutar un entrenamiento primero (e.g., 'python train_ga.py').")
        return

    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except Exception as e:
        print(f"❌ Error al leer el historial: {e}")
        return

    generations = history.get('generations', [])
    best_fitness = history.get('best_fitness', [])
    avg_fitness = history.get('avg_fitness', [])

    if not generations:
        print("❌ El historial está vacío.")
        return

    # Crear la figura
    plt.figure(figsize=(10, 6))
    
    # Dibujar las lineas
    plt.plot(generations, best_fitness, marker='o', linestyle='-', color='b', label='Mejor Fitness', linewidth=2)
    plt.plot(generations, avg_fitness, marker='s', linestyle='--', color='orange', label='Fitness Promedio', linewidth=2)
    
    # Configuración y estilos
    plt.title('Evolución del Algoritmo Genético - Othello AI', fontsize=14, fontweight='bold')
    plt.xlabel('Generación', fontsize=12)
    plt.ylabel('Fitness Score', fontsize=12)
    plt.xticks(generations) 
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(fontsize=12)
    
    # Guardar la imagen localmente
    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), 'ga', 'ga_evolution.png')
    plt.savefig(plot_path)
    
    print(f"✅ Gráfico guardado exitosamente en: {plot_path}")
    print("📈 Abriendo visor interactivo...")
    
    plt.show()

if __name__ == '__main__':
    plot_history()
