import sys
import threading
import time
from servidor import GameServer
from cliente_ia import ClienteIA

def run_server(host, port):
    print("Iniciando Servidor en hilo aislado...")
    server = GameServer(host, port)
    server.start()

def run_ia(host, port, depth, show_ui=False, use_optimized_weights=True):
    mode_label = "optimizados" if use_optimized_weights else "manuales"
    print(f"Iniciando Cliente IA automáticamente (Profundidad {depth}, pesos {mode_label})...")
    time.sleep(1) # Pequeña espera para asegurar que el server levantó
    client = ClienteIA(host, port, depth, use_optimized_weights=use_optimized_weights, show_ui=show_ui)
    client.run()


def run_human(host, port):
    print("Iniciando Cliente Humano...")
    from cliente_humano import ClienteHumano
    client = ClienteHumano(host, port)
    client.run()


def prompt_int(message, default_value, min_value=None, max_value=None):
    while True:
        raw_value = input(f"{message} [{default_value}]: ").strip()
        if not raw_value:
            return default_value

        try:
            value = int(raw_value)
        except ValueError:
            print("Ingresa un numero valido.")
            continue

        if min_value is not None and value < min_value:
            print(f"Ingresa un valor mayor o igual a {min_value}.")
            continue

        if max_value is not None and value > max_value:
            print(f"Ingresa un valor menor o igual a {max_value}.")
            continue

        return value


def prompt_host(message, default_value):
    raw_value = input(f"{message} [{default_value}]: ").strip()
    return raw_value or default_value


def prompt_yes_no(message, default_value=True):
    default_label = "s" if default_value else "n"

    while True:
        raw_value = input(f"{message} [{default_label}]: ").strip().lower()
        if not raw_value:
            return default_value

        if raw_value in ["s", "si", "sí", "y", "yes"]:
            return True

        if raw_value in ["n", "no"]:
            return False

        print("Responde s o n.")


def prompt_weight_mode():
    options = {
        "1": "Pesos optimizados",
        "2": "Pesos manuales"
    }

    while True:
        print("\n=== CONFIGURACION DE PESOS IA ===")
        for key, label in options.items():
            suffix = " (por defecto)" if key == "1" else ""
            print(f"{key}. {label}{suffix}")

        choice = input("Selecciona el tipo de pesos [1]: ").strip() or "1"
        if choice in options:
            return choice == "1"

        print("Opcion invalida. Elige 1 o 2.")


def prompt_mode():
    options = {
        "1": "Solo servidor",
        "2": "Solo agente IA",
        "3": "Solo cliente humano",
        "4": "Servidor + agente IA"
    }

    while True:
        print("\n=== OTHELLO LAUNCHER ===")
        for key, label in options.items():
            suffix = " (por defecto)" if key == "4" else ""
            print(f"{key}. {label}{suffix}")

        choice = input("Selecciona una opcion [4]: ").strip() or "4"
        if choice in options:
            return choice

        print("Opcion invalida. Elige 1, 2, 3 o 4.")


if __name__ == "__main__":
    mode = prompt_mode()
    host = prompt_host("Ingresa la IP o nombre de host", "127.0.0.1")
    port = prompt_int("Ingresa el puerto", 5555, min_value=1, max_value=65535)

    print(f"Red/IP configurada: {host}")
    print(f"Puerto configurado: {port}")

    if mode == "1":
        print("Modo seleccionado: Solo servidor")
        run_server(host, port)

    elif mode == "2":
        print("Modo seleccionado: Solo agente IA")
        depth = prompt_int("Ingresa la profundidad de la IA", 3, min_value=1)
        show_ui = prompt_yes_no("Mostrar interfaz grafica de la IA", True)
        use_optimized_weights = prompt_weight_mode()
        run_ia(host, port, depth, show_ui=show_ui, use_optimized_weights=use_optimized_weights)

    elif mode == "3":
        print("Modo seleccionado: Solo cliente humano")
        run_human(host, port)

    elif mode == "4":
        print("Modo seleccionado: Servidor + agente IA")
        depth = prompt_int("Ingresa la profundidad de la IA", 3, min_value=1)
        show_ui = prompt_yes_no("Mostrar interfaz grafica de la IA", True)
        use_optimized_weights = prompt_weight_mode()

        server_thread = threading.Thread(target=run_server, args=(host, port), daemon=True)
        server_thread.start()

        try:
            run_ia(host, port, depth, show_ui=show_ui, use_optimized_weights=use_optimized_weights)
        except KeyboardInterrupt:
            print("\n⏹️  Deteniendo el programa madre...")
            sys.exit(0)
