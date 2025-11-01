from __future__ import annotations
import arcade
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple
from core.game_object import GameObject

if TYPE_CHECKING:
    from dicewalk.main import DiceWalkGame

EDGE_COLOR = (0, 200, 255)


class DieSide(GameObject, ABC):
    """Abstract base class for a die side/face."""
    
    def __init__(self, name: str, face_id: str):
        super().__init__(name=name)
        self.face_id = face_id  # Unique identifier for this face (e.g., 'yellow', 'red')
    
    @abstractmethod
    def get_color(self) -> Tuple[int, int, int]:
        """Return the base color for this die side."""
        pass
    
    @abstractmethod
    def draw_symbols(self, game: DiceWalkGame, face_center: Tuple[float, float], 
                    face_poly: List[Tuple[float, float]], position: str):
        """
        Draw symbols/decorations on the die face.
        
        Args:
            game: The game instance for drawing context
            face_center: (x, y) center point of the face in screen coordinates
            face_poly: List of (x, y) points defining the face polygon
            position: Current logical position ('top', 'bottom', 'north', 'south', 'east', 'west')
        """
        pass
    
    def draw_face(self, game: DiceWalkGame, face_poly: List[Tuple[float, float]], position: str):
        """
        Draw the complete die face including fill, edges, and symbols.
        
        Args:
            game: The game instance for drawing context
            face_poly: List of (x, y) points defining the face polygon
            position: Current logical position ('top', 'bottom', 'north', 'south', 'east', 'west')
        """
        # Draw the filled polygon
        color = self.get_color()
        arcade.draw_polygon_filled(face_poly, color)
        
        # Draw edges
        for i in range(len(face_poly)):
            p1 = face_poly[i]
            p2 = face_poly[(i + 1) % len(face_poly)]
            arcade.draw_line(p1[0], p1[1], p2[0], p2[1], EDGE_COLOR, 2)
        
        # Draw symbols on top
        face_center = (sum(p[0] for p in face_poly) / len(face_poly), 
                      sum(p[1] for p in face_poly) / len(face_poly))
        self.draw_symbols(game, face_center, face_poly, position)
    
    def draw(self, surface=None) -> None:
        """Required by GameObject but not used for die sides."""
        pass


class BlankSide(DieSide):
    """A simple die side with just a solid color."""
    
    def __init__(self, face_id: str, color: Tuple[int, int, int]):
        super().__init__(name=f"Blank Side ({face_id})", face_id=face_id)
        self.color = color
    
    def get_color(self) -> Tuple[int, int, int]:
        """Return the solid color for this face."""
        return self.color
    
    def draw_symbols(self, game: DiceWalkGame, face_center: Tuple[float, float], 
                    face_poly: List[Tuple[float, float]], position: str):
        """Blank sides have no symbols - just the solid color."""
        pass
