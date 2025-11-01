from __future__ import annotations
import math
from ecs.world import World
from ecs.components import Position, DieFaces, RenderCube, TumbleAnim, DieSide, HP, Renderable
from ecs.attack_utils import get_attack_targets
import arcade

def draw_cube(geom, faces: DieFaces, pos_i: float, pos_j: float, scale: float):
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
        sx, sy = geom.iso_point(vi, vj)
        sy += vz * geom.tile_height
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


def draw_tumbling_cube(geom, faces_snapshot, active_faces, anim: TumbleAnim):
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
        sx, sy = geom.iso_point(vi, vj)
        sy += vz * geom.tile_height
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


def render_system(world: World):
    """System to render all entities with Renderable + Position.

    Assumes a singleton GridGeometry component is present (as earlier). This is invoked
    explicitly from the window's on_draw (not part of usual update ordering since drawing
    happens once per frame after logic systems).
    """
    # Locate geometry (first / only instance)
    from ecs.components import GridGeometry
    geom_store = world.get_component(GridGeometry)
    if not geom_store:
        return
    geom = next(iter(geom_store.values()))

    pos_store = world.get_component(Position)
    render_store = world.get_component(Renderable)
    cube_store = world.get_component(RenderCube)
    faces_store = world.get_component(DieFaces)
    anim_store = world.get_component(TumbleAnim)
    hp_store = world.get_component(HP)

    draw_list = []  # (depth_key, eid)
    # IMPORTANT PROJECT RULE: Larger (i + j) => FARTHER BACK.
    for eid, rend in render_store.items():
        if not rend.visible:
            continue
        p = pos_store.get(eid)
        if not p:
            continue
        # Depth key: negate (i+j) so larger sums (farther back) appear earlier after ascending sort.
        depth_key = (-(p.i + p.j), p.i, rend.layer, rend.z_bias)
        draw_list.append((depth_key, eid))

    draw_list.sort(key=lambda t: t[0])

    for _, eid in draw_list:
        rend = render_store[eid]
        p = pos_store.get(eid)
        if not p:
            continue
        if rend.kind == 'dice':
            cube = cube_store.get(eid)
            faces = faces_store.get(eid)
            if not (cube and faces):
                continue
            anim = anim_store.get(eid) if anim_store else None
            if anim:
                draw_tumbling_cube(geom, anim.faces_snapshot, faces.sides, anim)
            else:
                draw_cube(geom, faces, p.i, p.j, cube.scale)
            if hp_store and eid in hp_store:
                draw_hp_bar(geom, p.i, p.j, cube.scale, hp_store[eid])
        elif rend.kind == 'barrier':
            draw_barrier_cube(geom, p.i, p.j, 0.8)

    # Planned move highlights remain separate (invoked externally) to avoid transient entity churn.

def draw_planned_move_highlights(geom, world: World):
    """Draw translucent green highlight on tiles with planned enemy moves (planning phase only)."""
    from ecs.components import TurnState
    turn_store = world.get_component(TurnState)
    if not turn_store:
        return
    turn = next(iter(turn_store.values()))
    if turn.phase != 'planning':
        return
    pos_store = world.get_component(Position)
    for plan in turn.planned:
        ti = plan.get('ti'); tj = plan.get('tj')
        if ti is None or tj is None:
            # Fallback compute if missing (legacy plan dict without ti,tj)
            eid = plan.get('entity')
            pos = pos_store.get(eid) if eid in pos_store else None
            if not pos:
                continue
            di = plan.get('di', 0); dj = plan.get('dj', 0)
            ti = pos.i + di; tj = pos.j + dj
        # Build diamond polygon for tile target
        cx, cy = geom.tile_center(ti, tj)
        half_w = geom.tile_width / 2 * 0.5
        half_h = geom.tile_height / 2 * 0.5
        poly = [
            (cx, cy + half_h),
            (cx + half_w, cy),
            (cx, cy - half_h),
            (cx - half_w, cy),
        ]
        arcade.draw_polygon_filled(poly, (0, 200, 0, 80))
        arcade.draw_polygon_outline(poly, (0, 255, 0), 2)

def compute_planned_attack_preview(world: World) -> list[tuple[int,int]]:
    """Compute attack target tiles for planned enemy moves (planning phase).

    For forward-single: uses final destination + direction again (one tile beyond destination).
    Future patterns can branch here without touching renderer logic.
    """
    from ecs.components import TurnState, AttackSet, AttackSide
    turn_store = world.get_component(TurnState)
    if not turn_store:
        return []
    turn = next(iter(turn_store.values()))
    if turn.phase != 'planning':
        return []
    pos_store = world.get_component(Position)
    targets: list[tuple[int,int]] = []
    for plan in turn.planned:
        eid = plan.get('entity')
        if eid is None:
            continue
        di = plan.get('di', 0); dj = plan.get('dj', 0)
        dest_i = plan.get('ti'); dest_j = plan.get('tj')
        if (dest_i is None or dest_j is None) and eid in pos_store:
            p = pos_store[eid]
            dest_i = p.i + di; dest_j = p.j + dj
        if dest_i is None or dest_j is None:
            continue
        # Aggregate all per-effect tiles
        per_effect = get_attack_targets(world, eid, di, dj, dest_i, dest_j)
        for tiles in per_effect.values():
            for tile in tiles:
                targets.append(tile)
    # Deduplicate for preview
    targets = list(dict.fromkeys(targets))
    return targets

