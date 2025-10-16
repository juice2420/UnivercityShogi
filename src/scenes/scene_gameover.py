# scenes/scene_gameover.py

import pygame
import os
from .scene_base import BaseScene
from settings import *

class GameOverScene(BaseScene):
    """ゲーム終了画面。勝者を表示し、クリックでメニューに戻る。"""

    def __init__(self, game):
        """初期化処理"""
        super().__init__(game)
        
        # --- UI用の画像とフォントを準備 ---
        try:
            background_path = os.path.join(PROJECT_ROOT, 'images', 'wood_background.jpg')
            self.background_image = pygame.image.load(background_path).convert()
        except pygame.error:
            self.background_image = None
        
        self.title_font = self.game.font_large
        self.winner_font = self.game.font_medium
        self.prompt_font = self.game.font_game
        self.text_color = (50, 25, 0) # 暗い茶色

    def process_input(self, events, pressed_keys):
        """マウスクリックかキー入力でメニューに戻る処理"""
        from .scene_menu import MenuScene # 循環参照を避けるため、ここでインポート
        for event in events:
            # マウスクリック、または何らかのキーが押されたら
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                # go_to_menuを呼び出して安全にメニューに戻る
                self.switch_to_scene(self.game.go_to_menu())
                return

    def update(self):
        """状態更新（この画面では何もしない）"""
        pass

    def draw(self, screen):
        """ゲーム終了画面を描画する"""
        # 背景を描画
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill((210, 180, 140)) # 背景がない場合の代替色
            
        # テキストを描画
        center_x = (WIDTH + INFO_PANEL_WIDTH) / 2
        self.game.draw_text("ゲーム終了", self.title_font, self.text_color, (center_x, HEIGHT/2 - 80))
        
        # 勝者を表示
        winner_text = self.game.winner.capitalize().replace("player", "Player ")
        self.game.draw_text(f"勝者: {winner_text}", self.winner_font, self.text_color, (center_x, HEIGHT/2 + 20))
        
        # メニューに戻るよう促すテキスト
        self.game.draw_text("クリック または キー入力でメニューに戻る", self.prompt_font, self.text_color, (center_x, HEIGHT/2 + 120))