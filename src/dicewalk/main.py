import arcade
import sys
from pathlib import Path

# Add src directory to path to allow imports from game_objects
sys.path.insert(0, str(Path(__file__).parent.parent))

from game_objects.player_die import PlayerDie
from game_objects.enemy_die import EnemyDie
from core.game_object import GameObject
from core.event_listener import EventListener
from core.game_event import GameEvent, GameEventType
from dicewalk.level import Level

SCREEN_TITLE = "Dice Walk"
GRID_SIZE = 8


class DiceWalkGame(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, SCREEN_TITLE, fullscreen=True)
        self.set_fullscreen(True)
        self.screen_width, self.screen_height = self.get_size()
        arcade.set_background_color(arcade.color.BLACK)
        # Level encapsulates grid geometry and tiles
        self.level = Level(self.screen_width, self.screen_height, GRID_SIZE)
        
        # Event system
        self.event_listener = EventListener()
        
        # Create dice and register them to tiles (player diagonally below enemy)
        self.enemy_die = EnemyDie(grid_i=1, grid_j=1)
        self.player_die = PlayerDie(grid_i=2, grid_j=2)
        self.level.add_object(self.enemy_die, self.enemy_die.grid_i, self.enemy_die.grid_j)
        self.level.add_object(self.player_die, self.player_die.grid_i, self.player_die.grid_j)
        # Activate player die subscribing only to MOVE_REQUEST events
        self.player_die.activate(self, events=[GameEventType.MOVE_REQUEST])
        self.enemy_die.set_game_reference(self)
        self.enemy_die.activate(self)
        # Subscribe game to MOVE_COMPLETE to adjust tiles
        # Subscribe level to MOVE_COMPLETE updates
        self.event_listener.subscribe(self.level.on_event, [GameEventType.MOVE_COMPLETE])

    # Delegate geometry helpers expected by dice / tiles
    def _iso_point(self, i: float, j: float):
        return self.level.iso_point(i, j)

    def _tile_center(self, i: int, j: int):
        return self.level.tile_center(i, j)

    def on_draw(self):
        self.clear()
        # Delegate drawing to level (passes itself so tile draw can call _tile_center)
        self.level.draw(arcade)

    def on_key_press(self, key, modifiers):
        # System commands - handle directly
        if key == arcade.key.ESCAPE:
            self.close()
            return
        
        if key == arcade.key.P:
            self.player_die.paused = not self.player_die.paused
            return
        
        # Gameplay commands - publish as events
        if self.player_die.animating:
            return
        
        di = dj = 0
        if key == arcade.key.UP:
            dj = 1
        elif key == arcade.key.DOWN:
            dj = -1
        elif key == arcade.key.RIGHT:
            di = 1
        elif key == arcade.key.LEFT:
            di = -1
        
        if di != 0 or dj != 0:
            # Publish move request event instead of calling directly
            self.event_listener.publish(GameEvent(
                type=GameEventType.MOVE_REQUEST,
                source=self,
                payload={'di': di, 'dj': dj, 'game': self}
            ))

    def on_update(self, delta_time: float):
        self.player_die.update(delta_time)
        self.enemy_die.update(delta_time)

    # Window no longer handles MOVE_COMPLETE (delegated to Level)
    def on_event(self, event: GameEvent):
        pass


def main():
    DiceWalkGame()
    arcade.run()


if __name__ == '__main__':
    main()
