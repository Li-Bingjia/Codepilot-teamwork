# ...existing code...
import pygame
import os
from settings import *
from support import import_folder
from sprites import Generic
from random import randint, choice

class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        # use alpha surface so BLEND_RGBA_MULT behaves predictably
        self.full_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()

        # keep colors as lists for easy mutation
        self.start_color = [255, 255, 255]
        self.end_color = [38, 101, 189]

        # current & target for smooth transitions
        self.current = list(self.start_color)
        self.target = list(self.start_color)  # start as daytime by default

        # color units per second (tweak: larger -> faster transition)
        self.transition_speed = 60.0

        self.is_raining = False
 
    def set_time(self, progress):
        # progress: 0.0~1.0, 0=白天, 1=夜色
        self.target = [
            int(self.start_color[i] + (self.end_color[i] - self.start_color[i]) * progress)
            for i in range(3)
        ]
    def start_rain(self):
        self.target = list(self.end_color)
        self.is_raining = True

    def stop_rain(self):
        # smooth transition back to day
        self.target = list(self.start_color)
        self.is_raining = False

    def force_day(self):
        # immediate jump to day (no smoothing)
        self.target = list(self.start_color)
        self.current = list(self.start_color)
        self.is_raining = False

    def display(self, dt):
        # dt can be seconds or milliseconds; normalize to seconds
        if dt is None:
            return
        if dt > 1:
            dt = dt / 1000.0

        # move each channel toward its target at transition_speed per second
        for i in range(3):
            if self.current[i] < self.target[i]:
                self.current[i] = min(self.current[i] + self.transition_speed * dt, self.target[i])
            elif self.current[i] > self.target[i]:
                self.current[i] = max(self.current[i] - self.transition_speed * dt, self.target[i])

            # ensure integer in 0..255
            self.current[i] = max(0, min(255, int(self.current[i])))
        #print("Sky color:", self.current) 
        # fill and blit using multiply so underlying sprites keep tinting
        self.full_surf.fill(tuple(self.current))
        self.display_surface.blit(self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

class Drop(Generic):
    def __init__(self, surf, pos, moving, groups, z):
        # general setup
        super().__init__(pos, surf, groups, z)
        self.lifetime = randint(400, 500)
        self.start_time = pygame.time.get_ticks()

        # moving
        self.moving = moving
        if self.moving:
            self.pos = pygame.math.Vector2(self.rect.topleft)
            self.direction = pygame.math.Vector2(-2, 4)
            self.speed = randint(200, 250)

    def update(self, dt):
        # movement
        if self.moving:
            self.pos += self.direction * self.speed * dt
            self.rect.topleft = (round(self.pos.x), round(self.pos.y))

        # timer
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

class Rain:
    def __init__(self, all_sprites):
        self.all_sprites = all_sprites
        base = os.path.dirname(__file__)
        self.rain_drops = import_folder(os.path.join(base, '..', 'graphics', 'rain', 'drops'))
        self.rain_floor = import_folder(os.path.join(base, '..', 'graphics', 'rain', 'floor'))
        self.floor_w, self.floor_h = pygame.image.load(os.path.join(base, '..', 'graphics', 'world', 'ground.png')).get_size()

    def create_floor(self):
        Drop(
            surf = choice(self.rain_floor),
            pos = (randint(0, self.floor_w), randint(0, self.floor_h)),
            moving = False,
            groups = self.all_sprites,
            z = LAYERS['rain floor']
        )

    def create_drops(self):
        Drop(
            surf = choice(self.rain_drops),
            pos = (randint(0, self.floor_w), randint(0, self.floor_h)),
            moving = True,
            groups = self.all_sprites,
            z = LAYERS['rain drops']
        )

    def update(self):
        self.create_floor()
        self.create_drops()