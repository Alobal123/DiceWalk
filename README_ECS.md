# ECS Architecture (Final State)

The project has fully migrated from the legacy event-driven OOP dice model to a pure Entity–Component–System (ECS) architecture. All gameplay (movement, orientation, animation, AI, tile occupancy, rendering) is handled by ECS systems and components. Legacy artifacts (`EventListener`, `GameEvent`, `Die` subclasses, `GameObject` base, `DieSide` hierarchy) have been removed.

## Core Concepts
Components in use:
- `Position(i,j)` – Grid coordinates.
- `DieSide(face_id,color)` – Lightweight face data (color + id) replacing former class hierarchy.
- `DieFaces` – Logical face mapping (top/bottom/north/south/east/west) storing `DieSide` objects.
- `RenderCube(scale)` – Visual cube scale.
- `GridMove(start_i,start_j,di,dj,duration,elapsed)` – Active movement state.
- `TumbleAnim(start_i,start_j,di,dj,duration,elapsed,scale,faces_snapshot)` – Visual tumble interpolation + deferred orientation snapshot.
- `TileOccupancy(occupants)` – Sparse mapping (i,j) -> entity ids.
- `AIWalker(interval,timer)` – Emits periodic movement requests.
- `Tile` – Marker component for static grid tile entities (geometry reference; not tracked in occupancy).

Events (internal ECS queue):
- `MOVE_REQUEST` – Intent to move (produces a `GridMove` + `TumbleAnim`).
- `MOVE_STARTED` – Emitted when movement begins.
- `MOVE_COMPLETE` – Emitted after movement; orientation system rotates faces.

## Systems
- `movement_request_system` – Consumes `MOVE_REQUEST` → creates `GridMove` + `TumbleAnim`.
- `movement_progress_system` – Advances `GridMove.elapsed`, emits `MOVE_COMPLETE` when done, removes `GridMove` & `TumbleAnim`.
- `orientation_system` – Rotates `DieFaces` in response to `MOVE_COMPLETE` (face permutation logic centralized here).
- `tile_occupancy_system` – Updates occupancy lists when positions change.
- `ai_walker_system` – Ticks `AIWalker` components, emits `MOVE_REQUEST` at intervals.

## Rendering
`ecs/rendering.py` draws static and tumbling cubes. When a `TumbleAnim` is present, a rotational animation is shown; otherwise a standing cube. Painter order mimics legacy appearance using descending diagonal index.

## Dice Creation
`ecs/die_factory.py` provides `create_player_die` and `create_enemy_die` to spawn entities with all necessary components (faces, position, render info, AI for enemies, etc.).

## Input & AI
Keyboard input (`on_key_press`) directly emits ECS `MOVE_REQUEST` events. Enemy movement is autonomous via `AIWalker`.

## Removed Legacy Pieces
- `core/event_listener.py`, `core/game_event.py` – Replaced by ECS event queue.
- `game_objects/die.py`, `player_die.py`, `enemy_die.py` – Logic migrated into systems/components.
- `game_objects/die_side.py` & `core/game_object.py` – Replaced by `Face` dataclass + pure ECS rendering.
- Bridge & legacy tests (`test_event_listener.py`, `test_move_complete_tile.py`, `test_ecs_position_bridge.py`).

## Testing
Active tests focus on core ECS behavior:
- Movement creation & completion (`test_ecs_movement.py`).
- Orientation updates (`test_ecs_orientation.py`, `test_die_orientation.py`).
- AI movement (`test_enemy_die_movement.py`).

If you add new systems, prefer writing focused tests that:
1. Emit an event or create a component.
2. Run `world.update(dt)` until expected side-effects appear.
3. Assert on component presence/absence or face permutations.

## Extension Ideas
- Collision / blocked tile system.
- Turn/phase tracker (could add `TurnState` component + `TURN_START` events).
- Combat or scoring components.
- Pathfinding system replacing random AI walker.

## Troubleshooting (Current)
- Cube not animating: Ensure `GridMove` created (check component store) and `TumbleAnim` present.
- Orientation wrong after move: Verify `orientation_system` registered before any cleanup that might remove faces.
- Entity flicker or duplicate draw: Confirm only ECS rendering is invoked (legacy draw calls are gone) and sort order stable.

## Architecture Rationale
Separating concerns (data in components, logic in systems, events in a queue) enables incremental feature addition without modifying core objects. Rendering, movement, and orientation are isolated, simplifying future optimizations (e.g., batching draw calls or parallel movement updates).

This README reflects the finalized ECS state; earlier migration stages are no longer relevant to code operation but remain in version control history if needed.

## Running the Game

Preferred (module form with proper package resolution):

```bash
python -m dicewalk.main
```

Direct script path also works due to bootstrap logic in `dicewalk/main.py`:

```bash
python src/dicewalk/main.py
```

On Windows PowerShell from project root:

```powershell
python -m dicewalk.main
```

If using a venv:

```powershell
& .venv/Scripts/python.exe -m dicewalk.main
```

The window opens fullscreen; press ESC to quit.
