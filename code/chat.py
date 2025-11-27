SYSTEM_PROMPT = """
You are a helpful assistant for this farming game. You know everything about the game mechanics and can give precise advice.

=== GAME CONTROLS ===
- WASD or Arrow Keys: Move
- SPACE: Use tool (hoe, axe, water)
- Q: Switch tool (hoe → axe → water)
- E: Switch seed (corn → tomato)
- CTRL: Plant seed
- ENTER: Interact (Trader shop, Bed sleep)
- M: Open shop menu
- TAB: Toggle chat

=== TOOLS ===
- Hoe (Q): Till soil (F → X)
- Axe (Q): Chop trees (drop apples/wood)
- Water (Q): Water soil (X → XW)

=== CROPS ===
- Corn: 5 stages, needs water, sells for 20
- Tomato: 5 stages, needs water, sells for 20
- Seeds: Buy at Trader, plant on tilled soil (XW)

=== ECONOMY ===
- Start: 200 money, 5 corn seeds, 5 tomato seeds
- Apples: Pick from trees, sell 20
- Wood: Chop stumps, sell 20
- Crops: Harvest mature plants, sell 20

=== SHOP (Trader) ===
- Corn seeds: Buy 50
- Tomato seeds: Buy 50
- Sell all items at Trader

=== WORLD ===
- Trees: Chop 5 times → stump → wood
- Bed: Sleep to reset day (apples regrow)
- Rain: Auto-waters all tilled soil

=== GOALS ===
- Farm crops
- Chop trees for apples/wood
- Sell everything at Trader
- Buy more seeds
- Expand farm

Answer in one sentence as much as possible,Fewer than 25 English words, be direct like a game NPC!
"""
import pygame
import requests
import threading
import os
from settings import *
import queue
from player import Player

