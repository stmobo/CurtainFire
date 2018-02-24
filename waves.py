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

        self.wave_timer = base_wave_time

    def wave_completed(self):
        if len(self.bullets.sprites()) == 0 and self.n_bullets_spawned > 0:
            return True
        elif self.wave_timer <= 0:
            return True
        else:
            return False

    def update(self, dt):
        self.wave_timer -= dt

    def end(self):
        pass


class HomingBurstWave(Wave):
    name = "Raindrops"

    def update(self, dt):
        Wave.update(self, dt)

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

    def update(self, dt):
        Wave.update(self, dt)

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

    def update(self, dt):
        Wave.update(self, dt)

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

    def update(self, dt):
        Wave.update(self, dt)

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

    def update(self, dt):
        Wave.update(self, dt)
        self.t += dt

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
    fire_period = 0.5
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
                    random.uniform(-50, 50),
                    random.uniform(-50, 50)
                ))

                self.bullets.add(new_sprite)
                self.n_bullets_spawned += 1

    def update(self, dt):
        Wave.update(self, dt)
        self.t += dt

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
    name = "Tracker"
    fire_period = 0.75
    bullet_speed = 200
    leader_speed = 150
    spread_angle = 30

    initialized = False
    last_n = -1
    t = 0

    sub_n1 = -1
    sub_n2 = -1
    flash_timer = 0.25

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)

        travel_time = 795 / self.leader_speed
        firing_periods = math.floor(travel_time / self.fire_period)

        self.bullets_per_spread = int(wave_size / firing_periods)

        self.beam_group = pygame.sprite.Group()

        self.tracking_beam_color = pygame.Color(
            int(self.color.r / 3),
            int(self.color.g / 3),
            int(self.color.b / 3),
        )

    def update_tracking_beam(self, tracking_beam):
        for angle_offset in np.linspace(0, self.spread_angle, self.bullets_per_spread):
            if self.n_bullets_spawned <= self.wave_size:
                target_vector = entities.player.pos - tracking_beam.pos
                base_angle = np.arctan2(
                    -target_vector[0],
                    -target_vector[1]
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

    def update(self, dt):
        Wave.update(self, dt)

        self.t += dt
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

            self.tracking_beam_1 = entities.MovingTrackerRay(self.leader_1, entities.player, 1, self.tracking_beam_color)
            self.tracking_beam_2 = entities.MovingTrackerRay(self.leader_2, entities.player, 1, self.tracking_beam_color)
        else:
            n = math.floor(self.t / self.fire_period)

            if self.flash_timer > 0:
                self.flash_timer -= dt

                self.tracking_beam_1.color = (255, 255, 255, 255)
                self.tracking_beam_2.color = (255, 255, 255, 255)
            else:
                self.tracking_beam_1.color = self.tracking_beam_color
                self.tracking_beam_2.color = self.tracking_beam_color

            if n > self.last_n:
                self.flash_timer = 0.15
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

        base_angle = np.arctan2(disp_vec[0], disp_vec[1]) + np.radians(random.uniform(-15, 15))

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

    def update(self, dt):
        Wave.update(self, dt)
        self.t += dt

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


class BurstFireWave(Wave):
    name = "Turrets"

    # subtype 0 defaults
    beginning_cone_angle = 90
    end_cone_angle = 30
    lock_pause_time = 0.15
    bullet_speed = 300

    initial_track_time = 1  # extra time added to first burst

    def __init__(self, wave_size):
        Wave.__init__(self, wave_size)

        self.n_sources = random.randint(1, 3)
        self.bursts_per_source = random.randint(2, 4)
        self.lock_time = random.uniform(0.4, 0.75)

        self.initialized = False
        self.stopped = False
        self.sources = []
        self.firing_angles = []
        self.t = -self.initial_track_time
        self.n = 1

        subtype = random.randint(0, 2)

        if subtype == 1:
            # Tight (5 degree) spread, fast bullets and firing, more bursts
            self.n_sources = random.randint(2, 5)
            self.end_cone_angle = 5
            self.bullet_speed = 650
            self.bursts_per_source = random.randint(5, 9)
            self.lock_time = random.uniform(0.3, 0.5)
            self.lock_pause_time = 0.05
        elif subtype == 2:
            # Wide (90 degree) spread, fast convergence, slow bullets
            self.end_cone_angle = 45
            self.lock_time = random.uniform(0.3, 0.5)
            self.bullet_speed = 150

        cycles_per_burst = int(self.lock_pause_time / 0.025)
        n_cycles = int(self.n_sources * self.bursts_per_source * cycles_per_burst)

        self.bullets_per_cycle = math.ceil(wave_size / n_cycles)
        self.wave_size = self.bullets_per_cycle * n_cycles

        self.wave_timer = (self.lock_time + self.lock_pause_time) * self.n_sources * self.bursts_per_source
        self.wave_timer += self.initial_track_time
        self.tracking_beam_color = pygame.Color(
            int(self.color.r / 3),
            int(self.color.g / 3),
            int(self.color.b / 3)
        )

    def add_source(self):
        pos = np.array((
            random.randint(30, 770),
            random.randint(30, 770),
        ))

        m = entities.MarkerBullet(self.color, pos)
        r1 = entities.Ray(pos, np.zeros(2), 1, self.tracking_beam_color)
        r2 = entities.Ray(pos, np.zeros(2), 1, self.tracking_beam_color)

        self.bullets.add(m)
        self.firing_angles.append(0)

        self.sources.append((m, r1, r2))

    def angle_towards_target(self):
        for i, s in enumerate(self.sources):
            m, r1, r2 = s

            disp_vec = entities.player.pos - m.pos
            base_angle = np.arctan2(
                -disp_vec[0],
                -disp_vec[1],
            )

            self.firing_angles[i] = base_angle

            cone_angle_adj = (self.beginning_cone_angle - self.end_cone_angle) * ((self.lock_time - self.t) / self.lock_time)
            cone_angle_adj += self.end_cone_angle

            r1.end = m.pos+np.array((
                -np.sin(base_angle + np.radians(cone_angle_adj)),
                -np.cos(base_angle + np.radians(cone_angle_adj)),
            ))

            r2.end = m.pos+np.array((
                -np.sin(base_angle - np.radians(cone_angle_adj)),
                -np.cos(base_angle - np.radians(cone_angle_adj)),
            ))

    def fire_towards_target(self):
        for base_angle, src in zip(self.firing_angles, self.sources):
            m, r1, r2 = src

            for i in range(self.bullets_per_cycle):
                angle_adj = random.uniform(-self.end_cone_angle, self.end_cone_angle)
                angle = base_angle + np.radians(angle_adj)

                vel = np.array((
                    -np.sin(angle),
                    -np.cos(angle),
                )) * self.bullet_speed * random.uniform(0.85, 1.15)

                new_sprite = entities.ConstantPathBullet(
                    self.color, m.pos, vel, (0, 0)
                )
                self.bullets.add(new_sprite)
                self.n_bullets_spawned += 1


    def end(self):
        for m, r1, r2 in self.sources:
            m.kill()
            r1.kill()
            r2.kill()
        self.sources = []

    def update(self, dt):
        Wave.update(self, dt)
        self.t += dt

        if self.stopped:
            return

        if not self.initialized:
            self.initialized = True
            for i in range(self.n_sources):
                self.add_source()

        if self.t < 0:
            for m, r1, r2 in self.sources:
                m.set_color((128, 128, 128))
                r1.color = (0, 0, 0)
                r2.color = (0, 0, 0)
        elif self.t <= self.lock_time:
            self.angle_towards_target()
            for m, r1, r2 in self.sources:
                m.set_color(self.color)
                r1.color = self.tracking_beam_color
                r2.color = self.tracking_beam_color
        elif self.t < self.lock_time + self.lock_pause_time:
            self.fire_towards_target()
            for m, r1, r2 in self.sources:
                r1.color = (255, 255, 255)
                r2.color = (255, 255, 255)
        elif self.t > self.lock_time + self.lock_pause_time:
            self.t = 0
            self.n += 1

            if self.n >= self.bursts_per_source:
                self.stopped = True
                self.end()


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
    HomingTracerWave,
    BurstFireWave
]

