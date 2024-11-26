import random
from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from model.agents import CarAgent, PedestrianAgent, TrafficLightAgent, StaticAgent
from map.map import BUILDINGS, SIDEWALKS, PARKINGS, TRAFFIC_LIGHTS_RED, TRAFFIC_LIGHTS_GREEN, GLORIETA, DOORS

class TrafficModel(Model):
    def __init__(self, width, height, agent_configs, num_pedestrians=5):
        self.door_positions = DOORS

        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.sidewalk_positions = SIDEWALKS 

        # Agregar edificios
        for i, pos in enumerate(BUILDINGS):
            building = StaticAgent(f"building_{i}", self, "building", "gray")
            self.grid.place_agent(building, pos)

        # Agregar peatones
        for i in range(num_pedestrians):
            random_sidewalk = random.choice(self.sidewalk_positions)
            pedestrian = PedestrianAgent(self.next_id(), self, color="gray")
            self.grid.place_agent(pedestrian, random_sidewalk)
            self.schedule.add(pedestrian)

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

        # Configurar agentes de carros
        for i, (start_pos, dest_pos) in enumerate(agent_configs):
            car = CarAgent(self.next_id(), self, destination=dest_pos, color_index=i)
            self.schedule.add(car)
            self.grid.place_agent(car, start_pos)

        # Configurar agentes peatones
        for i in range(num_pedestrians):
            random_building = random.choice(BUILDINGS)
            pedestrian = PedestrianAgent(self.next_id(), self)
            self.schedule.add(pedestrian)
            self.grid.place_agent(pedestrian, random_building)

        # Agregar puertas
        for door_id, door_pos in DOORS.items():
            door = StaticAgent(f"door_{door_id}", self, "door", "gray")
            self.grid.place_agent(door, door_pos)

        # Dentro de la clase TrafficModel
        self.inside_building_positions = []  # Lista para celdas internas del edificio
        for building_pos in BUILDINGS:
            for dx in range(-1, 2):  # Considera un área interna alrededor del edificio
                for dy in range(-1, 2):
                    pos = (building_pos[0] + dx, building_pos[1] + dy)
                    if pos not in SIDEWALKS and pos not in PARKINGS and pos in BUILDINGS:
                        self.inside_building_positions.append(pos)


    def step(self):
        self.schedule.step()
