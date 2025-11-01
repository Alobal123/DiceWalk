import pytest
from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, DieSide, TurnState, HP
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST

# Minimal helper to create a die entity (simplified) for tests

def create_simple_die(world: World, i: int, j: int):
    eid = world.create_entity()
    world.add_component(eid, Position(i, j))
    faces = {
        'top': DieSide('top', (255,0,0)),
        'bottom': DieSide('bottom', (0,255,0)),
        'north': DieSide('north', (0,0,255)),
        'south': DieSide('south', (255,255,0)),
        'east': DieSide('east', (255,0,255)),
        'west': DieSide('west', (0,255,255)),
    }
    world.add_component(eid, DieFaces(faces))
    world.add_component(eid, RenderCube())
    world.add_component(eid, HP(current=3, max=3))
    return eid


def test_turn_cycle_basic():
    world = World()
    # Systems for turn flow (exclude occupancy/AI complexity)
    world.add_system(movement_request_system)
    world.add_system(movement_progress_system)
    world.add_system(orientation_system)
    world.add_system(enemy_planning_system)
    world.add_system(turn_advance_system)

    # Create player and enemy dice
    player = create_simple_die(world, 2, 2)
    enemy = create_simple_die(world, 1, 1)

    # Turn state singleton
    turn_eid = world.create_entity()
    world.add_component(turn_eid, TurnState())

    # Planning phase: enemy_planning_system should fill planned list
    world.update(0.016)
    turn = next(iter(world.get_component(TurnState).values()))
    assert turn.phase == 'planning'
    # We expect at most one planned move for enemy
    assert len(turn.planned) <= 1

    # Commit player move (simulate key press): emit player MOVE_REQUEST and enemy planned MOVE_REQUESTs
    # We'll just enqueue events directly
    world.emit(ECSEvent(type=MOVE_REQUEST, entity=player, data={'di': 1, 'dj': 0}))
    for plan in turn.planned:
        world.emit(ECSEvent(type=MOVE_REQUEST, entity=plan['entity'], data={'di': plan['di'], 'dj': plan['dj']}))
    turn.phase = 'executing'

    # Run updates until moves complete
    steps = 0
    while turn.phase == 'executing' and steps < 200:
        world.update(0.05)
        steps += 1

    assert turn.phase == 'planning', 'Turn did not advance back to planning after execution.'
    # Ensure positions updated for player
    pos_store = world.get_component(Position)
    assert pos_store[player].i == 3

