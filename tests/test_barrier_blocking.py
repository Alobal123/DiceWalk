from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, DieSide, TurnState, AIWalker, Barrier, HP
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST


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


def test_player_blocked_by_barrier():
    world = World()
    for sys in [movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system]:
        world.add_system(sys)
    player = create_die(world, 2, 2)
    barrier = world.create_entity()
    world.add_component(barrier, Position(3, 2))
    world.add_component(barrier, Barrier())
    turn_eid = world.create_entity()
    world.add_component(turn_eid, TurnState())
    world.update(0.016)
    turn = next(iter(world.get_component(TurnState).values()))
    # Simulate commit: player intends to move right into barrier tile (3,2)
    world.emit(ECSEvent(type=MOVE_REQUEST, entity=player, data={'di': 1, 'dj': 0}))
    # movement_request_system should cancel due to barrier
    world.update(0.05)
    pos_store = world.get_component(Position)
    assert pos_store[player].i == 2 and pos_store[player].j == 2


def test_enemy_planning_avoids_barrier():
    world = World()
    for sys in [movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system]:
        world.add_system(sys)
    enemy = create_die(world, 1, 1)
    world.add_component(enemy, AIWalker())
    barrier = world.create_entity()
    world.add_component(barrier, Position(2, 1))
    world.add_component(barrier, Barrier())
    turn_eid = world.create_entity()
    world.add_component(turn_eid, TurnState())
    world.update(0.016)
    turn = next(iter(world.get_component(TurnState).values()))
    # Enemy should not plan a move into (2,1)
    forbidden = any(p.get('ti') == 2 and p.get('tj') == 1 for p in turn.planned)
    assert not forbidden, 'Enemy planned move into barrier tile'
