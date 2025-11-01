from dicewalk.main import DiceWalkGame
from ecs.components import Position, AIWalker
from ecs.events import Event as ECSEvent, MOVE_REQUEST
import random

def test_enemy_ai_move(monkeypatch):
    game = DiceWalkGame()
    # Ensure enemy entity has AIWalker component (factory creates with AI by default)
    ai_store = game.world.get_component(AIWalker)
    enemy_entity = game.enemy_entity
    ai = ai_store.get(enemy_entity)
    assert ai is not None
    # Force interval trigger
    ai.timer = ai.interval
    # Deterministic direction ordering
    monkeypatch.setattr(random, 'shuffle', lambda lst: None)
    # Run update small dt to trigger ai_walker_system emission
    game.world.update(0.01)
    # Advance movement to completion
    game.world.update(0.36)
    pos_store = game.world.get_component(Position)
    pos = pos_store.get(enemy_entity)
    # First direction list is (1,0) east; expect i advanced by 1
    assert pos is not None
    # Enemy starts at (1,1); deterministic east move advances to (2,1)
    assert (pos.i, pos.j) == (2,1)
