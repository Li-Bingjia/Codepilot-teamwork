import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
import os
from random import choice

class SoilTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
    def __init__(self, plant_type, groups, soil, check_watered):
        super().__init__(groups)
        
        # 保留原路径：graphics/fruit/corn
        self.plant_type = plant_type
        self.frames = import_folder(os.path.join(os.path.dirname(__file__), '..', 'graphics', 'fruit', plant_type))
        
        # 防止 frames 为空（路径错或没图）
        if not self.frames:
            print(f"Warning: No plant frames found for {plant_type}! Using placeholder.")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((0, 255, 0))  # 绿色占位
            self.frames = [placeholder] * 3  # 至少3帧防崩溃

        self.soil = soil
        self.check_watered = check_watered

        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[plant_type]
        self.harvestable = False

        # 安全取帧
        self.image = self.frames[self.age]
        self.y_offset = -16 if plant_type == 'corn' else -8
        self.rect = self.image.get_rect(midbottom=soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
        self.z = LAYERS['ground plant']

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            # 安全更新图像
            frame_index = min(int(self.age), self.max_age)
            self.image = self.frames[frame_index]
            self.rect = self.image.get_rect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites):
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.soil_surfs = import_folder_dict(os.path.join(os.path.dirname(__file__), '..', 'graphics', 'soil'))
        self.water_surfs = import_folder(os.path.join(os.path.dirname(__file__), '..', 'graphics', 'soil_water'))

        self.create_soil_grid()
        self.create_hit_rects()

        self.hoe_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), '..', 'audio', 'hoe.wav'))
        self.hoe_sound.set_volume(0.1)
        self.plant_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), '..', 'audio', 'plant.wav')) 
        self.plant_sound.set_volume(0.2)

    def create_soil_grid(self):
        ground = pygame.image.load(os.path.join(os.path.dirname(__file__), '..', 'graphics', 'world', 'ground.png')).convert_alpha()
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE
        self.grid = [[[] for _ in range(h_tiles)] for _ in range(v_tiles)]
        for x, y, _ in load_pygame(os.path.join(os.path.dirname(__file__), '..', 'data', 'map.tmx')).get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')

    def create_hit_rects(self):
        self.hit_rects = []
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'F' in cell:
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    self.hit_rects.append(rect)

    # 新增：用于存档加载时重建耕地
    def create_soil_sprites(self):
        """重建所有耕地瓦片（存档加载专用）"""
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                    # 边界安全检查
                    t = index_row > 0 and 'X' in self.grid[index_row - 1][index_col]
                    b = index_row < len(self.grid) - 1 and 'X' in self.grid[index_row + 1][index_col]
                    r = index_col < len(row) - 1 and 'X' in row[index_col + 1]
                    l = index_col > 0 and 'X' in row[index_col - 1]

                    tile_type = 'o'
                    if all((t, r, b, l)): tile_type = 'x'
                    elif l and not any((t, r, b)): tile_type = 'r'
                    elif r and not any((t, l, b)): tile_type = 'l'
                    elif r and l and not any((t, b)): tile_type = 'lr'
                    elif t and not any((r, l, b)): tile_type = 'b'
                    elif b and not any((r, l, t)): tile_type = 't'
                    elif b and t and not any((r, l)): tile_type = 'tb'
                    elif l and b and not any((t, r)): tile_type = 'tr'
                    elif r and b and not any((t, l)): tile_type = 'tl'
                    elif l and t and not any((b, r)): tile_type = 'br'
                    elif r and t and not any((b, l)): tile_type = 'bl'
                    elif all((t, b, r)) and not l: tile_type = 'tbr'
                    elif all((t, b, l)) and not r: tile_type = 'tbl'
                    elif all((l, r, t)) and not b: tile_type = 'lrb'
                    elif all((l, r, b)) and not t: tile_type = 'lrt'

                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites]
                    )

    def get_hit(self, point):
        for rect in self.hit_rects:
            if rect.collidepoint(point):
                self.hoe_sound.play()
                x = rect.x // TILE_SIZE
                y = rect.y // TILE_SIZE
                if 'F' in self.grid[y][x]:
                    self.grid[y][x].append('X')
                    self.create_soil_tiles()
                    if self.raining:
                        self.water_all()

    def water(self, target_pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                self.grid[y][x].append('W')
                pos = soil_sprite.rect.topleft
                surf = choice(self.water_surfs)
                WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * TILE_SIZE
                    y = index_row * TILE_SIZE
                    WaterTile((x, y), choice(self.water_surfs), [self.all_sprites, self.water_sprites])
    def remove_water(self):
        for sprite in self.water_sprites.sprites():
            sprite.kill()
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def check_watered(self, pos):
        x = pos[0] // TILE_SIZE
        y = pos[1] // TILE_SIZE
        if 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]):
            return 'W' in self.grid[y][x]
        return False

    def plant_seed(self, target_pos, seed):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(target_pos):
                self.plant_sound.play()
                x = soil_sprite.rect.x // TILE_SIZE
                y = soil_sprite.rect.y // TILE_SIZE
                if 'P' not in self.grid[y][x]:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                    t = index_row > 0 and 'X' in self.grid[index_row - 1][index_col]
                    b = index_row < len(self.grid) - 1 and 'X' in self.grid[index_row + 1][index_col]
                    r = index_col < len(row) - 1 and 'X' in row[index_col + 1]
                    l = index_col > 0 and 'X' in row[index_col - 1]

                    tile_type = 'o'
                    if all((t, r, b, l)): tile_type = 'x'
                    elif l and not any((t, r, b)): tile_type = 'r'
                    elif r and not any((t, l, b)): tile_type = 'l'
                    elif r and l and not any((t, b)): tile_type = 'lr'
                    elif t and not any((r, l, b)): tile_type = 'b'
                    elif b and not any((r, l, t)): tile_type = 't'
                    elif b and t and not any((r, l)): tile_type = 'tb'
                    elif l and b and not any((t, r)): tile_type = 'tr'
                    elif r and b and not any((t, l)): tile_type = 'tl'
                    elif l and t and not any((b, r)): tile_type = 'br'
                    elif r and t and not any((b, l)): tile_type = 'bl'
                    elif all((t, b, r)) and not l: tile_type = 'tbr'
                    elif all((t, b, l)) and not r: tile_type = 'tbl'
                    elif all((l, r, t)) and not b: tile_type = 'lrb'
                    elif all((l, r, b)) and not t: tile_type = 'lrt'

                    SoilTile(
                        pos=(index_col * TILE_SIZE, index_row * TILE_SIZE),
                        surf=self.soil_surfs[tile_type],
                        groups=[self.all_sprites, self.soil_sprites]
                    )