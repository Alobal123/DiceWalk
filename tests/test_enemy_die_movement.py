from game_objects.enemy_die import EnemyDie
from game_objects.player_die import PlayerDie

class GameStub:
    def __init__(self):
        self.event_listener = type('EL', (), {'subscribe': lambda *a, **k: None, 'publish': lambda *a, **k: None})()
        self.tile_height = 10
        self.tile_width = 20
        self.origin_x = 0
        self.origin_y = 0
        def _iso_point(i,j):
            return (0,0)
        def _tile_center(i,j):
            return (0,0)
        self._iso_point = _iso_point
        self._tile_center = _tile_center
        self.tiles = [[[] for _ in range(8)] for _ in range(8)]

def test_enemy_ai_move(monkeypatch):
    g = GameStub()
    e = EnemyDie(3,3)
    e.set_game_reference(g)  # type: ignore[arg-type]
    # Force timer exceed
    e.move_timer = e.move_interval
    # Monkeypatch tumble to just update target instantly
    def fake_tumble(game, di, dj):
        e.grid_i += di
        e.grid_j += dj
    e.tumble = fake_tumble
    # Monkeypatch random.shuffle to keep order deterministic
    monkeypatch.setattr('random.shuffle', lambda lst: None)
    e.update(0.0)
    # First direction in list is (1,0), so position should advance east
    assert (e.grid_i, e.grid_j) == (4,3)
