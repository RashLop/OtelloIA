import json
import os
import re
import matplotlib.pyplot as plt
import numpy as np

def parse_experiment_data(data):
    parsed = {}
    for item in data:
        exp_name_full = item['experiment']
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

def build_dashboard():
    base_dir = os.path.dirname(__file__)
    report_path = os.path.join(base_dir, 'ga', 'benchmark_results.json')
    plots_dir = os.path.join(base_dir, 'ga', 'plots')
    
    if not os.path.exists(report_path):
        print(f"❌ No se encontró el reporte en: {report_path}")
        return

    os.makedirs(plots_dir, exist_ok=True)

    with open(report_path, 'r') as f:
        data = json.load(f)

    parsed = parse_experiment_data(data)
    if not parsed:
        print("❌ JSON incorrecto o sin datos de profundidad.")
        return

    # Definir diseño del Dashboard
    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.2)
    
    ax1 = fig.add_subplot(gs[0, :])   # Top: Todo el ancho para el Winrate
    ax2 = fig.add_subplot(gs[1, 0])   # Bottom Left: Genetica vs Manual
    ax3 = fig.add_subplot(gs[1, 1])   # Bottom Right: Genetica vs Random
    
    unique_depths = list(set(d for m in parsed.values() for d in m['depths']))
    unique_depths.sort()
    
    # -------------------------------------------------------------
    # 1. AX1: Winrate General (Líneas)
    # -------------------------------------------------------------
    # Colores base: Azul, Morado, Verde (idénticos a las imágenes estáticas)
    colors = ['#1f77b4', '#9467bd', '#2ca02c'] 
    markers = ['o', 's', '^']
    
    for idx, (exp_name, metrics) in enumerate(parsed.items()):
        ax1.plot(metrics['depths'], metrics['winrates'], marker=markers[idx % len(markers)],
                 color=colors[idx % len(colors)], label=exp_name, linewidth=2.5, markersize=8)
                 
    ax1.set_title('Resumen Global: Evolución del Winrate por Profundidad', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Winrate del Agente A (%)', fontsize=11)
    ax1.set_ylim(-5, 110)
    ax1.set_xticks(unique_depths)
    ax1.set_xticklabels([f'Depth {d}' for d in unique_depths], fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=10, loc='lower right')
    
    # -------------------------------------------------------------
    # Func Helper para Partidas Individuales
    # -------------------------------------------------------------
    def plot_dist(ax, metrics, title):
        depths = metrics['depths']
        x = np.arange(len(depths))
        width = 0.25
        
        b1 = ax.bar(x - width, metrics['wins_a'], width, label='Victorias', color='#2ca02c', alpha=0.9)
        b2 = ax.bar(x, metrics['draws'], width, label='Empates', color='#7f7f7f', alpha=0.9)
        b3 = ax.bar(x + width, metrics['wins_b'], width, label='Derrotas', color='#d62728', alpha=0.9)
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f'D{d}' for d in depths], fontsize=10)
        ax.set_ylabel('Num. Partidas')
        
        max_y = max(max(metrics['wins_a']), max(metrics['wins_b']), max(metrics['draws']))
        ax.set_ylim(0, max_y + (max_y * 0.20) + 1)
        ax.legend(fontsize=9, loc='upper left')
        
        for rects in [b1, b2, b3]:
            for rect in rects:
                h = rect.get_height()
                if h > 0:
                    ax.annotate(f'{int(h)}', xy=(rect.get_x() + rect.get_width() / 2, h),
                                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=9)

    # -------------------------------------------------------------
    # 2. AX2: Genética vs Manual (Competencia Principal)
    # -------------------------------------------------------------
    if "Genética vs Manual" in parsed:
        plot_dist(ax2, parsed["Genética vs Manual"], "🔴 Competencia Crítica:\nGenética vs Manual (Base)")

    # -------------------------------------------------------------
    # 3. AX3: Genética vs Random (Control de Calidad)
    # -------------------------------------------------------------
    if "Genética vs Random" in parsed:
        plot_dist(ax3, parsed["Genética vs Random"], "🟢 Control de Baseline:\nGenética vs Random")
        
        
    plt.suptitle("📊 DASHBOARD MAESTRO: RENDIMIENTO DE AGENTES OTHELLO", fontsize=16, fontweight='bold', y=0.95)
    
    dash_path = os.path.join(plots_dir, 'dashboard_resumen.png')
    plt.savefig(dash_path, bbox_inches='tight', dpi=150)
    
    print(f"✅ Dashboard generado exitosamente y guardado estáticamente en: {dash_path}")
    print("📈 Abriendo visor interactivo...")
    plt.show()

if __name__ == '__main__':
    build_dashboard()
