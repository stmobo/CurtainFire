import pygame
import numpy as np
import math
import random
import entities
import game_data

all_effects = pygame.sprite.Group()

class Effect(entities.Entity):
    def __init__(self, pos, rot, tm, scale):
        entities.Entity.__init__(self, pos, rot)
        all_effects.add(self)

        self.t = 0
        self.len = tm
        self.scale = scale

    def update(self, dt):
        self.t += dt


class ExplosionEffect(Effect):
    def __init__(self, pos, rot, length, scale):
        Effect.__init__(self, pos, rot, length, scale)

        self.image = pygame.Surface(game_data.screen_dims, flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0

        self.boxes = []
        for i in range(int(random.uniform(40, 55))):
            cen = np.array((
                random.uniform(-15, 15),
                random.uniform(-15, 15)
            ), dtype=np.int)

            sz = np.array((
                random.uniform(5, 15) * random.choice((-1, 1)),
                random.uniform(5, 15) * random.choice((-1, 1))
            ), dtype=np.float)

            col = pygame.color.Color(0, 0, 0, 0)
            col.hsva = (
                random.uniform(0, 65),
                100,
                100,
                100
            )

            self.boxes.append((cen, sz, col))

    def draw_box(self, box):
        t_factor = self.t / (self.len / 2)

        if self.t > self.len / 2:
            t_factor = 2 - t_factor

        scaled_sz = (self.scale * t_factor * box[1]).astype(np.int)

        r = pygame.rect.Rect((0, 0), scaled_sz)
        r.center = box[0] + self.pos

        pygame.draw.rect(self.image, box[2], r)

    def update(self, dt):
        Effect.update(self, dt)

        self.image.fill((0, 0, 0, 0))

        if self.t < self.len:
            for box in self.boxes:
                self.draw_box(box)
        else:
            self.kill()
