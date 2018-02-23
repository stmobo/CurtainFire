import pygame
import numpy as np
import math
import random
import entities
import game_data

def generate_wave_color():
    c = pygame.Color(255, 255, 255, 255)

    c.hsva = (
        random.uniform(0, 360),
        random.uniform(85, 100),
        100,
        100
    )

    return c

class Wave:
    def __init__(self, wave_size):
        self.bullets = pygame.sprite.Group()
        self.color = generate_wave_color()
        self.wave_size = wave_size
        self.n_bullets_spawned = 0

    def wave_completed(self):
        if len(self.bullets.sprites()) == 0 and self.n_bullets_spawned >= self.wave_size-20:
            return True
        else:
            return False

    def update(self):
        pass

    def end(self):
        pass


class HomingBurstWave(Wave):
    name = "Raindrops"

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
    name = "Wavefronts"
    spread_angle = 137
    speed = 200

    def __init__(self, wave_size):
        self.n_spawners = int(random.uniform(1, 4))
        Wave.__init__(self, int(wave_size))

        self.n_layers = int(random.uniform(2, 5))
        self.bullets_per_layer = int(wave_size / self.n_layers)
        self.starts = []
        self.angle_offsets = []

        for i in range(self.n_layers):
            self.starts.append((int(random.uniform(200, 600)), 100))
            self.angle_offsets.append(random.uniform(-15, 15))

    def update_spawner(self, i):
        if self.n_bullets_spawned <= self.wave_size:
            current_layer = math.floor(self.n_bullets_spawned / self.bullets_per_layer)

            layer_pos = self.n_bullets_spawned % self.bullets_per_layer

            angle = np.radians(
                (self.spread_angle * (layer_pos / self.bullets_per_layer))
                - (self.spread_angle / 2)
                + self.angle_offsets[i]
            )

            # implicitly rotate to screen coordinates
            vel_x = np.sin(angle) * self.speed
            vel_y = np.cos(angle) * self.speed

            new_sprite = entities.ConstantPathBullet(
                self.color, self.starts[i], (vel_x, vel_y), (0, 0)
            )

            self.bullets.add(new_sprite)
            self.n_bullets_spawned += 1

            new_layer = math.floor(self.n_bullets_spawned / self.bullets_per_layer)

            if current_layer != new_layer:
                self.angle_offsets[i] = random.uniform(-15, 15)

    def update(self):
        for i in range(len(self.starts)):
            self.update_spawner(i)

class TargetedSpreadWave(Wave):
    name = "Rubberhose"
    speed = 400

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
                angle_offset = random.uniform(-20, 20)
                disp_vec = self.start - entities.player.pos

                base_angle = np.arctan2(disp_vec[0], disp_vec[1])
                angle = np.radians(angle_offset) + base_angle

                vel_x = -np.sin(angle) * self.speed
                vel_y = -np.cos(angle) * self.speed

                new_sprite = None
                if self.homing:
                    new_sprite = entities.HomingBullet(
                        self.color, self.start, entities.player, 200
                    )
                    new_sprite.vel = np.array((vel_x, vel_y))
                else:
                    new_sprite = entities.ConstantPathBullet(
                        self.color, self.start, (vel_x, vel_y), (0, 0)
                    )

                self.bullets.add(new_sprite)
                self.n_bullets_spawned += 1


class ClusterWave(Wave):
    name = "MIRV"
    bullets_per_cluster = 6
    leader_speed = 350

    cluster_speed = 250
    homing_cluster_speed = 50

    leader_detonate_distance = 5
    initialized = False

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)

        self.n_clusters = math.ceil(wave_size / self.bullets_per_cluster)
        self.wave_size = self.n_clusters * self.bullets_per_cluster
        self.targets = []
        self.leaders = []

        for i in range(self.n_clusters):
            self.targets.append(np.array((
                random.uniform(50, 750),
                random.uniform(50, 750)
            ), dtype=np.int))

    def update(self):
        if not self.initialized:
            self.initialized = True
            leader_color = (255, 255, 255, 255)

            for target in self.targets:
                start = np.array(
                    (random.uniform(20, 780), 795), dtype=np.int
                )

                disp_vec = start - target
                disp_vec = disp_vec / np.sqrt(np.sum(disp_vec ** 2))

                new_sprite = entities.TracerBullet(
                    self.color, leader_color, start,
                    disp_vec * -self.leader_speed, (0, 0)
                )

                self.bullets.add(new_sprite)
                self.leaders.append(new_sprite)
                game_data.change_score(1)
                self.n_bullets_spawned += 1
        else:
            for i, l, t in zip(range(self.n_clusters), self.leaders, self.targets):
                if l is None:
                    continue

                dist = np.sqrt(np.sum((l.pos - t) ** 2))
                if dist <= self.leader_detonate_distance:
                    homing = random.random() > .5
                    s = self.homing_cluster_speed if homing else self.cluster_speed
                    for angle in np.linspace(0, 2*np.pi, self.bullets_per_cluster, endpoint=False):
                        vel_x = -np.sin(angle) * s
                        vel_y = -np.cos(angle) * s

                        new_sprite = None
                        if homing:
                            new_sprite = entities.HomingBullet(
                                self.color, l.pos, entities.player, 400
                            )
                            new_sprite.vel = np.array((vel_x, vel_y))
                        else:
                            new_sprite = entities.ConstantPathBullet(
                                self.color, l.pos, (vel_x, vel_y), (0, 0)
                            )

                        self.bullets.add(new_sprite)
                        self.n_bullets_spawned += 1
                    l.kill()
                    self.leaders[i] = None


