from core.game_state_enum import GameState
from typing import Callable, Optional

StateChangeCallback = Callable[[GameState, GameState], None]

class GameStateManager:
    def __init__(self, on_change: Optional[StateChangeCallback] = None):
        self.state = GameState.GAME_OVER
        self._on_change = on_change

    def _set(self, new_state: GameState):
        if new_state != self.state:
            old = self.state
            self.state = new_state
            if self._on_change:
                try:
                    self._on_change(old, new_state)
                except Exception:
                    pass
    
    def set_state(self, new_state: GameState):
        self._set(new_state)

    def get_state(self):
        return self.state


