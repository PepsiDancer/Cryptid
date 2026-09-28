import math
import sys
import pygame
from world_builder import get_available_vehicles, setup_game_environment

WIDTH, HEIGHT = 1280, 720
FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Soft-Body Crash Simulator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 20)
    title_font = pygame.font.SysFont("Consolas", 40, bold=True)

    state = "MENU"
    vehicles = get_available_vehicles()
    selected_idx = 0

    world, car, renderer = None, None, None
    selected_node = None
    dt = 1.0 / FPS

    while True:
        # --- 1. EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_idx = (selected_idx - 1) % len(vehicles)
                    elif event.key == pygame.K_DOWN:
                        selected_idx = (selected_idx + 1) % len(vehicles)
                    elif event.key == pygame.K_RETURN:
                        world, car, renderer = setup_game_environment(
                            vehicles[selected_idx], WIDTH, HEIGHT
                        )
                        state = "GAMEPLAY"

            elif state == "GAMEPLAY":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        vehicles = get_available_vehicles()
                        state = "MENU"
                    elif event.key == pygame.K_r:
                        world, car, renderer = setup_game_environment(
                            car.texture_name, WIDTH, HEIGHT
                        )
                    elif event.key == pygame.K_m:
                        renderer.show_wireframe = not renderer.show_wireframe

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    closest_dist = float("inf")
                    for i, node in enumerate(world.nodes):
                        dist = math.hypot(node.x - mx, node.y - my)
                        if dist < 30.0 and dist < closest_dist:
                            closest_dist, selected_node = dist, i
                elif event.type == pygame.MOUSEBUTTONUP:
                    selected_node = None

        # --- 2. STATE LOGIC ---
        if state == "MENU":
            screen.fill((30, 32, 40))

            title = title_font.render("SELECT VEHICLE", True, (255, 255, 255))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

            for i, name in enumerate(vehicles):
                color = (
                    (50, 220, 120) if i == selected_idx else (150, 150, 150)
                )
                prefix = ">> " if i == selected_idx else "   "
                text = font.render(f"{prefix}{name}", True, color)
                screen.blit(text, (WIDTH // 2 - 150, 250 + i * 35))

            inst = font.render(
                "Arrows to navigate | ENTER to start", True, (100, 100, 100)
            )
            screen.blit(
                inst, (WIDTH // 2 - inst.get_width() // 2, HEIGHT - 100)
            )

        elif state == "GAMEPLAY":
            if selected_node is not None:
                mx, my = pygame.mouse.get_pos()
                world.nodes[selected_node].x = float(mx)
                world.nodes[selected_node].y = float(my)
                world.nodes[selected_node].vx = 0.0
                world.nodes[selected_node].vy = 0.0

            car.apply_inputs(pygame.key.get_pressed(), dt)
            car.apply_tire_friction(dt)

            # C++ engine performs internal 8x sub-stepping per step call
            world.step(dt, float(WIDTH), float(HEIGHT))

            screen.fill((45, 48, 56))
            renderer.render(screen, world, car, selected_node, dt)

            hud = [
                f"Vehicle : {car.texture_name}",
                "WASD    : Drive",
                "R       : Repair / Reset",
                "M       : Toggle Wireframe",
                "ESC     : Back to Menu",
            ]
            for idx, line in enumerate(hud):
                screen.blit(
                    font.render(line, True, (200, 210, 225)),
                    (15, 15 + idx * 22),
                )

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()