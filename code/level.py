import pygame
import os
from settings import *
from random import randint
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from support import import_folder
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from menu import Menu
from save import SaveSystem
from pet import Pet
from chat import ChatBox
from timer import Timer


class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()


        # 精灵组
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()

        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)

        # 必须先加载地图和玩家
        self.setup()

        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)

        self.rain = Rain(self.all_sprites)
        self.raining = randint(0, 10) > 7
        self.soil_layer.raining = self.raining
        self.sky = Sky()

        self.shop_active = False

        # 音效（找不到也不崩溃）
        base_dir = os.path.dirname(__file__)
        success_path = os.path.join(base_dir, '..', 'audio', 'success.wav')
        music_path = os.path.join(base_dir, '..', 'audio', 'music.mp3')

        if os.path.exists(success_path):
            self.success = pygame.mixer.Sound(success_path)
            self.success.set_volume(0.3)
        else:
            self.success = None

        game_bgm = os.path.join(base_dir, '..', 'audio', 'music.mp3')
        if os.path.exists(game_bgm):
            pygame.mixer.Channel(0).stop()
            self.game_music_sound = pygame.mixer.Sound(game_bgm)
            self.game_music_channel = pygame.mixer.Channel(0)  # 用通道0
            self.game_music_channel.set_volume(0.1)
            self.game_music_channel.play(self.game_music_sound, loops=-1)

        self.save_system = SaveSystem()
        if not self.save_system.load_game(self.player, self):
            print("Starting new game...")

        self.day_length = 60  # 一天多少秒（你可以自定义，比如60秒一轮）
        self.time = 0  

        # 宠物
        Pet(self.player, self.all_sprites)

        self.chat_cooldown = Timer(150)

        # ！！！关键：最后创建 ChatBox，此时 self 已经完全初始化！！
        self.chatbox = ChatBox(
            screen=self.display_surface,
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            font_path='font/LycheeSoda.ttf',
            level=self          # 这里传的 self 绝对不是 None
        )

        self.m_key_pressed = False

    def setup(self):
        tmx_data = load_pygame(os.path.join(os.path.dirname(__file__), '..', 'data', 'map.tmx'))

        # House bottom
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])

        # House top
        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites)

        # Fence
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

        # Water
        water_frames = import_folder(os.path.join(os.path.dirname(__file__), '..', 'graphics', 'water'))
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water((x * TILE_SIZE, y * TILE_SIZE), water_frames, self.all_sprites)

        # Trees
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree(pos=(obj.x, obj.y),
                 surf=obj.image,
                 groups=[self.all_sprites, self.collision_sprites, self.tree_sprites],
                 name=obj.name,
                 player_add=self.player_add)

        # Decoration
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

        # Invisible collision
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)

        # Player & interactions
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos=(obj.x, obj.y),
                    group=self.all_sprites,
                    collision_sprites=self.collision_sprites,
                    tree_sprites=self.tree_sprites,
                    interaction=self.interaction_sprites,
                    soil_layer=self.soil_layer,
                    toggle_shop=self.toggle_shop)
            if obj.name == 'Bed':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, 'Bed')
            if obj.name == 'Trader':
                Interaction((obj.x, obj.y), (obj.width, obj.height), self.interaction_sprites, 'Trader')

        # Ground
        Generic(pos=(0, 0),
                surf=pygame.image.load(os.path.join(os.path.dirname(__file__), '..', 'graphics', 'world', 'ground.png')).convert_alpha(),
                groups=self.all_sprites,
                z=LAYERS['ground'])

        # 宠物：只创建一次，不赋值给 self.pet
        Pet(self.player, self.all_sprites)   

        self.menu = Menu(self.player, self.toggle_shop)

    def player_add(self, item):
        self.player.item_inventory[item] += 1
        if self.success:
            self.success.play()

    def toggle_shop(self):
        print("Toggling shop menu.")
        self.shop_active = not self.shop_active

    def next_day(self):
        if hasattr(self, 'sky'):
            self.just_new_day = True
        self.time = 0
        self.soil_layer.update_plants()
        self.soil_layer.remove_water()
        
    def reset(self):
        self.next_day()
        self.soil_layer.update_plants()
        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 7
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_fruit()

        if hasattr(self, 'sky'):
            self.sky.stop_rain()

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.plant_collision_rect):
                    self.player_add(plant.plant_type)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image, self.all_sprites, LAYERS['main'])
                    row = plant.rect.centery // TILE_SIZE
                    col = plant.rect.centerx // TILE_SIZE
                    if 'P' in self.soil_layer.grid[row][col]:
                        self.soil_layer.grid[row][col].remove('P')

    def run(self, dt):
        # 1. 事件处理（必须最先）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            # 聊天框处理事件（输入、TAB、滚轮等）
            if self.chatbox.handle_event(event):
                continue  # 事件已被聊天框消费，不再传给其他系统

            if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                self.save_system.save_game(self.player, self)            

        # 2. 背景绘制
        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)

        # 3. 按键检测：M 开商店 + TAB 开聊天（防连点）
        keys = pygame.key.get_pressed()

        # M 键开商店（聊天时禁止开商店）
        if keys[pygame.K_m] and not self.chatbox.active:
            if not self.m_key_pressed:
                self.toggle_shop()
                self.m_key_pressed = True
        elif not keys[pygame.K_m]:
            self.m_key_pressed = False

        # 新增：锁定所有持续按键交互（如 Q/E/CTRL/SPACE）在聊天时无效
        if not self.shop_active and not self.chatbox.active:
            # 只有彻底自由时才更新游戏世界
            self.plant_collision()
            
        self.all_sprites.update(dt)

        # 4. 核心：只要商店或聊天开着 → 玩家完全冻结！
        if self.shop_active or self.chatbox.active:
            # 什么都不做 → 玩家不能动、不能用工具、不能种地
            pass
        else:
            # 只有彻底自由时才更新游戏世界
            self.plant_collision()

        # 5. 天空与雨：只在非菜单状态更新
        if not self.shop_active and not self.chatbox.active:
            self.time += dt
            if self.time >= self.day_length:
                self.time = 0
            progress = min(self.time / self.day_length, 1.0)

            if hasattr(self, 'just_new_day') and self.just_new_day:
                # 强制白天
                self.sky.current = [255, 255, 255]
                self.sky.target = [255, 255, 255]
                self.just_new_day = False

            self.sky.set_time(progress)
            self.sky.display(dt)
        else:
            self.sky.display(0)

        # 6. UI 永远最上层绘制
        self.overlay.display()

        if self.shop_active:
            self.menu.update()

        self.chatbox.update()   # 更新思考状态、接收回复
        self.chatbox.draw()     # 绘制聊天框

        # 7. 睡觉过渡
        if self.player.sleep:
            self.transition.play()

        self.save_system.draw_message()     

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

        # 可选：如果你还想画大背景地面，就留着这几行
        # self.ground_surf = pygame.image.load('../graphics/world/ground.png').convert_alpha()
        # self.ground_rect = self.gound_surf.get_rect(topleft=(0, 0))

    def custom_draw(self, player):
        # 相机以玩家为中心
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        # 可选：绘制超大背景地面（如果你有的话）
        # ground_offset = self.ground_rect.topleft - self.offset
        # self.display_surface.blit(self.ground_surf, ground_offset)

        # 核心：按层级 + Y轴排序绘制（Y轴越小越在后面，完美实现前后遮挡）
        for sprite in sorted(self.sprites(), key=lambda s: (s.z, s.rect.centery)):
            offset_rect = sprite.rect.copy()
            offset_rect.center -= self.offset
            self.display_surface.blit(sprite.image, offset_rect)

            # Draw dialogue bubble if sprite provides one
            if hasattr(sprite, 'get_dialogue_surf'):
                try:
                    bubble_surf = sprite.get_dialogue_surf()
                    if bubble_surf:
                        bubble_rect = bubble_surf.get_rect()
                        bubble_rect.midbottom = (offset_rect.centerx, offset_rect.top - 10)
                        self.display_surface.blit(bubble_surf, bubble_rect)
                except Exception:
                    pass
