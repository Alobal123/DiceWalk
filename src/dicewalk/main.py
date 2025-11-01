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
from ecs.components import Tile, Position, GridGeometry, TurnState, Barrier, Renderable
from ecs.world import World
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, tile_occupancy_system, attack_effect_system, player_turn_commit_system
from ecs.rendering import render_system, draw_planned_move_highlights, draw_planned_attack_highlights
from ecs.events import Event as ECSEvent, MOVE_REQUEST as ECS_MOVE_REQUEST, PLAYER_MOVE_INTENT

SCREEN_TITLE = "Dice Walk"
GRID_SIZE = 8


class DiceWalkGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, SCREEN_TITLE, fullscreen=True)
        self.set_fullscreen(True)
        self.screen_width, self.screen_height = self.get_size()
        arcade.set_background_color(arcade.color.BLACK)
        # ECS World
        self.world = World()
        # Inline grid geometry (replaces Level class)
        tile_height = 0.7 * self.screen_height / (GRID_SIZE - 1)
        tile_width = 2 * tile_height
        origin_x = self.screen_width / 2
        origin_y = self.screen_height / 2 - (GRID_SIZE - 1) * tile_height / 2
        def iso_point_local(i: float, j: float):
            x = origin_x + (i - j) * (tile_width / 2)
            y = origin_y + (i + j) * (tile_height / 2)
            return x, y
        grid_lines = []
        for i in range(GRID_SIZE + 1):
            grid_lines.append((*iso_point_local(i, 0), *iso_point_local(i, GRID_SIZE)))
        for j in range(GRID_SIZE + 1):
            grid_lines.append((*iso_point_local(0, j), *iso_point_local(GRID_SIZE, j)))
        geom = GridGeometry(GRID_SIZE, tile_height, tile_width, origin_x, origin_y, tuple(grid_lines))
        self.grid_entity = self.world.create_entity()
        self.world.add_component(self.grid_entity, geom)
        # Systems
        self.world.add_system(movement_request_system)
        self.world.add_system(movement_progress_system)
        self.world.add_system(orientation_system)
        self.world.add_system(attack_effect_system)
        self.world.add_system(tile_occupancy_system)
        # New turn-based systems
        from ecs.systems import enemy_planning_system, turn_advance_system
        self.world.add_system(enemy_planning_system)
        self.world.add_system(turn_advance_system)
        self.world.add_system(player_turn_commit_system)
        # Autonomous ai_walker_system removed: enemy will only move via planned turn execution.

        # Tile entities (static grid)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                tid = self.world.create_entity()
                self.world.add_component(tid, Position(i, j))
                self.world.add_component(tid, Tile())

        # Dice entities
        # Enemy created with AIWalker so planning system can generate moves
        self.enemy_entity = create_enemy_die(self.world, 1, 1, ai=True)
        self.world.add_component(self.enemy_entity, Renderable(kind='dice', layer=1, z_bias=0.1))
        self.player_entity = create_player_die(self.world, 2, 2)
        self.world.add_component(self.player_entity, Renderable(kind='dice', layer=1, z_bias=0.1))
        # Turn state singleton
        turn_eid = self.world.create_entity()
        self.world.add_component(turn_eid, TurnState())
        # Sample barriers
        for (bi, bj) in [(4,4), (5,2), (2,5)]:
            beid = self.world.create_entity()
            self.world.add_component(beid, Position(bi, bj))
            self.world.add_component(beid, Barrier())
            self.world.add_component(beid, Renderable(kind='barrier', layer=0, z_bias=0.0))
        # Boundary barriers (invisible): surround grid to prevent leaving
        # Positions just outside 0..GRID_SIZE-1
        for i in range(GRID_SIZE):
            for (oi, oj) in [(-1, i), (GRID_SIZE, i)]:  # left/right outside columns
                b_eid = self.world.create_entity()
                self.world.add_component(b_eid, Position(oi, oj))
                self.world.add_component(b_eid, Barrier())
                # Boundary barriers invisible: skip Renderable so they are not drawn
        for j in range(GRID_SIZE):
            for (oi, oj) in [(j, -1), (j, GRID_SIZE)]:  # bottom/top outside rows
                b_eid = self.world.create_entity()
                self.world.add_component(b_eid, Position(oi, oj))
                self.world.add_component(b_eid, Barrier())

    def _iso_point(self, i: float, j: float):
        geom = self.world.get_component(GridGeometry)[self.grid_entity]
        x = geom.origin_x + (i - j) * (geom.tile_width / 2)
        y = geom.origin_y + (i + j) * (geom.tile_height / 2)
        return x, y

    def _tile_center(self, i: int, j: int):
        return self._iso_point(i + 0.5, j + 0.5)

    def is_ecs_oriented(self, die) -> bool:
        return True

    def on_draw(self):
        self.clear()
        geom = self.world.get_component(GridGeometry)[self.grid_entity]
        # Draw grid lines
        for (x1, y1, x2, y2) in geom.grid_lines:
            arcade.draw_line(x1, y1, x2, y2, arcade.color.WHITE, 1)
        # Planned enemy move & attack highlights during planning phase
        draw_planned_move_highlights(geom, self.world)
        draw_planned_attack_highlights(geom, self.world)
        # Render all entities with Renderable component
        render_system(self.world)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.close(); return
        di = dj = 0
        if key == arcade.key.UP: dj = 1
        elif key == arcade.key.DOWN: dj = -1
        elif key == arcade.key.RIGHT: di = 1
        elif key == arcade.key.LEFT: di = -1
        if di or dj:
            # Emit intent event; system will validate and commit if allowed
            self.world.emit(ECSEvent(type=PLAYER_MOVE_INTENT, entity=self.player_entity, data={'di': di, 'dj': dj}))

    def on_update(self, delta_time: float):
        self.world.update(delta_time)


def main():
    DiceWalkGame()
    arcade.run()


if __name__ == "__main__":
    main()

def _build_grid_lines(grid_size: int, iso_point_fn):
    # Deprecated helper (geometry now inlined in __init__); retained temporarily for reference.
    lines = []
    for i in range(grid_size + 1):
        lines.append((*iso_point_fn(i, 0), *iso_point_fn(i, grid_size)))
    for j in range(grid_size + 1):
        lines.append((*iso_point_fn(0, j), *iso_point_fn(grid_size, j)))
    return tuple(lines)


