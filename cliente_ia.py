import time
import numpy as np
from cliente_base import ClienteBase
from AgenteIA.AgenteJugador import AgenteJugador
from collections import namedtuple
from interfaz_grafica import InterfazJuego

ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')

class ClienteIA(ClienteBase):
    def __init__(self, host='127.0.0.1', port=5555, depth=3, use_optimized_weights=False, show_ui=False):
        super().__init__(host, port)
        self.depth = depth
        self.use_optimized_weights = use_optimized_weights
        self.show_ui = show_ui
        self.ui = None
        self.running = True
        self.agente = None
        self.on_message_received = self.custom_handle_message

    def on_quit(self):
        self.running = False
        self.disconnect("Usuario cerró la ventana")

    def custom_handle_message(self, message):
        msg_type = message.get('type')
        if msg_type in ['game_start', 'game_update']:
            print(f"[DEBUG CLIENTE IA] Recibió {msg_type}")
            
            # Verificación 4.1: game_state existe
            if not self.game_state:
                print("[DEBUG CLIENTE IA] ERROR: self.game_state es None o vacío.")
                return

            print(f"[DEBUG CLIENTE IA] game_over={self.game_state.get('game_over')}, "
                  f"current_player={self.game_state.get('current_player')}, "
                  f"my_color={self.player_color}")

            # Verificación 5: Chequeo de fin de juego usando self.game_state
            if self.game_state.get('game_over'):
                print("[DEBUG CLIENTE IA] El juego ha terminado según state.")
                return

            # Verificación 4: Comparación
            if self.game_state.get('current_player') == self.player_color:
                print(f"[DEBUG CLIENTE IA] ¡ES MI TURNO! Lanzando hacer_jugada()...")
                time.sleep(0.1)
                self.hacer_jugada()
            else:
                print("[DEBUG CLIENTE IA] No es mi turno.")

    def hacer_jugada(self):
        valid_moves = self.game_state.get('valid_moves', [])
        valid_moves_tuples = [tuple(m) for m in valid_moves]

        print(f"[DEBUG CLIENTE IA] valid_moves parseados a tuplas: {valid_moves_tuples}")
        
        if not valid_moves_tuples:
            print("🤖 IA: Sin movimientos válidos, el servidor procesará el turno.")
            return

        print(f"🤖 IA pensando... (Profundidad: {self.depth})")
        
        # Verificación 6: convertir_game_state_a_estado
        tablero = np.array(self.game_state['board'])
        estado_ia = ElEstado(
            jugador=self.player_color,
            get_utilidad=None,
            tablero=tablero,
            movidas=valid_moves_tuples
        )
        print(f"[DEBUG CLIENTE IA] Estado creado -> Jugador: {estado_ia.jugador}, Movidas: {len(estado_ia.movidas)}")

        if not self.agente:
            print(f"[DEBUG CLIENTE IA] Instanciando AgenteJugador por primera vez (Optimizados: {self.use_optimized_weights}).")
            self.agente = AgenteJugador(altura=self.depth, jugador_ia=self.player_color, use_optimized_weights=self.use_optimized_weights)
            
        self.agente.estado = estado_ia
        
        print("[DEBUG CLIENTE IA] Entrando a agente.programa() (MINIMAX)...")
        self.agente.programa()
        print("[DEBUG CLIENTE IA] Salió de agente.programa() exitosamente.")
        mejor_accion = self.agente.get_acciones()
        
        if mejor_accion:
            row, col = mejor_accion
            print(f"✅ IA decide mover a: ({row}, {col})")
            self.send_move(row, col)
        else:
            if valid_moves_tuples:
                fallback_move = valid_moves_tuples[0]
                self.send_move(fallback_move[0], fallback_move[1])

    def run(self):
        if not self.connect():
            return

        if self.show_ui:
            self.ui = InterfazJuego()

        try:
            while self.connected and self.running:
                if self.ui:
                    if not self.ui.run_event_loop(on_quit=self.on_quit):
                        break

                    if not self.connected or self.waiting_for_opponent:
                        color_info = f"{'Negro' if self.player_color == 1 else 'Blanco'}" if self.player_color else ""
                        self.ui.draw_waiting_screen(self.connection_status, color_info)
                    else:
                        self.ui.draw_game_state(self.game_state, self.player_color)

                    self.ui.clock.tick(30)
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⏹️  Deteniendo Cliente IA...")
        finally:
            self.disconnect()
            if self.ui:
                try:
                    self.ui.quit()
                except SystemExit:
                    pass
