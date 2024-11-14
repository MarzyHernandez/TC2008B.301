# server.py

from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.visualization.ModularVisualization import ModularServer
from model import TrafficModel
from agents import CarAgent, TrafficLightAgent, StaticAgent
from map import PARKINGS

# Visualización de cantidad de carros y semáforos
class StatsDisplay(TextElement):
    def render(self, model):
        total_cars = sum(1 for agent in model.schedule.agents if isinstance(agent, CarAgent))
        total_traffic_lights = sum(1 for agent in model.schedule.agents if isinstance(agent, TrafficLightAgent))
        return f"Carros: {total_cars} | Semáforos: {total_traffic_lights}"

# Visualización de agentes
def agent_portrayal(agent):
    if isinstance(agent, CarAgent):
        return {"Shape": "circle", "Filled": "true", "Layer": 1, "Color": agent.color, "r": 0.5}
    elif isinstance(agent, TrafficLightAgent):
        color = "green" if agent.state == "green" else "yellow" if agent.state == "yellow" else "red"
        return {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": color, "w": 0.8, "h": 0.8}
    elif isinstance(agent, StaticAgent):
        color_map = {
            "building": "gray",
            "parking": "yellow",
            "glorieta": "brown"
        }
        color = color_map.get(agent.agent_type, "white")
        return {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": color, "w": 0.9, "h": 0.9}
    return {}

# Iniciar el servidor
def start_server():
    grid_size = 24
    grid = CanvasGrid(agent_portrayal, grid_size, grid_size, 500, 500)
    stats_display = StatsDisplay()

    # Solicitar la cantidad de agentes
    num_agents = int(input("Ingrese la cantidad de carros en la simulación (máximo 5): "))
    num_agents = min(num_agents, 5)

    # Configurar los pares de origen y destino para cada agente
    agent_configs = []
    for i in range(num_agents):
        start_parking = int(input(f"Ingrese el número de estacionamiento de inicio para el carro {i+1}: "))
        destination_parking = int(input(f"Ingrese el número de estacionamiento de destino para el carro {i+1}: "))

        # Convertir los números de estacionamiento en posiciones
        start_parking_pos = next((pos for pos, num in PARKINGS.items() if num == start_parking), None)
        destination_parking_pos = next((pos for pos, num in PARKINGS.items() if num == destination_parking), None)

        agent_configs.append((start_parking_pos, destination_parking_pos))

    # Servidor de visualización
    server = ModularServer(
        TrafficModel,
        [stats_display, grid],
        "Simulación de Tráfico",
        {"width": grid_size, "height": grid_size, "agent_configs": agent_configs}
    )
    server.port = 8521
    server.launch()

if __name__ == "__main__":
    start_server()
