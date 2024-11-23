from mesa import Agent
import random
from map.map import PARKINGS, DIRECTIONS


from mesa import Agent
import random
from map.map import PARKINGS, DIRECTIONS

from mesa import Agent
import random
from map.map import PARKINGS, DIRECTIONS

from mesa import Agent
import random
from map.map import PARKINGS, DIRECTIONS

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
        self.wait_steps = 0  
        self.max_wait_steps = 0  
        print(f"Auto iniciado en estacionamiento {self.start_parking}, destino: {self.destination_parking}, color: {self.color}")

    def within_grid(self, pos):
        x, y = pos
        return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height

    def get_allowed_moves(self):
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

    def can_advance_at_light(self, pos):
        """
        Verifica si puede avanzar en un semáforo. Revisa tanto la celda actual
        como la celda adyacente correspondiente al semáforo.
        """
        cell_agents = self.model.grid.get_cell_list_contents(pos)
        traffic_lights = [agent for agent in cell_agents if isinstance(agent, TrafficLightAgent)]
        if not traffic_lights:
            return True  

        for light in traffic_lights:
            x, y = light.position
            adjacent_positions = [
                (x + 1, y), (x - 1, y),
                (x, y + 1), (x, y - 1)
            ]
            semaforo_positions = [pos for pos in adjacent_positions if self.within_grid(pos)]
            semaforo_positions.append(light.position)

            for semaforo_pos in semaforo_positions:
                if any(isinstance(agent, PedestrianAgent) for agent in self.model.grid.get_cell_list_contents(semaforo_pos)):
                    print(f"Carro {self.unique_id} detenido: Peatón en semáforo en {semaforo_pos}.")
                    return False

        return True

    def can_move_to(self, pos):
        if not self.can_advance_at_light(pos):
            return False

        if self.model.grid.is_cell_empty(pos):
            return True

        cell_agents = self.model.grid.get_cell_list_contents(pos)
        if any(isinstance(agent, PedestrianAgent) for agent in cell_agents):
            print(f"Carro {self.unique_id} esperando porque hay peatón en {pos}.")
            return False

        for agent in cell_agents:
            if isinstance(agent, TrafficLightAgent):
                if agent.state == "green":
                    return True
                elif agent.state == "yellow":
                    return random.choice([True, False])

        return False

    def distance_to_destination(self, pos):
        return abs(pos[0] - self.destination[0]) + abs(pos[1] - self.destination[1])

    def move(self):
        if self.has_arrived:
            return

        x, y = self.pos
        adjacent_positions = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        if self.destination in adjacent_positions:
            self.model.grid.move_agent(self, self.destination)
            print(f"Moviendo el auto directamente al destino: {self.destination}")
            self.has_arrived = True
            self.max_wait_steps = random.randint(1000, 5000)  
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

    def choose_new_destination(self):
        parking_numbers = list(PARKINGS.values())
        new_parking = random.choice(parking_numbers)

        while new_parking == self.destination_parking:
            new_parking = random.choice(parking_numbers)

        self.destination_parking = new_parking
        self.destination = next(pos for pos, num in PARKINGS.items() if num == new_parking)
        self.has_arrived = False
        self.wait_steps = 0
        print(f"Auto {self.unique_id} eligió nuevo destino: {self.destination_parking} ({self.destination})")

    def step(self):
        print(f"Posición actual del auto: {self.pos}")

        if self.has_arrived:
            self.wait_steps += 1
            print(f"Auto {self.unique_id} esperando en el estacionamiento. Pasos: {self.wait_steps}/{self.max_wait_steps}")
            if self.wait_steps >= self.max_wait_steps:
                self.choose_new_destination()
            return

        self.move()

