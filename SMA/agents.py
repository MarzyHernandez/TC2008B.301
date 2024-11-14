# agents.py

from mesa import Agent
import random
from map import PARKINGS, DIRECTIONS 

class CarAgent(Agent):
    COLORS = ["blue", "orange", "purple", "pink", "cyan"]  

    def __init__(self, unique_id, model, destination, color_index):
        super().__init__(unique_id, model)
        self.destination = destination
        self.has_arrived = False
        self.start_parking = PARKINGS.get(self.pos, "Desconocido")
        self.destination_parking = PARKINGS.get(self.destination, "Desconocido")
        self.previous_position = None
        self.color = CarAgent.COLORS[color_index % len(CarAgent.COLORS)]
        print(f"Auto iniciado en estacionamiento {self.start_parking}, destino: {self.destination_parking}, color: {self.color}")

    # Verifica si la posición está dentro del grid
    def within_grid(self, pos):
        x, y = pos
        return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height

    # Posiciiones válidas en la celda actual
    def get_allowed_moves(self):
        """Obtiene las posiciones válidas en las direcciones permitidas para la celda actual."""
        allowed_directions = DIRECTIONS.get(self.pos, [])
        x, y = self.pos

        moves = []
        if 'up' in allowed_directions and self.within_grid((x, y + 1)):
            moves.append((x, y + 1))
        if 'down' in allowed_directions and self.within_grid((x, y - 1)):
            moves.append((x, y - 1))
        if 'right' in allowed_directions and self.within_grid((x + 1, y)):
            moves.append((x + 1, y))
        if 'left' in allowed_directions and self.within_grid((x - 1, y)):
            moves.append((x - 1, y))

        return moves

    # Verifica si se puede mover a la posición
    def can_move_to(self, pos):
        """Verifica si el movimiento es válido según el estado del semáforo en la posición"""
        if self.model.grid.is_cell_empty(pos):
            return True
        for agent in self.model.grid.get_cell_list_contents(pos):
            if isinstance(agent, TrafficLightAgent):
                if agent.state == "green":
                    return True
                elif agent.state == "yellow":
                    return random.choice([True, False])  # Avanza o se detiene de forma aleatoria en amarillo
        return False

    # Distancia  al destino
    def distance_to_destination(self, pos):
        """Calcula la distancia  desde una posición hasta el destino del auto."""
        return abs(pos[0] - self.destination[0]) + abs(pos[1] - self.destination[1])

    # Movimiento del auto
    def move(self):
        if self.has_arrived:
            return

        x, y = self.pos
        adjacent_positions = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        if self.destination in adjacent_positions:
            self.model.grid.move_agent(self, self.destination)
            print(f"Moviendo el auto directamente al destino: {self.destination}")
            self.has_arrived = True
            return

        possible_moves = self.get_allowed_moves()

        valid_moves = [
            pos for pos in possible_moves
            if self.can_move_to(pos) and pos != self.previous_position
        ]

        if not valid_moves:
            print(f"No hay movimientos válidos para el auto en {self.pos}. Esperando o evitando ciclo.")
            return

        best_move = min(valid_moves, key=lambda pos: self.distance_to_destination(pos))

        cell_agents = self.model.grid.get_cell_list_contents(best_move)
        if any(isinstance(agent, TrafficLightAgent) and agent.state == "red" for agent in cell_agents):
            print(f"Semáforo en rojo en {best_move}. Esperando.")
            return 

        primary_direction = DIRECTIONS.get(self.pos, [])[0] if DIRECTIONS.get(self.pos) else None
        primary_move = None

        if primary_direction == 'up':
            primary_move = (x, y + 1)
        elif primary_direction == 'down':
            primary_move = (x, y - 1)
        elif primary_direction == 'right':
            primary_move = (x + 1, y)
        elif primary_direction == 'left':
            primary_move = (x - 1, y)

        moves_options = [best_move]
        weights = [0.6]

        if primary_move in valid_moves and primary_move != best_move:
            moves_options.append(primary_move)
            weights.append(0.3)

        secondary_moves = [move for move in valid_moves if move not in moves_options]
        moves_options.extend(secondary_moves)
        weights.extend([0.1] * len(secondary_moves))

        chosen_move = random.choices(moves_options, weights=weights, k=1)[0]

        self.previous_position = self.pos
        self.model.grid.move_agent(self, chosen_move)
        print(f"Moviendo el auto a la posición elegida: {chosen_move}")

    def step(self):
        print(f"Posición actual del auto: {self.pos}")
        self.move()

# Agente semáforo
class TrafficLightAgent(Agent):
    def __init__(self, unique_id, model, position, green_time=10, yellow_time=3, red_time=10, is_green=True):
        super().__init__(unique_id, model)
        self.position = position
        self.green_time = green_time
        self.yellow_time = yellow_time
        self.red_time = red_time
        self.state = "green" if is_green else "red"
        self.timer = self.green_time if is_green else self.red_time

    # Cambio de color del semáforo
    def change_color(self):
        if self.state == "green":
            self.state = "yellow"
            self.timer = self.yellow_time
        elif self.state == "yellow":
            self.state = "red"
            self.timer = self.red_time
        elif self.state == "red":
            self.state = "green"
            self.timer = self.green_time

    def step(self):
        self.timer -= 1
        if self.timer <= 0:
            self.change_color()

# Edificios, estacionamientos y glorieta para el mapa
class StaticAgent(Agent):
    def __init__(self, unique_id, model, agent_type, color):
        super().__init__(unique_id, model)
        self.agent_type = agent_type  
        self.color = color 
