from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass(slots=True)
class Event:
    type: str
    entity: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0

# Common event type constants (string form keeps it lightweight)
MOVE_REQUEST = "MoveRequest"
MOVE_STARTED = "MoveStarted"
MOVE_COMPLETE = "MoveComplete"
