from dataclasses import dataclass

@dataclass
class Tile:
    i: int
    j: int
    has_cube: bool = False

    def toggle_cube(self):
        self.has_cube = not self.has_cube
