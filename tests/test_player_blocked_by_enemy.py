import pytest
from ecs.world import World
from ecs.components import Position, GridGeometry, TurnState, Renderable
from ecs.die_factory import create_player_die, create_enemy_die
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, tile_occupancy_system, attack_effect_system, enemy_planning_system, turn_advance_system, player_turn_commit_system
from ecs.events import Event as ECSEvent, PLAYER_MOVE_INTENT

# Grid helper
GRID_SIZE = 8

def setup_world():
    world = World()
    # Minimal geometry
    geom = GridGeometry(GRID_SIZE, 10, 20, 0, 0, tuple())
    gid = world.create_entity(); world.add_component(gid, geom)
    # Systems
    world.add_system(movement_request_system)
    world.add_system(movement_progress_system)
    world.add_system(orientation_system)
    world.add_system(attack_effect_system)
    world.add_system(tile_occupancy_system)
    world.add_system(enemy_planning_system)
    world.add_system(turn_advance_system)
    world.add_system(player_turn_commit_system)
    # Turn state
    turn_eid = world.create_entity(); world.add_component(turn_eid, TurnState())
    # Entities
    enemy = create_enemy_die(world, 3, 3, ai=True)
    world.add_component(enemy, Renderable(kind='dice', layer=1, z_bias=0))
    player = create_player_die(world, 2, 3)
    world.add_component(player, Renderable(kind='dice', layer=1, z_bias=0))
    return world, player, enemy


def test_player_cannot_move_onto_enemy_tile():
    world, player, enemy = setup_world()
    # Planning phase: enemy_planning_system may plan move; regardless player tries to move east onto enemy current tile (3,3)
    world.update(0.01)  # Run systems (planning occurs)
    # Emit intent to move east (di=1)
    world.emit(ECSEvent(type=PLAYER_MOVE_INTENT, entity=player, data={'di':1,'dj':0}))
    world.update(0.01)
    # Player should remain at (2,3)
    pos_store = world.get_component(Position)
    p_pos = pos_store.get(player)
    assert p_pos is not None, "Player position component missing"
    assert p_pos.i == 2 and p_pos.j == 3, "Player moved onto enemy tile but should have been blocked"

