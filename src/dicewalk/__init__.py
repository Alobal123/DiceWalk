"""dicewalk package initializer.

Ensures tests can import `dicewalk.main` when running under pytest.
Re-exports DiceWalkGame for convenience.
"""

from .main import DiceWalkGame  # noqa: F401
