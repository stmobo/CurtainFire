import pygame
import numpy as np
import math
import random
import entities

def generate_wave_color():
    n_tries = 0
    while True:
        n1 = random.uniform(0, 255)
        n2 = random.uniform(32, 96)
        n3 = random.uniform(32, 96)

        if random.choice((True, False)):
            n2 = int(np.clip(n1+n2, 0, 255))
        else:
            n2 = int(np.clip(n1-n2, 0, 255))

        if random.choice((True, False)):
            n3 = int(np.clip(n1+n3, 0, 255))
        else:
            n3 = int(np.clip(n1-n3, 0, 255))

        candidate = random.sample((n1, n2, n3), k=3)

        if n_tries >= 4 or np.sum(candidate) > 96:
            return candidate

class Wave:
    def __init__(self, wave_size):
        self.bullets = pygame.sprite.Group()
        self.color = generate_wave_color()
        self.wave_size = wave_size
        self.n_bullets_spawned = 0

    def wave_completed(self):
        if len(self.bullets.sprites()) == 0 and self.n_bullets_spawned >= self.wave_size:
            return True
        else:
            return False

    def update(self):
        pass


class HomingBurstWave(Wave):
    def update(self):
        if self.n_bullets_spawned <= self.wave_size:
            new_sprite = entities.HomingBullet(
                self.color, (400, 100), entities.player, 100
            )

            new_sprite.vel = np.array([
                random.uniform(-200, 200),
                random.uniform(-50, 200)
            ])

            self.bullets.add(new_sprite)
            self.n_bullets_spawned += 1


class FixedSpreadWave(Wave):
    spread_angle = 137
    angle_offset = 0
    speed = 200

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)
        self.n_layers = random.uniform(3, 7)
        self.bullets_per_layer = int(wave_size / self.n_layers)

    def update(self):
        if self.n_bullets_spawned <= self.wave_size:
            current_layer = math.floor(self.n_bullets_spawned / self.bullets_per_layer)

            layer_pos = self.n_bullets_spawned % self.bullets_per_layer

            angle = np.radians(
                (self.spread_angle * (layer_pos / self.bullets_per_layer))
                - (self.spread_angle / 2)
                + self.angle_offset
            )

            # implicitly rotate to screen coordinates
            vel_x = np.sin(angle) * self.speed
            vel_y = np.cos(angle) * self.speed

            new_sprite = entities.ConstantPathBullet(
                self.color, (400, 100), (vel_x, vel_y), (0, 0)
            )

            self.bullets.add(new_sprite)
            self.n_bullets_spawned += 1

            new_layer = math.floor(self.n_bullets_spawned / self.bullets_per_layer)

            if current_layer != new_layer:
                self.angle_offset = random.uniform(-15, 15)


class TargetedSpreadWave(Wave):
    speed = 300

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)
        self.bullets_per_tick = int(random.uniform(1, 3))
        self.homing = random.choice((True, False))

        start_choices = [
            (10, 10),
            (10, 790),
            (790, 10),
            (790, 790)
        ]

        valid_starts = []

        for pt in start_choices:
            if np.sqrt(np.sum((entities.player.pos - pt) ** 2)) > self.speed:
                valid_starts.append(pt)

        self.start = np.array(random.choice(valid_starts), dtype=np.int)

    def update(self):
        for i in range(self.bullets_per_tick):
            if self.n_bullets_spawned <= self.wave_size:
                angle_offset = random.uniform(-30, 30)
                disp_vec = self.start - entities.player.pos

                base_angle = np.arctan2(disp_vec[0], disp_vec[1])
                angle = np.radians(angle_offset) + base_angle

                vel_x = -np.sin(angle) * self.speed
                vel_y = -np.cos(angle) * self.speed

                new_sprite = None
                if self.homing:
                    new_sprite = entities.HomingBullet(
                        self.color, self.start, entities.player, 400
                    )
                    new_sprite.vel = np.array((vel_x, vel_y))
                else:
                    new_sprite = entities.ConstantPathBullet(
                        self.color, self.start, (vel_x, vel_y), (0, 0)
                    )

                self.bullets.add(new_sprite)
                self.n_bullets_spawned += 1