class GridLockWave(Wave):
    name = "Gridlock"
    grid_spacing = 30
    n_per_line = 10
    speed = 200

    def __init__(self, wave_size):
        self.n_side = math.floor((800 - 1) / self.grid_spacing)
        self.n_per_line = math.ceil(wave_size / (2 * self.n_side))

        Wave.__init__(self, 2 * self.n_side * self.n_per_line)

        self.t = 0

        self.bullet_spacing = 800 / self.speed / self.n_per_line / 2
        self.last_fire_cycle = -1

    def update(self):
        self.t += 0.025
        fire_cycle = math.floor(self.t / self.bullet_spacing)

        if fire_cycle > self.last_fire_cycle:
            self.last_fire_cycle = fire_cycle
            cycle_offset_x = random.uniform(-self.grid_spacing, self.grid_spacing)
            cycle_offset_y = random.uniform(-self.grid_spacing, self.grid_spacing)
            if self.n_bullets_spawned <= self.wave_size:
                for i in range(self.n_side):
                    if random.choice((True, False)):
                        x_sprite = entities.ConstantPathBullet(
                            self.color,
                            (1+(i*self.grid_spacing)+cycle_offset_x, 1),
                            (0, self.speed), (0, 0)
                        )
                        self.bullets.add(x_sprite)
                        self.n_bullets_spawned += 1

                    if random.choice((True, False)):
                        y_sprite = entities.ConstantPathBullet(
                            self.color,
                            (1, 1+(i*self.grid_spacing)+cycle_offset_y),
                            (self.speed, 0), (0, 0)
                        )
                        self.bullets.add(y_sprite)
                        self.n_bullets_spawned += 1


class HomingTracerWave(Wave):
    name = "Bombing Run"
    fire_period = 0.75
    bullet_speed = 200
    leader_speed = 300
    bullets_per_spread = 20

    initialized = False
    last_n = -1
    t = 0

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)

        self.bullets_per_spread = int(wave_size / 5)

    def update_leader(self, leader):
        for i in range(self.bullets_per_spread):
            if self.n_bullets_spawned <= self.wave_size:
                new_sprite = entities.HomingBullet(
                    self.color, leader.pos, entities.player, 400
                )

                new_sprite.vel = np.array((
                    random.uniform(-100, 100),
                    random.uniform(-100, 100)
                ))

                self.bullets.add(new_sprite)
                self.n_bullets_spawned += 1

    def update(self):
        self.t += 0.025
        if not self.initialized:
            self.initialized = True

            if random.choice((True, False)):
                self.leader_1 = entities.TracerBullet(
                    self.color, (255, 255, 255, 255),
                    (100, 5), (-50, self.leader_speed), (300, 0)
                )

                self.bullets.add(self.leader_1)

                self.leader_2 = entities.TracerBullet(
                    self.color, (255, 255, 255, 255),
                    (700, 795), (50, -self.leader_speed), (-300, 0)
                )

                self.bullets.add(self.leader_2)
            else:
                self.leader_1 = entities.TracerBullet(
                    self.color, (255, 255, 255, 255),
                    (795, 100), (-self.leader_speed, -50), (0, 300)
                )

                self.bullets.add(self.leader_1)

                self.leader_2 = entities.TracerBullet(
                    self.color, (255, 255, 255, 255),
                    (5, 700), (self.leader_speed, 50), (0, -300)
                )

                self.bullets.add(self.leader_2)
        else:
            n = math.floor(self.t / self.fire_period)

            if n > self.last_n:
                self.last_n = n

                if not self.leader_1.dead:
                    self.update_leader(self.leader_1)

                if not self.leader_2.dead:
                    self.update_leader(self.leader_2)


