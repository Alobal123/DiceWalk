from __future__ import annotations
from typing import List, Tuple, Dict
from ecs.world import World
from ecs.components import Position, DieFaces, AttackSet, AttackSide


def get_attack_effects(world: World, eid: int):
    """Resolve all active AttackEffects for an entity based on its current top face.

    Returns a list (possibly empty). AttackSet may hold multiple effects per face.
    """
    faces_store = world.get_component(DieFaces)
    if not faces_store or eid not in faces_store:
        return []
    faces = faces_store[eid]
    top = faces.sides.get('top')
    if not top:
        return []
    attack_set_store = world.get_component(AttackSet)
    if attack_set_store and eid in attack_set_store:
        eff_list = attack_set_store[eid].effects.get(top.face_id, [])
        return list(eff_list)
    attack_side_store = world.get_component(AttackSide)
    if attack_side_store and eid in attack_side_store:
        atk_side = attack_side_store[eid]
        if atk_side.face_id == top.face_id:
            return [atk_side.effect]
    return []


def get_attack_targets(world: World, eid: int, di: int, dj: int, post_move_i: int, post_move_j: int) -> Dict[str, List[Tuple[int,int]]]:
    """Compute per-effect target tiles for active attacks.

    Returns dict mapping effect.target_type -> list[(i,j)] (no dedup across keys).
    """
    result: Dict[str, List[Tuple[int,int]]] = {}
    if di == 0 and dj == 0:
        return result
    for effect in get_attack_effects(world, eid):
        ttype = effect.target_type
        tiles: List[Tuple[int,int]] = []
        if ttype == 'forward-single':
            tiles.append((post_move_i + di, post_move_j + dj))
        elif ttype == 'left-single':
            if di != 0:
                perp = (0, -1) if di == 1 else (0, 1)
            else:
                perp = (1, 0) if dj == 1 else (-1, 0)
            tiles.append((post_move_i + perp[0], post_move_j + perp[1]))
        elif ttype == 'right-single':
            if di != 0:
                perp = (0, 1) if di == 1 else (0, -1)
            else:
                perp = (-1, 0) if dj == 1 else (1, 0)
            tiles.append((post_move_i + perp[0], post_move_j + perp[1]))
        if tiles:
            result.setdefault(ttype, []).extend(tiles)
    return result
