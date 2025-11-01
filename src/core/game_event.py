from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

class GameEventType(Enum):
    TURN_START = auto()
    MOVE_REQUEST = auto()
    MOVE_COMPLETE = auto()


@dataclass(slots=True)
class GameEvent:
    type: GameEventType
    source: Any | None = None
    payload: Optional[dict[str, Any]] = None

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default) if self.payload else default

    def __repr__(self) -> str:  # Helpful for debugging
        return f"GameEvent(type={self.type}, payload={self.payload})"
