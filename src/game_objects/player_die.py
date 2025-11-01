from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional
from game_objects.die import Die
from game_objects.die_side import DieSide, BlankSide
from core.game_event import GameEvent, GameEventType

if TYPE_CHECKING:
    from dicewalk.main import DiceWalkGame


class PlayerDie(Die):
    """Player-controlled die that responds to movement input."""
    
    def __init__(self, grid_i: int, grid_j: int, scale: float = 0.8, sides: Optional[Dict[str, DieSide]] = None):
        # Default colorful sides for player
        if sides is None:
            sides = {
                'top': BlankSide('yellow', (255, 255, 0)),
                'bottom': BlankSide('gray', (128, 128, 128)),
                'north': BlankSide('green', (0, 255, 0)),
                'south': BlankSide('blue', (0, 0, 255)),
                'east': BlankSide('red', (255, 0, 0)),
                'west': BlankSide('magenta', (255, 0, 255)),
            }
        super().__init__(grid_i, grid_j, scale, sides)
        self.name = "Player Die"
    
    def on_event(self, event: GameEvent) -> None:
        """React to player movement requests."""
        if event.type == GameEventType.MOVE_REQUEST:
            di = event.get('di', 0)
            dj = event.get('dj', 0)
            game = event.get('game')
            if game and (di != 0 or dj != 0):
                self.tumble(game, di, dj)
