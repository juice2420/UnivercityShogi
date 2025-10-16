# src/scenes/scene_game.py

import pygame
import random
import os
from .scene_base import BaseScene
from .scene_gameover import GameOverScene
from settings import *

class GameScene(BaseScene):
    """メインの対局画面の処理を担当するクラス"""

    def __init__(self, game):
        """初期化処理"""
        super().__init__(game)
        self.selected_index = None
        self.is_flipped = False
        
        try:
            background_path = os.path.join(PROJECT_ROOT, 'images', 'wood_background.jpg')
            self.background_image = pygame.image.load(background_path).convert()
        except pygame.error:
            self.background_image = None
            
        btn_w, btn_h = 200, 60
        btn_x = WIDTH + (INFO_PANEL_WIDTH - btn_w) / 2
        btn_y = HEIGHT - btn_h - 40
        self.ingame_menu_button = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    def process_input(self, events, pressed_keys):
        """ユーザーの入力（クリック、キー入力）を処理する"""
        if self.game.game_mode == "online" and self.game.turn != self.game.player_role:
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game.game_mode == "local":
                    self.is_flipped = not self.is_flipped

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.ingame_menu_button.collidepoint(event.pos):
                    if self.game.game_mode == "online":
                        self.game.winner = "player2" if self.game.player_role == "player1" else "player1"
                        self.game.client.send("RESIGN")
                    else:
                        self.switch_to_scene(self.game.go_to_menu())
                    return

                mx, my = pygame.mouse.get_pos()
                clicked_col_visual, clicked_row_visual = mx // CELL_SIZE, my // CELL_SIZE
                if not (0 <= clicked_col_visual < COLS and 0 <= clicked_row_visual < ROWS):
                    continue
                
                clicked_row_logical, clicked_col_logical = self._visual_to_logical(clicked_row_visual, clicked_col_visual)
                clicked_cell = (clicked_row_logical, clicked_col_logical)

                clicked_piece_index = None
                for i, piece in enumerate(self.game.pieces):
                    if piece["pos"] == clicked_cell and piece["team"] == self.game.turn:
                        clicked_piece_index = i
                        break
                
                move_targets = self._get_move_targets()
                if clicked_piece_index is not None:
                    self.selected_index = None if self.selected_index == clicked_piece_index else clicked_piece_index
                elif self.selected_index is not None and clicked_cell in move_targets:
                    original_index = self.selected_index
                    self.move_piece(self.selected_index, clicked_cell)
                    if self.game.game_mode == 'online':
                        self.game.client.send(f"MOVE,{original_index},{clicked_row_logical},{clicked_col_logical}")

    def update(self):
        """ゲーム状態の更新（相手の通信処理、勝敗判定）"""
        if self.game.game_mode == 'online' and self.game.q and not self.game.q.empty():
            msg = self.game.q.get()
            parts = msg.split(',')
            command = parts[0]
            if command == "MOVE":
                try:
                    s_idx, r, c = map(int, parts[1:])
                    self.move_piece(s_idx, (r, c))
                except (ValueError, IndexError):
                    print(f"不正なMOVEメッセージを受信: {msg}")
            elif command == "RESIGN":
                self.game.winner = self.game.player_role

        if self.game.winner is not None:
            self.switch_to_scene(GameOverScene(self.game))

    def _visual_to_logical(self, r_vis, c_vis):
        """見た目の座標を、内部的な論理座標に変換する"""
        is_p2_online_view = (self.game.game_mode == "online" and self.game.player_role == "player2")
        if is_p2_online_view or self.is_flipped:
            logical_r = ROWS - 1 - r_vis
            logical_c = COLS - 1 - c_vis
            return logical_r, logical_c
        return r_vis, c_vis

    def _get_display_pos(self, logical_r, logical_c):
        """論理座標を、現在のプレイヤー視点での描画用座標に変換する"""
        is_p2_online_view = (self.game.game_mode == "online" and self.game.player_role == "player2")
        if is_p2_online_view or self.is_flipped:
            display_r = ROWS - 1 - logical_r
            display_c = COLS - 1 - logical_c
            return display_r, display_c
        return logical_r, logical_c

    def draw(self, screen):
        """対局画面を描画する"""
        if self.background_image: screen.blit(self.background_image, (0, 0))
        else: screen.fill((210, 180, 140))

        move_targets = self._get_move_targets()
        
        show_highlight = self.game.game_mode == "local" or (self.game.game_mode == "online" and self.game.turn == self.game.player_role)
        if self.selected_index is not None and show_highlight:
            selected_pos_logical = self.game.pieces[self.selected_index]["pos"]
            selected_pos_display = self._get_display_pos(*selected_pos_logical)
            move_targets_display = {self._get_display_pos(*pos) for pos in move_targets}
            for r_vis in range(ROWS):
                for c_vis in range(COLS):
                    rect = pygame.Rect(c_vis * CELL_SIZE, r_vis * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    if (r_vis, c_vis) == selected_pos_display: pygame.draw.rect(screen, HIGHLIGHT_YELLOW, rect)
                    elif (r_vis, c_vis) in move_targets_display: pygame.draw.rect(screen, HIGHLIGHT_GREEN, rect)

        for x in range(COLS + 1): pygame.draw.line(screen, GRID_COLOR, (x * CELL_SIZE, 0), (x * CELL_SIZE, HEIGHT), 2)
        for y in range(ROWS + 1): pygame.draw.line(screen, GRID_COLOR, (0, y * CELL_SIZE), (WIDTH, y * CELL_SIZE), 2)
        
        for piece in self.game.pieces:
            r_logical, c_logical = piece["pos"]
            r_display, c_display = self._get_display_pos(r_logical, c_logical)
            

            # 元の画像を変更しないようにコピーを作成
            img_to_draw = piece["img"].copy()
            
            # チームに応じて色を上乗せ（ティント）する
            if piece["team"] == "player1":
                img_to_draw.fill((50, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            else: # player2
                img_to_draw.fill((0, 0, 50), special_flags=pygame.BLEND_RGB_ADD)
            
            # 視点に応じて画像を180度回転させる
            perspective_team = "player1"
            if (self.game.game_mode == "online" and self.game.player_role == "player2") or \
               (self.game.game_mode == "local" and self.is_flipped):
                perspective_team = "player2"
            
            if piece["team"] != perspective_team:
                img_to_draw = pygame.transform.rotate(img_to_draw, 180)
            # ★★★ 修正ここまで ★★★

            screen.blit(img_to_draw, (c_display * CELL_SIZE + MARGIN, r_display * CELL_SIZE + MARGIN))
        
        self._draw_info_panel(screen)

    def _draw_info_panel(self, screen):
        """情報パネルを描画する"""
        panel_rect = pygame.Rect(WIDTH, 0, INFO_PANEL_WIDTH, HEIGHT)
        panel_bg_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_bg_surface.fill((0, 0, 0, 80))
        screen.blit(panel_bg_surface, panel_rect.topleft)

        info_panel_center_x = WIDTH + (INFO_PANEL_WIDTH / 2)
        y_pos = 100
        text_color = WHITE
        
        self.game.draw_text("撃破数", self.game.font_game, text_color, (info_panel_center_x, y_pos)); y_pos += 50
        self.game.draw_text(f"Player1: {self.game.capture_count['player1']}", self.game.font_game, text_color, (info_panel_center_x, y_pos)); y_pos += 40
        self.game.draw_text(f"Player2: {self.game.capture_count['player2']}", self.game.font_game, text_color, (info_panel_center_x, y_pos)); y_pos += 60
        self.game.draw_text(f"ターン数: {self.game.turn_count}", self.game.font_game, text_color, (info_panel_center_x, y_pos)); y_pos += 60

        if self.game.game_mode == "online": turn_text = "あなたのターン" if self.game.turn == self.game.player_role else "相手のターン"
        else: turn_text = f"{self.game.turn.replace('player', 'Player ')} のターン"
        self.game.draw_text(f"{turn_text}", self.game.font_game, text_color, (info_panel_center_x, y_pos)); y_pos += 60
        
        if self.game.game_mode == "online":
            self.game.draw_text(f"あなたは {self.game.player_role.replace('player', 'Player ')}", self.game.font_game, text_color, (info_panel_center_x, y_pos))
        else:
            self.game.draw_text("Rキー: 視点反転", self.game.font_game, text_color, (info_panel_center_x, y_pos))

        mouse_pos = pygame.mouse.get_pos()
        is_hovering = self.ingame_menu_button.collidepoint(mouse_pos)
        btn_color = (210, 180, 140) if is_hovering else (196, 164, 132)
        btn_text_color = (50, 25, 0)
        shadow_rect = self.ingame_menu_button.move(5, 5)
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, btn_color, self.ingame_menu_button, border_radius=10)
        self.game.draw_text("メニューへ", self.game.font_game, btn_text_color, self.ingame_menu_button.center)

    def _get_move_targets(self):
        """選択中の駒が移動できるマスを計算する"""
        if self.selected_index is None: return []
        targets = []
        piece = self.game.pieces[self.selected_index]
        r0, c0 = piece["pos"]
        for i, move in enumerate(piece["move_list"]):
            if move:
                dr, dc = self.game.directions[i]
                if piece["team"] == "player2": dr *= -1; dc *= -1
                tr, tc = self.torus_wrap(r0 + dr, c0 + dc)
                is_target_vacant = True
                for p in self.game.pieces:
                    if p["pos"] == (tr, tc) and p["team"] == piece["team"]: is_target_vacant = False; break
                if is_target_vacant: targets.append((tr, tc))
        return targets

    def move_piece(self, piece_index, target_pos):
        """駒を動かし、ターンを進め、ゲーム終了条件をチェックする"""
        current_moving_piece_team = self.game.pieces[piece_index]["team"]
        for i, p in enumerate(list(self.game.pieces)):
            if p["pos"] == target_pos:
                self.game.pieces.pop(i)
                self.game.capture_count[current_moving_piece_team] += 1
                if i < piece_index:
                    piece_index -= 1
                break
        self.game.pieces[piece_index]["pos"] = target_pos
        self.selected_index = None
        self.game.turn = "player2" if self.game.turn == "player1" else "player1"
        self.game.turn_count += 1
        self._check_game_end_conditions()

    def torus_wrap(self, r, c):
        """座標が盤面からはみ出た場合に、反対側につなげる（トーラス）"""
        return r % ROWS, c % COLS

    def get_board_signature(self):
        """現在の盤面を識別するための一意の署名（文字列）を生成する"""
        state = sorted((p["team"], p["pos"]) for p in self.game.pieces)
        return (str(state), self.game.turn, self.is_flipped)

    def _check_game_end_conditions(self):
        """各種のゲーム終了条件をチェックする"""
        for team, count in self.game.capture_count.items():
            if count >= 3:
                self.game.winner = team
                return
        sig = self.get_board_signature()
        history = self.game.position_history
        history[sig] = history.get(sig, 0) + 1
        if history[sig] >= 3:
            self.game.winner = "Draw (Repetition)"
            return
        if self.game.turn_count >= MAX_TURNS:
            self.game.winner = "Draw (Turn Limit)"
            return