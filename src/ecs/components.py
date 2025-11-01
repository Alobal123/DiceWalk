from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(slots=True)
class DieSide:
    """Simple die side holding a color (lightweight replacement of legacy class)."""
    face_id: str
    color: Tuple[int, int, int]

    def get_color(self) -> Tuple[int, int, int]:
        return self.color

@dataclass(slots=True)
class Position:
    i: int
    j: int


@dataclass(slots=True)
class RenderCube:
    scale: float = 0.8

@dataclass(slots=True)
class DieFaces:
    sides: Dict[str, DieSide]
    snapshot: Optional[Dict[str, DieSide]] = None

@dataclass(slots=True)
class GridMove:
    start_i: int
    start_j: int
    di: int
    dj: int
    duration: float = 0.35
    elapsed: float = 0.0
    mode: str = "tumble"  # or 'slide'

@dataclass(slots=True)
class TumbleAnim:
    """Active tumble animation state for rendering interpolation.

    Mirrors GridMove timing; stores a snapshot of faces (Face objects) pre-rotation.
    """
    start_i: int
    start_j: int
    di: int
    dj: int
    duration: float
    elapsed: float = 0.0
    scale: float = 0.8
    faces_snapshot: Optional[Dict[str, DieSide]] = None

@dataclass(slots=True)
class AIWalker:
    interval: float = 1.5
    timer: float = 0.0

@dataclass(slots=True)
class TileOccupancy:
    """Sparse occupancy mapping: (i,j) -> list of entity ids occupying tile."""
    occupants: Dict[tuple[int,int], list[int]] = field(default_factory=dict)

@dataclass(slots=True)
class Tile:
    """Marker component for a grid tile entity (static background geometry)."""
    pass

@dataclass(slots=True)
class GridGeometry:
    """Holds isometric grid metrics and precomputed grid lines."""
    grid_size: int
    tile_height: float
    tile_width: float
    origin_x: float
    origin_y: float
    grid_lines: Tuple[tuple[float,float,float,float], ...]

    # Provide helpers matching removed Level class interface so rendering code
    # (and any future tile utilities) can call geom.iso_point/geom.tile_center.
    def iso_point(self, i: float, j: float) -> Tuple[float, float]:
        x = self.origin_x + (i - j) * (self.tile_width / 2)
        y = self.origin_y + (i + j) * (self.tile_height / 2)
        return x, y

    def tile_center(self, i: int, j: int) -> Tuple[float, float]:
        return self.iso_point(i + 0.5, j + 0.5)


@dataclass(slots=True)
class TurnState:
    """Singleton component tracking current turn phase and planned enemy moves.

    phase: 'planning' | 'executing'
    planned: list of dicts {entity, di, dj}
    """
    phase: str = 'planning'
    planned: list[dict] = field(default_factory=list)
    planning_elapsed: float = 0.0  # time spent in current planning phase (for preview gating)

@dataclass(slots=True)
class Barrier:
    """Immovable barrier tile rendered as wireframe cube."""
    pass

@dataclass(slots=True)
class HP:
    """Hit points component for entities that can take damage."""
    current: int
    max: int

@dataclass(slots=True)
class Renderable:
    """Generic render metadata.

    kind: semantic type (e.g., 'dice', 'barrier') used by renderer dispatch.
    layer: coarse ordering bucket (higher rendered later for same depth key)
    z_bias: fine float bias for tie-breaking within layer.
    visible: toggle without removing component.
    """
    kind: str
    layer: int = 0
    z_bias: float = 0.0
    visible: bool = True

@dataclass(slots=True)
class AttackEffect:
    """Effect definition: strength (damage) and targeting type.

    target_type: currently only 'forward-single' (one tile ahead relative to move direction)
    strength: integer damage applied to HP of entities in target tiles.
    """
    target_type: str = 'forward-single'
    strength: int = 1

@dataclass(slots=True)
class AttackSide:
    """Marks that a die side carries an attack effect.

    Associate with DieFaces via face_id mapping; when that face becomes 'top' after movement,
    the effect triggers.
    effect: AttackEffect instance.
    face_id: die side id string (e.g., 'top','north', etc.)
    """
    face_id: str
    effect: AttackEffect

@dataclass(slots=True)
class AttackSet:
    """Collection of face_id -> list[AttackEffect] for a die.

    Allows multiple independent patterns (e.g., forward-single + left-single + right-single) per face.
    """
    effects: Dict[str, list[AttackEffect]]

@dataclass(slots=True)
class Patrol:
    """Deterministic patrol: move each turn by (di,dj); reverse upon barrier/bounds block."""
    di: int
    dj: int
