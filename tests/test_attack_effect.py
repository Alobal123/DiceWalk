from ecs.world import World
from ecs.components import Position, TurnState, Barrier, HP
from ecs.die_factory import create_player_die, create_enemy_die
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, attack_effect_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST as ECS_MOVE_REQUEST

def _setup_world():
    w = World()
    # Minimal systems needed for movement + orientation + attack
    w.add_system(movement_request_system)
    w.add_system(movement_progress_system)
    w.add_system(orientation_system)
    w.add_system(attack_effect_system)
    return w

def test_attack_triggers_on_tile_one_ahead_beyond_destination():
    w = _setup_world()
    # Attacker at (2,2) moves north to (2,3); forward-single now targets (2,4) one beyond final.
    attacker = create_player_die(w, 2, 2)
    # Place target at (2,4) (two ahead of start, one ahead of destination)
    target = create_enemy_die(w, 2, 4, ai=False)
    w.emit(ECSEvent(type=ECS_MOVE_REQUEST, entity=attacker, data={'di': 0, 'dj': 1}))
    total = 0.0
    while total < 0.4:
        w.update(0.1)
        total += 0.1
    hp_store = w.get_component(HP)
    assert hp_store[target].current == 4, f"Expected target HP 4 after forward-single beyond destination, got {hp_store[target].current}"

def test_no_attack_without_movement():
    w = _setup_world()
    attacker = create_player_die(w, 1, 1)
    target = create_enemy_die(w, 1, 2, ai=False)
    # Do NOT emit movement; just run updates
    for _ in range(5):
        w.update(0.1)
    hp_store = w.get_component(HP)
    assert hp_store[target].current == 5, "Attack should not trigger without movement"

def test_enemy_attack_triggers_on_tile_one_ahead():
    w = _setup_world()
    enemy = create_enemy_die(w, 3, 3, ai=False)
    # Enemy moves north to (3,4); attack applies to (3,5). Place victim at (3,5).
    victim = create_player_die(w, 3, 5)
    w.emit(ECSEvent(type=ECS_MOVE_REQUEST, entity=enemy, data={'di':0,'dj':1}))
    total = 0.0
    while total < 0.4:
        w.update(0.1)
        total += 0.1
    hp_store = w.get_component(HP)
    assert hp_store[victim].current == 9, f"Expected victim HP 9 after enemy forward-single beyond destination, got {hp_store[victim].current}"