import sys
import threading
import time
from servidor import GameServer
from cliente_ia import ClienteIA

def run_server(host, port):
    print("Iniciando Servidor en hilo aislado...")
    server = GameServer(host, port)
    server.start()

def run_ia(host, port, depth):
    print(f"Iniciando Cliente IA automáticamente (Profundidad {depth})...")
    time.sleep(1) # Pequeña espera para asegurar que el server levantó
    client = ClienteIA(host, port, depth, use_optimized_weights=True)
    client.run()

if __name__ == "__main__":
    host = '127.0.0.1'
    port = 5555
    depth = 3
    
    # Manejo simple por sys.argv como se pidió, sin argparse complejo
    if len(sys.argv) > 1:
        try:
            depth = int(sys.argv[1])
        except ValueError:
            print("Argumento inválido para profundidad. Usando profundidad 3 por defecto.")

    print("=== OTHELLO: STARTING CORE (SERVER + IA) ===")
    
    # Levantar Servidor
    server_thread = threading.Thread(target=run_server, args=(host,port), daemon=True)
    server_thread.start()
    
    # Levantar Cliente IA
    ia_thread = threading.Thread(target=run_ia, args=(host,port,depth), daemon=True)
    ia_thread.start()
    
    try:
        # Loop principal activo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️  Deteniendo el programa madre...")
        sys.exit(0)
