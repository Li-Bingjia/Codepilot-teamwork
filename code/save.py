import pygame
import json
import os

class SaveSystem:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'save.json')
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        self.screen = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 36)
        self.message = ""
        self.message_color = (255, 255, 255)
        self.message_timer = 0

    def show_message(self, text, color=(0, 255, 0)):
        self.message = text
        self.message_color = color
        self.message_timer = pygame.time.get_ticks()

    def draw_message(self):
        if self.message and pygame.time.get_ticks() - self.message_timer < 1500:
            text_surf = self.font.render(self.message, True, self.message_color)
            text_rect = text_surf.get_rect(center=(self.screen.get_width() // 2, 50))
            pygame.draw.rect(self.screen, (0, 0, 0), text_rect.inflate(20, 10))
            self.screen.blit(text_surf, text_rect)
        else:
            self.message = ""

    def save_game(self, player, level):
        data = {
            'player': {
                'pos_x': player.pos.x,
                'pos_y': player.pos.y,
                'money': player.money,
                'item_inventory': player.item_inventory,
                'seed_inventory': player.seed_inventory,
                'selected_tool': player.selected_tool,
                'selected_seed': player.selected_seed,
            },
            'level': {
                'raining': level.raining,
                'soil_grid': level.soil_layer.grid
            }
        }
        
        
        if hasattr(level, 'pet') and level.pet:
            data['pet'] = {
                'pos_x': level.pet.pos.x,
                'pos_y': level.pet.pos.y
            }

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print("Saved successfully! Path:", self.file_path)
            self.show_message("Game Saved!", (0, 255, 0))
        except Exception as e:
            print("Save failed:", e)
            self.show_message("Save Failed!", (255, 0, 0))

    def load_game(self, player, level):
        if not os.path.exists(self.file_path):
            print("No save file, new game launched")
            return False

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 恢复玩家
            p = data['player']
            player.pos = pygame.math.Vector2(p['pos_x'], p['pos_y'])
            player.rect.center = player.pos
            player.hitbox.center = player.rect.center
            player.money = p['money']
            player.item_inventory = p['item_inventory']
            player.seed_inventory = p['seed_inventory']
            player.selected_tool = p['selected_tool']
            player.selected_seed = p['selected_seed']

            # 恢复天气
            level.raining = data['level']['raining']
            level.soil_layer.raining = level.raining

            # 恢复耕地数据
            level.soil_layer.grid = data['level']['soil_grid']
            level.soil_layer.create_soil_sprites()

            # 恢复宠物位置
            if 'pet' in data and hasattr(level, 'pet') and level.pet:
                pet_data = data['pet']
                level.pet.pos = pygame.math.Vector2(pet_data['pos_x'], pet_data['pos_y'])
                level.pet.rect.center = level.pet.pos

            print("Save file loaded successfully! 耕地图形已恢复")
            self.show_message("Game Loaded!", (0, 255, 0))
            return True
            
        except Exception as e:
            print("Save file loading failed:", e)
            self.show_message("Load Failed!", (255, 0, 0))
            return False
        