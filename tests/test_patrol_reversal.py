import pytest
from ecs.world import World
from ecs.components import GridGeometry, TurnState, Position, Barrier, Renderable, Patrol, AIWalker
from ecs.die_factory import create_enemy_die
from ecs.systems import enemy_planning_system, movement_request_system, movement_progress_system, orientation_system, turn_advance_system, player_turn_commit_system, attack_effect_system, tile_occupancy_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST

GRID = 6

def make_world():
    w = World()
    geom = GridGeometry(GRID, 10, 20, 0, 0, tuple())
    gid = w.create_entity(); w.add_component(gid, geom)
    turn_eid = w.create_entity(); w.add_component(turn_eid, TurnState())
    # Systems minimal for planning + movement
    w.add_system(enemy_planning_system)
    w.add_system(movement_request_system)
    w.add_system(movement_progress_system)
    w.add_system(orientation_system)
    w.add_system(turn_advance_system)
    w.add_system(attack_effect_system)
    w.add_system(tile_occupancy_system)
    w.add_system(player_turn_commit_system)
    return w

def advance_turn(w):
    # Simulate planning -> execution -> finish
    w.update(0.01)  # planning systems run (enemy plans)
    # Execute planned enemy move(s)
    turn = next(iter(w.get_component(TurnState).values()))
    for plan in turn.planned:
        w.emit(ECSEvent(type=MOVE_REQUEST, entity=plan['entity'], data={'di': plan['di'], 'dj': plan['dj']}))
    turn.phase = 'executing'
    # Run movement to completion
    # Loop until phase returns to planning
    for _ in range(50):
        w.update(0.05)
        turn = next(iter(w.get_component(TurnState).values()))
        if turn.phase == 'planning':
            break

def test_patrol_reverses_on_barrier():
    w = make_world()
    # Enemy facing east with barrier immediately east
    enemy = create_enemy_die(w, 2, 2, ai=True)
    w.add_component(enemy, Renderable(kind='dice', layer=1, z_bias=0))
    # Its Patrol should already be (1,0)
    # Place barrier at (3,2)
    b = w.create_entity(); w.add_component(b, Position(3,2)); w.add_component(b, Barrier())
    # First planning: should reverse and plan west move instead
    w.update(0.01)
    turn = next(iter(w.get_component(TurnState).values()))
    assert len(turn.planned) == 1, "Enemy should have a planned move after planning"
    plan = turn.planned[0]
    assert plan['di'] == -1 and plan['dj'] == 0, f"Expected west move after barrier block, got {plan['di']},{plan['dj']}"
    # Execute move
    advance_turn(w)
    # Next planning: now at (1,2) patrol direction should still be -1, attempt (0,2) if open
    w.update(0.01)
    turn = next(iter(w.get_component(TurnState).values()))
    plan2 = turn.planned[0]
    assert plan2['di'] == -1, "Patrol should continue west after initial reversal"

def test_patrol_reverses_at_grid_edge():
    w = make_world()
    # Enemy near right edge moving east
    enemy = create_enemy_die(w, GRID-2, 3, ai=True)  # at (4,3) in 0..5 grid
    w.add_component(enemy, Renderable(kind='dice', layer=1, z_bias=0))
    # Planning: target (5,3) inside grid (allowed)
    w.update(0.01)
    turn = next(iter(w.get_component(TurnState).values()))
    plan = turn.planned[0]
    assert plan['di'] == 1 and plan['ti'] == GRID-1, "Should move east to edge tile first"
    advance_turn(w)
    # Now at edge (5,3); next planning should reverse to west since (6,3) out of bounds
    w.update(0.01)
    turn = next(iter(w.get_component(TurnState).values()))
    plan2 = turn.planned[0]
    assert plan2['di'] == -1, f"Expected reversal west at edge, got {plan2['di']}"