wave_queue = []
current_wave = None
wave_completion_time = None

starting_wave_time = 11
base_wave_time = starting_wave_time
wave_time_decrease = .5
min_wave_time = 3

starting_wave_size = 60
base_wave_size = starting_wave_size
wave_size_increase = 5

wave_size_sigma = wave_size_increase

force_starting_wave = None

def reset():
    global current_wave, wave_completion_time, wave_queue, base_wave_size
    global force_starting_wave, base_wave_time, starting_wave_time, wave_time_decrease
    global wave_size_increase, starting_wave_size

    wave_queue = random.sample(
        possible_wave_types, k=len(possible_wave_types)
    )

    if game_data.difficulty == 0:
        starting_wave_time = 13
        wave_time_decrease = .25
        starting_wave_size = 40
        wave_size_increase = 5
    elif game_data.difficulty == 2:
        starting_wave_time = 9
        wave_time_decrease = .5
        starting_wave_size = 80
        wave_size_increase = 15

    base_wave_time = starting_wave_time
    base_wave_size = starting_wave_size
    game_data.current_wave_size = int(random.uniform(
        base_wave_size - wave_size_increase, base_wave_size + wave_size_increase
    ))

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
    global base_wave_size, wave_size_increase, base_wave_time, wave_time_decrease

    game_data.current_wave_number += 1

    if len(wave_queue) == 0:
        wave_queue = random.sample(
            possible_wave_types, k=len(possible_wave_types)
        )

    base_wave_size += wave_size_increase
    game_data.current_wave_size = int(random.uniform(
        base_wave_size - wave_size_increase, base_wave_size + wave_size_increase
    ))

    base_wave_time -= wave_time_decrease
    if base_wave_time < min_wave_time:
        base_wave_time = min_wave_time

    print("  Spawned {} out of {} bullets in last wave".format(
        current_wave.n_bullets_spawned, current_wave.wave_size
    ))

    print("  Starting wave "+str(game_data.current_wave_number))
    print("  Current wave size: "+str(game_data.current_wave_size))
    print("  Current score: "+str(game_data.score))

    current_wave = wave_queue.pop()(game_data.current_wave_size)
    wave_completion_time = None

def update(dt):
    global current_wave, wave_completion_time

    current_wave.update(dt)
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
