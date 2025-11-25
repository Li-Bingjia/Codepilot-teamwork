# start.py
import pygame
import os
import math
from settings import *

# 如果你想统一管理音乐路径，建议在 settings.py 里加这一行：
# START_BGM_PATH = os.path.join('audio', 'bgm', 'title.ogg')   # ← 改成你的音乐路径
# 没加也没事，下面直接写死路径也行

class StartMenu:
    def __init__(self, screen, switch_callback):
        self.screen = screen
        self.switch = switch_callback

        # ================== 初始化BGM（只播放一次）==================
        try:
            bgm_path = os.path.join('audio','title.ogg')  # ← 改成你的音乐文件名
            if os.path.exists(bgm_path):
                pygame.mixer.music.load(bgm_path)
                pygame.mixer.music.set_volume(0.4)   # 音量 0.0~1.0，随你喜欢
                pygame.mixer.music.play(-1)          # -1 = 循环播放
        except Exception as e:
            print(f"标题BGM加载失败（可以忽略）：{e}")

        # 字体
        self.font_title = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 90)
        self.font_menu  = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 50)
        self.font_small = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 30)

        self.options = ["New Game", "Load Game", "Controls", "Quit"]
        self.selected = 0
        self.alpha = 0
        self.fade_in = True

        # ================== 四层背景加载 ==================
        folder = os.path.join('graphics', 'title')
        self.bg_sky    = self.load_and_scale(f'{folder}/sky.png')
        self.bg_far    = self.load_and_scale(f'{folder}/far.png')
        self.bg_near   = self.load_and_scale(f'{folder}/near.png')
        self.bg_clouds = self.load_and_scale(f'{folder}/clouds.png')

    def load_and_scale(self, path):
        if not os.path.exists(path):
            return None
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.select()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.check_mouse_click(event.pos)

    def check_mouse_click(self, pos):
        for i, option in enumerate(self.options):
            rect = self.get_option_rect(i)
            if rect.collidepoint(pos):
                self.selected = i
                self.select()

    def get_option_rect(self, i):
        surf = self.font_menu.render(self.options[i], True, (255, 255, 255))
        return surf.get_rect(center=(SCREEN_WIDTH//2, 320 + i * 80))

    def select(self):
        choice = self.options[self.selected]
        if choice == "New Game":
            self.switch(new_game=True, load_save=False)
        elif choice == "Load Game":
            self.switch(new_game=False, load_save=True)
        elif choice == "Controls":
            from __main__ import main_instance
            main_instance.show_controls()
        elif choice == "Quit":
            pygame.quit()
            exit()

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            self.handle_event(event)

        # 呼吸动画（已优化频率和幅度）
        time = pygame.time.get_ticks() * 0.001
        self.breathe = math.sin(time * 2.8)           # 呼吸节奏（自然又活泼）
        self.sway    = math.sin(time * 3.2) * 0.5     # 左右轻微摇曳

        if self.fade_in and self.alpha < 255:
            self.alpha = min(255, self.alpha + 6)

        self.draw()

    def draw(self):
        # 1. 天空 + 远景（完全静止）
        if self.bg_sky:
            self.screen.blit(self.bg_sky, (0, 0))
        if self.bg_far:
            self.screen.blit(self.bg_far, (0, 0))

        # 2. 中景草地（轻微摇曳）
        if self.bg_near:
            offset_x = self.sway * 25
            fixed_y = 0
            self.screen.blit(self.bg_near, (offset_x, fixed_y))

        # 3. 云朵 —— Y轴完全固定，X轴双向呼吸（你最满意的版本）
        if self.bg_clouds:
            fixed_y = -22                                  # ← 只改这一个数字！调云的高度
            cloud_x = self.sway * 38                       # 左右呼吸幅度

            alpha_surf = self.bg_clouds.copy()
            alpha_surf.set_alpha(180 + int(self.breathe * 50))

            # 三张无缝循环（永不露边）
            self.screen.blit(alpha_surf, (cloud_x, fixed_y))
            self.screen.blit(alpha_surf, (cloud_x + SCREEN_WIDTH, fixed_y))
            self.screen.blit(alpha_surf, (cloud_x - SCREEN_WIDTH, fixed_y))

        # 标题（淡入，不上下跳）
        title = self.font_title.render("Farming Land", True, (200, 255, 200))
        title.set_alpha(self.alpha)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 140)))

        # 菜单（几乎不动，只轻微呼吸）
        for i, text in enumerate(self.options):
            color = (255, 255, 120) if i == self.selected else (220, 220, 220)
            surf = self.font_menu.render(text, True, color)
            y_pos = 320 + i * 80 + self.breathe * 3        # 非常轻微的呼吸感
            rect = surf.get_rect(center=(SCREEN_WIDTH//2, y_pos))
            self.screen.blit(surf, rect)

            if i == self.selected:
                line_y = rect.centery
                pygame.draw.line(self.screen, (255, 255, 120),
                               (rect.left - 60, line_y), (rect.left - 20, line_y), 6)
                pygame.draw.line(self.screen, (255, 255, 120),
                               (rect.right + 20, line_y), (rect.right + 60, line_y), 6)

        # 版本号
        ver = self.font_small.render("v1.0", True, (180, 180, 180))
        self.screen.blit(ver, (SCREEN_WIDTH - ver.get_width() - 20, SCREEN_HEIGHT - 40))


# ================== Controls 界面（不变）==================
class ControlsScreen:
    def __init__(self, screen, back_callback):
        self.screen = screen
        self.back = back_callback
        self.font_big = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 70)
        self.font = pygame.font.Font(os.path.join('font', 'LycheeSoda.ttf'), 42)

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.back()

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
            "Arrows             → Move", "SPACE         → Use tool", "Q             → Switch tool",
            "E             → Switch seed", "CTRL          → Plant seed",
            "ENTER         → Interact / Sleep", "M             → Open shop",
            "TAB           → Toggle chat", "ESC           → Back to title", "",
            "Click or press any key to return"
        ]
        for i, text in enumerate(lines):
            color = (255, 255, 180) if i < 9 else (180, 180, 180)
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH//2, 220 + i * 52)))