class PedestrianAgent(Agent):
    def __init__(self, unique_id, model, color="orange"):
        super().__init__(unique_id, model)
        self.color = color
        self.is_crossing = False  
        self.crossing_path = []  
        self.last_position = None  
        self.non_crossable_lights = [(1, 6), (5, 1), (17, 8), (8, 22)]  
        self.current_direction = None 

    def within_grid(self, pos):
        """Verifica si una posición está dentro del grid."""
        x, y = pos
        return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height

    def is_valid_sidewalk(self, pos):
        """Verifica si la posición es una banqueta válida."""
        return pos in self.model.sidewalk_positions

    def is_valid_red_light(self, pos):
        """
        Verifica si el semáforo rojo en una posición es válido para cruzar.
        """
        if pos in self.non_crossable_lights:
            return False
        for agent in self.model.grid.get_cell_list_contents(pos):
            if isinstance(agent, TrafficLightAgent) and agent.state == "red":
                return True
        return False

    def get_valid_moves(self):
        """
        Calcula los movimientos válidos, excluyendo la posición anterior, a menos que sea la única opción.
        """
        x, y = self.pos
        possible_moves = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        valid_moves = []

        for move in possible_moves:
            if not self.within_grid(move):
                continue
            if self.is_valid_sidewalk(move) or self.is_valid_red_light(move):
                valid_moves.append(move)

        if len(valid_moves) == 1 and valid_moves[0] == self.last_position:
            return valid_moves

        valid_moves = [move for move in valid_moves if move != self.last_position]
        return valid_moves

    def move(self):
        """
        Mueve al peatón considerando los semáforos y las restricciones.
        """
        if self.is_crossing:
            if self.crossing_path:
                next_pos = self.crossing_path.pop(0)
                self.model.grid.move_agent(self, next_pos)
                print(f"Peatón {self.unique_id} continúa cruzando hacia {next_pos}")
                return

        # Obtener movimientos válidos
        valid_moves = self.get_valid_moves()
        if not valid_moves:
            print(f"Peatón {self.unique_id} no tiene movimientos válidos en {self.pos}.")
            return

        # Si encuentra un semáforo rojo válido, fuerza el cruce
        for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            next_pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
            if self.is_valid_red_light(next_pos):
                self.initiate_crossing(direction)
                return

        # Elegir un movimiento al azar entre los válidos
        chosen_move = random.choice(valid_moves)
        self.last_position = self.pos
        self.model.grid.move_agent(self, chosen_move)
        print(f"Peatón {self.unique_id} moviéndose a: {chosen_move}")

    def initiate_crossing(self, direction):
        """
        Inicia el cruce del semáforo y establece el camino hacia la próxima celda azul.
        """
        x, y = self.pos
        self.crossing_path = [(x + direction[0], y + direction[1])]
        while self.within_grid(self.crossing_path[-1]) and not self.is_valid_sidewalk(self.crossing_path[-1]):
            nx, ny = self.crossing_path[-1]
            self.crossing_path.append((nx + direction[0], ny + direction[1]))

        self.is_crossing = True
        print(f"Peatón {self.unique_id} inicia cruce hacia: {self.crossing_path[0]}")

    def step(self):
        """Moverse cada 2 pasos."""
        if self.model.schedule.steps % 2 == 0:  # Moverse cada 2 pasos
            self.move()

class TrafficLightAgent(Agent):
    def __init__(self, unique_id, model, position, green_time=10, yellow_time=3, red_time=10, is_green=True):
        super().__init__(unique_id, model)
        self.position = position
        self.green_time = green_time
        self.yellow_time = yellow_time
        self.red_time = red_time
        self.state = "green" if is_green else "red"
        self.timer = self.green_time if is_green else self.red_time

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


class StaticAgent(Agent):
    def __init__(self, unique_id, model, agent_type, color):
        super().__init__(unique_id, model)
        self.agent_type = agent_type  
        self.color = color 
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
       self.wait_steps = 0 
       self.max_wait_steps = 0 
       print(f"Auto iniciado en estacionamiento {self.start_parking}, destino: {self.destination_parking}, color: {self.color}")


   def within_grid(self, pos):
       x, y = pos
       return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height


   def get_allowed_moves(self):
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


   def can_advance_at_light(self, pos):
       """
       Verifica si puede avanzar en un semáforo. Revisa tanto la celda actual
       como la celda adyacente correspondiente al semáforo.
       """
       cell_agents = self.model.grid.get_cell_list_contents(pos)
       traffic_lights = [agent for agent in cell_agents if isinstance(agent, TrafficLightAgent)]
       if not traffic_lights:
           return True 


       for light in traffic_lights:
           x, y = light.position
           adjacent_positions = [
               (x + 1, y), (x - 1, y),
               (x, y + 1), (x, y - 1)
           ]
           semaforo_positions = [pos for pos in adjacent_positions if self.within_grid(pos)]
           semaforo_positions.append(light.position)


           for semaforo_pos in semaforo_positions:
               if any(isinstance(agent, PedestrianAgent) for agent in self.model.grid.get_cell_list_contents(semaforo_pos)):
                   print(f"Carro {self.unique_id} detenido: Peatón en semáforo en {semaforo_pos}.")
                   return False


       return True


   def can_move_to(self, pos):
       if not self.can_advance_at_light(pos):
           return False


       if self.model.grid.is_cell_empty(pos):
           return True


       cell_agents = self.model.grid.get_cell_list_contents(pos)
       if any(isinstance(agent, PedestrianAgent) for agent in cell_agents):
           print(f"Carro {self.unique_id} esperando porque hay peatón en {pos}.")
           return False


       for agent in cell_agents:
           if isinstance(agent, TrafficLightAgent):
               if agent.state == "green":
                   return True
               elif agent.state == "yellow":
                   return random.choice([True, False])


       return False


   def distance_to_destination(self, pos):
       return abs(pos[0] - self.destination[0]) + abs(pos[1] - self.destination[1])


   def move(self):
       if self.has_arrived:
           return


       x, y = self.pos
       adjacent_positions = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
       if self.destination in adjacent_positions:
           self.model.grid.move_agent(self, self.destination)
           print(f"Moviendo el auto directamente al destino: {self.destination}")
           self.has_arrived = True
           self.max_wait_steps = random.randint(1000, 5000) 
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


   def choose_new_destination(self):
       parking_numbers = list(PARKINGS.values())
       new_parking = random.choice(parking_numbers)


       while new_parking == self.destination_parking:
           new_parking = random.choice(parking_numbers)


       self.destination_parking = new_parking
       self.destination = next(pos for pos, num in PARKINGS.items() if num == new_parking)
       self.has_arrived = False
       self.wait_steps = 0
       print(f"Auto {self.unique_id} eligió nuevo destino: {self.destination_parking} ({self.destination})")


   def step(self):
       print(f"Posición actual del auto: {self.pos}")


       if self.has_arrived:
           self.wait_steps += 1
           print(f"Auto {self.unique_id} esperando en el estacionamiento. Pasos: {self.wait_steps}/{self.max_wait_steps}")
           if self.wait_steps >= self.max_wait_steps:
               self.choose_new_destination()
           return


       self.move()


