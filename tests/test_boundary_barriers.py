from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, DieSide, TurnState, Barrier
from ecs.systems import movement_request_system, movement_progress_system, orientation_system
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
    return eid


def spawn_boundary_barriers(world: World, grid_size: int):
    # Surround grid with barrier positions outside bounds
    for i in range(grid_size):
        for (oi, oj) in [(-1, i), (grid_size, i)]:
            b = world.create_entity(); world.add_component(b, Position(oi, oj)); world.add_component(b, Barrier())
    for j in range(grid_size):
        for (oi, oj) in [(j, -1), (j, grid_size)]:
            b = world.create_entity(); world.add_component(b, Position(oi, oj)); world.add_component(b, Barrier())


def test_edge_movement_blocked():
    world = World()
    world.add_system(movement_request_system)
    world.add_system(movement_progress_system)
    world.add_system(orientation_system)
    grid_size = 8
    spawn_boundary_barriers(world, grid_size)
    die = create_die(world, 0, 0)
    # Attempt to move left (di=-1) into barrier outside grid
    world.emit(ECSEvent(type=MOVE_REQUEST, entity=die, data={'di': -1, 'dj': 0}))
    world.update(0.05)
    pos_store = world.get_component(Position)
    assert pos_store[die].i == 0 and pos_store[die].j == 0
    # Attempt move up outside grid top boundary (dj=-1 from j=0)
    world.emit(ECSEvent(type=MOVE_REQUEST, entity=die, data={'di': 0, 'dj': -1}))
    world.update(0.05)
    assert pos_store[die].i == 0 and pos_store[die].j == 0
