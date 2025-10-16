import sqlite3
import os
from settings import DB_PATH

# データベースに挿入する駒の初期データ
INITIAL_PIECES = [
    ('K', '10110101', os.path.join('images', 'K.png')),
    ('Y', '10100010', os.path.join('images', 'Y.png')),
    ('O', '11111111', os.path.join('images', 'O.png')),
    ('S', '01100110', os.path.join('images', 'S.png')),
    ('A', '01000101', os.path.join('images', 'A.png')),
    ('N', '10111101', os.path.join('images', 'N.png')),
    ('I', '01000010', os.path.join('images', 'I.png')),
    ('D', '11011001', os.path.join('images', 'D.png')),
    ('U', '10111111', os.path.join('images', 'U.png')),
    ('R', '11111101', os.path.join('images', 'R.png')),

]

def create_database():
    """データベースファイルとテーブルを作成し、初期データを挿入する"""
    
    if os.path.exists(DB_PATH):
        print(f"データベースファイル '{DB_PATH}' は既に存在します。")
        return

    print(f"データベースファイル '{DB_PATH}' を新規作成します...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        print("テーブル 'piece_definitions' を作成中...")
        cur.execute("""
        CREATE TABLE piece_definitions (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            move_list TEXT NOT NULL,
            image_path TEXT NOT NULL
        )
        """)

        print("駒の初期データを挿入中...")
        cur.executemany("INSERT INTO piece_definitions (name, move_list, image_path) VALUES (?, ?, ?)", INITIAL_PIECES)

        conn.commit()
        conn.close()
        
        print(f"'{DB_PATH}' の作成が正常に完了しました。")

    except Exception as e:
        print(f"データベースの作成中にエラーが発生しました: {e}")
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

if __name__ == "__main__":
    create_database()