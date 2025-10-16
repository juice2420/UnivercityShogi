# すべてのシーンの基底クラス
class BaseScene:
    # シーンの初期化処理
    def __init__(self, game):
        self.game = game
        self.next_scene = self

    # ユーザーからの入力を処理
    def process_input(self, events, pressed_keys):
        raise NotImplementedError

    # ゲームの状態を更新する処理
    def update(self):
        raise NotImplementedError

    # 盤面のオブジェクトを描画する処理
    def draw(self, screen):
        raise NotImplementedError

    # 次のシーンに切り替えるための処理
    def switch_to_scene(self, next_scene):
        self.next_scene = next_scene