from __future__ import annotations
import random
from typing import TYPE_CHECKING, Dict, Optional
from game_objects.die import Die
from game_objects.die_side import DieSide, BlankSide
from core.game_event import GameEvent, GameEventType

if TYPE_CHECKING:
    from dicewalk.main import DiceWalkGame


class EnemyDie(Die):
    """AI-controlled enemy die that moves automatically."""
    
    def __init__(self, grid_i: int, grid_j: int, scale: float = 0.6, sides: Optional[Dict[str, DieSide]] = None):
        # Default green sides for enemy
        if sides is None:
            green_shades = [
                (0, 100, 0),    # dark green
                (0, 120, 0),    
                (0, 140, 0),
                (0, 160, 0),
                (0, 180, 0),
                (0, 200, 0),    # lighter green
            ]
            sides = {
                'top': BlankSide('green1', green_shades[0]),
                'bottom': BlankSide('green2', green_shades[1]),
                'north': BlankSide('green3', green_shades[2]),
                'south': BlankSide('green4', green_shades[3]),
                'east': BlankSide('green5', green_shades[4]),
                'west': BlankSide('green6', green_shades[5]),
            }
        super().__init__(grid_i, grid_j, scale, sides)
        self.name = "Enemy Die"
        self.move_timer = 0.0
        self.move_interval = 1.5  # Move every 1.5 seconds
    
    def on_event(self, event: GameEvent) -> None:
        """Enemy doesn't respond to player input."""
        pass
    
    def update(self, delta_time: float):
        """Update animation and AI movement."""
        # Update animation
        super().update(delta_time)
        
        # AI movement logic
        if not self.animating:
            self.move_timer += delta_time
            if self.move_timer >= self.move_interval:
                self.move_timer = 0.0
                self._make_ai_move()
    
    def _make_ai_move(self):
        """Make a random valid move."""
        # Get the game instance from the event listener if available
        # For now, we'll try random directions
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)
        
        # Try each direction until we find a valid one
        for di, dj in directions:
            ni = self.grid_i + di
            nj = self.grid_j + dj
            # Check bounds (TODO: get GRID_SIZE from game)
            if 0 <= ni < 8 and 0 <= nj < 8:
                # For now, we need the game instance to tumble
                # This will be set when we integrate with main
                if hasattr(self, '_game_ref'):
                    self.tumble(self._game_ref, di, dj)
                break
    
    def set_game_reference(self, game: DiceWalkGame):
        """Set reference to game instance for AI movement."""
        self._game_ref = game
