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
