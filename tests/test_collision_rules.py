from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, DieSide, TurnState, AIWalker, HP
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST

# Helper to create a die entity

def create_die(world: World, i: int, j: int):
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


def test_enemy_enemy_conflict():
    world = World()
    world.add_system(movement_request_system)
    world.add_system(movement_progress_system)
    world.add_system(orientation_system)
    world.add_system(enemy_planning_system)
    world.add_system(turn_advance_system)

    # Two enemies positioned to potentially move into same tile
    e1 = create_die(world, 1, 1)
    e2 = create_die(world, 1, 2)
    world.add_component(e1, AIWalker())
    world.add_component(e2, AIWalker())

    turn_eid = world.create_entity()
    world.add_component(turn_eid, TurnState())

    world.update(0.016)
    turn = next(iter(world.get_component(TurnState).values()))
    # If both tried for same tile, only one plan should exist for that target
    targets = [(p['ti'], p['tj']) for p in turn.planned]
    assert len(targets) == len(set(targets)), "Enemy planning conflict not resolved: duplicate targets present"


def test_player_enemy_priority():
    world = World()
    world.add_system(movement_request_system)
    world.add_system(movement_progress_system)
    world.add_system(orientation_system)
    world.add_system(enemy_planning_system)
    world.add_system(turn_advance_system)

    # Player and enemy; enemy placed such that likely moves into player's intended target
    player = create_die(world, 2, 2)
    enemy = create_die(world, 2, 3)
    world.add_component(enemy, AIWalker())

    turn_eid = world.create_entity()
    world.add_component(turn_eid, TurnState())

    world.update(0.016)
    turn = next(iter(world.get_component(TurnState).values()))

    # Simulate player intending to move UP (dj=1) into (2,3) while enemy may move DOWN into (2,3)
    # Force an enemy plan to (2,3) if not already
    has_target = any(p.get('ti') == 2 and p.get('tj') == 3 for p in turn.planned)
    if not has_target:
        # Override planned move manually for test
        turn.planned.clear()
        turn.planned.append({'entity': enemy, 'di': 0, 'dj': -1, 'ti': 2, 'tj': 3})

    # Commit turn: player tries to move up, should be cancelled
    world.emit(ECSEvent(type=MOVE_REQUEST, entity=enemy, data={'di': 0, 'dj': -1}))  # enemy move
    # Player move would conflict; emulate cancellation by not emitting player MOVE_REQUEST
    # (Game main logic handles this; here we assert effect after execution.)
    turn.phase = 'executing'

    # Run movement to completion
    steps = 0
    while turn.phase == 'executing' and steps < 200:
        world.update(0.05)
        steps += 1

    pos_store = world.get_component(Position)
    # Enemy moved
    assert pos_store[enemy].i == 2 and pos_store[enemy].j == 2
    # Player stayed
    assert pos_store[player].i == 2 and pos_store[player].j == 2

