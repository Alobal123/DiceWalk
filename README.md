# DiceWalk

Experimental isometric (dimetric 2:1) grid in Python using the [Arcade](https://api.arcade.academy/en/latest/) library. Left-click tiles to toggle a white extruded cube.

## Current Features
- Fullscreen window with black background.
- Adaptive 8x8 dimetric grid sized to ~70% of display height.
- Accurate screen<->grid coordinate conversion.
- Click to toggle cube (each tile has a `Tile` object with `has_cube`).

## Requirements
- Python 3.10+ recommended
- Arcade (pinned in `requirements.txt`)

## Setup (Windows PowerShell)
```powershell
# From repository root
python -m venv .venv
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
# Upgrade pip (optional)
pip install --upgrade pip
# Install dependencies
pip install -r requirements.txt
```

## Run the Game (Module form preferred)
```powershell
# Ensure venv is activated
python -m src.dicewalk.main
```
If you run directly:
```powershell
python src/dicewalk/main.py
```
an import fallback is used so it still works.

## Project Layout
```
src/
  dicewalk/
    __init__.py        # Package marker
    tile.py            # Tile dataclass (i, j, has_cube)
    main.py            # Window, drawing, input, cube rendering
requirements.txt       # Third-party libraries (arcade)
.gitignore             # Standard Python ignores
README.md              # Project documentation
```

## Next Steps / Ideas
- Shaded cube faces for depth.
- Hover highlight of tile under cursor.
- Stackable cube heights (elevation attribute on `Tile`).
- Save/load grid state (JSON).
- Performance batching (vertex lists).

## Contributing
Keep grid math consistent (2:1 ratio: `tile_width = 2*tile_height`). Use `DiceWalkGame._iso_point` and `_screen_to_grid` for coordinate work—avoid duplicating formulas.
