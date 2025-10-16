# src/settings.py

import os
from enum import Enum

# --- パス設定 ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'pieces.db')

# --- 大学ごとの駒編成データ ---
UNIVERSITY_DATA = {
    "KYOUSAN":  [" ", "K", "Y", "O", "S", "A", "N", " "], 
    "KINKIDAI": [" ", "K", "I", "N", "D", "A", "I", " "],
    "KOUNAN":   [" ", "K", "O", "U", "N", "A", "N", " "],
    "RYUKOKU":  ["R", "Y", "U", "K", "O", "K", "U", " "]
}

# --- 定数設定 ---
CELL_SIZE =100
COLS = 8
ROWS = 7
WIDTH = CELL_SIZE * COLS
HEIGHT = CELL_SIZE * ROWS
MARGIN = 5
INFO_PANEL_WIDTH = 300
MAX_TURNS = 100
# --- 色の定数 ---
WHITE = (255, 255, 255)
GRID_COLOR = (0, 0, 0)
HIGHLIGHT_YELLOW = (230, 200, 100)
HIGHLIGHT_GREEN = (170, 210, 170)
BLUE = (100, 100, 255)
GRAY = (200, 200, 200)
BLACK = (0, 0, 0)

# --- ネットワーク設定 ---
DISCOVERY_PORT = 60000
GAME_PORT = 60001
DISCOVERY_MESSAGE = "PYGAME_SHOGI_DISCOVERY_V1"

# --- ゲーム状態 ---
class GameState(Enum):
    MENU = 1
    HOSTING_LOBBY = 2
    JOINING_LOBBY = 3
    IN_GAME = 4
    GAME_OVER = 5