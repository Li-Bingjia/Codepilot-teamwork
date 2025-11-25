# main.py
import pygame
from settings import *
from start import *  
from game import Game

# 让 start.py 能调用到 Main 实例
main_instance = None

class Main:
    def __init__(self):
        global main_instance
        main_instance = self

        pygame.init()
        pygame.mixer.init()
        pygame.key.set_repeat(150, 30)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Farming Land')

        # 场景
        self.start_menu = StartMenu(self.screen, self.start_game)
        self.controls = None
        self.game = None
        self.current_scene = 'start'   # 'start' / 'game' / 'controls'

    def start_game(self, new_game=False, load_save=False):
        # 目前 Level 不支持参数，直接忽略也没事
        self.game = Game(self.screen)
        self.current_scene = 'game'

    def show_controls(self):
        self.controls = ControlsScreen(self.screen, self.back_to_start)
        self.current_scene = 'controls'

    def back_to_start(self):
        self.current_scene = 'start'

    def run(self):
        while True:
            self.screen.fill((0, 0, 0))   # 防止残影

            if self.current_scene == 'start':
                self.start_menu.update()

            elif self.current_scene == 'controls':
                self.controls.update()

            elif self.current_scene == 'game':
                self.game.run()                     # 按 ESC 会 return
                self.current_scene = 'start' 
                
                pygame.mixer.Channel(0).stop()
                pygame.mixer.music.load(os.path.join('audio', 'title.ogg'))
                pygame.mixer.music.play(-1)       # 游戏结束后回到标题

            pygame.display.update()

# ===== ControlsScreen（直接写在这里最简单，也可放 start.py）=====
class ControlsScreen:
    def __init__(self, screen, back_callback):
        self.screen = screen
        self.back = back_callback
        self.font_big = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 70)
        self.font = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 42)

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.back()   # 任意键或鼠标点击都返回

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            self.handle_event(event)
        self.draw()
    def draw(self):
        self.screen.fill((30, 35, 60))

        title = self.font_big.render("Controls", True, (200, 255, 200))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 100)))

        lines = [
            "Arrow Keys       → Move",
            "SPACE            → Use tool (hoe/axe/water)",
            "Q                → Switch tool",
            "E                → Switch seed",
            "CTRL             → Plant seed",
            "ENTER            → Interact / Sleep",
            "M                → Open shop",
            "TAB              → Toggle chat",
            "ESC              → Back to title",
            "",
            "Click or press any key to return"
        ]

        for i, text in enumerate(lines):
            color = (255, 255, 180) if i < 9 else (180, 180, 180)
            surf = self.font.render(text, True, color)
            rect = surf.get_rect(center=(SCREEN_WIDTH//2, 220 + i * 52))
            self.screen.blit(surf, rect)

# ==============================================================

if __name__ == '__main__':
    Main().run()