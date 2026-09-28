import glob
import math
import os
import physics_core
from renderer import Renderer
from vehicle import Car


def create_obstacle_box(world, start_x, start_y, size=80.0):
    n0, n1 = world.add_node(1.5, start_x, start_y), world.add_node(
        1.5, start_x + size, start_y
    )
    n2, n3 = world.add_node(1.5, start_x, start_y + size), world.add_node(
        1.5, start_x + size, start_y + size
    )
    k, c, yield_t, creep = 3000.0, 30.0, 25000.0, 12.0
    d_len = math.hypot(size, size)
    for pair, l in [
        ((n0, n1), size),
        ((n1, n3), size),
        ((n3, n2), size),
        ((n2, n0), size),
        ((n0, n3), d_len),
        ((n1, n2), d_len),
    ]:
        world.add_beam(pair[0], pair[1], l, k, c, yield_t, creep)


def create_concrete_pillar(world, start_x, start_y, size=60.0):
    n0, n1 = world.add_node(0.0, start_x, start_y), world.add_node(
        0.0, start_x + size, start_y
    )
    n2, n3 = world.add_node(0.0, start_x, start_y + size), world.add_node(
        0.0, start_x + size, start_y + size
    )
    k, c, yield_t, creep = 10000.0, 100.0, 1e9, 0.0
    d_len = math.hypot(size, size)
    for pair, l in [
        ((n0, n1), size),
        ((n1, n3), size),
        ((n3, n2), size),
        ((n2, n0), size),
        ((n0, n3), d_len),
        ((n1, n2), d_len),
    ]:
        world.add_beam(pair[0], pair[1], l, k, c, yield_t, creep)


def setup_game_environment(car_texture_name, width, height):
    world = physics_core.PhysicsWorld()
    car = Car(world, width // 2 - 200, height // 2, car_texture_name)
    create_concrete_pillar(world, width - 250, height // 2 - 80, size=70.0)
    create_obstacle_box(world, width - 450, height // 2 - 120, size=90.0)
    create_obstacle_box(world, width - 450, height // 2 + 30, size=90.0)

    renderer = Renderer(world)
    renderer.load_car_texture(car)
    return world, car, renderer


def get_available_vehicles():
    os.makedirs("vehicles", exist_ok=True)
    files = glob.glob("vehicles/*.png")
    names = [os.path.basename(f).replace(".png", "") for f in files]
    return names if names else ["Default Wireframe Car"]