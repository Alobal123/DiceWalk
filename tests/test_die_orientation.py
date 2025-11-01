from game_objects.player_die import PlayerDie
from game_objects.die_side import BlankSide

class DummyGame:
    def __init__(self):
        self.tile_height = 10
        self.tile_width = 20
        self.origin_x = 0
        self.origin_y = 0
        def _iso_point(i,j):
            x = self.origin_x + (i - j) * (self.tile_width / 2)
            y = self.origin_y + (i + j) * (self.tile_height / 2)
            return x, y
        def _tile_center(i,j):
            return _iso_point(i+0.5,j+0.5)
        self._iso_point = _iso_point
        self._tile_center = _tile_center
        class EL: # minimal stub
            def publish(self, ev):
                pass
        self.event_listener = EL()

# Helper to finish tumble
def finish_tumble(die):
    die.animating = True
    die.anim_type = 'tumble'
    die.anim_elapsed = die.anim_duration
    die._commit_orientation()
    die.animating = False

def test_orientation_east():
    die = PlayerDie(0,0)
    die.anim_di = 1; die.anim_dj = 0
    start_top = die.sides['top']
    finish_tumble(die)
    # After east tumble: previous west goes to top per mapping
    assert die.sides['top'] is not start_top

def test_orientation_west():
    die = PlayerDie(0,0)
    die.anim_di = -1; die.anim_dj = 0
    start_top = die.sides['top']
    finish_tumble(die)
    assert die.sides['top'] is not start_top

def test_orientation_north():
    die = PlayerDie(0,0)
    die.anim_di = 0; die.anim_dj = 1
    start_top = die.sides['top']
    finish_tumble(die)
    assert die.sides['top'] is not start_top

def test_orientation_south():
    die = PlayerDie(0,0)
    die.anim_di = 0; die.anim_dj = -1
    start_top = die.sides['top']
    finish_tumble(die)
    assert die.sides['top'] is not start_top
