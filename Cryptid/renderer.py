import math
import pygame
import pygame.gfxdraw
from particle_system import ParticleSystem


class Renderer:
    def __init__(self, world):
        self.particle_system = ParticleSystem()
        self.prev_rest_lengths = [b.rest_length for b in world.beams]
        self.show_wireframe = False
        self.car_texture_data = None

        # Universal tire sprite rendered under the chassis
        self.tire_surface = pygame.Surface((16, 32), pygame.SRCALPHA)
        pygame.draw.rect(
            self.tire_surface, (25, 25, 25), (0, 0, 16, 32), border_radius=4
        )
        for y in range(4, 29, 6):  # Tread lines
            pygame.draw.line(
                self.tire_surface, (10, 10, 10), (2, y), (14, y), 2
            )

    def load_car_texture(self, car):
        """UV Maps the car image exactly to the scaled rest_positions to prevent stretching."""
        if not car.texture_name or car.texture_name == "Default Wireframe Car":
            self.show_wireframe = True
            return

        try:
            raw_img = pygame.image.load(
                f"vehicles/{car.texture_name}.png"
            ).convert_alpha()
            crop_rect = raw_img.get_bounding_rect(min_alpha=1)
            if crop_rect.width > 0 and crop_rect.height > 0:
                img = raw_img.subsurface(crop_rect)
            else:
                img = raw_img
        except Exception as e:
            print(
                f"Warning: vehicles/{car.texture_name}.png not found. Falling back to wireframe. ({e})"
            )
            self.show_wireframe = True
            return

        img_w, img_h = img.get_size()

        # Get exact bounding box of the resting nodes
        pts = list(car.rest_positions.values())
        min_x, max_x = min(p[0] for p in pts), max(p[0] for p in pts)
        min_y, max_y = min(p[1] for p in pts), max(p[1] for p in pts)

        range_x = max_x - min_x if max_x - min_x > 0 else 1.0
        range_y = max_y - min_y if max_y - min_y > 0 else 1.0

        self.car_texture_data = {}

        # Crop normalized UV patches straight from the original high-res image
        for r in range(len(car.grid) - 1):
            for c in range(len(car.grid[r]) - 1):
                # Get the 4 nodes of this quad
                n_tl = car.rest_positions[car.grid[r][c]]
                n_tr = car.rest_positions[car.grid[r][c + 1]]
                n_bl = car.rest_positions[car.grid[r + 1][c]]
                n_br = car.rest_positions[car.grid[r + 1][c + 1]]

                # Find AABB of this specific quad
                patch_min_x = min(n_tl[0], n_tr[0], n_bl[0], n_br[0])
                patch_max_x = max(n_tl[0], n_tr[0], n_bl[0], n_br[0])
                patch_min_y = min(n_tl[1], n_tr[1], n_bl[1], n_br[1])
                patch_max_y = max(n_tl[1], n_tr[1], n_bl[1], n_br[1])

                # Map to normalized 0.0-1.0 space
                u1 = (patch_min_x - min_x) / range_x
                v1 = (patch_min_y - min_y) / range_y
                u2 = (patch_max_x - min_x) / range_x
                v2 = (patch_max_y - min_y) / range_y

                # Crop from actual PNG using UV bounds
                quad_crop_rect = pygame.Rect(
                    int(u1 * img_w),
                    int(v1 * img_h),
                    max(1, int((u2 - u1) * img_w)),
                    max(1, int((v2 - v1) * img_h)),
                )
                quad_crop_rect.clamp_ip(img.get_rect())

                patch = pygame.Surface(quad_crop_rect.size, pygame.SRCALPHA)
                patch.blit(img, (0, 0), quad_crop_rect)
                self.car_texture_data[(r, c)] = patch

    def draw_car_shadow(self, surface, car):
        corner_indices = [
            car.grid[0][0],
            car.grid[0][-1],
            car.grid[-1][-1],
            car.grid[-1][0],
        ]
        avg_vx = sum(car.world.nodes[i].vx for i in car.node_indices) / len(
            car.node_indices
        )
        avg_vy = sum(car.world.nodes[i].vy for i in car.node_indices) / len(
            car.node_indices
        )

        pts = []
        for idx in corner_indices:
            node = car.world.nodes[idx]
            pts.append(
                (
                    int(node.x + (-avg_vx * 0.02) + 2),
                    int(node.y + (-avg_vy * 0.02) + 12),
                )
            )
        pygame.gfxdraw.filled_polygon(surface, pts, (0, 0, 0, 90))

    def draw_tires(self, surface, car):
        fx, fy = car.get_heading_vector()

        car_angle_deg = math.degrees(math.atan2(-fy, fx)) - 90
        front_angle_deg = car_angle_deg - math.degrees(car.current_steer_angle)

        for w_idx in car.rear_wheels:
            node = car.world.nodes[w_idx]
            if math.isnan(node.x):
                continue
            rotated = pygame.transform.rotate(
                self.tire_surface, car_angle_deg
            )
            rect = rotated.get_rect(center=(int(node.x), int(node.y)))
            surface.blit(rotated, rect.topleft)

        for w_idx in car.front_wheels:
            node = car.world.nodes[w_idx]
            if math.isnan(node.x):
                continue
            rotated = pygame.transform.rotate(
                self.tire_surface, front_angle_deg
            )
            rect = rotated.get_rect(center=(int(node.x), int(node.y)))
            surface.blit(rotated, rect.topleft)

    def draw_skinned_car(self, surface, car):
        if not self.car_texture_data:
            return

        for r in range(len(car.grid) - 1):
            for c in range(len(car.grid[r]) - 1):
                tl = car.world.nodes[car.grid[r][c]]
                tr = car.world.nodes[car.grid[r][c + 1]]
                bl = car.world.nodes[car.grid[r + 1][c]]
                br = car.world.nodes[car.grid[r + 1][c + 1]]

                center_x = (tl.x + tr.x + bl.x + br.x) / 4.0
                center_y = (tl.y + tr.y + bl.y + br.y) / 4.0

                w = (
                    math.hypot(tr.x - tl.x, tr.y - tl.y)
                    + math.hypot(br.x - bl.x, br.y - bl.y)
                ) / 2.0
                h = (
                    math.hypot(bl.x - tl.x, bl.y - tl.y)
                    + math.hypot(br.x - tr.x, br.y - tr.y)
                ) / 2.0

                tc_x, tc_y = (tl.x + tr.x) / 2.0, (tl.y + tr.y) / 2.0
                bc_x, bc_y = (bl.x + br.x) / 2.0, (bl.y + br.y) / 2.0
                angle = math.atan2(bc_y - tc_y, bc_x - tc_x) - math.pi / 2.0

                patch = self.car_texture_data.get((r, c))
                if patch is None:
                    continue

                scaled = pygame.transform.smoothscale(
                    patch, (max(1, int(w) + 2), max(1, int(h) + 2))
                )
                rotated = pygame.transform.rotate(
                    scaled, -math.degrees(angle)
                )

                rect = rotated.get_rect(center=(int(center_x), int(center_y)))
                surface.blit(rotated, rect.topleft)

    def render(self, surface, world, car, selected_node, dt):
        while len(self.prev_rest_lengths) < len(world.beams):
            self.prev_rest_lengths.append(
                world.beams[len(self.prev_rest_lengths)].rest_length
            )

        for i, beam in enumerate(world.beams):
            diff = abs(beam.rest_length - self.prev_rest_lengths[i])
            if diff > 0.02:
                n_a, n_b = world.nodes[beam.node_a], world.nodes[beam.node_b]
                self.particle_system.emit(
                    (n_a.x + n_b.x) / 2.0, (n_a.y + n_b.y) / 2.0, count=1
                )
            self.prev_rest_lengths[i] = beam.rest_length

        self.draw_car_shadow(surface, car)

        if not self.show_wireframe:
            self.draw_tires(surface, car)

        self.draw_skinned_car(surface, car)

        car_beam_set = set(car.beam_indices)
        car_node_set = set(car.node_indices)

        for i, beam in enumerate(world.beams):
            if not self.show_wireframe and i in car_beam_set:
                continue

            n_a, n_b = world.nodes[beam.node_a], world.nodes[beam.node_b]
            if math.isnan(n_a.x) or math.isnan(n_b.x):
                continue

            stress = abs(
                math.hypot(n_b.x - n_a.x, n_b.y - n_a.y) - beam.rest_length
            )
            stress_factor = min(stress / 25.0, 1.0)

            r, g, b = (
                255,
                int(255 * (1.0 - stress_factor)),
                int(200 * (1.0 - stress_factor)),
            )
            thickness = 2 if stress_factor < 0.4 else 4
            pygame.draw.line(
                surface,
                (r, g, b),
                (int(n_a.x), int(n_a.y)),
                (int(n_b.x), int(n_b.y)),
                thickness,
            )

        for i, node in enumerate(world.nodes):
            if not self.show_wireframe and i in car_node_set:
                continue
            if math.isnan(node.x) or math.isnan(node.y):
                continue

            color, radius = (50, 220, 120), 5
            if i in car.front_wheels or i in car.rear_wheels:
                color, radius = (255, 200, 50), 7
            elif node.mass <= 0.0:
                color, radius = (120, 120, 120), 6

            if i == selected_node:
                color = (255, 50, 50)
            pygame.draw.circle(
                surface, color, (int(node.x), int(node.y)), radius
            )

        self.particle_system.update(dt)
        self.particle_system.draw(surface)