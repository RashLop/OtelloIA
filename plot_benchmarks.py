import json
import os
import re
import matplotlib.pyplot as plt
import numpy as np

def parse_experiment_data(data):
    parsed = {}
    for item in data:
        exp_name_full = item['experiment']
        # Buscar patrón como "Manual vs Random (D2)" o "(D3)"
        match = re.search(r'(.*) \(+D(\d+)\)+', exp_name_full)
        if not match:
            continue
            
        base_name = match.group(1).strip()
        depth = int(match.group(2))
        
        if base_name not in parsed:
            parsed[base_name] = {'depths': [], 'winrates': [], 'wins_a': [], 'wins_b': [], 'draws': []}
            
        parsed[base_name]['depths'].append(depth)
        parsed[base_name]['winrates'].append(item['winrate_a'])
        parsed[base_name]['wins_a'].append(item['wins_a'])
        parsed[base_name]['wins_b'].append(item['wins_b'])
        parsed[base_name]['draws'].append(item['draws'])
        
    for k in parsed.keys():
        sorted_indices = np.argsort(parsed[k]['depths'])
        parsed[k]['depths'] = [parsed[k]['depths'][i] for i in sorted_indices]
        parsed[k]['winrates'] = [parsed[k]['winrates'][i] for i in sorted_indices]
        parsed[k]['wins_a'] = [parsed[k]['wins_a'][i] for i in sorted_indices]
        parsed[k]['wins_b'] = [parsed[k]['wins_b'][i] for i in sorted_indices]
        parsed[k]['draws'] = [parsed[k]['draws'][i] for i in sorted_indices]
        
    return parsed

def plot_benchmarks():
    base_dir = os.path.dirname(__file__)
    report_path = os.path.join(base_dir, 'ga', 'benchmark_results.json')
    plots_dir = os.path.join(base_dir, 'ga', 'plots')
    
    if not os.path.exists(report_path):
        print(f"❌ No se encontró el reporte en: {report_path}")
        print("👉 Debes ejecutar 'python run_benchmarks.py' de nuevo para generar data compatible.")
        return

    os.makedirs(plots_dir, exist_ok=True)

    with open(report_path, 'r') as f:
        data = json.load(f)

    if not data:
        print("❌ JSON vacío.")
        return

    parsed = parse_experiment_data(data)
    if not parsed:
        print("❌ No se pudieron estructurar las profundidades. Tal vez tengas JSON viejo.")
        print("Borra 'benchmark_results.json' y corre 'python run_benchmarks.py' nuevamente.")
        return

    # ---------------------------------------------------------
    # 1. GRÁFICA DE WINRATE LINEAL (Comparativa multi-línea)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    colors = ['#1f77b4', '#9467bd', '#2ca02c'] 
    markers = ['o', 's', '^']
    
    unique_depths = list(set(d for m in parsed.values() for d in m['depths']))
    unique_depths.sort()
    
    for idx, (exp_name, metrics) in enumerate(parsed.items()):
        plt.plot(metrics['depths'], metrics['winrates'], marker=markers[idx % len(markers)],
                 color=colors[idx % len(colors)], label=exp_name, linewidth=2.5, markersize=8)
                 
    plt.title('Estabilidad del Winrate por Profundidad', fontsize=15, fontweight='bold')
    plt.xlabel('Profundidad Minimax (Depth)', fontsize=12)
    plt.ylabel('Winrate del Agente A (%)', fontsize=12)
    plt.ylim(-5, 110)
    plt.xticks(unique_depths, [f'Depth {d}' for d in unique_depths], fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    
    p1 = os.path.join(plots_dir, 'winrate_por_profundidad.png')
    plt.savefig(p1, bbox_inches='tight')
    plt.close()
    
    # ---------------------------------------------------------
    # 2. GRÁFICAS SEPARADAS DE DISTRIBUCIÓN
    # ---------------------------------------------------------
    for exp_name, metrics in parsed.items():
        depths = metrics['depths']
        x = np.arange(len(depths))
        width = 0.25
        
        plt.figure(figsize=(8, 5.5))
        b1 = plt.bar(x - width, metrics['wins_a'], width, label='Victorias Agente A', color='#2ca02c', alpha=0.9)
        b2 = plt.bar(x, metrics['draws'], width, label='Empates', color='#7f7f7f', alpha=0.9)
        b3 = plt.bar(x + width, metrics['wins_b'], width, label='Victorias Rival B', color='#d62728', alpha=0.9)
        
        plt.ylabel('Cantidad de Partidas', fontsize=12)
        plt.title(f'Distribución de Resultados:\n{exp_name.upper()}', fontsize=14, fontweight='bold')
        plt.xticks(x, [f'Depth {d}' for d in depths], fontsize=11)
        
        # Ajuste inteligente de altura para que los números no se corten
        max_y = max(max(metrics['wins_a']), max(metrics['wins_b']), max(metrics['draws']))
        plt.ylim(0, max_y + (max_y * 0.15) + 1)
        
        plt.legend(fontsize=10, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        
        for rects in [b1, b2, b3]:
            for rect in rects:
                h = rect.get_height()
                if h > 0:
                    plt.annotate(f'{int(h)}', xy=(rect.get_x() + rect.get_width() / 2, h),
                                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
        
        safe_name = exp_name.lower().replace(" ", "_")
        p_dist = os.path.join(plots_dir, f'distribucion_{safe_name}.png')
        plt.savefig(p_dist, bbox_inches='tight')
        plt.close()

    print(f"\n✅ Gráficas profesionales guardadas en la carpeta: {plots_dir}")
    print("  📂 winrate_por_profundidad.png")
    for exp_name in parsed.keys():
        print(f"  📂 distribucion_{exp_name.lower().replace(' ', '_')}.png")
    print("\nTip: Revísalas desde tu explorador de archivos para enviarlas como reporte visual limpio.")

if __name__ == '__main__':
    plot_benchmarks()
