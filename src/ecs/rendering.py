from __future__ import annotations
import math
from ecs.world import World
from ecs.components import Position, DieFaces, RenderCube, TumbleAnim, DieSide
import arcade

# Isometric projection helper delegating to Level
def iso_point(level, i: float, j: float):
    return level.iso_point(i, j)

def draw_cube(level, faces: DieFaces, pos_i: float, pos_j: float, scale: float):
    """Draw a static cube with its faces."""
    half = 0.5 * scale
    height = scale
    ci0 = pos_i + 0.5
    cj0 = pos_j + 0.5
    verts = [
        [ci0 - half, cj0 - half, 0.0], [ci0 - half, cj0 + half, 0.0],
        [ci0 + half, cj0 - half, 0.0], [ci0 + half, cj0 + half, 0.0],
        [ci0 - half, cj0 - half, height], [ci0 - half, cj0 + half, height],
        [ci0 + half, cj0 - half, height], [ci0 + half, cj0 + half, height],
    ]
    screen = []
    for (vi, vj, vz) in verts:
        sx, sy = iso_point(level, vi, vj)
        sy += vz * level.tile_height
        screen.append((sx, sy))
    face_defs = [
        ([0,1,3,2], 'bottom'), ([4,5,7,6], 'top'),
        ([0,1,5,4], 'west'), ([2,3,7,6], 'east'),
        ([0,2,6,4], 'south'), ([1,3,7,5], 'north'),
    ]
    position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'west': 4, 'top': 5}
    to_draw = []
    for face, logical in face_defs:
        depth = sum(screen[i][1] for i in face) / len(face)
        to_draw.append((depth, face, logical))
    to_draw.sort(key=lambda x: position_priority.get(x[2], 99))
    for _, face, position in to_draw:
        poly = [screen[i] for i in face]
        side = faces.sides.get(position)
        if side:
            draw_face_polygon(poly, side)


def draw_tumbling_cube(level, faces_snapshot, active_faces, anim: TumbleAnim):
    """Draw cube mid-tumble interpolating rotation and slight slide."""
    t = min(anim.elapsed / anim.duration, 1.0)
    angle = (3.14159265 / 2) * t
    si = anim.start_i
    sj = anim.start_j
    di = anim.di
    dj = anim.dj
    half = 0.5 * anim.scale
    height = anim.scale
    ci0 = si + 0.5
    cj0 = sj + 0.5
    # Slight slide second half
    if t > 0.5:
        raw = (t - 0.5) / 0.5
        slide_t = 1 - (1 - raw) * (1 - raw)
        correction = (1.0 - anim.scale) * slide_t
        ci0 += di * correction
        cj0 += dj * correction
    verts = [
        [ci0 - half, cj0 - half, 0.0], [ci0 - half, cj0 + half, 0.0],
        [ci0 + half, cj0 - half, 0.0], [ci0 + half, cj0 + half, 0.0],
        [ci0 - half, cj0 - half, height], [ci0 - half, cj0 + half, height],
        [ci0 + half, cj0 - half, height], [ci0 + half, cj0 + half, height],
    ]
    if di != 0:
        pivot_i = ci0 + half * di
        for v in verts:
            i_off = v[0] - pivot_i
            z = v[2]
            sin_sign = -1 if di == 1 else 1
            v[0] = pivot_i + i_off * math.cos(angle) - z * math.sin(angle) * sin_sign
            v[2] = i_off * math.sin(angle) * sin_sign + z * math.cos(angle)
    elif dj != 0:
        pivot_j = cj0 + half * dj
        for v in verts:
            j_off = v[1] - pivot_j
            z = v[2]
            sin_sign = -1 if dj == 1 else 1
            v[1] = pivot_j + j_off * math.cos(angle) - z * math.sin(angle) * sin_sign
            v[2] = j_off * math.sin(angle) * sin_sign + z * math.cos(angle)
    face_defs = [
        ([0,1,3,2], 'bottom'), ([4,5,7,6], 'top'),
        ([0,1,5,4], 'west'), ([2,3,7,6], 'east'),
        ([0,2,6,4], 'south'), ([1,3,7,5], 'north'),
    ]
    screen = []
    for (vi, vj, vz) in verts:
        sx, sy = iso_point(level, vi, vj)
        sy += vz * level.tile_height
        screen.append((sx, sy))
    faces_to_draw = []
    for face, logical in face_defs:
        depth = sum(screen[i][1] for i in face) / len(face)
        faces_to_draw.append((depth, face, logical))
    # Face draw priority depends on movement direction for correct overlap
    if di == 1 or dj == 1:
        position_priority = {'north': 0, 'east': 1, 'bottom': 2, 'top': 3, 'south': 4, 'west': 5}
    elif di == -1:
        position_priority = {'north': 0, 'bottom': 1, 'east': 2, 'west': 3, 'south': 4, 'top': 5}
    elif dj == -1:
        position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'top': 4, 'west': 5}
    else:
        position_priority = {'bottom': 0, 'east': 1, 'north': 2, 'south': 3, 'west': 4, 'top': 5}
    faces_to_draw.sort(key=lambda x: position_priority.get(x[2], 99))
    active_sides = faces_snapshot if faces_snapshot is not None else active_faces
    for _, face, position in faces_to_draw:
        poly = [screen[i] for i in face]
        side = active_sides.get(position)
        if side:
            draw_face_polygon(poly, side)


def render_ecs(level, world: World):
    pos_store = world.get_component(Position)
    cube_store = world.get_component(RenderCube)
    faces_store = world.get_component(DieFaces)
    anim_store = world.get_component(TumbleAnim)
    entities = [eid for eid in faces_store.keys() if eid in pos_store and eid in cube_store]
    # Painter order: far to near descending (i+j), tie-break by i
    entities.sort(key=lambda eid: (
        -(pos_store[eid].i + pos_store[eid].j),  # negative for descending
        -pos_store[eid].i
    ))
    for eid in entities:
        pos = pos_store.get(eid)
        cube = cube_store.get(eid)
        faces = faces_store.get(eid)
        if not (pos and cube and faces):
            continue
        anim = anim_store.get(eid) if anim_store else None
        if anim:
            # Render tumbling using snapshot (pre-rotation) sides
            draw_tumbling_cube(level, anim.faces_snapshot, faces.sides, anim)
        else:
            # Skip legacy anim state; rely purely on ECS
            draw_cube(level, faces, pos.i, pos.j, cube.scale)


def draw_face_polygon(poly, face: DieSide):
    """Draw a filled face polygon with outline using arcade."""
    color = face.get_color()
    arcade.draw_polygon_filled(poly, color)
    for i in range(len(poly)):
        p1 = poly[i]
        p2 = poly[(i + 1) % len(poly)]
        arcade.draw_line(p1[0], p1[1], p2[0], p2[1], (0, 200, 255), 2)
