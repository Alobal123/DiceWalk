# DiceWalk# DiceWalk



Turn-based isometric dice tactics prototype using a lightweight custom ECS.Experimental isometric (dimetric 2:1) grid in Python using the [Arcade](https://api.arcade.academy/en/latest/) library. Left-click tiles to toggle a white extruded cube.



## Overview## Current Features

DiceWalk renders an isometric grid where each die (player or enemy) occupies a tile and may plan & execute tumble moves. Movement, planning, collision resolution, and HP management are handled through ECS components & systems explicitly—no monolithic game object class.- Fullscreen window with black background.

- Adaptive 8x8 dimetric grid sized to ~70% of display height.

## Core Concepts- Accurate screen<->grid coordinate conversion.

- **Entities**: Integer IDs created by the `World`.- Click to toggle cube (each tile has a `Tile` object with `has_cube`).

- **Components**: Plain dataclasses stored in dicts keyed by entity id. Key components:

  - `Position(i,j)` tile coordinates.## Requirements

  - `RenderCube(scale)` visual cube scale.- Python 3.10+ recommended

  - `DieFaces` + `DieSide` hold color data for cube faces.- Arcade (pinned in `requirements.txt`)

  - `GridMove` / `TumbleAnim` drive movement & interpolation.

  - `TurnState` stores phase (`planning` | `executing`) and enemy planned moves list.## Setup (Windows PowerShell)

  - `Barrier` marks immovable blocking tiles (optionally rendered if in-bounds).```powershell

  - `HP(current,max)` hit points for dice + UI bar.# From repository root

  - `Renderable(kind, layer, z_bias)` generic rendering metadata.python -m venv .venv

  - `GridGeometry` singleton: isometric projection & grid metrics.# Activate the virtual environment

- **Systems**: Pure functions run each update: movement requests, progress, orientation, occupancy, enemy planning, turn advance, and the explicit draw system (`render_system`) called from `on_draw`..\.venv\Scripts\Activate.ps1

- **Events**: Simple queued events (e.g., `MOVE_REQUEST`, `MOVE_STARTED`, `MOVE_COMPLETE`) for decoupling movement phases.# Upgrade pip (optional)

pip install --upgrade pip

## Turn Flow# Install dependencies

1. Phase = planning:pip install -r requirements.txt

   - Enemies generate one intended move each (avoiding barriers & conflicts) and store in `TurnState.planned` with precomputed target (ti,tj).```

   - Player chooses a direction. If target tile blocked by barrier or enemy planned target, the turn aborts (remains planning).

2. Player commits move (if valid): an event is emitted for the player plus events for each planned enemy move; phase switches to executing.## Run the Game (Module form preferred)

3. Execution: movement systems animate tumbles; upon all moves completing the turn phase resets to planning and new enemy plans are generated.```powershell

# Ensure venv is activated

## Movement & Collision Rulespython -m src.dicewalk.main

- Enemy vs enemy destination conflicts resolved deterministically: earlier planned move wins; later conflicting enemy loses its move.```

- Player attempting to move into an enemy planned tile or barrier: player move cancelled, enemies do not execute (turn stays planning).If you run directly:

- Barriers (including invisible boundary ring) block planning and movement.```powershell

python src/dicewalk/main.py

## Rendering```

- **Depth Rule**: Larger (i + j) is FARTHER BACK. (Important project convention.)an import fallback is used so it still works.

- Depth key: `(-(i+j), i, layer, z_bias)` sorted ascending (so back draws first, front last). Dice use layer 1; barriers layer 0.

- `Renderable.kind` dispatches: `dice` draws cube faces (+ HP bar), `barrier` wireframe.## Project Layout

- Planned enemy move highlights drawn separately before main render pass.```

- HP bars & X/Y text drawn above each die.src/

  dicewalk/

## Running    __init__.py        # Package marker

```bash    tile.py            # Tile dataclass (i, j, has_cube)

python -m dicewalk.main    main.py            # Window, drawing, input, cube rendering

```requirements.txt       # Third-party libraries (arcade)

(Full-screen window; ESC exits.).gitignore             # Standard Python ignores

README.md              # Project documentation

## Project Layout```

```

src/## Next Steps / Ideas

  ecs/- Shaded cube faces for depth.

    components.py   # All component dataclasses (including Renderable, TurnState, HP, etc.)- Hover highlight of tile under cursor.

    systems.py      # Movement, planning, turn advance, occupancy, orientation- Stackable cube heights (elevation attribute on `Tile`).

    rendering.py    # Draw helpers + render_system- Save/load grid state (JSON).

    die_factory.py  # Helper constructors for player/enemy dice- Performance batching (vertex lists).

    events.py       # Event dataclasses and constants

    world.py        # Minimal ECS world (entity id, components, systems, events)## Contributing

  dicewalk/Keep grid math consistent (2:1 ratio: `tile_width = 2*tile_height`). Use `DiceWalkGame._iso_point` and `_screen_to_grid` for coordinate work—avoid duplicating formulas.

    main.py         # Window bootstrap & wiring
```

## Adding New Visual Entities
1. Create entity, add `Position`.
2. Add any domain components (e.g., Barrier, HP).
3. Add `Renderable(kind='your_kind', layer=..., z_bias=...)`.
4. Extend `render_system` dispatch: handle `your_kind` (draw primitive / sprite).

## Extensibility Ideas
- Damage system + death (remove HP or entity when HP <= 0).
- Multiple dice per side & initiative ordering.
- Combat log driven by events.
- Debug overlays (depth keys, entity ids).
- Path preview multi-step planning.

## Testing
Pytest targets core behaviors: HP presence, movement conflicts, barrier blocking, boundary enforcement, turn abort logic. Add new tests by importing `World` and composing entities with components—no heavy fixtures required.

## Style & Conventions
- Components are pure data (no methods except tiny helpers like `DieSide.get_color`).
- Systems should be stateless functions: `(world, dt) -> None`.
- Keep rendering side-effects isolated to `render_system` & helper draw functions.
- Preserve the depth rule comment anywhere depth logic is touched.

## License
(Add license info here if/when defined.)

## Credits
Prototype structure & ECS scaffolding authored during iterative refactor sessions.
