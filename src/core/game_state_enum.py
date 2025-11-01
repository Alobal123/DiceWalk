from enum import Enum, auto

class GameState(Enum):
    GAME_OVER = auto()  # Game ended (failure or victory), show results