class PatternedWave(Wave):
    # spawn points and target points are matched; spreads are fired from
    # spawn_points[i] to target_points[i]
    spread_angle = 120
    speed = 200
    layer_time = 1

    def __init__(self, wave_size, n_layers, spawn_points, target_points, color):
        Wave.__init__(self, wave_size)

        self.spawn_points = spawn_points
        self.target_points = target_points
        self.color = color

        self.t = 0
        self.last_layer = -1
        self.n_layers = n_layers
        self.bullets_per_layer = int(wave_size / self.n_layers)
        #self.wave_size = self.n_layers * self.bullets_per_layer
        self.bullets_per_point = int(self.bullets_per_layer / len(self.spawn_points))

    def spawn_spread(self, start, target):
        angle_offset = random.uniform(-3, 3)
        disp_vec = start - target

        base_angle = np.arctan2(disp_vec[0], disp_vec[1])

        for i in range(self.bullets_per_point):
            if self.n_bullets_spawned > self.wave_size:
                return

            angle = np.radians(
                (self.spread_angle * (i / self.bullets_per_point))
                - (self.spread_angle / 2)
                + angle_offset
            ) + base_angle

            vel_x = -np.sin(angle) * self.speed
            vel_y = -np.cos(angle) * self.speed

            new_sprite = entities.ConstantPathBullet(
                self.color, start, (vel_x, vel_y), (0, 0)
            )
            self.bullets.add(new_sprite)
            self.n_bullets_spawned += 1

    def update(self):
        self.t += 0.025
        if self.n_bullets_spawned <= self.wave_size:
            current_layer = math.floor(self.t / self.layer_time)

            if current_layer > self.last_layer:
                for start, target in zip(self.spawn_points, self.target_points):
                    self.spawn_spread(np.array(start), np.array(target))
                self.last_layer = current_layer


class TrianglePatternWave(PatternedWave):
    def __init__(self, wave_size):
        PatternedWave.__init__(
            self, wave_size, int(random.uniform(3, 7)),
            [(400, 5), (5, 795), (795, 795)],
            [(400, 400), (400, 400), (400, 400)],
            generate_wave_color()
        )


class HorizontalPatternWave(PatternedWave):
    def __init__(self, wave_size):
        PatternedWave.__init__(
            self, wave_size, int(random.uniform(2, 4)),
            [(10, 400), (790, 400)],
            [(790, 400), (10, 400)],
            generate_wave_color()
        )

        self.spread_angle = 180


class VerticalPatternWave(PatternedWave):
    def __init__(self, wave_size):
        PatternedWave.__init__(
            self, wave_size, int(random.uniform(2, 4)),
            [(400, 10), (400, 790)],
            [(400, 790), (400, 10)],
            generate_wave_color()
        )

        self.spread_angle = 180


possible_wave_types = [
    FixedSpreadWave,
    HomingBurstWave,
    TrianglePatternWave,
    HorizontalPatternWave,
    VerticalPatternWave,
    TargetedSpreadWave
]

wave_queue = []
current_wave = None
wave_completion_time = None

base_wave_size = 40
wave_size_increase = 15
wave_size_sigma = wave_size_increase / 2

current_wave_size = 0
current_wave_number = 0
score = 0

def reset():
    global current_wave, wave_completion_time, wave_queue, base_wave_size
    global current_wave_number, score, current_wave_size

    wave_queue = []
    base_wave_size = 75
    current_wave_number = 1
    score = 0
    current_wave_size = int(random.normalvariate(base_wave_size, wave_size_sigma))

    print("Starting waves..")
    print("  Starting wave "+str(current_wave_number))
    print("  Current wave size: "+str(current_wave_size))

    current_wave = random.choice(possible_wave_types)(current_wave_size)
    wave_completion_time = None

def next_wave():
    global current_wave, wave_completion_time, wave_queue
    global base_wave_size, wave_size_increase, current_wave_number, current_wave_size

    current_wave_number += 1

    if len(wave_queue) == 0:
        wave_queue = random.sample(
            possible_wave_types, k=len(possible_wave_types)
        )

    base_wave_size += wave_size_increase
    current_wave_size = int(random.normalvariate(base_wave_size, wave_size_sigma))
    print("  Starting wave "+str(current_wave_number))
    print("  Current wave size: "+str(current_wave_size))
    print("  Current score: "+str(score))

    current_wave = wave_queue.pop()(current_wave_size)
    wave_completion_time = None

def update():
    global current_wave, wave_completion_time

    current_wave.update()
    if current_wave.wave_completed():
        if wave_completion_time is None:
            print("Wave completed!")
            wave_completion_time = pygame.time.get_ticks()

        break_time = pygame.time.get_ticks() - wave_completion_time
        if break_time >= 500:  # .5 seconds
            next_wave()
    else:
        wave_completion_time = None

def wave_active():
    global current_wave, wave_completion_time

    if current_wave is None:
        return True
    return not current_wave.wave_completed()

def wave_completed():
    global current_wave, wave_completion_time

    return current_wave.wave_completed()