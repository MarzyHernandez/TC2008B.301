# mesa_runner.py

from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.visualization.ModularVisualization import ModularServer
from model.model import TrafficModel
from model.agents import CarAgent, TrafficLightAgent, PedestrianAgent, StaticAgent
from map.map import PARKINGS

import random

class StatsDisplay(TextElement):
    def render(self, model):
        total_cars = sum(1 for agent in model.schedule.agents if isinstance(agent, CarAgent))
        total_pedestrians = sum(1 for agent in model.schedule.agents if isinstance(agent, PedestrianAgent))
        total_traffic_lights = sum(1 for agent in model.schedule.agents if isinstance(agent, TrafficLightAgent))
        return f"Carros: {total_cars} | Peatones: {total_pedestrians} | Semáforos: {total_traffic_lights}"

def agent_portrayal(agent):
    if isinstance(agent, CarAgent):
        return {"Shape": "circle", "Filled": "true", "Layer": 1, "Color": agent.color, "r": 0.5}
    elif isinstance(agent, PedestrianAgent):
        return {"Shape": "circle", "Filled": "true", "Layer": 2, "Color": "orange", "r": 0.3}  
    elif isinstance(agent, TrafficLightAgent):
        color = "green" if agent.state == "green" else "yellow" if agent.state == "yellow" else "red"
        return {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": color, "w": 0.8, "h": 0.8}
    elif isinstance(agent, StaticAgent):
        color_map = {
            "building": "blue",
            "parking": "yellow",
            "glorieta": "brown"
        }
        color = color_map.get(agent.agent_type, "white")
        return {"Shape": "rect", "Filled": "true", "Layer": 0, "Color": color, "w": 0.9, "h": 0.9}
    return {}

def start_server():
    grid_size = 24
    grid = CanvasGrid(agent_portrayal, grid_size, grid_size, 500, 500)
    stats_display = StatsDisplay()

    agent_configs = []
    parking_numbers = list(range(1, 18)) 

    for _ in range(20):  # 20 autos
        start_parking = random.choice(parking_numbers)
        destination_parking = random.choice(parking_numbers)
        while destination_parking == start_parking:
            destination_parking = random.choice(parking_numbers)

        start_parking_pos = next((pos for pos, num in PARKINGS.items() if num == start_parking), None)
        destination_parking_pos = next((pos for pos, num in PARKINGS.items() if num == destination_parking), None)

        agent_configs.append((start_parking_pos, destination_parking_pos))

    server = ModularServer(
        TrafficModel,
        [stats_display, grid],
        "Simulación de Tráfico",
        {"width": grid_size, "height": grid_size, "agent_configs": agent_configs, "num_pedestrians": 10}  
    )
    server.port = 8521  
    server.launch()

if __name__ == "__main__":
    start_server()
