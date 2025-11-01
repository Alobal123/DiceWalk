from ecs.world import World
from ecs.components import Position, Barrier


def test_barrier_creation_and_immutability():
    world = World()
    # Create barrier
    eid = world.create_entity()
    world.add_component(eid, Position(3, 3))
    world.add_component(eid, Barrier())

    pos_store = world.get_component(Position)
    barrier_store = world.get_component(Barrier)

    assert eid in barrier_store
    assert pos_store[eid].i == 3 and pos_store[eid].j == 3

    # Update world with no systems affecting barrier
    world.update(0.1)
    assert pos_store[eid].i == 3 and pos_store[eid].j == 3
