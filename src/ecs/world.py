from __future__ import annotations
from typing import Dict, Type, TypeVar, Callable, List, Iterable, Any
from ecs.events import Event

C = TypeVar("C")

class World:
    def __init__(self):
        self._next_entity_id = 1
        self.components: Dict[Type, Dict[int, Any]] = {}
        self.systems: List[Callable[["World", float], None]] = []
        self.event_queue: List[Event] = []
        self._next_events: List[Event] = []
        self._processing_events = False

    # --- Entity / Component management ---
    def create_entity(self) -> int:
        eid = self._next_entity_id
        self._next_entity_id += 1
        return eid

    def add_component(self, entity: int, comp: Any):
        store = self.components.setdefault(type(comp), {})
        store[entity] = comp
        return comp

    def get_component(self, comp_type: Type[C]) -> Dict[int, C]:
        return self.components.setdefault(comp_type, {})  # type: ignore

    def entities_with(self, *comp_types: Type) -> Iterable[int]:
        if not comp_types:
            return []
        first = self.get_component(comp_types[0])
        for eid in first.keys():
            ok = True
            for ct in comp_types[1:]:
                if eid not in self.get_component(ct):
                    ok = False
                    break
            if ok:
                yield eid

    # --- Events ---
    def emit(self, event: Event):
        if self._processing_events:
            self._next_events.append(event)
        else:
            self.event_queue.append(event)
        return event

    def flush_events(self):
        if self._next_events:
            self.event_queue.extend(self._next_events)
            self._next_events.clear()

    # --- Systems ---
    def add_system(self, system_fn: Callable[["World", float], None]):
        self.systems.append(system_fn)

    def update(self, dt: float):
        # Let systems run (they may enqueue events or mutate components)
        for sys_fn in self.systems:
            sys_fn(self, dt)
        # (Optional) process event phases later when we add consumers
        self._processing_events = True
        # Here we could route events to dedicated consumers; initial stage leaves them queued.
        self._processing_events = False
        self.flush_events()
