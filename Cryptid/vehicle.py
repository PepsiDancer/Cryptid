import math
import pygame

# ---------------------------------------------------------
# DATA-DRIVEN VEHICLE BLUEPRINT
# ---------------------------------------------------------
CAR_BLUEPRINT = {
    "nodes": [
        # Row 0: Front Bumper (Curved)
        {"pos": (-24, -85), "mass": 1.0},  # 0
        {"pos": (  0, -90), "mass": 1.0},  # 1 
        {"pos": ( 24, -85), "mass": 1.0},  # 2
        # Row 1: Front Axle
        {"pos": (-32, -50), "mass": 1.5, "is_front_wheel": True},  # 3
        {"pos": (  0, -50), "mass": 1.5},  # 4
        {"pos": ( 32, -50), "mass": 1.5, "is_front_wheel": True},  # 5
        # Row 2: Cabin Front
        {"pos": (-34, -15), "mass": 1.2},  # 6
        {"pos": (  0, -15), "mass": 1.0},  # 7
        {"pos": ( 34, -15), "mass": 1.2},  # 8
        # Row 3: Cabin Middle
        {"pos": (-34,  15), "mass": 1.2},  # 9
        {"pos": (  0,  15), "mass": 1.0},  # 10
        {"pos": ( 34,  15), "mass": 1.2},  # 11
        # Row 4: Cabin Rear
        {"pos": (-32,  45), "mass": 1.2},  # 12
        {"pos": (  0,  45), "mass": 1.0},  # 13
        {"pos": ( 32,  45), "mass": 1.2},  # 14
        # Row 5: Rear Axle
        {"pos": (-30,  70), "mass": 1.5, "is_rear_wheel": True},   # 15
        {"pos": (  0,  70), "mass": 1.0},  # 16
        {"pos": ( 30,  70), "mass": 1.5, "is_rear_wheel": True},   # 17
        # Row 6: Rear Bumper
        {"pos": (-24,  95), "mass": 1.0},  # 18
        {"pos": (  0,  98), "mass": 1.0},  # 19
        {"pos": ( 24,  95), "mass": 1.0},  # 20
    ],
    "zone_properties": {
        "crumple_zone_front": {"stiffness": 2200.0, "damping": 25.0, "yield_thresh": 18000.0, "creep": 15.0},
        "cabin_rigid":         {"stiffness": 8000.0, "damping": 60.0, "yield_thresh": 250000.0, "creep": 2.0},
        "crumple_zone_rear":  {"stiffness": 2000.0, "damping": 25.0, "yield_thresh": 16000.0, "creep": 15.0}
    },
    "beams": {
        "crumple_zone_front": [
            (0,1), (1,2), (3,4), (4,5), (0,3), (1,4), (2,5), (3,6), (4,7), (5,8), 
            (0,4), (1,3), (1,5), (2,4), (3,7), (4,6), (4,8), (5,7), (0,5), (2,3), (3,8), (5,6)
        ],
        "cabin_rigid": [
            (6,7), (7,8), (6,8), (9,10), (10,11), (9,11), (12,13), (13,14), (12,14),
            (6,9), (7,10), (8,11), (9,12), (10,13), (11,14), (6,10), (7,9), (7,11), 
            (8,10), (9,13), (10,12), (10,14), (11,13), (6,11), (8,9), (9,14), (11,12)
        ],
        "crumple_zone_rear": [
            (15,16), (16,17), (18,19), (19,20), (12,15), (13,16), (14,17), (15,18), (16,19), (17,20),
            (12,16), (13,15), (13,17), (14,16), (15,19), (16,18), (16,20), (17,19), (12,17), (14,15), (15,20), (17,18)
        ]
    }
}

