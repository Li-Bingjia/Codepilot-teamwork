import pygame
from settings import *
from random import randint, choice
from timer import Timer
import os

class Generic(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups, z = LAYERS['main']):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = z
		self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)

class Interaction(Generic):
	def __init__(self, pos, size, groups, name):
		surf = pygame.Surface(size)
		super().__init__(pos, surf, groups)
		self.name = name

class Water(Generic):
	def __init__(self, pos, frames, groups):

		#animation setup
		self.frames = frames
		self.frame_index = 0

		# sprite setup
		super().__init__(
				pos = pos, 
				surf = self.frames[self.frame_index], 
				groups = groups, 
				z = LAYERS['water']) 

	def animate(self,dt):
		self.frame_index += 5 * dt
		if self.frame_index >= len(self.frames):
			self.frame_index = 0
		self.image = self.frames[int(self.frame_index)]

	def update(self,dt):
		self.animate(dt)

class WildFlower(Generic):
	def __init__(self, pos, surf, groups):
		super().__init__(pos, surf, groups)
		self.hitbox = self.rect.copy().inflate(-20,-self.rect.height * 0.9)

class Particle(Generic):
	def __init__(self, pos, surf, groups, z, duration = 200):
		super().__init__(pos, surf, groups, z)
		self.start_time = pygame.time.get_ticks()
		self.duration = duration

		# white surface 
		mask_surf = pygame.mask.from_surface(self.image)
		new_surf = mask_surf.to_surface()
		new_surf.set_colorkey((0,0,0))
		self.image = new_surf

	def update(self,dt):
		current_time = pygame.time.get_ticks()
		if current_time - self.start_time > self.duration:
			self.kill()

class Tree(Generic):
    def __init__(self, pos, surf, groups, name, player_add):
        super().__init__(pos, surf, groups)

        # tree attributes
        self.health = 5
        self.alive = True
        self.player_add = player_add
        
        # 树桩
        stump_path = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'stumps', f'{"small" if name == "Small" else "large"}.png')
        self.stump_surf = pygame.image.load(stump_path).convert_alpha()

        # 苹果
        apple_path = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'fruit', 'apple.png')
        self.apple_surf = pygame.image.load(apple_path).convert_alpha()
        self.apple_pos = APPLE_POS[name]

        # ============ 关键修改：彻底干掉循环导入 ============
        # 完全不导入 CameraGroup！只看它有没有 custom_draw 方法
        self.all_sprites = next((g for g in groups if hasattr(g, 'custom_draw')), None)
        if not self.all_sprites:
            raise ValueError("Tree 必须加入一个有 custom_draw 方法的组（也就是 CameraGroup）！")
        # =====================================================

        # 苹果专用组
        self.apple_sprites = pygame.sprite.Group()

        # 声音
        self.axe_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), '..', 'audio', 'axe.mp3'))
        self.axe_sound.set_volume(0.4)

        # 创建苹果
        self.create_fruit()

    def create_fruit(self):
        self.apple_sprites.empty()  # 清空旧苹果

        for pos in self.apple_pos:
            if randint(0, 10) < 4:  
                x = self.rect.left + pos[0]
                y = self.rect.top + pos[1]

                apple = Generic(
                    pos=(x, y),
                    surf=self.apple_surf,
                    groups=self.all_sprites,      # 正确！加入能被绘制的组
                    z=LAYERS['fruit']
                )
                self.apple_sprites.add(apple)     # 同时加入管理组

    def damage(self):
        # 扣血
        self.health -= 1
        self.axe_sound.play()

        # 掉一个苹果
        if len(self.apple_sprites) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            Particle(
                pos=random_apple.rect.topleft,
                surf=random_apple.image,
                groups=self.all_sprites,
                z=LAYERS['fruit'],
                duration=400
            )
            random_apple.kill()  # 自动从两个组移除
            self.player_add('apple')

        # 树死掉
        if self.health <= 0 and self.alive:
            self.alive = False

            # 大粒子特效
            Particle(
                pos=self.rect.topleft,
                surf=self.image,
                groups=self.all_sprites,
                z=LAYERS['fruit'],
                duration=300
            )

            # 变成树桩
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)

            # 加木头（只加一次！）
            self.player_add('wood')