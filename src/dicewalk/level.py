from __future__ import annotations
from typing import List
from core.tile import Tile
from core.game_object import GameObject


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
        self.tiles: list[list[Tile]] = [[Tile(i, j) for j in range(grid_size)] for i in range(grid_size)]
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

    # --- Object management ---
    def add_object(self, obj: GameObject, i: int, j: int):
        if 0 <= i < self.grid_size and 0 <= j < self.grid_size:
            self.tiles[i][j].add(obj)

    # --- Event handling (MOVE_COMPLETE updates) ---
    def on_event(self, event):  # GameEvent type hinted externally
        try:
            from core.game_event import GameEventType
        except Exception:
            return
        if event.type != GameEventType.MOVE_COMPLETE:
            return
        p = event.payload or {}
        oi = p.get('old_i'); oj = p.get('old_j'); ni = p.get('new_i'); nj = p.get('new_j')
        mover = event.source
        if oi is None or oj is None or ni is None or nj is None:
            return
        try:
            oi = int(oi)  # type: ignore[arg-type]
            oj = int(oj)  # type: ignore[arg-type]
            ni = int(ni)  # type: ignore[arg-type]
            nj = int(nj)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return
        if not (0 <= oi < self.grid_size and 0 <= oj < self.grid_size and 0 <= ni < self.grid_size and 0 <= nj < self.grid_size):
            return
        try:
            # Remove from old tile
            if mover in self.tiles[oi][oj].objects:
                self.tiles[oi][oj].remove(mover)
            # Add to new tile
            if mover not in self.tiles[ni][nj].objects:
                self.tiles[ni][nj].add(mover)
        except Exception:
            pass

    # --- Drawing ---
    def draw(self, arcade_mod):  # pass arcade to avoid global import issues in tests
        # Draw grid lines
        for (x1, y1, x2, y2) in self.grid_lines:
            arcade_mod.draw_line(x1, y1, x2, y2, arcade_mod.color.WHITE, 1)
        # Painter order: far to near -> descending (i+j)
        coords = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size)]
        for i, j in sorted(coords, key=lambda t: (t[0] + t[1], t[0]), reverse=True):
            self.tiles[i][j].draw(self)  # Level provides tile_center via delegation

    # Expose methods used by Tile/Die drawing
    # Tile.draw expects game._tile_center; we let Level stand in when passed as 'game'
    _tile_center = tile_center
    _iso_point = iso_point