def draw_planned_attack_highlights(geom, world: World):
    """Draw red highlights for tiles projected to be attacked after planned moves."""
    attack_tiles = compute_planned_attack_preview(world)
    if not attack_tiles:
        return
    # Exclude barrier tiles from preview drawing
    from ecs.components import Barrier
    barrier_store = world.get_component(Barrier)
    pos_store = world.get_component(Position)
    barrier_positions = set()
    if barrier_store:
        for b_eid in barrier_store.keys():
            b_pos = pos_store.get(b_eid)
            if b_pos:
                barrier_positions.add((b_pos.i, b_pos.j))
    half_w = geom.tile_width / 2 * 0.5
    half_h = geom.tile_height / 2 * 0.5
    for (ti, tj) in attack_tiles:
        if (ti, tj) in barrier_positions:
            continue
        cx, cy = geom.tile_center(ti, tj)
        poly = [
            (cx, cy + half_h),
            (cx + half_w, cy),
            (cx, cy - half_h),
            (cx - half_w, cy),
        ]
        arcade.draw_polygon_outline(poly, (255, 0, 0), 2)


def draw_face_polygon(poly, face: DieSide):
    """Draw a filled face polygon with outline using arcade."""
    color = face.get_color()
    arcade.draw_polygon_filled(poly, color)
    for i in range(len(poly)):
        p1 = poly[i]
        p2 = poly[(i + 1) % len(poly)]
        arcade.draw_line(p1[0], p1[1], p2[0], p2[1], (0, 200, 255), 2)

def draw_barrier_cube(geom, pos_i: int, pos_j: int, scale: float):
    """Draw an immovable barrier as a wireframe cube (white lines only)."""
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
        sx, sy = geom.iso_point(vi, vj)
        sy += vz * geom.tile_height
        screen.append((sx, sy))
    # Edges (pairs of vertex indices)
    edges = [
        (0,1),(1,3),(3,2),(2,0),  # bottom square
        (4,5),(5,7),(7,6),(6,4),  # top square
        (0,4),(1,5),(2,6),(3,7)   # verticals
    ]
    for a,b in edges:
        p1 = screen[a]; p2 = screen[b]
        arcade.draw_line(p1[0], p1[1], p2[0], p2[1], arcade.color.WHITE, 2)

def draw_hp_bar(geom, pos_i: int, pos_j: int, scale: float, hp: HP):
    """Draw a small health bar and text X/Y above the cube center."""
    # Base position: top center of tile
    cx, cy = geom.tile_center(pos_i, pos_j)
    # Vertical offset above cube: proportional to tile_height and scale
    offset_y = geom.tile_height * (0.6 * scale + 0.2)
    bar_width = geom.tile_width * 0.35
    bar_height = geom.tile_height * 0.12
    x_left = cx - bar_width / 2
    x_right = cx + bar_width / 2
    y_bottom = cy + offset_y
    y_top = y_bottom + bar_height
    # Background
    # Background (approximate) using polygon if rectangle helpers unavailable
    bg_poly = [
        (x_left, y_bottom), (x_right, y_bottom), (x_right, y_top), (x_left, y_top)
    ]
    arcade.draw_polygon_filled(bg_poly, (40,40,40,200))
    arcade.draw_polygon_outline(bg_poly, arcade.color.WHITE, 1)
    # Fill proportion
    if hp.max > 0 and hp.current > 0:
        ratio = max(0.0, min(1.0, hp.current / hp.max))
        fill_w = bar_width * ratio
        fill_color = (int(255*(1-ratio)), int(255*ratio), 32)
        fill_poly = [
            (x_left, y_bottom + bar_height*0.35),
            (x_left + fill_w, y_bottom + bar_height*0.35),
            (x_left + fill_w, y_bottom + bar_height*0.65),
            (x_left, y_bottom + bar_height*0.65),
        ]
        arcade.draw_polygon_filled(fill_poly, fill_color)
    # Text HP X/Y just to right of bar
    label = f"{hp.current}/{hp.max}"
    arcade.draw_text(label, x_right + 4, y_bottom - 2, arcade.color.WHITE, 12, anchor_x="left", anchor_y="bottom")