class TrackingSpreadWave(Wave):
    name = "Sharpshooter"
    fire_period = 1
    bullet_speed = 200
    leader_speed = 150
    spread_angle = 30

    initialized = False
    last_n = -1
    t = 0

    sub_n1 = -1
    sub_n2 = -1

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)

        self.bullets_per_spread = wave_size / 9

        self.beam_group = pygame.sprite.Group()

    def update_tracking_beam(self, tracking_beam):
        for angle_offset in np.linspace(0, self.spread_angle, self.bullets_per_spread):
            if self.n_bullets_spawned <= self.wave_size:
                base_angle = np.arctan2(
                    -tracking_beam.target_vector[0],
                    -tracking_beam.target_vector[1]
                )

                r_off = np.radians(angle_offset) - (np.radians(self.spread_angle) / 2)

                vel = np.array((
                    -np.sin(base_angle + r_off) * self.bullet_speed,
                    -np.cos(base_angle + r_off) * self.bullet_speed
                ))

                new_sprite = entities.ConstantPathBullet(
                    self.color, tracking_beam.pos, vel, np.zeros(2)
                )

                self.bullets.add(new_sprite)
                self.n_bullets_spawned += 1

    def update(self):
        self.t += 0.025
        if not self.initialized:
            self.initialized = True

            self.leader_1 = entities.TracerBullet(
                self.color, (255, 255, 255, 255),
                (100, 5), (0, self.leader_speed), (0, 0)
            )

            self.bullets.add(self.leader_1)

            self.leader_2 = entities.TracerBullet(
                self.color, (255, 255, 255, 255),
                (700, 795), (0, -self.leader_speed), (0, 0)
            )

            self.bullets.add(self.leader_2)

            self.tracking_beam_1 = entities.MovingTrackerRay(self.leader_1, entities.player, 1, self.color)
            self.tracking_beam_2 = entities.MovingTrackerRay(self.leader_2, entities.player, 1, self.color)
        else:
            n = math.floor(self.t / self.fire_period)

            if n > self.last_n:
                self.last_n = n

                if not self.leader_1.dead:
                    self.update_tracking_beam(self.tracking_beam_1)
                else:
                    self.tracking_beam_1.kill()

                if not self.leader_2.dead:
                    self.update_tracking_beam(self.tracking_beam_2)
                else:
                    self.tracking_beam_2.kill()

    def end(self):
        self.tracking_beam_1.kill()
        self.tracking_beam_2.kill()


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
    name = "Pulsar"

    def __init__(self, wave_size):
        PatternedWave.__init__(
            self, wave_size, int(random.uniform(3, 7)),
            [(400, 5), (5, 795), (795, 795)],
            [(400, 400), (400, 400), (400, 400)],
            generate_wave_color()
        )

        self.spread_angle = 60


class HorizontalPatternWave(PatternedWave):
    name = "Resonance"

    def __init__(self, wave_size):
        PatternedWave.__init__(
            self, wave_size, int(random.uniform(2, 4)),
            [(10, 400), (790, 400)],
            [(790, 400), (10, 400)],
            generate_wave_color()
        )

        self.spread_angle = 180


class VerticalPatternWave(PatternedWave):
    name = "Supercollider"

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
    TargetedSpreadWave,
    GridLockWave,
    ClusterWave,
    TrackingSpreadWave,
    HomingTracerWave
]

wave_queue = []
current_wave = None
wave_completion_time = None

starting_wave_size = 60
base_wave_size = starting_wave_size
wave_size_increase = 5
wave_size_sigma = wave_size_increase

force_starting_wave = FixedSpreadWave

def reset():
    global current_wave, wave_completion_time, wave_queue, base_wave_size
    global force_starting_wave

    wave_queue = random.sample(
        possible_wave_types, k=len(possible_wave_types)
    )

    base_wave_size = starting_wave_size
    game_data.current_wave_size = int(random.normalvariate(base_wave_size, wave_size_sigma))

    print("Starting waves..")
    print("  Starting wave "+str(game_data.current_wave_number))
    print("  Current wave size: "+str(game_data.current_wave_size))

    if current_wave is not None:
        current_wave.end()

    if force_starting_wave is not None:
        current_wave = force_starting_wave(game_data.current_wave_size)
    else:
        current_wave = wave_queue.pop()(game_data.current_wave_size)

    wave_completion_time = None

def next_wave():
    global current_wave, wave_completion_time, wave_queue
    global base_wave_size, wave_size_increase

    game_data.current_wave_number += 1

    if len(wave_queue) == 0:
        wave_queue = random.sample(
            possible_wave_types, k=len(possible_wave_types)
        )

    base_wave_size += wave_size_increase
    game_data.current_wave_size = int(random.normalvariate(base_wave_size, wave_size_sigma))
    print("  Starting wave "+str(game_data.current_wave_number))
    print("  Current wave size: "+str(game_data.current_wave_size))
    print("  Current score: "+str(game_data.score))

    current_wave = wave_queue.pop()(game_data.current_wave_size)
    wave_completion_time = None

def update():
    global current_wave, wave_completion_time

    current_wave.update()
    game_data.current_wave_size = current_wave.wave_size
    if current_wave.wave_completed():
        current_wave.end()

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
