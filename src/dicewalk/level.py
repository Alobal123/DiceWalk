from __future__ import annotations
from typing import List


class Level:
    """Encapsulates grid, tiles and painter-order drawing for a level."""
    def __init__(self, screen_width: int, screen_height: int, grid_size: int):
        self.grid_size = grid_size
        # Derive tile metrics (mirrors previous logic from main window)
        self.tile_height = 0.7 * screen_height / (grid_size - 1)
        self.tile_width = 2 * self.tile_height
        self.origin_x = screen_width / 2
        self.origin_y = screen_height / 2 - (grid_size - 1) * self.tile_height / 2
        self.grid_lines: List[tuple[float, float, float, float]] = []
    # Legacy Tile grid removed; ECS handles entity placement.
        self._build_grid_lines()

    # --- Geometry helpers ---
    def iso_point(self, i: float, j: float):
        x = self.origin_x + (i - j) * (self.tile_width / 2)
        y = self.origin_y + (i + j) * (self.tile_height / 2)
        return x, y

    def tile_center(self, i: int, j: int):
        return self.iso_point(i + 0.5, j + 0.5)

    def _build_grid_lines(self):
        lines = []
        for i in range(self.grid_size + 1):
            lines.append((*self.iso_point(i, 0), *self.iso_point(i, self.grid_size)))
        for j in range(self.grid_size + 1):
            lines.append((*self.iso_point(0, j), *self.iso_point(self.grid_size, j)))
        self.grid_lines = lines

    # Object management & legacy events removed (pure ECS now).

    # --- Drawing ---
    def draw(self, arcade_mod):  # pass arcade to avoid global import issues in tests
        # Draw grid lines
        for (x1, y1, x2, y2) in self.grid_lines:
            arcade_mod.draw_line(x1, y1, x2, y2, arcade_mod.color.WHITE, 1)
    # Painter order handled separately during ECS cube rendering.

    # Expose methods used by Tile/Die drawing
    # Tile.draw expects game._tile_center; we let Level stand in when passed as 'game'
    _tile_center = tile_center
    _iso_point = iso_point