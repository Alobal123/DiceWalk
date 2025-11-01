from core.tile import Tile
from core.game_object import GameObject

class Dummy(GameObject):
    def __init__(self):
        super().__init__('Dummy')
        self.draw_called = False
        self.draw_on_game_called = False
    def draw(self, surface=None):
        self.draw_called = True
    def draw_on_game(self, game):
        self.draw_on_game_called = True

class GameStub:
    def __init__(self):
        self.tile_height = 10
        self.tile_width = 20
        self.origin_x = 0
        self.origin_y = 0
    def _iso_point(self, i,j):
        return (0,0)
    def _tile_center(self, i,j):
        return (0,0)

def test_tile_draw_calls_draw_on_game():
    t = Tile(0,0)
    g = GameStub()
    d = Dummy()
    t.add(d)
    t.draw(g)
    assert d.draw_on_game_called
