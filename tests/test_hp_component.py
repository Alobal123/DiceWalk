from ecs.world import World
from ecs.components import HP, Position, RenderCube, DieFaces, DieSide


def test_hp_component_basic():
    world = World()
    # Manually add HP
    eid = world.create_entity()
    world.add_component(eid, HP(current=7, max=10))
    hp_store = world.get_component(HP)
    assert eid in hp_store
    assert hp_store[eid].current == 7
    assert hp_store[eid].max == 10


def test_player_enemy_factory_hp():
    # Ensure factories attach HP
    from ecs.die_factory import create_player_die, create_enemy_die
    world = World()
    p = create_player_die(world, 1, 1)
    e = create_enemy_die(world, 2, 2)
    hp_store = world.get_component(HP)
    assert hp_store[p].current == 10 and hp_store[p].max == 10
    assert hp_store[e].current == 5 and hp_store[e].max == 5
