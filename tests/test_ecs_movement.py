from dicewalk.main import DiceWalkGame
from ecs.events import Event as ECSEvent, MOVE_REQUEST, MOVE_COMPLETE, MOVE_STARTED
from ecs.components import GridMove, Position
from dataclasses import replace

def test_move_request_creates_gridmove():
    game = DiceWalkGame()
    # Emit ECS MoveRequest directly (bypassing legacy) for player entity
    game.world.emit(ECSEvent(type=MOVE_REQUEST, entity=game.player_entity, data={'di':1,'dj':0}))
    # Run one update tick (systems process)
    game.world.update(0.01)
    move_store = game.world.get_component(GridMove)
    assert game.player_entity in move_store
    gm = move_store[game.player_entity]
    assert gm.di == 1 and gm.dj == 0
    # elapsed may have advanced during same update tick
    assert gm.elapsed >= 0.0


def test_gridmove_progress_and_complete():
    game = DiceWalkGame()
    # Create snapshot (slots dataclass: use manual copy)
    current = game.world.get_component(Position)[game.player_entity]
    start_snapshot = Position(current.i, current.j)
    game.world.emit(ECSEvent(type=MOVE_REQUEST, entity=game.player_entity, data={'di':1,'dj':0}))
    # Advance time in chunks until completion
    total = 0.0
    while total < 0.40:  # duration is 0.35
        game.world.update(0.05)
        total += 0.05
    # After completion, GridMove should be removed and Position advanced
    move_store = game.world.get_component(GridMove)
    assert game.player_entity not in move_store
    pos = game.world.get_component(Position)[game.player_entity]
    assert pos.i == start_snapshot.i + 1 and pos.j == start_snapshot.j
    # MOVE_COMPLETE event may have been consumed by orientation_system; position & component removal suffice.
