import sys
from pathlib import Path
import pytest

# Add src path for imports
SRC_DIR = Path(__file__).parent.parent / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.event_listener import EventListener
from core.game_event import GameEvent, GameEventType
from core.tile import Tile

class FakeGame:
    GRID_SIZE = 8
    def __init__(self):
        self.event_listener = EventListener()
        self.tile_height = 10
        self.tile_width = 20
        self.origin_x = 0
        self.origin_y = 0
        self.tiles = [[Tile(i,j) for j in range(self.GRID_SIZE)] for i in range(self.GRID_SIZE)]
    def _iso_point(self, i: float, j: float):
        x = self.origin_x + (i - j) * (self.tile_width / 2)
        y = self.origin_y + (i + j) * (self.tile_height / 2)
        return x, y
    def _tile_center(self, i:int, j:int):
        return self._iso_point(i+0.5, j+0.5)

@pytest.fixture
def game():
    return FakeGame()
