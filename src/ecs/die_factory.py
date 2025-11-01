from __future__ import annotations
from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, AIWalker, DieSide
from typing import Dict

def create_player_die(world: World, i: int, j: int):
    sides: Dict[str, DieSide] = {
        'top': DieSide('yellow', (255, 255, 0)),
        'bottom': DieSide('gray', (128, 128, 128)),
        'north': DieSide('green', (0, 255, 0)),
        'south': DieSide('blue', (0, 0, 255)),
        'east': DieSide('red', (255, 0, 0)),
        'west': DieSide('magenta', (255, 0, 255)),
    }
    eid = world.create_entity()
    world.add_component(eid, Position(i, j))
    world.add_component(eid, RenderCube(scale=0.8))
    world.add_component(eid, DieFaces(sides))
    return eid

def create_enemy_die(world: World, i: int, j: int, ai: bool = True):
    green_shades = [
        (0, 100, 0), (0, 120, 0), (0, 140, 0), (0, 160, 0), (0, 180, 0), (0, 200, 0)
    ]
    sides: Dict[str, DieSide] = {
        'top': DieSide('green1', green_shades[0]),
        'bottom': DieSide('green2', green_shades[1]),
        'north': DieSide('green3', green_shades[2]),
        'south': DieSide('green4', green_shades[3]),
        'east': DieSide('green5', green_shades[4]),
        'west': DieSide('green6', green_shades[5]),
    }
    eid = world.create_entity()
    world.add_component(eid, Position(i, j))
    world.add_component(eid, RenderCube(scale=0.6))
    world.add_component(eid, DieFaces(sides))
    if ai:
        world.add_component(eid, AIWalker())
    return eid