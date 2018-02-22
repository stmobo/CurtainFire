import pygame
import numpy as np
import math

screen_dims = (800, 800)

all_bullets = pygame.sprite.Group()
homing_bullets = pygame.sprite.Group()

class Entity(pygame.sprite.Sprite):
    def __init__(self, pos, rot):
        pygame.sprite.Sprite.__init__(self)

        self.pos = np.array(pos, dtype=np.float64)
        self.rot = rot

        self.vel = np.zeros(2, dtype=np.float64)
        self.acc = np.zeros(2, dtype=np.float64)

        self.rvel = 0
        self.racc = 0

    def update_pos(self, dt):
        self.vel = self.vel + (self.acc * dt)
        self.pos = self.pos + (self.vel * dt)

        self.rvel += self.racc * dt
        self.rot += self.rvel * dt

    def accelerate_to(self, target, magnitude, x_only=False, y_only=False):
        disp_vec = target - self.pos
        dist = np.sqrt(np.sum(disp_vec ** 2))
        unit_disp_vec = disp_vec / dist

        self.acc = unit_disp_vec * magnitude

        if y_only:
            self.acc[0] = 0

        if x_only:
            self.acc[1] = 0

    def rotate_to_velocity(self):
        rot = np.arctan2(self.vel[1], self.vel[0])

        self.image = pygame.transform.rotate(self.base_image, -np.degrees(rot))

    def update_rect(self):
        self.rect = self.image.get_rect()
        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

    def update(self, dt):
        self.update_pos(dt)
        self.update_rect()


class Player(Entity):
    movement_magnitude = 300

    def __init__(self, pos, rot):
        Entity.__init__(self, pos, rot)
        self.start_pos = pos
        self.start_rot = rot

        self.image = pygame.Surface([5, 5], flags=pygame.SRCALPHA)
        self.image.fill((0, 255, 0, 255))

    def update_movement(self):
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]:
            self.movement_magnitude = 150
        else:
            self.movement_magnitude = 300

        if pressed[pygame.K_LEFT] == pressed[pygame.K_RIGHT]:
            self.vel[0] = 0
        elif pressed[pygame.K_LEFT]:
            self.vel[0] = -self.movement_magnitude
        elif pressed[pygame.K_RIGHT]:
            self.vel[0] = self.movement_magnitude

        if pressed[pygame.K_UP] == pressed[pygame.K_DOWN]:
            self.vel[1] = 0
        elif pressed[pygame.K_UP]:
            self.vel[1] = -self.movement_magnitude
        elif pressed[pygame.K_DOWN]:
            self.vel[1] = self.movement_magnitude

    def reset(self):
        self.pos = np.array(self.start_pos)
        self.vel = np.zeros(2)
        self.acc = np.zeros(2)

        self.rot = self.start_rot
        self.rvel = self.racc = 0

    def update(self, dt):
        self.update_movement()
        self.update_pos(dt)

        if self.pos[0] < 0:
            self.pos[0] = 0
        elif self.pos[0] > screen_dims[0]:
            self.pos[0] = screen_dims[0]

        if self.pos[1] < 0:
            self.pos[1] = 0
        elif self.pos[1] > screen_dims[1]:
            self.pos[1] = screen_dims[1]

        self.update_rect()


class Bullet(Entity):
    def __init__(self, color, pos, rot):
        Entity.__init__(self, pos, rot)
        self.color = color

        all_bullets.add(self)


class ConstantPathBullet(Bullet):
    def __init__(self, color, pos, vel, acc):
        Bullet.__init__(self, color, pos, 0)

        self.vel = np.array(vel)
        self.acc = np.array(acc)

        self.base_image = pygame.Surface((20, 10), flags=pygame.SRCALPHA)
        self.base_image.fill((0, 0, 0, 0))
        pygame.draw.polygon(
            self.base_image, self.color,
            [(0, 0), (0, 10), (20, 5)]
        )

        self.image = self.base_image
        self.rect = self.image.get_rect()

    def update(self, dt):
        self.update_pos(dt)
        self.rotate_to_velocity()
        self.update_rect()


class HomingBullet(Bullet):
    def __init__(self, color, pos, target, target_acc):
        Bullet.__init__(self, color, pos, 0)

        self.target = target
        self.target_acc = target_acc

        self.base_image = pygame.Surface((20, 10), flags=pygame.SRCALPHA)
        self.base_image.fill((0, 0, 0, 0))
        pygame.draw.polygon(
            self.base_image, self.color,
            [(0, 0), (5, 5), (0, 10), (20, 5)]
        )

        self.image = self.base_image
        self.rect = self.image.get_rect()

        homing_bullets.add(self)

    def update(self, dt):
        self.accelerate_to(self.target.pos, self.target_acc)

        self.update_pos(dt)
        self.rotate_to_velocity()
        self.update_rect()

player = Player((400, 400), 0)
