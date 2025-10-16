# scenes/scene_menu.py

import pygame
import threading
import queue
import os
from .scene_base import BaseScene
from .scene_lobby import LobbyScene
from .scene_university_select import UniversitySelectScene
from settings import *
from network import Client, Server, broadcast_presence, listen_for_hosts

class MenuScene(BaseScene):
    # ... (__init__は変更なし) ...
    def __init__(self, game):
        super().__init__(game)
        # player_roleはここでリセットせず、reset_game_stateに任せる
        
        try:
            background_path = os.path.join(PROJECT_ROOT, 'images', 'wood_background.jpg')
            self.background_image = pygame.image.load(background_path).convert()
            self.background_image = pygame.transform.scale(self.background_image, (WIDTH + INFO_PANEL_WIDTH, HEIGHT))
        except pygame.error:
            self.background_image = None
        
        self.title_font = self.game.font_large
        self.button_font = self.game.font_game
        self.button_color = (196, 164, 132)
        self.button_hover_color = (210, 180, 140)
        self.button_text_color = (50, 25, 0)

    def process_input(self, events, pressed_keys):
        """ボタンのクリックを処理する"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # ★★★ いずれかのボタンが押されたら、まずゲーム状態をリセットする ★★★
                if self.game.local_play_button.collidepoint(event.pos):
                    self.game.reset_game_state() # ★リセット
                    self.game.game_mode = "local"
                    self.switch_to_scene(UniversitySelectScene(self.game))

                elif self.game.host_button.collidepoint(event.pos):
                    self.game.reset_game_state() # ★リセット
                    self.game.game_mode = "online"
                    self.game.player_role = "player1"
                    self.game.q = queue.Queue()
                    self.game.client = Client(self.game.q)
                    self.game.server = Server(self.game.q, self.game.client, self.game.shared_data, GAME_PORT)
                    threading.Thread(target=broadcast_presence, args=(self.game.shared_data,), daemon=True).start()
                    self.switch_to_scene(LobbyScene(self.game))

                elif self.game.join_button.collidepoint(event.pos):
                    self.game.reset_game_state() # ★リセット
                    self.game.game_mode = "online"
                    self.game.player_role = "player2"
                    threading.Thread(target=listen_for_hosts, args=(self.game.shared_data,), daemon=True).start()
                    self.switch_to_scene(LobbyScene(self.game))

    # ... (update, drawメソッドは変更なし) ...
    def update(self):
        pass

    def draw(self, screen):
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill((210, 180, 140))

        self.game.draw_text("大学将棋", self.title_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, 120))

        buttons_to_draw = {
            "二人で対戦 (オフライン)": self.game.local_play_button,
            "オンライン対戦 (ホスト)": self.game.host_button,
            "オンライン対戦 (参加)": self.game.join_button
        }
        
        mouse_pos = pygame.mouse.get_pos()

        for text, button_rect in buttons_to_draw.items():
            is_hovering = button_rect.collidepoint(mouse_pos)
            color = self.button_hover_color if is_hovering else self.button_color
            shadow_rect = button_rect.move(5, 5)
            pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=12)
            pygame.draw.rect(screen, color, button_rect, border_radius=10)
            self.game.draw_text(text, self.button_font, self.button_text_color, button_rect.center)