class PedestrianAgent(Agent):
   def __init__(self, unique_id, model, color="orange"):
       super().__init__(unique_id, model)
       self.color = color
       self.is_crossing = False 
       self.crossing_path = [] 
       self.last_position = None 
       self.non_crossable_lights = [(1, 6), (5, 1), (17, 8), (8, 22)] 
       self.current_direction = None


   def within_grid(self, pos):
       """Verifica si una posición está dentro del grid."""
       x, y = pos
       return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height


   def is_valid_sidewalk(self, pos):
       """Verifica si la posición es una banqueta válida."""
       return pos in self.model.sidewalk_positions


   def is_valid_red_light(self, pos):
       """
       Verifica si el semáforo rojo en una posición es válido para cruzar.
       """
       if pos in self.non_crossable_lights:
           return False
       for agent in self.model.grid.get_cell_list_contents(pos):
           if isinstance(agent, TrafficLightAgent) and agent.state == "red":
               return True
       return False


   def get_valid_moves(self):
       """
       Calcula los movimientos válidos, excluyendo la posición anterior, a menos que sea la única opción.
       """
       x, y = self.pos
       possible_moves = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
       valid_moves = []


       for move in possible_moves:
           if not self.within_grid(move):
               continue
           if self.is_valid_sidewalk(move) or self.is_valid_red_light(move):
               valid_moves.append(move)


       if len(valid_moves) == 1 and valid_moves[0] == self.last_position:
           return valid_moves


       valid_moves = [move for move in valid_moves if move != self.last_position]
       return valid_moves


   def move(self):
       """
       Mueve al peatón considerando los semáforos y las restricciones.
       """
       if self.is_crossing:
           if self.crossing_path:
               next_pos = self.crossing_path.pop(0)
               self.model.grid.move_agent(self, next_pos)
               print(f"Peatón {self.unique_id} continúa cruzando hacia {next_pos}")
               return


       # Obtener movimientos válidos
       valid_moves = self.get_valid_moves()
       if not valid_moves:
           print(f"Peatón {self.unique_id} no tiene movimientos válidos en {self.pos}.")
           return


       # Si encuentra un semáforo rojo válido, fuerza el cruce
       for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
           next_pos = (self.pos[0] + direction[0], self.pos[1] + direction[1])
           if self.is_valid_red_light(next_pos):
               self.initiate_crossing(direction)
               return


       # Elegir un movimiento al azar entre los válidos
       chosen_move = random.choice(valid_moves)
       self.last_position = self.pos
       self.model.grid.move_agent(self, chosen_move)
       print(f"Peatón {self.unique_id} moviéndose a: {chosen_move}")


   def initiate_crossing(self, direction):
       """
       Inicia el cruce del semáforo y establece el camino hacia la próxima celda azul.
       """
       x, y = self.pos
       self.crossing_path = [(x + direction[0], y + direction[1])]
       while self.within_grid(self.crossing_path[-1]) and not self.is_valid_sidewalk(self.crossing_path[-1]):
           nx, ny = self.crossing_path[-1]
           self.crossing_path.append((nx + direction[0], ny + direction[1]))


       self.is_crossing = True
       print(f"Peatón {self.unique_id} inicia cruce hacia: {self.crossing_path[0]}")


   def step(self):
       """Moverse cada 2 pasos."""
       if self.model.schedule.steps % 2 == 0:  # Moverse cada 2 pasos
           self.move()


class TrafficLightAgent(Agent):
   def __init__(self, unique_id, model, position, green_time=10, yellow_time=3, red_time=10, is_green=True):
       super().__init__(unique_id, model)
       self.position = position
       self.green_time = green_time
       self.yellow_time = yellow_time
       self.red_time = red_time
       self.state = "green" if is_green else "red"
       self.timer = self.green_time if is_green else self.red_time


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




class StaticAgent(Agent):
   def __init__(self, unique_id, model, agent_type, color):
       super().__init__(unique_id, model)
       self.agent_type = agent_type 
       self.color = color
