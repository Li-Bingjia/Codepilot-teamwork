# game.py
import pygame, sys
from settings import *
from level import Level
from chat import ChatBox

class Game:
    def __init__(self, screen, new_game=False, load_save=False):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        # 关键修复：直接创建 Level，不传任何参数
        self.level = Level()   # 这样保证 100% 能进游戏
        
        # 如果你以后要做存档功能，可以在这里加判断：
        # if load_save and hasattr(self.level, 'load_game'):
        #     self.level.load_game()
        
        self.chatbox = ChatBox(self.screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        #pygame.mixer.music.load('audio/bg.mp3')
        #pygame.mixer.music.set_volume(0.4)
        #pygame.mixer.music.play(-1)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return  # 按 ESC 返回标题
                self.chatbox.handle_event(event)

            dt = self.clock.tick(60) / 1000.0
            self.level.run(dt)
            self.chatbox.update()
            self.chatbox.draw()
            pygame.display.update()