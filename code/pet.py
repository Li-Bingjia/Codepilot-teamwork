import pygame
from settings import *
import os
from support import import_folder
from random import randint, choice

class Pet(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        try:
            if isinstance(groups, pygame.sprite.Group):
                group_iter = [groups]
            else:
                group_iter = list(groups)
            for g in group_iter:   
                for spr in g.sprites():
                    if isinstance(spr, Pet):
                        spr.kill()    
        except Exception:    
            pass        
        
        super().__init__(groups)
        self.player = player
        self.import_assets()
        
        self.status = 'idle'
        self.frame_index = 0
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(center=self.player.rect.center + pygame.Vector2(-80, 0))
        self.z = LAYERS['main']
        
        self.pos = pygame.Vector2(self.rect.center)
        self.speed = 150
        self.follow_distance = 60

        # 加载气泡图片
        bubble_path = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'pet', 'bubble.png')
        self.bubble_img = pygame.image.load(bubble_path).convert_alpha()

        # 英文对话列表
        self.dialogues = [
            "Woof! Woof!",
            "You're the best, boss!",
            "Adventure time!",
            "I'm hungry...",
            "Don't leave me behind!",
            "I love apples!",
            "Nice weather today!",
            "It's time to plant!",
            "Hehe~",
            "Good job!"
        ]
        self.dialogue_text = ""
        self.show_dialogue = False
        self.dialogue_timer = 0
        self.dialogue_display_time = 0
        self.next_dialogue_time = randint(300, 600)
        self.font = pygame.font.Font(os.path.join(os.path.dirname(__file__), '..', 'font', 'LycheeSoda.ttf'), 20)

    def import_assets(self):
        idle_path = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'pet', 'idle')
        walk_path = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'pet', 'walk')
        
        right_idle = import_folder(idle_path)
        right_walk = import_folder(walk_path)
        
        left_walk = [pygame.transform.flip(frame, True, False) for frame in right_walk]
        up_walk = right_walk
        down_walk = right_walk

        self.animations = {
            'idle': right_idle,
            'walk_right': right_walk,
            'walk_left': left_walk,
            'walk_up': up_walk,
            'walk_down': down_walk,
        }

    def follow_player(self, dt):
        offset = pygame.Vector2(-80, 0)
        target_pos = self.player.rect.center + offset
        direction_vec = target_pos - self.pos
        distance = direction_vec.magnitude()

        if distance > self.follow_distance and distance > 0:
            direction = direction_vec.normalize()
            self.pos += direction * self.speed * dt
            player_dir = self.player.status.split('_')[0]
            self.status = f'walk_{player_dir}'
        else:
            self.status = 'idle'

        self.rect.center = self.pos

    def update_dialogue(self, dt):
        current_time = pygame.time.get_ticks()
        
        if not self.show_dialogue and current_time > self.next_dialogue_time:
            self.dialogue_text = choice(self.dialogues)
            self.show_dialogue = True
            self.dialogue_display_time = current_time + randint(1500, 2500)
            self.next_dialogue_time = current_time + randint(5000, 10000)
        
        if self.show_dialogue and current_time > self.dialogue_display_time:
            self.show_dialogue = False
            self.dialogue_text = ""

    def get_dialogue_surf(self):
        if not self.show_dialogue:
            return None

        text_surf = self.font.render(self.dialogue_text, True, (50, 50, 50))
        text_rect = text_surf.get_rect()

        # 目标气泡宽高：比文字略大
        bubble_width = text_rect.width + 40
        bubble_height = text_rect.height + 30

        # 动态缩放气泡图片
        bubble_surf = pygame.transform.smoothscale(self.bubble_img, (bubble_width, bubble_height))

        # 居中绘制文字
        text_rect.center = (bubble_width // 2, bubble_height // 2)
        bubble_surf.blit(text_surf, text_rect)

        return bubble_surf

    def animate(self, dt):
        self.frame_index += 8 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0
        
        self.image = self.animations[self.status][int(self.frame_index)]

    def update(self, dt):
        self.follow_player(dt)
        self.update_dialogue(dt)
        self.animate(dt)