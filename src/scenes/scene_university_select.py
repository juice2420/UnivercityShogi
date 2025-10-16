# scenes/scene_university_select.py

import pygame
import os
from .scene_base import BaseScene
from .scene_game import GameScene
from settings import *

class UniversitySelectScene(BaseScene):
    """大学を選択する画面。オフライン・オンライン両対応。"""

    def __init__(self, game):
        """初期化処理"""
        super().__init__(game)
        
        try:
            background_path = os.path.join(PROJECT_ROOT, 'images', 'wood_background.jpg')
            self.background_image = pygame.image.load(background_path).convert()
            self.background_image = pygame.transform.scale(self.background_image, (WIDTH + INFO_PANEL_WIDTH, HEIGHT))
        except pygame.error:
            self.background_image = None

        self.title_font = self.game.font_medium
        self.button_font = self.game.font_game
        self.info_font = self.game.font_game
        
        self.button_color = (196, 164, 132)
        self.button_hover_color = (210, 180, 140)
        self.button_text_color = (50, 25, 0)
        self.button_selected_color = (148, 115, 80)
        self.button_selected_text_color = WHITE

        self.buttons = {}
        y_pos = 200
        uni_names_in_order = ["KYOUSAN", "KINKIDAI", "KOUNAN", "RYUKOKU"]
        for uni_name in uni_names_in_order:
            button_width = 500
            button_x = (WIDTH + INFO_PANEL_WIDTH) / 2 - button_width / 2
            self.buttons[uni_name] = pygame.Rect(button_x, y_pos, button_width, 80)
            y_pos += 100

        self.selection_turn = "player1"
        self.p1_choice, self.p2_choice = None, None
        self.my_choice, self.opponent_choice = None, None

    def process_input(self, events, pressed_keys):
        """クリックイベントを処理して大学を選択、または戻る"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # ★★★ 戻るボタンのクリック判定を先頭に追加 ★★★
                if self.game.back_button.collidepoint(event.pos):
                    # go_to_menuを呼び出してメニューに戻る
                    self.switch_to_scene(self.game.go_to_menu())
                    return # メニューに戻るので、以降の処理は不要

                # 大学選択ボタンのクリック判定
                for uni_name, button_rect in self.buttons.items():
                    if button_rect.collidepoint(event.pos):
                        if self.game.game_mode == "local":
                            self._handle_local_selection(uni_name)
                        elif self.game.game_mode == "online":
                            self._handle_online_selection(uni_name)
                        return

    def _handle_local_selection(self, uni_name):
        """オフラインモードでの選択処理"""
        if self.selection_turn == "player1":
            self.p1_choice = uni_name
            self.selection_turn = "player2"
        elif self.selection_turn == "player2":
            self.p2_choice = uni_name
            self.game.setup_game(self.p1_choice, self.p2_choice)
            self.switch_to_scene(GameScene(self.game))

    def _handle_online_selection(self, uni_name):
        """オンラインモードでの選択処理"""
        if not self.my_choice:
            self.my_choice = uni_name
            self.game.client.send(f"CHOICE:{uni_name}")

    def update(self):
        """オンラインモードで相手の選択を待つ処理"""
        if self.game.game_mode == "online":
            if self.game.q and not self.game.q.empty():
                msg = self.game.q.get()
                if msg.startswith("CHOICE:"):
                    self.opponent_choice = msg.split(':')[1]
            
            if self.my_choice and self.opponent_choice:
                p1_uni = self.my_choice if self.game.player_role == "player1" else self.opponent_choice
                p2_uni = self.opponent_choice if self.game.player_role == "player1" else self.my_choice
                self.game.setup_game(p1_uni, p2_uni)
                self.switch_to_scene(GameScene(self.game))

    def draw(self, screen):
        """大学選択画面を描画する"""
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill((210, 180, 140))

        mouse_pos = pygame.mouse.get_pos()
        
        # 戻るボタンを描画
        is_hovering_back = self.game.back_button.collidepoint(mouse_pos)
        self._draw_button(screen, self.game.back_button, "← 戻る", is_hovering_back, False)

        # モードに応じた描画処理
        if self.game.game_mode == "local":
            player_text = "Player 1" if self.selection_turn == "player1" else "Player 2"
            self.game.draw_text(f"{player_text}: 使用する大学を選択", self.title_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, 100))
            for uni_name, button_rect in self.buttons.items():
                is_selected = (self.p1_choice == uni_name)
                is_hovering = button_rect.collidepoint(mouse_pos)
                self._draw_button(screen, button_rect, uni_name, is_hovering, is_selected)
        
        elif self.game.game_mode == "online":
            self.game.draw_text("使用する大学を選択してください", self.title_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, 100))
            if not self.opponent_choice:
                self.game.draw_text("相手の選択を待っています...", self.info_font, self.button_text_color, ((WIDTH + INFO_PANEL_WIDTH)/2, 150))
            else:
                self.game.draw_text(f"相手の大学: {self.opponent_choice}", self.info_font, (0, 50, 150), ((WIDTH + INFO_PANEL_WIDTH)/2, 150))
            
            for uni_name, button_rect in self.buttons.items():
                is_selected = (self.my_choice == uni_name)
                is_hovering = button_rect.collidepoint(mouse_pos)
                self._draw_button(screen, button_rect, uni_name, is_hovering, is_selected)
    
    def _draw_button(self, screen, rect, text, is_hovering, is_selected):
        """統一感のあるボタンを描画するヘルパー関数"""
        if is_selected:
            color = self.button_selected_color
            text_color = self.button_selected_text_color
        elif is_hovering:
            color = self.button_hover_color
            text_color = self.button_text_color
        else:
            color = self.button_color
            text_color = self.button_text_color
            
        shadow_rect = rect.move(5, 5)
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        self.game.draw_text(text, self.button_font, text_color, rect.center)