class ChatBox:
    def __init__(self, screen, screen_width, screen_height, font_path=None, level=None):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = 600
        self.height = 400
        self.rect = pygame.Rect((self.screen_width - self.width) // 2, 200, self.width, self.height)
        
        bg_path = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'chat_bg.png')
        self.bg_img = pygame.image.load(bg_path).convert_alpha()
        self.border_color = (133, 79, 34)
        self.text_color = (220, 220, 220)
        self.input_bg = (50, 50, 60)
        
        self.font_size = 24
        self.font = pygame.font.Font(font_path or pygame.font.get_default_font(), self.font_size)
        
        self.active = False
        self.input_text = ""
        self.history = [
            {"role": "assistant", "content": "Hello! Ask me anything in English."}
        ]
        self.thinking = False
        self.scroll_offset = 0
        self.max_scroll = 0

        self.level = level          
        self.pending_reply = None
        self.reply_ready = False

        self.reply_queue = queue.Queue()
        
        self.api_url = "http://localhost:1234/v1/chat/completions"
        self.model = "openai/gpt-oss-20b"     

    def toggle(self):
        self.active = not self.active

    def handle_event(self, event):
        # 【关键修复1】：如果商店菜单开着，聊天框完全不抢任何事件（包括TAB）
        if self.level is None or getattr(self.level, 'shop_active', None) is None:
            return False

        # 未打开聊天框：只监听 TAB 打开
        if not self.active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.toggle()          # 打开聊天框
                return True            # 事件已消费
            return False               # 其他键全部放行给游戏

        # ---------- 下面是聊天框已激活的状态 ----------
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset += event.y * 30
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:           # TAB 关闭聊天框
                self.toggle()
                return True

            elif event.key == pygame.K_RETURN:      # 回车发送
                if self.input_text.strip() and not self.thinking:
                    self.send_message(self.input_text.strip())
                self.input_text = ""
                return True

            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True

            # 可选：支持 ESC 也关闭聊天框
            elif event.key == pygame.K_ESCAPE:
                self.toggle()
                return True

            return False
        
        elif event.type == pygame.TEXTINPUT:        # 支持中文、表情等
            self.input_text += event.text
            return True

        return True


    def send_message(self, text):
        # 1. 把玩家输入加进历史
        self.history.append({"role": "user", "content": text})
        self.history = self.history[-20:]          # 最多保留20条对话
        self.thinking = True

        # 2. 获取当前游戏状态（你只需要把 level 传进来一次就行，后面会补）
        # 假设你在创建 ChatBox 时传了 level： ChatBox(..., level=self)
        try:
            money = self.level.player.money
            tool = self.level.player.selected_tool.capitalize()
            seed = self.level.player.selected_seed.capitalize() if self.level.player.selected_seed else "None"
            day = self.level.day
            raining = "Yes" if self.level.raining else "No"
        except:
            money = tool = seed = day = raining = "???"

        # 3. 动态状态提示（每次对话都会更新最新数值）
        status_prompt = f"""
Current status:
- Money: {money}
- Tool: {tool}
- Seed: {seed}
- Day: {day}
- Raining: {raining}
"""

        # 4. 完整的消息列表（系统提示永远排在最前面）
        messages_for_llm = [
            {"role": "system", "content": SYSTEM_PROMPT + status_prompt},
            *self.history[-15:]   # 最多只给 LLM 最近15条对话，防止超 token
        ]

        def thread_func():
            try:
                payload = {
                    "model": self.model,
                    "messages": messages_for_llm,
                    "temperature": 0.7,
                    "max_tokens": 120,
                    "stream": False
                }
                response = requests.post(self.api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
                reply = response.json()['choices'][0]['message']['content'].strip()

                # 存进类属性，等 update() 轮询
                self.pending_reply = reply
                self.reply_ready = True
                print("[LLM] Reply ready:", reply)

            except Exception as e:
                print("[LLM ERROR]", e)
                self.pending_reply = "Oops, I couldn't reach the server..."
                self.reply_ready = True

        threading.Thread(target=thread_func, daemon=True).start()

    def update(self):
        """从类属性取回复 – 彻底解决 Thinking 卡死"""
        if hasattr(self, 'reply_ready') and self.reply_ready:
            reply = self.pending_reply
            print(f"[LLM] Reply displayed: {reply}")
            self.history.append({"role": "assistant", "content": reply})
            self.thinking = False
            self.reply_ready = False      # 重置
            self.pending_reply = None

# chat.py → draw() 方法（替换原函数）
    def draw(self):
        if not self.active:
            return

        # 聊天框背景图片
        bg_surf = pygame.transform.smoothscale(self.bg_img, (self.width, self.height))
        self.screen.blit(bg_surf, (self.rect.x, self.rect.y))

        font = pygame.font.Font(FONT_PATH, FONT_SIZE)
        text_color = UI_COLORS['text']
        border_color = UI_COLORS['border']

        # 半透明历史消息区
        chat_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 55, self.rect.width - 30, self.rect.height - 110)
        chat_bg = pygame.Surface((chat_rect.width, chat_rect.height), pygame.SRCALPHA)
        chat_bg.fill((40, 40, 50, 140))  # 深色半透明
        self.screen.blit(chat_bg, chat_rect.topleft)

        # 半透明输入框
        input_rect = pygame.Rect(self.rect.x + 15, self.rect.y + self.rect.height - 50, self.rect.width - 30, 35)
        input_bg = pygame.Surface((input_rect.width, input_rect.height), pygame.SRCALPHA)
        input_bg.fill((255, 255, 255, 180))  # 白色半透明
        self.screen.blit(input_bg, input_rect.topleft)
        pygame.draw.rect(self.screen, border_color, input_rect, 2, border_radius=8)

        # 聊天框边框
        pygame.draw.rect(self.screen, border_color, self.rect, 3, border_radius=12)

        # 标题
        title = font.render("AI Chat (English)", True, text_color)
        self.screen.blit(title, (self.rect.x + 20, self.rect.y + 15))

        # 聊天历史
        y = chat_rect.y + 10 - self.scroll_offset
        line_height = FONT_SIZE + 8
        total_height = 0

        for msg in self.history:
            lines = self.wrap_text(msg["content"], chat_rect.width - 20)
            for line in lines:
                color = (0, 0, 0) if msg["role"] == "assistant" else (220, 220, 100)
                text_surf = font.render(line, True, color)
                text_surf.set_alpha(255)
                if y + line_height > chat_rect.y and y < chat_rect.bottom:
                    self.screen.blit(text_surf, (chat_rect.x + 10, y))
                y += line_height
                total_height += line_height
            y += 8
            total_height += 8

        # 计算最大可滚动距离
        self.max_scroll = max(0, total_height - chat_rect.height + 50)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)

        if self.thinking:
            think = font.render("Thinking...", True, (150, 150, 255))
            self.screen.blit(think, (chat_rect.x + 10, y))

        # 输入框内容
        cursor = "█" if (pygame.time.get_ticks() // 500) % 2 else ""
        input_surf = font.render(self.input_text + cursor, True, (0, 0, 0))
        self.screen.blit(input_surf, (input_rect.x + 10, input_rect.y + 5))

        # 提示
        hint = font.render("TAB to open | TAB to close | Enter to send", True, (150, 150, 150))
        self.screen.blit(hint, (self.rect.x + 15, self.rect.y + self.rect.height - 20))

    def wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = current + (" " if current else "") + word
            if self.font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        return lines
