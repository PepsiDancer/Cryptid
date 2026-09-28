import math
import random
import pygame


class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(100.0, 400.0)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.color = color
        self.life, self.decay = 1.0, random.uniform(1.5, 3.5)

    def update(self, dt):
        self.vy += 800.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= self.decay * dt


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=3, color=(255, 230, 100)):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            c = (
                int(p.color[0] * p.life),
                int(p.color[1] * p.life),
                int(p.color[2] * p.life),
            )
            pygame.draw.circle(
                surface, c, (int(p.x), int(p.y)), max(1, int(2 * p.life))
            )