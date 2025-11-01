from __future__ import annotations
from ecs.world import World
from ecs.components import Position, RenderCube, DieFaces, AIWalker, DieSide, HP, AttackEffect, AttackSet, Patrol, Barrier
from typing import Dict

def create_player_die(world: World, i: int, j: int):
    # Use side keys as face_id so orientation_system permutations keep logical identifiers.
    sides: Dict[str, DieSide] = {
        'top': DieSide('top', (255, 255, 0)),
        'bottom': DieSide('bottom', (128, 128, 128)),
        'north': DieSide('north', (0, 255, 0)),
        'south': DieSide('south', (0, 0, 255)),
        'east': DieSide('east', (255, 0, 0)),
        'west': DieSide('west', (255, 0, 255)),
    }
    eid = world.create_entity()
    world.add_component(eid, Position(i, j))
    world.add_component(eid, RenderCube(scale=0.8))
    world.add_component(eid, DieFaces(sides))
    world.add_component(eid, HP(current=10, max=10))
    # Player: forward-single only on all faces
    player_attacks = {face: [AttackEffect(strength=1, target_type='forward-single')] for face in ['top','north','south','east','west','bottom']}
    world.add_component(eid, AttackSet(effects=player_attacks))
    return eid

def create_enemy_die(world: World, i: int, j: int, ai: bool = True):
    green_shades = [
        (0, 100, 0), (0, 120, 0), (0, 140, 0), (0, 160, 0), (0, 180, 0), (0, 200, 0)
    ]
    sides: Dict[str, DieSide] = {
        'top': DieSide('top', green_shades[0]),
        'bottom': DieSide('bottom', green_shades[1]),
        'north': DieSide('north', green_shades[2]),
        'south': DieSide('south', green_shades[3]),
        'east': DieSide('east', green_shades[4]),
        'west': DieSide('west', green_shades[5]),
    }
    eid = world.create_entity()
    world.add_component(eid, Position(i, j))
    world.add_component(eid, RenderCube(scale=0.6))
    world.add_component(eid, DieFaces(sides))
    world.add_component(eid, HP(current=5, max=5))
    # Enemy: forward, left, right single patterns (all strength 1)
    enemy_attacks = {face: [
        AttackEffect(strength=1, target_type='forward-single'),
        AttackEffect(strength=1, target_type='left-single'),
        AttackEffect(strength=1, target_type='right-single'),
    ] for face in ['top','north','south','east','west','bottom']}
    world.add_component(eid, AttackSet(effects=enemy_attacks))
    # Attach AIWalker so enemy_planning_system can consider this die when planning turns.
    if ai:
        world.add_component(eid, AIWalker())
        world.add_component(eid, Patrol(di=1, dj=0))
    # Treat enemy as a barrier for movement intent resolution (blocks player moving onto it)
    world.add_component(eid, Barrier())
    return eid