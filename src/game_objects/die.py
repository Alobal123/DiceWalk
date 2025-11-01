from __future__ import annotations
import arcade
import math
from typing import TYPE_CHECKING, Dict, Optional
from core.game_object import GameObject
from core.game_event import GameEvent, GameEventType
from game_objects.die_side import DieSide, BlankSide

if TYPE_CHECKING:
    from dicewalk.main import DiceWalkGame


class Die(GameObject):
    """Base class for a die that can tumble on an isometric grid."""
    
    def __init__(self, grid_i: int, grid_j: int, scale: float = 0.8, sides: Optional[Dict[str, DieSide]] = None):
        super().__init__(name="Die")
        self.grid_i = grid_i
        self.grid_j = grid_j
        self.scale = scale
        
        # Die sides: position (top/bottom/north/south/east/west) -> DieSide object
        self.sides = sides if sides is not None else {}
        
        # Animation state
        self.animating = False
        self.anim_type = 'slide'
        self.anim_elapsed = 0.0
        self.anim_duration = 0.35
        self.anim_di = 0
        self.anim_dj = 0
        self.anim_start_i = grid_i
        self.anim_start_j = grid_j
        self.anim_start_x = 0.0
        self.anim_start_y = 0.0
        self.anim_target_x = 0.0
        self.anim_target_y = 0.0
        self.anim_target_i = grid_i
        self.anim_target_j = grid_j
        self._faces_snapshot = None
        self.paused = False
    
    def on_event(self, event: GameEvent) -> None:
        """Override in subclasses to react to game events."""
        pass
    
    def draw(self, surface=None) -> None:
        """Required by GameObject but not used - use draw_on_game instead."""
        pass
    
    def draw_on_game(self, game: DiceWalkGame):
        """Draw the die in its current state."""
        if self.animating:
            t = min(self.anim_elapsed / self.anim_duration, 1.0)
            if self.anim_type == 'slide':
                cx = self.anim_start_x + (self.anim_target_x - self.anim_start_x) * t
                cy = self.anim_start_y + (self.anim_target_y - self.anim_start_y) * t
                self._draw_standing(game, cx, cy)
            else:
                self._draw_tumble(game, t)
            
            if t >= 1.0 and not self.paused:
                self.animating = False
                if self.anim_type == 'tumble':
                    self._commit_orientation()
                self.anim_type = 'slide'
        else:
            cx, cy = game._tile_center(self.grid_i, self.grid_j)
            self._draw_standing(game, cx, cy)

    def on_activate(self, game):  # store game reference for tile updates
        self._game = game
    
    def _draw_standing(self, game: DiceWalkGame, cx: float, cy: float):
        """Draw die at rest."""
        half = 0.5 * self.scale
        height = self.scale
        ci0 = self.grid_i + 0.5
        cj0 = self.grid_j + 0.5
        
        verts = [
            [ci0 - half, cj0 - half, 0.0], [ci0 - half, cj0 + half, 0.0],
            [ci0 + half, cj0 - half, 0.0], [ci0 + half, cj0 + half, 0.0],
            [ci0 - half, cj0 - half, height], [ci0 - half, cj0 + half, height],
            [ci0 + half, cj0 - half, height], [ci0 + half, cj0 + half, height],
        ]
        
        face_defs = [
            ([0,1,3,2], 'bottom'), ([4,5,7,6], 'top'),
            ([0,1,5,4], 'west'), ([2,3,7,6], 'east'),
            ([0,2,6,4], 'south'), ([1,3,7,5], 'north'),
        ]
        
        screen = []
        for (vi, vj, vz) in verts:
            sx, sy = game._iso_point(vi, vj)
            sy += vz * game.tile_height
            screen.append((sx, sy))
        
        faces_to_draw = []
        for face, logical in face_defs:
            depth = sum(screen[i][1] for i in face) / len(face)
            faces_to_draw.append((depth, face, logical))
        
        position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'west': 4, 'top': 5}
        faces_to_draw.sort(key=lambda x: position_priority.get(x[2], 99))
        
        for _, face, position in faces_to_draw:
            poly = [screen[i] for i in face]
            side = self.sides.get(position)
            if side:
                side.draw_face(game, poly, position)
    
    def _draw_tumble(self, game: DiceWalkGame, t: float):
        """Draw die during tumble animation."""
        angle = (math.pi / 2) * t
        si = self.anim_start_i
        sj = self.anim_start_j
        di = self.anim_di
        dj = self.anim_dj
        half = 0.5 * self.scale
        height = self.scale
        # Base center at start tile
        ci0 = si + 0.5
        cj0 = sj + 0.5

        # Apply a subtle slide toward target center for smaller dice.
        # We only start translating after halfway through rotation to avoid visual mismatch.
        # The needed correction is (1 - scale) in grid units (difference between full tile and cube footprint).
        if t > 0.5:
            raw = (t - 0.5) / 0.5  # remap second half of animation to 0..1
            # Quadratic ease-out: f(x)=1-(1-x)^2 gives fast start, gentle finish
            slide_t = 1 - (1 - raw) * (1 - raw)
            correction = (1.0 - self.scale) * slide_t  # proportional correction
            ci0 += di * correction
            cj0 += dj * correction
        
        verts = [
            [ci0 - half, cj0 - half, 0.0], [ci0 - half, cj0 + half, 0.0],
            [ci0 + half, cj0 - half, 0.0], [ci0 + half, cj0 + half, 0.0],
            [ci0 - half, cj0 - half, height], [ci0 - half, cj0 + half, height],
            [ci0 + half, cj0 - half, height], [ci0 + half, cj0 + half, height],
        ]
        
        if di != 0:
            pivot_i = ci0 + half * di
            for v in verts:
                i_off = v[0] - pivot_i
                z = v[2]
                sin_sign = -1 if di == 1 else 1
                v[0] = pivot_i + i_off * math.cos(angle) - z * math.sin(angle) * sin_sign
                v[2] = i_off * math.sin(angle) * sin_sign + z * math.cos(angle)
        elif dj != 0:
            pivot_j = cj0 + half * dj
            for v in verts:
                j_off = v[1] - pivot_j
                z = v[2]
                sin_sign = -1 if dj == 1 else 1
                v[1] = pivot_j + j_off * math.cos(angle) - z * math.sin(angle) * sin_sign
                v[2] = j_off * math.sin(angle) * sin_sign + z * math.cos(angle)
        
        face_defs = [
            ([0,1,3,2], 'bottom'), ([4,5,7,6], 'top'),
            ([0,1,5,4], 'west'), ([2,3,7,6], 'east'),
            ([0,2,6,4], 'south'), ([1,3,7,5], 'north'),
        ]
        
        screen = []
        for (vi, vj, vz) in verts:
            sx, sy = game._iso_point(vi, vj)
            sy += vz * game.tile_height
            screen.append((sx, sy))
        
        faces_to_draw = []
        for face, logical in face_defs:
            depth = sum(screen[i][1] for i in face) / len(face)
            faces_to_draw.append((depth, face, logical))
        
        if di == 1 or dj == 1:
            position_priority = {'north': 0, 'east': 1, 'bottom': 2, 'top': 3, 'south': 4, 'west': 5}
        elif dj == 1:
            position_priority = {'north': 0, 'east': 1, 'bottom': 2, 'top': 3, 'south': 4, 'west': 5}
        elif di == -1:
            position_priority = {'north': 0, 'bottom': 1, 'east': 2, 'west': 3, 'south': 4, 'top': 5}
        elif dj == -1:
            position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'top': 4, 'west': 5}
        else:
            position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'west': 4, 'top': 5}
        
        faces_to_draw.sort(key=lambda x: position_priority.get(x[2], 99))
        
        for _, face, position in faces_to_draw:
            poly = [screen[i] for i in face]
            active_sides = self._faces_snapshot if (self._faces_snapshot is not None and self.animating and self.anim_type == 'tumble') else self.sides
            side = active_sides.get(position)
            if side:
                side.draw_face(game, poly, position)
    
    def _commit_orientation(self):
        """Update side positions after tumble completes."""
        di = self.anim_di
        dj = self.anim_dj
        s = self.sides
        
        if di == 1:
            s['top'], s['east'], s['bottom'], s['west'] = s['west'], s['top'], s['east'], s['bottom']
        elif di == -1:
            s['top'], s['west'], s['bottom'], s['east'] = s['east'], s['top'], s['west'], s['bottom']
        elif dj == 1:
            s['top'], s['north'], s['bottom'], s['south'] = s['south'], s['top'], s['north'], s['bottom']
        elif dj == -1:
            s['top'], s['south'], s['bottom'], s['north'] = s['north'], s['top'], s['south'], s['bottom']
        
        self._faces_snapshot = None
        
        # Update grid position only after animation completes
        old_i, old_j = self.grid_i, self.grid_j
        self.grid_i = self.anim_target_i
        self.grid_j = self.anim_target_j
        # Emit MOVE_COMPLETE so game can update tiles
        game = getattr(self, '_game', None)
        if game:
            from core.game_event import GameEvent, GameEventType
            ev = GameEvent(
                type=GameEventType.MOVE_COMPLETE,
                source=self,
                payload={'old_i': old_i, 'old_j': old_j, 'new_i': self.grid_i, 'new_j': self.grid_j}
            )
            try:
                game.event_listener.publish(ev)
            except Exception:
                pass
    
    def tumble(self, game: DiceWalkGame, di: int, dj: int):
        """Start tumbling animation in direction (di, dj)."""
        if self.animating:
            return
        
        ni = self.grid_i + di
        nj = self.grid_j + dj
        
        # Validate bounds
        if not (0 <= ni < 8 and 0 <= nj < 8):  # TODO: use GRID_SIZE
            return
        
        self.anim_type = 'tumble'
        self.anim_di = di
        self.anim_dj = dj
        self.anim_start_i = self.grid_i
        self.anim_start_j = self.grid_j
        self.anim_target_i = ni
        self.anim_target_j = nj
        self.anim_start_x, self.anim_start_y = game._tile_center(self.grid_i, self.grid_j)
        self.anim_target_x, self.anim_target_y = game._tile_center(ni, nj)
        self.anim_elapsed = 0.0
        self.animating = True
        self._faces_snapshot = dict(self.sides)
        # Don't update grid_i, grid_j until animation completes
    
    def update(self, delta_time: float):
        """Update animation state."""
        if self.animating and not self.paused:
            self.anim_elapsed += delta_time