class Car:
    def __init__(self, world, x, y, texture_name="Default Wireframe Car"):
        self.world = world
        self.texture_name = texture_name
        self.node_indices = []
        self.beam_indices = []
        self.front_wheels = []
        self.rear_wheels = []
        self.rest_positions = {} 
        
        self.grid = [
            [0, 1, 2],    # Bumper F
            [3, 4, 5],    # Axle F
            [6, 7, 8],    # Cabin F
            [9, 10, 11],  # Cabin M
            [12, 13, 14], # Cabin R
            [15, 16, 17], # Axle R
            [18, 19, 20]  # Bumper R
        ]
        
        self.engine_force = 18000.0       
        self.max_steer_angle = math.radians(28.0)  
        self.current_steer_angle = 0.0
        self.steer_speed = math.radians(140.0)    
        self.lateral_grip = 0.92          
        self.rolling_resistance = 0.08   
        
        # Calculate Aspect Ratio based on non-transparent pixel boundary rect
        img_aspect = 68.0 / 188.0
        if texture_name and texture_name != "Default Wireframe Car":
            try:
                img = pygame.image.load(f"vehicles/{texture_name}.png").convert_alpha()
                crop_rect = img.get_bounding_rect(min_alpha=1)
                if crop_rect.width > 0 and crop_rect.height > 0:
                    img_aspect = crop_rect.width / float(crop_rect.height)
                else:
                    img_aspect = img.get_width() / float(img.get_height())
            except Exception as e:
                print(f"Warning: Could not read image aspect ratio: {e}")
        
        self.build_from_blueprint(x, y, img_aspect)

    def build_from_blueprint(self, start_x, start_y, aspect_ratio):
        idx_offset = len(self.world.nodes) 
        
        bp_min_x = min(n["pos"][0] for n in CAR_BLUEPRINT["nodes"])
        bp_max_x = max(n["pos"][0] for n in CAR_BLUEPRINT["nodes"])
        bp_min_y = min(n["pos"][1] for n in CAR_BLUEPRINT["nodes"])
        bp_max_y = max(n["pos"][1] for n in CAR_BLUEPRINT["nodes"])
        
        bp_width = bp_max_x - bp_min_x
        bp_length = bp_max_y - bp_min_y
        
        target_width = bp_length * aspect_ratio
        scale_x = target_width / bp_width if bp_width > 0 else 1.0

        for i, node_data in enumerate(CAR_BLUEPRINT["nodes"]):
            lx = node_data["pos"][0] * scale_x
            ly = node_data["pos"][1] 
            
            node_idx = self.world.add_node(node_data["mass"], start_x + lx, start_y + ly)
            self.node_indices.append(node_idx)
            self.rest_positions[node_idx] = (lx, ly)
            
            if node_data.get("is_front_wheel"): self.front_wheels.append(node_idx)
            if node_data.get("is_rear_wheel"): self.rear_wheels.append(node_idx)

        for r in range(len(self.grid)):
            for c in range(len(self.grid[r])):
                self.grid[r][c] += idx_offset

        for zone_name, beam_pairs in CAR_BLUEPRINT["beams"].items():
            props = CAR_BLUEPRINT["zone_properties"][zone_name]
            for (n1_local, n2_local) in beam_pairs:
                n1_global, n2_global = n1_local + idx_offset, n2_local + idx_offset
                n1, n2 = self.world.nodes[n1_global], self.world.nodes[n2_global]
                rest_len = math.hypot(n2.x - n1.x, n2.y - n1.y)
                b_idx = self.world.add_beam(n1_global, n2_global, rest_len, 
                                            props["stiffness"], props["damping"], 
                                            props["yield_thresh"], props["creep"])
                self.beam_indices.append(b_idx)

    def get_heading_vector(self):
        rl, rr = self.world.nodes[self.rear_wheels[0]], self.world.nodes[self.rear_wheels[1]]
        fl, fr = self.world.nodes[self.front_wheels[0]], self.world.nodes[self.front_wheels[1]]
        rx, ry = (rl.x + rr.x) * 0.5, (rl.y + rr.y) * 0.5
        fx, fy = (fl.x + fr.x) * 0.5, (fl.y + fr.y) * 0.5
        dx, dy = fx - rx, fy - ry
        dist = math.hypot(dx, dy)
        return (0.0, -1.0) if dist < 1e-5 else (dx / dist, dy / dist)

    def apply_inputs(self, keys_pressed, dt):
        target_steer = 0.0
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]: target_steer -= self.max_steer_angle
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]: target_steer += self.max_steer_angle

        steer_diff = target_steer - self.current_steer_angle
        max_delta = self.steer_speed * dt
        self.current_steer_angle += max(-max_delta, min(max_delta, steer_diff))

        fx, fy = self.get_heading_vector()
        cos_s, sin_s = math.cos(self.current_steer_angle), math.sin(self.current_steer_angle)
        s_fx, s_fy = fx * cos_s - fy * sin_s, fx * sin_s + fy * cos_s

        throttle = 0.0
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]: throttle += 1.0
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]: throttle -= 0.6  

        if abs(throttle) > 0.01:
            drive_force = throttle * self.engine_force
            for w_idx in self.rear_wheels:
                node = self.world.nodes[w_idx]
                if node.mass > 0.0:
                    node.vx += (drive_force * fx / node.mass) * dt
                    node.vy += (drive_force * fy / node.mass) * dt
            for w_idx in self.front_wheels:
                node = self.world.nodes[w_idx]
                if node.mass > 0.0:
                    node.vx += (drive_force * s_fx / node.mass) * dt
                    node.vy += (drive_force * s_fy / node.mass) * dt

    def apply_tire_friction(self, dt):
        fx, fy = self.get_heading_vector()
        rx, ry = -fy, fx  
        cos_s, sin_s = math.cos(self.current_steer_angle), math.sin(self.current_steer_angle)
        s_fx, s_fy = fx * cos_s - fy * sin_s, fx * sin_s + fy * cos_s
        s_rx, s_ry = -s_fy, s_fx

        grip_factor = max(0.0, 1.0 - (self.lateral_grip * dt * 60.0))
        roll_factor = max(0.0, 1.0 - (self.rolling_resistance * dt * 60.0))

        for idx in self.node_indices:
            node = self.world.nodes[idx]
            if node.mass <= 0.0: continue
            
            cur_fx, cur_fy, cur_rx, cur_ry = (s_fx, s_fy, s_rx, s_ry) if idx in self.front_wheels else (fx, fy, rx, ry)

            v_long = node.vx * cur_fx + node.vy * cur_fy
            v_lat  = node.vx * cur_rx + node.vy * cur_ry

            node.vx = (v_long * roll_factor) * cur_fx + (v_lat * grip_factor) * cur_rx
            node.vy = (v_long * roll_factor) * cur_fy + (v_lat * grip_factor) * cur_ry