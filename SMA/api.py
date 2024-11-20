from flask import Flask, jsonify
from flask_cors import CORS  # Importamos CORS
from model.model import TrafficModel
from model.agents import CarAgent, TrafficLightAgent, PedestrianAgent, StaticAgent
import random
from threading import Thread
from map.map import PARKINGS, TRAFFIC_LIGHTS_RED, TRAFFIC_LIGHTS_GREEN

app = Flask(__name__)

# Habilitar CORS para todas las rutas
CORS(app)

# Crear una instancia global del modelo para que no se cree cada vez que se accede a la API
model = None

def invert_y(y):
    """Convierte la coordenada y para ajustarla al sistema donde y crece de abajo hacia arriba"""
    return 23 - y  # Invertir para que y crezca de abajo hacia arriba

# Función para inicializar el modelo de tráfico
def create_model():
    global model
    grid_size = 24
    agent_configs = []
    parking_numbers = list(range(1, 18))  # Estacionamientos del 1 al 17

    # Crear configuración de agentes para los autos
    for _ in range(2):  # 2 autos por prueba
        start_parking = random.choice(parking_numbers)
        print(f"Estacionamiento {start_parking}")
        destination_parking = random.choice(parking_numbers)
        print(f"Estacionamiento {destination_parking}")
        while destination_parking == start_parking:
            destination_parking = random.choice(parking_numbers)

        # Obtener las posiciones de los estacionamientos utilizando el diccionario PARKINGS
        start_parking_pos = next((pos for pos, num in PARKINGS.items() if num == start_parking), None)
        destination_parking_pos = next((pos for pos, num in PARKINGS.items() if num == destination_parking), None)

        # Verificar que las posiciones están siendo encontradas correctamente
        print(f"Estacionamiento {start_parking} tiene la posición {start_parking_pos}")
        print(f"Estacionamiento {destination_parking} tiene la posición {destination_parking_pos}")

        # Si no encontramos una posición válida, mostramos un mensaje de error
        if start_parking_pos is None or destination_parking_pos is None:
            print(f"Error: Estacionamiento {start_parking} o {destination_parking} no tiene una posición válida.")
            continue  # Ignorar este par de estacionamientos si no tienen posición válida

        # Agregar la configuración de los autos al modelo con posiciones correctas
        agent_configs.append((start_parking_pos, destination_parking_pos))

    # Crear el modelo de tráfico con los autos y peatones
    model = TrafficModel(grid_size, grid_size, agent_configs, num_pedestrians=10)

# Función para obtener las posiciones de los autos
@app.route('/getCars', methods=['GET'])
def get_cars():
    # Si el modelo aún no está creado, crearlo
    if model is None:
        create_model()

    # Avanzar un paso en la simulación para que las posiciones estén actualizadas
    model.step()

    # Recuperar las posiciones de los autos
    cars_positions = []
    for agent in model.schedule.agents:
        if isinstance(agent, CarAgent):
            # Obtener las coordenadas sin invertirlas
            x, y = agent.pos  # Las coordenadas ya deben ser correctas

            # Invertir solo la 'y' para mostrar la correcta en el sistema visual
            car_data = {
                "id": agent.unique_id,
                "position": [x, y]  # Invertir solo la 'y' para que crezca de abajo hacia arriba
            }
            cars_positions.append(car_data)

    return jsonify(cars_positions)

# Función para obtener el estado de los semáforos
@app.route('/getLights', methods=['GET'])
def get_lights():
    if model is None:
        create_model()

    traffic_lights = []

    # Recuperar todos los semáforos del modelo
    for agent in model.schedule.agents:
        if isinstance(agent, TrafficLightAgent):
            x, y = agent.position

            # Devolver el estado (color) y la posición de cada semáforo
            traffic_lights.append({
                "id": f"{agent.state}_{x}_{y}",  # Identificador único para cada semáforo por estado y posición
                "position": [x, y],
                "color": agent.state  # El color del semáforo (green, yellow, red)
            })

    return jsonify(traffic_lights)

# Función para cambiar el estado de los peatones
@app.route('/getPeaton', methods=['GET'])
def get_peaton():
    if model is None:
        create_model()

    # Recuperar los peatones
    pedestrians = []

    # Recuperar todos los peatones del modelo
    for agent in model.schedule.agents:
        if isinstance(agent, PedestrianAgent):
            x, y = agent.pos

            # Devolver la posición y el color del peatón
            pedestrians.append({
                "id": f"peaton_{agent.unique_id}",
                "position": [x, y],
                "color": agent.color  # El color del peatón (por defecto "orange" o el valor dado)
            })

    return jsonify(pedestrians)


@app.route('/getPeatonEscalado', methods=['GET'])
def get_peaton_escalado():
    if model is None:
        create_model()

    # Recuperar los peatones y calcular la posición escalada
    pedestrians = []

    for agent in model.schedule.agents:
        if isinstance(agent, PedestrianAgent):
            x, y = agent.pos

            # Verificar si el peatón está en un lado "blanco"
            new_position = get_scaled_position(agent)

            pedestrians.append({
                "id": f"peaton_{agent.unique_id}",
                "position": new_position,
                "color": agent.color  # El color del peatón
            })

    return jsonify(pedestrians)

@app.route('/getCarrosEscalado', methods=['GET'])
def get_carros_escalado():
    if model is None:
        create_model()

    # Recuperar las posiciones de los autos y escalar
    cars_positions = []

    for agent in model.schedule.agents:
        if isinstance(agent, CarAgent):
            x, y = agent.pos

            # Calcular la posición escalada
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

    # Adyacentes que el peatón puede considerar
    adjacent_positions = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    # Revisar las celdas adyacentes
    for nx, ny in adjacent_positions:
        # Verificar si la celda es blanca (sin edificio, estacionamiento, etc.)
        if is_white(nx, ny):
            # Escalar la posición
            return scale_position(nx, ny)

    # Si no encuentra ninguna celda blanca adyacente, no escala
    return [x, y]

def is_white(x, y):
    """
    Verificar si la celda en (x, y) es blanca (vacía, sin edificio o estacionamiento).
    """
    # Recuperar el contenido de la celda
    contents = model.grid.get_cell_list_contents((x, y))

    # Si no hay edificios ni estacionamientos, la celda es blanca
    if not any(isinstance(agent, StaticAgent) for agent in contents):
        return True
    return False

def scale_position(x, y):
    """
    Escalar la posición según las reglas definidas (ejemplo: convertir coordenadas simples en una más grande).
    """
    # Aquí definimos la lógica de escala, por ejemplo:
    return [x * 10, y * 10]  # Ejemplo de escala



# Para correr el servidor Flask
def run_flask():
    app.run(debug=True, use_reloader=False, port=5003)  # Usamos el puerto 5003

# Función principal para ejecutar Flask en un hilo y luego la simulación
if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
