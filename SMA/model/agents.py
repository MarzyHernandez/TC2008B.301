from mesa import Agent
import random
from map.map import PARKINGS, DIRECTIONS, DOORS, DOOR_GROUPS, DIRECTIONS_MAP, PEDESTRIAN_DIRECTIONS




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
       self.detection_distance = 3  # Distancia máxima para detectar congestión en la calle
       self.congestion_threshold = 5  # Número de carros considerados congestión
       self.visited_routes = {}  # Diccionario para rutas visitadas
       print(f"Auto iniciado en estacionamiento {self.start_parking}, destino: {self.destination_parking}, color: {self.color}")


   def within_grid(self, pos):
       x, y = pos
       return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height


   def reserve_position(self, pos):
       """Reserva una posición para evitar colisiones."""
       if not hasattr(self.model, "reserved_positions"):
           self.model.reserved_positions = set()
       self.model.reserved_positions.add(pos)


   def release_position(self, pos):
       """Libera una posición reservada."""
       if hasattr(self.model, "reserved_positions") and pos in self.model.reserved_positions:
           self.model.reserved_positions.remove(pos)




   def can_advance_at_light(self, pos):
       cell_agents = self.model.grid.get_cell_list_contents(pos)
       for agent in cell_agents:
           if isinstance(agent, TrafficLightAgent):
               if pos in agent.green_positions + agent.red_positions:
                   if agent.state == "green":
                       return True
                   elif agent.state == "yellow":
                       # Decidir si avanzar o detenerse en amarillo
                       decision = random.choice([True, False])
                       print(f"Carro {self.unique_id} decide {'avanzar' if decision else 'detenerse'} en amarillo en {pos}.")
                       return decision
                   elif agent.state == "red":
                       print(f"Carro {self.unique_id} detenido: semáforo en rojo en {pos}.")
                       return False
       return True




   def can_move_to(self, pos):
       """Verifica si el auto puede moverse a la posición dada."""
       # Verificar semáforos
       if not self.can_advance_at_light(pos):
           return False


       # Verificar si hay peatones en celdas controladas por semáforos
       cell_agents = self.model.grid.get_cell_list_contents(pos)
       for agent in cell_agents:
           if isinstance(agent, TrafficLightAgent):
               # Combinar posiciones controladas por el semáforo
               controlled_positions = agent.green_positions + agent.red_positions
               for controlled_pos in controlled_positions:
                   controlled_cell_agents = self.model.grid.get_cell_list_contents(controlled_pos)
                   if any(isinstance(a, PedestrianAgent) for a in controlled_cell_agents):
                       print(f"Carro {self.unique_id} detenido: peatón en semáforo en {controlled_pos}.")
                       return False


       # Verificar reservas de posición
       if hasattr(self.model, "reserved_positions") and pos in self.model.reserved_positions:
           print(f"Carro {self.unique_id} no puede moverse a {pos}: ya está reservado.")
           return False


       # Verificar ocupación de celdas
       if self.model.grid.is_cell_empty(pos):
           return True


       if any(isinstance(agent, PedestrianAgent) for agent in cell_agents):
           print(f"Carro {self.unique_id} esperando porque hay peatón en {pos}.")
           return False


       return True








   def detect_congestion(self):
       """
       Detecta la cantidad de carros parados en un rango visible a lo largo de las calles (no radial).
       """
       x, y = self.pos
       congestion_count = 0
       allowed_directions = DIRECTIONS.get(self.pos, [])


       print(f"Carro {self.unique_id} analizando congestión desde posición {self.pos}.")
       for direction in allowed_directions:
           dx, dy = 0, 0
           if direction == "up":
               dx, dy = 0, 1
           elif direction == "down":
               dx, dy = 0, -1
           elif direction == "right":
               dx, dy = 1, 0
           elif direction == "left":
               dx, dy = -1, 0
           elif direction == "up-right" or direction == "right-up":
               dx, dy = 1, 1
           elif direction == "up-left" or direction == "left-up":
               dx, dy = -1, 1
           elif direction == "down-right" or direction == "right-down":
               dx, dy = 1, -1
           elif direction == "down-left" or direction == "left-down":
               dx, dy = -1, -1


           for distance in range(1, self.detection_distance + 1):
               neighbor_pos = (x + dx * distance, y + dy * distance)
               if not self.within_grid(neighbor_pos):
                   print(f"Posición {neighbor_pos} fuera del grid, terminando búsqueda en dirección {direction}.")
                   break


               agents = self.model.grid.get_cell_list_contents(neighbor_pos)
               found_cars = [agent for agent in agents if isinstance(agent, CarAgent) and not agent.has_arrived]
               congestion_count += len(found_cars)


               print(f"Revisando posición {neighbor_pos} en dirección {direction}: {len(found_cars)} autos encontrados.")


               if congestion_count >= self.congestion_threshold:
                   print(f"Congestión detectada: {congestion_count} autos en dirección {direction} desde {self.pos}.")
                   return True


       print(f"No hay congestión cerca de {self.pos}. Total autos encontrados: {congestion_count}.")
       return False


   def distance_to_destination(self, pos):
       return abs(pos[0] - self.destination[0]) + abs(pos[1] - self.destination[1])


   def update_visited_routes(self, pos):
       """Actualiza el contador de visitas a las rutas y registra estacionamientos cercanos."""
       if pos not in self.visited_routes:
           self.visited_routes[pos] = {"count": 0, "nearby_parkings": []}
      
       self.visited_routes[pos]["count"] += 1


       # Revisar si hay estacionamientos cercanos
       for neighbor_pos, parking in PARKINGS.items():
           if neighbor_pos in self.visited_routes[pos]["nearby_parkings"]:
               continue  # Ya registrado
           if abs(pos[0] - neighbor_pos[0]) + abs(pos[1] - neighbor_pos[1]) <= 1:
               self.visited_routes[pos]["nearby_parkings"].append(parking)


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
       if 'up-right' in allowed_directions and self.within_grid((x + 1, y + 1)):
           moves.append((x + 1, y + 1))
       if 'up-left' in allowed_directions and self.within_grid((x - 1, y + 1)):
           moves.append((x - 1, y + 1))
       if 'down-right' in allowed_directions and self.within_grid((x + 1, y - 1)):
           moves.append((x + 1, y - 1))
       if 'down-left' in allowed_directions and self.within_grid((x - 1, y - 1)):
           moves.append((x - 1, y - 1))
       if 'right-up' in allowed_directions and self.within_grid((x + 1, y + 1)):
           moves.append((x + 1, y + 1))
       if 'right-down' in allowed_directions and self.within_grid((x + 1, y - 1)):
           moves.append((x + 1, y - 1))
       if 'left-up' in allowed_directions and self.within_grid((x - 1, y + 1)):
           moves.append((x - 1, y + 1))
       if 'left-down' in allowed_directions and self.within_grid((x - 1, y - 1)):
           moves.append((x - 1, y - 1))


       return moves
  
   def wants_to_cross(self, traffic_light_pos):
       """El carro desea cruzar si su destino está más allá del semáforo."""
       return self.distance_to_destination(traffic_light_pos) <= self.detection_distance


   def estimate_steps(self, traffic_light_pos):
       """Calcula pasos estimados hacia el semáforo."""
       return abs(self.pos[0] - traffic_light_pos[0]) + abs(self.pos[1] - traffic_light_pos[1])


   def nearby_count(self, traffic_light_pos):
       """Cuenta agentes cercanos en el área del semáforo."""
       neighbors = self.model.grid.get_neighbors(traffic_light_pos, moore=False, include_center=False, radius=1)
       return sum(1 for agent in neighbors if isinstance(agent, CarAgent))


   def move(self):
       if self.has_arrived:
           return


       if self.detect_congestion():
           print(f"Carro {self.unique_id} detectó congestión cerca de {self.pos}. Cambiando de ruta.")
           self.choose_new_destination()
           return


       x, y = self.pos
       adjacent_positions = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
       if self.destination in adjacent_positions:
           self.release_position(self.pos)
           self.reserve_position(self.destination)
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


       # Aplicar pesos basados en rutas previas y congestión
       weighted_moves = []
       for move in valid_moves:
           weight = 1 / (self.visited_routes.get(move, {"count": 1})["count"])  # Menos peso para rutas ya visitadas
           if self.detect_congestion():
               weight *= 0.5  # Reducir peso si hay congestión


           # Reducir peso para movimientos diagonales (cambio de carril)
           dx, dy = move[0] - self.pos[0], move[1] - self.pos[1]
           if (dx, dy) in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
               print(f"Reduciendo peso para movimiento diagonal: {self.pos} -> {move}")
               weight *= 0.0001  # Prioridad extremadamente baja para cambios de carril


           weighted_moves.append((move, weight))


       chosen_move = random.choices(
           [move for move, weight in weighted_moves],
           weights=[weight for move, weight in weighted_moves],
           k=1
       )[0]


       self.update_visited_routes(chosen_move)
       self.reserve_position(chosen_move)
       self.release_position(self.pos)


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
       self.is_crossing = False  # Indica si está cruzando actualmente
       self.crossing_path = []  # Ruta que sigue al cruzar
       self.last_position = None  # Última posición para evitar ciclos
       self.target_door = None  # Puerta objetivo
       self.non_crossable_lights = [(1, 6), (5, 1), (17, 8), (8, 22)]  # Lugares no permitidos
       self.current_direction = None  # Dirección de movimiento actual
       self.waiting_for_green = False  # Si está esperando que el semáforo cambie a verde


   def within_grid(self, pos):
       """Verifica si una posición está dentro del grid."""
       x, y = pos
       return 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height


   def is_valid_sidewalk(self, pos):
       """Verifica si la posición es una banqueta válida."""
       return pos in self.model.sidewalk_positions


   def is_valid_red_light(self, pos):
       """Verifica si el semáforo en rojo permite cruzar."""
       if pos in self.non_crossable_lights:
           return False
       for agent in self.model.grid.get_cell_list_contents(pos):
           if isinstance(agent, TrafficLightAgent) and agent.state == "red":
               return True
       return False


   def is_door(self, pos):
       """Verifica si una posición corresponde a una puerta."""
       return pos in self.model.door_positions.values()


   def get_group_for_door(self, door_id):
       """
       Obtiene el grupo al que pertenece una puerta por su ID.
       """
       for group, doors in DOOR_GROUPS.items():
           if door_id in doors:
               return group
       return None


   def get_valid_moves(self):
       """
       Calcula los movimientos válidos, excluyendo la posición anterior,
       pero permitiendo que vuelva si es la única opción.
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


   def choose_next_door(self):
       """
       Elige una nueva puerta aleatoria dentro del grupo actual.
       """
       current_group = self.get_group_for_door(self.target_door)
       group_doors = [
           door_id for door_id, pos in self.model.door_positions.items()
           if self.get_group_for_door(door_id) == current_group
       ]
       group_doors = [door_id for door_id in group_doors if door_id != self.target_door]
       if group_doors:
           self.target_door = random.choice(group_doors)
           print(f"Peatón {self.unique_id} eligió la puerta {self.target_door} como nuevo objetivo.")
       else:
           print(f"Peatón {self.unique_id} no tiene más puertas para elegir en el grupo.")


   def move(self):
       """
       Mueve al peatón considerando los semáforos y las restricciones.
       """
       # Si el peatón no tiene una puerta objetivo, elige la más cercana inicialmente
       if self.target_door is None:
           distances = {
               door_id: abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])
               for door_id, pos in self.model.door_positions.items()
           }
           self.target_door = min(distances, key=distances.get)
           print(f"Peatón {self.unique_id} encontró la puerta {self.target_door} como objetivo inicial.")
           return


       # Si el peatón alcanza su puerta objetivo, elige otra
       target_pos = self.model.door_positions.get(self.target_door)
       if target_pos and self.pos == target_pos:
           print(f"Peatón {self.unique_id} llegó a la puerta {self.target_door}.")
           self.choose_next_door()
           return


       # Obtener movimientos válidos
       valid_moves = self.get_valid_moves()
       if not valid_moves:
           print(f"Peatón {self.unique_id} no tiene movimientos válidos en {self.pos}.")
           return


       # Elegir el movimiento hacia el objetivo más cercano
       if target_pos:
           best_move = min(
               valid_moves,
               key=lambda move: abs(move[0] - target_pos[0]) + abs(move[1] - target_pos[1])
           )
           self.last_position = self.pos
           self.model.grid.move_agent(self, best_move)
           print(f"Peatón {self.unique_id} moviéndose a: {best_move}")
       else:
           print(f"Peatón {self.unique_id} no tiene un objetivo claro en este momento.")


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


   def wants_to_cross(self, traffic_light_pos):
       """El peatón desea cruzar si está cerca de su destino."""
       return self.estimate_steps(traffic_light_pos) <= 2


   def estimate_steps(self, traffic_light_pos):
       """Calcula pasos estimados hacia el semáforo."""
       return abs(self.pos[0] - traffic_light_pos[0]) + abs(self.pos[1] - traffic_light_pos[1])


   def nearby_count(self, traffic_light_pos):
       """Cuenta peatones cercanos al semáforo."""
       neighbors = self.model.grid.get_neighbors(traffic_light_pos, moore=False, include_center=False, radius=1)
       return sum(1 for agent in neighbors if isinstance(agent, PedestrianAgent))


   def step(self):
       """Moverse cada 2 pasos."""
       if self.model.schedule.steps % 2 == 0:
           self.move()








class TrafficLightAgent(Agent):
   def __init__(self, unique_id, model, red_positions, green_positions, green_time=10, yellow_time=3, red_time=10, is_green=False):
       super().__init__(unique_id, model)
       self.red_positions = red_positions
       self.green_positions = green_positions
       self.green_time = green_time
       self.yellow_time = yellow_time
       self.red_time = red_time
       self.state = "green" if is_green else "red"
       self.timer = self.green_time if is_green else self.red_time
       self.cruce_partner = None
       self.proposals = []


   def set_partner(self, partner):
       """Configura el semáforo opuesto del mismo cruce."""
       self.cruce_partner = partner


   def solicit_proposals(self):
       """Solicita propuestas a los agentes cercanos a las posiciones del semáforo."""
       self.proposals = []
       all_positions = self.red_positions + self.green_positions
       for pos in all_positions:
           nearby_agents = self.model.grid.get_neighbors(pos, moore=False, include_center=False, radius=3)
           for agent in nearby_agents:
               if isinstance(agent, (CarAgent, PedestrianAgent)) and agent.wants_to_cross(pos):
                   proposal = {
                       "agent": agent,
                       "steps": agent.estimate_steps(pos),
                       "type": "vehicle" if isinstance(agent, CarAgent) else "pedestrian",
                       "nearby_count": agent.nearby_count(pos)
                   }
                   self.proposals.append(proposal)


       # Debug: imprime propuestas recibidas
       if self.proposals:
           print(f"Semáforo {self.unique_id} recibió las siguientes propuestas:")
           for p in self.proposals:
               print(f"  - Agente {p['agent'].unique_id}, tipo: {p['type']}, pasos: {p['steps']}, adyacentes: {p['nearby_count']}")


   def evaluate_proposals(self):
       """Selecciona la mejor propuesta basada en las prioridades."""
       if not self.proposals:
           return None


       # Prioridad para vehículos si hay al menos 3 con 1-2 adyacentes
       car_priority = sum(
           1 for p in self.proposals if p["type"] == "vehicle" and 1 <= p["nearby_count"] <= 2
       ) >= 3
       if car_priority:
           sorted_proposals = sorted(
               [p for p in self.proposals if p["type"] == "vehicle"],
               key=lambda p: (p["steps"], -p["nearby_count"])
           )
       else:
           # Prioridad general: menor tiempo, más adyacentes, peatones primero
           sorted_proposals = sorted(
               self.proposals,
               key=lambda p: (p["steps"], -p["nearby_count"], 1 if p["type"] == "pedestrian" else 2)
           )
       return sorted_proposals[0]


   def change_color(self):
       """Cambia el estado del semáforo y sincroniza con el del cruce opuesto."""
       if self.state == "green":
           # Pasar a amarillo antes de rojo
           self.state = "yellow"
           self.timer = self.yellow_time
           print(f"Semáforo {self.unique_id} cambia a amarillo.")
           # Asegurar que el semáforo opuesto está en rojo
           if self.cruce_partner:
               self.cruce_partner.state = "red"
               self.cruce_partner.timer = self.cruce_partner.red_time
               print(f"Semáforo opuesto {self.cruce_partner.unique_id} sincronizado a rojo.")
       elif self.state == "yellow":
           # Pasar a rojo y sincronizar con el cruce opuesto
           self.state = "red"
           self.timer = self.red_time
           print(f"Semáforo {self.unique_id} cambia a rojo.")
           if self.cruce_partner:
               self.cruce_partner.state = "green"
               self.cruce_partner.timer = self.cruce_partner.green_time
               print(f"Semáforo opuesto {self.cruce_partner.unique_id} sincronizado a verde.")
       elif self.state == "red":
           # Evaluar propuestas antes de pasar a verde
           proposal = self.evaluate_proposals()
           if proposal:
               self.state = "green"
               self.timer = self.green_time
               print(f"Semáforo {self.unique_id} cambia a verde por propuesta.")
               if self.cruce_partner:
                   self.cruce_partner.state = "red"
                   self.cruce_partner.timer = self.cruce_partner.red_time
                   print(f"Semáforo opuesto {self.cruce_partner.unique_id} sincronizado a rojo.")
           else:
               # Si no hay propuestas, permanecer en rojo
               self.timer = self.red_time
               print(f"Semáforo {self.unique_id} permanece en rojo por falta de propuestas.")


   def step(self):
       """Reduce el temporizador y gestiona cambios de estado."""
       self.timer -= 1
       if self.timer <= 0:
           # Siempre pasar por amarillo antes de rojo
           if self.state == "green":
               self.change_color()  # Verde -> Amarillo
           elif self.state == "yellow":
               self.change_color()  # Amarillo -> Rojo
           elif self.state == "red":
               self.solicit_proposals()
               self.change_color()  # Rojo -> Verde si hay propuestas




class StaticAgent(Agent):
   def __init__(self, unique_id, model, agent_type, color):
       super().__init__(unique_id, model)
       self.agent_type = agent_type 
       self.color = color
