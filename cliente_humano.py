# cliente_humano.py
from cliente_base import ClienteBase
from interfaz_grafica import InterfazJuego
import time


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


class ClienteHumano(ClienteBase):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.ui = InterfazJuego()
        self.running = True

    def handle_click(self, pos):
        if not self.game_state or self.game_state['game_over']: return
        if self.game_state['current_player'] != self.player_color: return

        row, col = self.ui.get_clicked_cell(pos)
        if row is not None:
            # Validar si el movimiento está en la lista de movimientos válidos
            valid_moves = [tuple(m) for m in self.game_state.get('valid_moves', [])]
            if (row, col) in valid_moves:
                self.send_move(row, col)
            else:
                print(f"❌ Movimiento inválido en ({row}, {col})")
    
    def on_quit(self):
        self.running = False
        self.disconnect("Usuario cerró la ventana")

    def run(self):
        self.connect()
        
        while self.running:
            # Manejar eventos de Pygame
            if not self.ui.run_event_loop(on_click=self.handle_click, on_quit=self.on_quit):
                break

            # Dibujar el estado actual
            if not self.connected or self.waiting_for_opponent:
                color_info = f"{'Negro' if self.player_color == 1 else 'Blanco'}" if self.player_color else ""
                self.ui.draw_waiting_screen(self.connection_status, color_info)
            else:
                self.ui.draw_game_state(self.game_state, self.player_color)
            
            self.ui.clock.tick(30)
        
        self.ui.quit()

if __name__ == "__main__":
    host = prompt_host("Ingresa la IP o nombre de host", "127.0.0.1")
    port = prompt_int("Ingresa el puerto", 5555, min_value=1, max_value=65535)

    print(f"Conectando cliente humano a {host}:{port}...")

    cliente = ClienteHumano(host, port)
    cliente.run()