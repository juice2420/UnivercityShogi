# scenes/scene_lobby.py

import pygame
import queue
import os
from .scene_base import BaseScene
from .scene_university_select import UniversitySelectScene
from settings import *
from network import Client, Server

class LobbyScene(BaseScene):
    """オンライン対戦の待合室画面"""

    def __init__(self, game):
        """初期化処理"""
        super().__init__(game)
        print(f"{self.game.player_role} としてロビーに入室しました。")
        
        # --- UI用の画像とフォントを準備 ---
        try:
            background_path = os.path.join(PROJECT_ROOT, 'images', 'wood_background.jpg')
            self.background_image = pygame.image.load(background_path).convert()
            self.background_image = pygame.transform.scale(self.background_image, (WIDTH + INFO_PANEL_WIDTH, HEIGHT))
        except pygame.error:
            self.background_image = None

        self.title_font = self.game.font_large
        self.prompt_font = self.game.font_medium
        self.button_font = self.game.font_game
        
        # ボタンの配色を他のシーンと統一
        self.button_color = (196, 164, 132)
        self.button_hover_color = (210, 180, 140)
        self.button_text_color = (50, 25, 0)
        self.button_text_white = WHITE

    def process_input(self, events, pressed_keys):
        """入力処理。戻るボタンやホスト選択ボタンの判定"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 戻るボタンのクリック判定
                if self.game.back_button.collidepoint(event.pos):
                    self.switch_to_scene(self.game.go_to_menu())
                    return

                # 【参加者側】ホスト選択のクリック判定
                if self.game.player_role == "player2":
                    for i, (host_ip, port) in enumerate(self.game.shared_data.found_hosts.items()):
                        button_width = 500
                        button_x = (WIDTH + INFO_PANEL_WIDTH) / 2 - button_width / 2
                        button_rect = pygame.Rect(button_x, 150 + i*100, button_width, 80)
                        if button_rect.collidepoint(event.pos):
                            target_address = (host_ip, port)
                            self.game.q = queue.Queue()
                            self.game.client = Client(self.game.q, target_address)
                            self.game.server = Server(self.game.q, self.game.client, self.game.shared_data, 0)
                            my_listening_port = self.game.server.my_port
                            self.game.client.send(f"HELLO:{my_listening_port}")
                            self.game.shared_data.connection_established = True
                            self.switch_to_scene(UniversitySelectScene(self.game))
                            return

    def update(self):
        """【ホスト側】参加者からの接続を待つ"""
        if self.game.player_role == "player1":
            if self.game.q and not self.game.q.empty() and self.game.q.get() == "CONNECTION_OK":
                self.switch_to_scene(UniversitySelectScene(self.game))

    def draw(self, screen):
        """待合室の画面を描画する"""
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill((210, 180, 140))
        
        mouse_pos = pygame.mouse.get_pos()

        is_hovering_back = self.game.back_button.collidepoint(mouse_pos)
        self._draw_button(screen, self.game.back_button, "← 戻る", is_hovering_back)

        if self.game.player_role == "player1":
            self.game.draw_text("対戦相手を待っています...", self.prompt_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, HEIGHT/2))
        else:
            self.game.draw_text("参加可能なゲーム", self.title_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, 80))
            if not self.game.shared_data.found_hosts:
                self.game.draw_text("ゲームが見つかりません", self.prompt_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, HEIGHT/2))
            else:
                for i, (host_ip, port) in enumerate(self.game.shared_data.found_hosts.items()):
                    button_width = 500
                    button_x = (WIDTH + INFO_PANEL_WIDTH) / 2 - button_width / 2
                    button_rect = pygame.Rect(button_x, 150 + i*100, button_width, 80)
                    is_hovering = button_rect.collidepoint(mouse_pos)
                    self._draw_button(screen, button_rect, f"{host_ip} に参加", is_hovering, is_join_button=True)

    def _draw_button(self, screen, rect, text, is_hovering, is_join_button=False):
        """統一感のあるボタンを描画するヘルパー関数"""
        if is_join_button:
            color = self.button_hover_color if is_hovering else BLUE
            text_color = WHITE
        else:
            color = self.button_hover_color if is_hovering else self.button_color
            text_color = self.button_text_color
            
        shadow_rect = rect.move(5, 5)
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        
        font = self.prompt_font if is_join_button else self.button_font
        self.game.draw_text(text, font, text_color, rect.center)