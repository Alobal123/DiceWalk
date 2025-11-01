from __future__ import annotations
from typing import List
from core.game_object import GameObject

class Tile:
    """Represents a grid tile holding game objects located on it."""
    __slots__ = ("i","j","objects")
    def __init__(self, i: int, j: int):
        self.i = i
        self.j = j
        self.objects: List[GameObject] = []
    
    def add(self, obj: GameObject):
        if obj not in self.objects:
            self.objects.append(obj)
    
    def remove(self, obj: GameObject):
        if obj in self.objects:
            self.objects.remove(obj)
    
    def draw(self, game):
        # Depth sort by screen y center if possible
        def center_y(o):
            if hasattr(o, 'grid_i') and hasattr(o, 'grid_j'):
                cx, cy = game._tile_center(o.grid_i, o.grid_j)
                return cy
            return 0
        for obj in sorted(self.objects, key=center_y):
            obj.draw_on_game(game)
