import pygame
import numpy as np
import math
import game_data

all_bullets = pygame.sprite.Group()
all_beams = pygame.sprite.Group()
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

        self.dead = False

    def kill(self):
        self.dead = True
        pygame.sprite.Sprite.kill(self)

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

    def rotate_towards_point(self, target):
        disp = self.pos - target
        rot = np.arctan2(disp[1], disp[0])

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

    def set_color(self, color):
        self.image.fill(color)

    def update_movement(self):
        pressed = pygame.key.get_pressed()

        left = pressed[pygame.K_LEFT] or pressed[pygame.K_a]
        right = pressed[pygame.K_RIGHT] or pressed[pygame.K_d]
        up = pressed[pygame.K_UP] or pressed[pygame.K_w]
        down = pressed[pygame.K_DOWN] or pressed[pygame.K_s]

        if pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]:
            self.movement_magnitude = 150
        else:
            self.movement_magnitude = 300

        if left == right:
            self.vel[0] = 0
        elif left:
            self.vel[0] = -self.movement_magnitude
        elif right:
            self.vel[0] = self.movement_magnitude

        if up == down:
            self.vel[1] = 0
        elif up:
            self.vel[1] = -self.movement_magnitude
        elif down:
            self.vel[1] = self.movement_magnitude

    def reset(self):
        self.pos = np.array(self.start_pos)
        self.vel = np.zeros(2)
        self.acc = np.zeros(2)

        self.rot = self.start_rot
        self.rvel = self.racc = 0

        self.dead = False

    def kill(self):
        Entity.kill(self)
        self.pos = np.zeros(2)

    def update(self, dt):
        if game_data.get_game_state() != 'title':
            self.update_movement()
            self.update_pos(dt)

        if self.pos[0] < 15:
            self.pos[0] = 15
        elif self.pos[0] > game_data.screen_dims[0]-15:
            self.pos[0] = game_data.screen_dims[0]-15

        if self.pos[1] < 15:
            self.pos[1] = 15
        elif self.pos[1] > game_data.screen_dims[1]-15:
            self.pos[1] = game_data.screen_dims[1]-15

        self.update_rect()


class Beam(Entity):
    def __init__(self, start, end, width, color):
        Entity.__init__(self, start, 0)
        self.color = color
        self.end = end
        self.width = width

        all_beams.add(self)

    def update(self, dt):
        self.update_pos(dt)

        self.image = pygame.Surface(game_data.screen_dims, flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        pygame.draw.line(
            self.image, self.color, self.pos, self.end, self.width
        )

        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0


class Ray(Beam):
    def __init__(self, start, end, width, color):
        Beam.__init__(self, start, end, width, color)
        self.target_vector = np.array((0, 1))

    def update(self, dt):
        self.update_pos(dt)

        disp_vec = self.end.astype(np.float) - self.pos.astype(np.float)
        disp_vec = disp_vec / np.sqrt(np.sum(disp_vec ** 2))
        self.target_vector = disp_vec

        endpt = np.zeros(2)

        if abs(disp_vec[0]) < abs(disp_vec[1]):
            r = disp_vec[0] / disp_vec[1]
            if disp_vec[1] < 0:
                endpt[1] = 0
                endpt[0] = self.pos[0] + (-r * self.pos[1])
            else:
                endpt[1] = game_data.screen_dims[1]
                endpt[0] = self.pos[0] + (r * (game_data.screen_dims[1] - self.pos[1]))
        else:
            r = disp_vec[1] / disp_vec[0]
            if disp_vec[0] < 0:
                endpt[0] = 0
                endpt[1] = self.pos[1] + (-r * self.pos[0])
            else:
                endpt[0] = game_data.screen_dims[0]
                endpt[1] = self.pos[1] + (r * (game_data.screen_dims[0] - self.pos[0]))

        self.image = pygame.Surface(game_data.screen_dims, flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        pygame.draw.line(
            self.image, self.color, self.pos, endpt, self.width
        )

        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0


class TrackingRay(Ray):
    def __init__(self, start, target, width, color):
        Ray.__init__(self, start, target.pos, width, color)

        self.target = target

    def update(self, dt):
        self.end = self.target.pos
        Ray.update(self, dt)


class MovingTrackerRay(TrackingRay):
    def __init__(self, following, target, width, color):
        TrackingRay.__init__(self, following.pos, target, width, color)

        self.following = following

    def update(self, dt):
        self.pos = self.following.pos
        TrackingRay.update(self, dt)


class TrackingBeam(Beam):
    def __init__(self, start, target, width, color):
        Beam.__init__(self, start, target.pos, width, color)

        self.target = target

    def update(self, dt):
        self.end = self.target.pos
        Beam.update(self, dt)


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


class TracerBullet(Bullet):
    def __init__(self, c1, c2, pos, vel, acc):
        Bullet.__init__(self, c1, pos, 0)

        self.color_2 = c2
        self.vel = np.array(vel)
        self.acc = np.array(acc)

        self.base1 = pygame.Surface((20, 10), flags=pygame.SRCALPHA)
        self.base1.fill((0, 0, 0, 0))
        pygame.draw.polygon(
            self.base1, self.color,
            [(0, 0), (0, 10), (20, 5)]
        )

        self.base2 = pygame.Surface((20, 10), flags=pygame.SRCALPHA)
        self.base2.fill((0, 0, 0, 0))
        pygame.draw.polygon(
            self.base2, self.color_2,
            [(0, 0), (0, 10), (20, 5)]
        )

        self.image = self.base_image = self.base1
        self.rect = self.image.get_rect()

    def update(self, dt):
        self.update_pos(dt)

        if pygame.time.get_ticks() % 200 > 100:
            self.base_image = self.base1
        else:
            self.base_image = self.base2

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
