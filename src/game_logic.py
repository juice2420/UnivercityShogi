# src/game_logic.py

import pygame
import sys
import sqlite3
import platform
import queue
import threading
import os

from settings import *
from network import SharedData, Server, Client, broadcast_presence, listen_for_hosts

class Game:
    def __init__(self):
        pygame.init()
        font_name = self.get_japanese_font()

        # ★★★ ここから修正 ★★★
        # 1. フルスクリーンモードでディスプレイを初期化
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        
        # 2. 実際の画面サイズを取得
        self.screen_width, self.screen_height = self.screen.get_size()
        
        # 3. ゲームコンテンツを描画するための「仮想スクリーン」を作成
        #    このサイズはsettings.pyの値に基づいて決まる
        self.game_surface = pygame.Surface((WIDTH + INFO_PANEL_WIDTH, HEIGHT))
        # ★★★ 修正ここまで ★★★

    def __init__(self):
        """ゲーム全体の初期化処理"""
        pygame.init()
        font_name = self.get_japanese_font()
        self.screen = pygame.display.set_mode((WIDTH + INFO_PANEL_WIDTH, HEIGHT))
        pygame.display.set_caption("大学将棋")
        self.font_large = pygame.font.SysFont(font_name, 74)
        self.font_medium = pygame.font.SysFont(font_name, 50)
        self.font_game = pygame.font.SysFont(font_name, 36)
        self.clock = pygame.time.Clock()
        
        self.reset_game_state()

        button_width = 500
        button_x = (WIDTH + INFO_PANEL_WIDTH) / 2 - button_width / 2
        self.local_play_button = pygame.Rect(button_x, 200, button_width, 80)
        self.host_button = pygame.Rect(button_x, 300, button_width, 80)
        self.join_button = pygame.Rect(button_x, 400, button_width, 80)
        self.back_button = pygame.Rect(20, 20, 120, 50)
        
        self.directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        from scenes.scene_menu import MenuScene
        self.current_scene = MenuScene(self)
        
    def reset_game_state(self):
        """ゲームの状態をまとめて初期化/リセットする"""
        self.shared_data = SharedData()
        self.player_role = None
        self.winner = None
        self.q = None
        self.client = None
        self.server = None
        self.pieces = []
        self.turn = "player1"
        self.capture_count = {"player1": 0, "player2": 0}
        self.game_mode = None
        self.turn_count = 0
        self.position_history = {}

    def go_to_menu(self):
        """現在の通信などを中断し、新しいメニューシーンのインスタンスを返す"""
        if self.shared_data:
            self.shared_data.is_running = False
        
        if self.server and self.server.sock:
            self.server.sock.close()
            
        from scenes.scene_menu import MenuScene
        return MenuScene(self)

    def run(self):
        """ゲームのメインループ。シーン管理に徹する"""
        while self.current_scene is not None:
            events = pygame.event.get()
            pressed_keys = pygame.key.get_pressed()
            for event in events:
                if event.type == pygame.QUIT:
                    if self.shared_data:
                        self.shared_data.is_running = False
                    self.current_scene.switch_to_scene(None)
            
            if self.current_scene:
                self.current_scene.process_input(events, pressed_keys)
                self.current_scene.update()
                self.current_scene.draw(self.screen)
                self.current_scene = self.current_scene.next_scene
            
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

    def get_japanese_font(self):
        """OSに応じた日本語フォントを探して返す"""
        os_name = platform.system()
        fonts = []
        if os_name == "Windows": fonts = ["meiryo", "yugothic", "msgothic"]
        elif os_name == "Darwin": fonts = ["hiraginosans", "hiraginokakugothicpron"]
        else: fonts = ["ipaexg", "notosanscjkjp"]
        for font in fonts:
            if pygame.font.match_font(font): return font
        return None
        
    def load_pieces_from_db(self, order_p1, order_p2):
        """データベースから駒の定義を読み込み、駒オブジェクトのリストを生成する"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT name, move_list, image_path FROM piece_definitions")
            rows = cur.fetchall()
            conn.close()
        except sqlite3.OperationalError as e:
            print(f"データベースエラー: {e}")
            self.current_scene.switch_to_scene(None)
            return []
        
        piece_definitions = {name: (move_list, image_path) for name, move_list, image_path in rows}
        piece_size = CELL_SIZE - 2 * MARGIN
        loaded_pieces = []

        def load_image_with_full_path(relative_path):
            full_path = os.path.join(PROJECT_ROOT, relative_path)
            return pygame.image.load(full_path)

        for i, name in enumerate(order_p1):
            if name.strip() == "" or name not in piece_definitions:
                continue
            move_str, image_path = piece_definitions[name]
            img = load_image_with_full_path(image_path)
            loaded_pieces.append({"pos": (5, i), "move_list": [int(c) for c in move_str], "img": pygame.transform.scale(img, (piece_size, piece_size)), "team": "player1", "name": name})
        
        for i, name in enumerate(order_p2):
            if name.strip() == "" or name not in piece_definitions:
                continue
            move_str, image_path = piece_definitions[name]
            img = load_image_with_full_path(image_path)
            col = COLS - 1 - i
            loaded_pieces.append({"pos": (1, col), "move_list": [int(c) for c in move_str], "img": pygame.transform.scale(img, (piece_size, piece_size)), "team": "player2", "name": name})
        return loaded_pieces

    def setup_game(self, p1_university, p2_university):
        """指定された大学の駒編成でゲームを準備する"""
        order_p1 = UNIVERSITY_DATA.get(p1_university, [])
        order_p2 = UNIVERSITY_DATA.get(p2_university, [])
        
        self.pieces = self.load_pieces_from_db(order_p1, order_p2)
        if not self.pieces: return
        
        self.turn = "player1"
        self.capture_count = {"player1": 0, "player2": 0}
        self.winner = None
        self.turn_count = 0
        self.position_history = {}

    def draw_text(self, text, font, color, center_pos):
        """画面に中央揃えのテキストを描画する"""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=center_pos)
        self.screen.blit(text_surface, text_rect)