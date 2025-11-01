from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, DieSide, TurnState, Barrier, AIWalker, HP
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST

# We test logic indirectly by replicating main's commit rules in a helper.

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


def test_turn_not_advanced_when_player_blocked():
    world = World()
    for sys in [movement_request_system, movement_progress_system, orientation_system, enemy_planning_system, turn_advance_system]:
        world.add_system(sys)
    player = create_die(world, 2, 2)
    enemy = create_die(world, 3, 2)
    world.add_component(enemy, AIWalker())
    # Barrier directly to the right of player (3,2)
    b = world.create_entity(); world.add_component(b, Position(3,2)); world.add_component(b, Barrier())
    turn_eid = world.create_entity(); world.add_component(turn_eid, TurnState())
    world.update(0.016)
    turn = next(iter(world.get_component(TurnState).values()))
    assert turn.phase == 'planning'
    # Player attempts to move right into barrier; mimic main logic: should abort turn
    # Determine enemy planned moves first (already done in update)
    p_pos = world.get_component(Position)[player]
    intended_ti = p_pos.i + 1; intended_tj = p_pos.j
    enemy_targets = {(plan.get('ti'), plan.get('tj')) for plan in turn.planned if plan.get('ti') is not None}
    barrier_store = world.get_component(Barrier)
    barrier_positions = world.get_component(Position)
    barrier_blocked = False
    for b_eid in barrier_store.keys():
        b_pos = barrier_positions.get(b_eid)
        if b_pos and b_pos.i == intended_ti and b_pos.j == intended_tj:
            barrier_blocked = True
            break
    player_cancelled = (intended_ti, intended_tj) in enemy_targets or barrier_blocked
    if player_cancelled:
        # Abort (no events emitted, phase stays planning)
        pass
    else:
        world.emit(ECSEvent(type=MOVE_REQUEST, entity=player, data={'di':1,'dj':0}))
        for plan in turn.planned:
            world.emit(ECSEvent(type=MOVE_REQUEST, entity=plan['entity'], data={'di': plan['di'], 'dj': plan['dj']}))
        turn.phase = 'executing'
    # Advance simulation a bit
    world.update(0.05)
    assert turn.phase == 'planning', 'Turn phase advanced despite player being blocked by barrier.'
    # Ensure player and enemy positions unchanged
    pos_store = world.get_component(Position)
    assert pos_store[player].i == 2 and pos_store[player].j == 2
    assert pos_store[enemy].i == 3 and pos_store[enemy].j == 2
