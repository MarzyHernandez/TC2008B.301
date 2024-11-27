import random
from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from model.agents import CarAgent, PedestrianAgent, TrafficLightAgent, StaticAgent
from map.map import BUILDINGS, SIDEWALKS, PARKINGS, TRAFFIC_LIGHTS_RED, TRAFFIC_LIGHTS_GREEN, GLORIETA, DOORS

class TrafficModel(Model):
    def __init__(self, width, height, agent_configs, num_pedestrians=5):
        self.door_positions = DOORS
        self.blue_positions = set(BUILDINGS + SIDEWALKS)

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

        # Agregar semáforos por cruces (pares de rojo y verde)
        num_traffic_lights = len(TRAFFIC_LIGHTS_RED) // 2
        for i in range(num_traffic_lights):
            red_positions = TRAFFIC_LIGHTS_RED[2 * i: 2 * i + 2]
            green_positions = TRAFFIC_LIGHTS_GREEN[2 * i: 2 * i + 2]

            # Crear semáforo rojo y verde como agentes separados
            red_light = TrafficLightAgent(
                unique_id=f"red_light_{i}",
                model=self,
                red_positions=red_positions,
                green_positions=green_positions,
                is_green=False
            )
            green_light = TrafficLightAgent(
                unique_id=f"green_light_{i}",
                model=self,
                red_positions=red_positions,
                green_positions=green_positions,
                is_green=True
            )

            # Configurar relación de emparejamiento
            red_light.set_partner(green_light)
            green_light.set_partner(red_light)

            # Añadir semáforos a la simulación
            self.schedule.add(red_light)
            self.schedule.add(green_light)

            # Colocar los semáforos en las celdas correspondientes
            for pos in red_positions:
                self.grid.place_agent(red_light, pos)
            for pos in green_positions:
                self.grid.place_agent(green_light, pos)

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
