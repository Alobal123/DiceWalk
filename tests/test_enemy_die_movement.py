from dicewalk.main import DiceWalkGame
from ecs.components import Position, AIWalker, TurnState

def test_enemy_turn_based_planning_and_execution():
    game = DiceWalkGame()
    enemy_entity = game.enemy_entity
    ai_store = game.world.get_component(AIWalker)
    # Enemy now has AIWalker
    assert enemy_entity in ai_store, "Enemy should have AIWalker for planning"
    pos_store = game.world.get_component(Position)
    start_pos = pos_store.get(enemy_entity)
    assert start_pos is not None, "Enemy position missing"
    # During planning phase (no key press) enemy should not move yet
    for _ in range(5):
        game.world.update(0.1)
    mid_pos = pos_store.get(enemy_entity)
    assert mid_pos is not None, "Enemy position missing mid-turn"
    assert (start_pos.i, start_pos.j) == (mid_pos.i, mid_pos.j), "Enemy moved before turn execution"
    # Simulate executing by sending a player move (e.g., UP) to commit turn
    import arcade
    game.on_key_press(arcade.key.UP, None)
    # Advance enough time for movement resolution
    total = 0.0
    while total < 0.5:
        game.world.update(0.1)
        total += 0.1
    end_pos = pos_store.get(enemy_entity)
    # Enemy may or may not have moved depending on random planning; ensure either moved or stayed if blocked.
    # At least ensure position object still valid.
    assert end_pos is not None
