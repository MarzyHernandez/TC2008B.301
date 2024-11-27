from flask import Flask, jsonify
from flask_cors import CORS 
from model.model import TrafficModel
from model.agents import CarAgent, TrafficLightAgent, PedestrianAgent, StaticAgent
import random
from threading import Thread
from map.map import PARKINGS, TRAFFIC_LIGHTS_RED, TRAFFIC_LIGHTS_GREEN


app = Flask(__name__)


CORS(app)


model = None


def invert_y(y):
   """Convierte la coordenada y para ajustarla al sistema donde y crece de abajo hacia arriba"""
   return 23 - y 


# Función para inicializar el modelo de tráfico
def create_model():
   global model
   grid_size = 24
   agent_configs = []
   parking_numbers = list(range(1, 18)) 


   for _ in range(20):
       start_parking = random.choice(parking_numbers)
       print(f"Estacionamiento {start_parking}")
       destination_parking = random.choice(parking_numbers)
       print(f"Estacionamiento {destination_parking}")
       while destination_parking == start_parking:
           destination_parking = random.choice(parking_numbers)


       start_parking_pos = next((pos for pos, num in PARKINGS.items() if num == start_parking), None)
       destination_parking_pos = next((pos for pos, num in PARKINGS.items() if num == destination_parking), None)


       print(f"Estacionamiento {start_parking} tiene la posición {start_parking_pos}")
       print(f"Estacionamiento {destination_parking} tiene la posición {destination_parking_pos}")


       if start_parking_pos is None or destination_parking_pos is None:
           print(f"Error: Estacionamiento {start_parking} o {destination_parking} no tiene una posición válida.")
           continue


       agent_configs.append((start_parking_pos, destination_parking_pos))


   model = TrafficModel(grid_size, grid_size, agent_configs, num_pedestrians=10)


# Función para obtener las posiciones de los autos
@app.route('/getCars', methods=['GET'])
def get_cars():
   if model is None:
       create_model()


   model.step()


   cars_positions = []
   for agent in model.schedule.agents:
       if isinstance(agent, CarAgent):
           x, y = agent.pos


           car_data = {
               "id": agent.unique_id,
               "position": [x, y] 
           }
           cars_positions.append(car_data)


   return jsonify(cars_positions)


# Función para obtener el estado de los semáforos
@app.route('/getLights', methods=['GET'])
def getLights():
   if model is None:
       create_model()


   lights = []


   for agent in model.schedule.agents:
       if isinstance(agent, TrafficLightAgent):
           x, y = agent.pos


           light_data = {
               "id": agent.unique_id,
               "color": agent.state,
               "position": [x, y]
           }
           lights.append(light_data)


   return jsonify(lights)


# Función para cambiar el estado de los peatones
@app.route('/getPeaton', methods=['GET'])
def get_peaton():
   if model is None:
       create_model()


   pedestrians = []


   for agent in model.schedule.agents:
       if isinstance(agent, PedestrianAgent):
           x, y = agent.pos


           pedestrians.append({
               "id": f"peaton_{agent.unique_id}",
               "position": [x, y],
               "color": agent.color
           })


   return jsonify(pedestrians)




@app.route('/getPeatonEscalado', methods=['GET'])
def get_peaton_escalado():
   if model is None:
       create_model()


   pedestrians = []


   for agent in model.schedule.agents:
       if isinstance(agent, PedestrianAgent):
           x, y = agent.pos


           new_position = get_scaled_position(agent)


           pedestrians.append({
               "id": f"peaton_{agent.unique_id}",
               "position": new_position,
               "color": agent.color
           })


   return jsonify(pedestrians)


@app.route('/getCarrosEscalado', methods=['GET'])
def get_carros_escalado():
   if model is None:
       create_model()


   model.step()


   cars_positions = []


   for agent in model.schedule.agents:
       if isinstance(agent, CarAgent):
           x, y = agent.pos


           scaled_x = x * 10 + 5
           scaled_y = y * 10 + 5


           car_data = {
               "id": agent.unique_id,
               "position": [scaled_x, scaled_y]
           }
           cars_positions.append(car_data)


   return jsonify(cars_positions)






def get_scaled_position(agent):
   """
   Lógica para escalar la posición del peatón según las celdas adyacentes 'blancas'.
   """
   x, y = agent.pos
   '''
   adjacent_positions = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


   for nx, ny in adjacent_positions:
       if is_white(nx, ny):
           return scale_position(nx, ny)
   '''
   return scale_position(x, y)


def is_white(x, y):
   """
   Verificar si la celda en (x, y) es blanca (vacía, sin edificio o estacionamiento).
   """
   contents = model.grid.get_cell_list_contents((x, y))


   if not any(isinstance(agent, StaticAgent) for agent in contents):
       return True
   return False


def scale_position(x, y):
   """
   Escalar la posición según las reglas definidas
   """
   return [x * 10 + 3, y * 10 + 3] 






# Para correr el servidor Flask
def run_flask():
   app.run(debug=True, use_reloader=False, port=5003) 


# Función principal para ejecutar Flask en un hilo y luego la simulación
if __name__ == "__main__":
   flask_thread = Thread(target=run_flask)
   flask_thread.start()
