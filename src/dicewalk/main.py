"""Entry point for DiceWalkGame used by tests and runtime.

Supports running directly as a script (python path/to/main.py) by bootstrapping
the project src directory onto sys.path if needed.
"""

import arcade
import sys, pathlib

# Ensure src directory (this file's parent parent) is on sys.path when run directly
_here = pathlib.Path(__file__).resolve()
_src_root = _here.parent.parent
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

from ecs.die_factory import create_player_die, create_enemy_die
from ecs.components import Tile, Position
from dicewalk.level import Level
from ecs.world import World
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, tile_occupancy_system, ai_walker_system
from ecs.rendering import render_ecs
from ecs.events import Event as ECSEvent, MOVE_REQUEST as ECS_MOVE_REQUEST

SCREEN_TITLE = "Dice Walk"
GRID_SIZE = 8


class DiceWalkGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, SCREEN_TITLE, fullscreen=True)
        self.set_fullscreen(True)
        self.screen_width, self.screen_height = self.get_size()
        arcade.set_background_color(arcade.color.BLACK)
        self.level = Level(self.screen_width, self.screen_height, GRID_SIZE)

        # ECS World and systems
        self.world = World()
        self.world.add_system(movement_request_system)
        self.world.add_system(movement_progress_system)
        self.world.add_system(orientation_system)
        self.world.add_system(tile_occupancy_system)
        self.world.add_system(ai_walker_system)

        # Tile entities (static grid)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                tid = self.world.create_entity()
                self.world.add_component(tid, Position(i, j))
                self.world.add_component(tid, Tile())

        # Dice entities
        self.enemy_entity = create_enemy_die(self.world, 1, 1)
        self.player_entity = create_player_die(self.world, 2, 2)

    def _iso_point(self, i: float, j: float):
        return self.level.iso_point(i, j)

    def _tile_center(self, i: int, j: int):
        return self.level.tile_center(i, j)

    def is_ecs_oriented(self, die) -> bool:
        return True

    def on_draw(self):
        self.clear()
        self.level.draw(arcade)
        render_ecs(self.level, self.world)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close(); return
        di = dj = 0
        if key == arcade.key.UP: dj = 1
        elif key == arcade.key.DOWN: dj = -1
        elif key == arcade.key.RIGHT: di = 1
        elif key == arcade.key.LEFT: di = -1
        if di or dj:
            self.world.emit(ECSEvent(type=ECS_MOVE_REQUEST, entity=self.player_entity, data={'di': di, 'dj': dj}))

    def on_update(self, delta_time: float):
        self.world.update(delta_time)


def main():
    DiceWalkGame()
    arcade.run()


if __name__ == "__main__":
    main()
