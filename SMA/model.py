# model.py

import random
from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from agents import CarAgent, TrafficLightAgent, StaticAgent
from map import BUILDINGS, PARKINGS, TRAFFIC_LIGHTS_RED, TRAFFIC_LIGHTS_GREEN, GLORIETA

class TrafficModel(Model):
    def __init__(self, width, height, agent_configs):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Agregar edificios
        for i, pos in enumerate(BUILDINGS):
            building = StaticAgent(f"building_{i}", self, "building", "gray")
            self.grid.place_agent(building, pos)

        # Agregar estacionamientos
        for pos, number in PARKINGS.items():
            parking = StaticAgent(f"parking_{number}", self, "parking", "yellow")
            self.grid.place_agent(parking, pos)

        # Agregar glorieta
        for i, pos in enumerate(GLORIETA):
            glorieta = StaticAgent(f"glorieta_{i}", self, "glorieta", "brown")
            self.grid.place_agent(glorieta, pos)

        # Agregar semáforos en rojo
        for i, pos in enumerate(TRAFFIC_LIGHTS_RED):
            traffic_light = TrafficLightAgent(f"traffic_light_red_{i}", self, pos, is_green=False)
            self.schedule.add(traffic_light)
            self.grid.place_agent(traffic_light, pos)

        # Agregar semáforos en verde
        for i, pos in enumerate(TRAFFIC_LIGHTS_GREEN):
            traffic_light = TrafficLightAgent(f"traffic_light_green_{i}", self, pos, is_green=True)
            self.schedule.add(traffic_light)
            self.grid.place_agent(traffic_light, pos)

        # Configurar agentes 
        for i, (start_pos, dest_pos) in enumerate(agent_configs):
            car = CarAgent(self.next_id(), self, destination=dest_pos, color_index=i)
            self.schedule.add(car)
            self.grid.place_agent(car, start_pos)

            start_parking_number = PARKINGS[start_pos]
            destination_parking_number = PARKINGS[dest_pos]
            print(f"Carro {i+1} iniciado en estacionamiento {start_parking_number} ({start_pos}), destino: estacionamiento {destination_parking_number} ({dest_pos}), color: {car.color}")

    def step(self):
        self.schedule.step()

