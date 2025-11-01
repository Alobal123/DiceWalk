from __future__ import annotations
from typing import List
from ecs.world import World
from ecs.components import Position, GridMove, DieFaces, TumbleAnim, RenderCube, TileOccupancy, AIWalker, Tile, TurnState, AttackSide, AttackEffect, HP, AttackSet, Patrol
from ecs.components import Barrier
from ecs.events import MOVE_REQUEST, MOVE_STARTED, MOVE_COMPLETE, PLAYER_MOVE_INTENT, Event as ECSEvent
from ecs.attack_utils import get_attack_targets, get_attack_effects



def movement_request_system(world: World, dt: float):
    """Consume MOVE_REQUEST events and create GridMove components when free.

    Assumes no collision / bounds for now (handled later)."""
    pos_store = world.get_component(Position)
    move_store = world.get_component(GridMove)
    anim_store = world.get_component(TumbleAnim)
    faces_store = world.get_component(DieFaces)
    cube_store = world.get_component(RenderCube)
    new_events: List[ECSEvent] = []
    remaining_events = []
    for ev in world.event_queue:
        if ev.type == MOVE_REQUEST and ev.entity is not None:
            # Ignore if already moving
            if ev.entity in move_store or ev.entity in anim_store:
                continue
            pos = pos_store.get(ev.entity)
            if not pos:
                continue
            di = ev.data.get('di'); dj = ev.data.get('dj')
            if di in (None, ) or dj in (None, ):
                continue
            # Barrier collision: if target tile has a barrier, cancel move
            barrier_store = world.get_component(Barrier)
            blocked = False
            if barrier_store:
                target_i = pos.i + di
                target_j = pos.j + dj
                # Iterate barriers to see if any at target position
                barrier_positions = world.get_component(Position)
                for b_eid in barrier_store.keys():
                    b_pos = barrier_positions.get(b_eid)
                    if b_pos and b_pos.i == target_i and b_pos.j == target_j:
                        blocked = True
                        break
            if blocked:
                continue  # Skip creating movement for blocked target
            move_store[ev.entity] = GridMove(start_i=pos.i, start_j=pos.j, di=di, dj=dj)
            # Create tumble animation component (render interpolation & orientation deferral)
            faces = faces_store.get(ev.entity)
            cube = cube_store.get(ev.entity)
            anim_store[ev.entity] = TumbleAnim(
                start_i=pos.i,
                start_j=pos.j,
                di=di,
                dj=dj,
                duration=move_store[ev.entity].duration,
                scale=cube.scale if cube else 0.8,
                faces_snapshot=dict(faces.sides) if faces else None,
            )
            new_events.append(ECSEvent(type=MOVE_STARTED, entity=ev.entity, data={'from_i': pos.i, 'from_j': pos.j, 'di': di, 'dj': dj}))
        else:
            remaining_events.append(ev)
    world.event_queue = remaining_events
    for ne in new_events:
        world.emit(ne)


def movement_progress_system(world: World, dt: float):
    """Advance GridMove animations and finalize into Position, emitting MOVE_COMPLETE with direction."""
    pos_store = world.get_component(Position)
    move_store = world.get_component(GridMove)
    anim_store = world.get_component(TumbleAnim)
    completed: List[int] = []
    for eid, move in list(move_store.items()):
        move.elapsed += dt
        # Mirror elapsed into animation component if present
        anim = anim_store.get(eid)
        if anim:
            anim.elapsed = move.elapsed
        if move.elapsed >= move.duration:
            # Complete move
            pos = pos_store.get(eid)
            if pos:
                pos.i = move.start_i + move.di
                pos.j = move.start_j + move.dj
            completed.append(eid)
            world.emit(ECSEvent(type=MOVE_COMPLETE, entity=eid, data={'i': pos.i if pos else None, 'j': pos.j if pos else None, 'di': move.di, 'dj': move.dj}))
    for eid in completed:
        move_store.pop(eid, None)
        # Keep animation component until orientation_system consumes MOVE_COMPLETE; then remove in orientation_system


def orientation_system(world: World, dt: float):
    """Rotate DieFaces components after movement completes (face permutation)."""
    faces_store = world.get_component(DieFaces)
    anim_store = world.get_component(TumbleAnim)
    remaining = []
    deferred: List[ECSEvent] = []
    for ev in world.event_queue:
        if ev.type == MOVE_COMPLETE and ev.entity in faces_store and not ev.data.get('orientation_done'):
            faces = faces_store[ev.entity].sides
            di = ev.data.get('di', 0)
            dj = ev.data.get('dj', 0)
            if di == 1:
                faces['top'], faces['east'], faces['bottom'], faces['west'] = faces['west'], faces['top'], faces['east'], faces['bottom']
            elif di == -1:
                faces['top'], faces['west'], faces['bottom'], faces['east'] = faces['east'], faces['top'], faces['west'], faces['bottom']
            elif dj == 1:  # moving north (test expectation: top becomes previous south)
                faces['top'], faces['north'], faces['bottom'], faces['south'] = faces['south'], faces['top'], faces['north'], faces['bottom']
            elif dj == -1:  # moving south (test expectation: top becomes previous north)
                faces['top'], faces['south'], faces['bottom'], faces['north'] = faces['north'], faces['top'], faces['south'], faces['bottom']
            # Orientation applied; remove tumble animation component if present
            anim_store.pop(ev.entity, None)
            # Tag event so it won't rotate again
            ev.data['orientation_done'] = True
            remaining.append(ev)
        else:
            remaining.append(ev)
    # Re-queue deferred events to try again next frame
    world.event_queue = remaining + deferred  # deferred currently always empty


def tile_occupancy_system(world: World, dt: float):
    """Maintain TileOccupancy component based on MOVE_STARTED/MOVE_COMPLETE events.

    On MOVE_STARTED: temporarily keep entity at start tile (no change).
    On MOVE_COMPLETE: move entity to new tile.
    Initializes occupancy from current Position if component empty.
    """
    pos_store = world.get_component(Position)
    occ_store = world.get_component(TileOccupancy)
    if not occ_store:
        return
    # Single global occupancy component assumed (entity id 0 special) or first entry
    occ_entity = next(iter(occ_store.keys()), None)
    if occ_entity is None:
        # Create a singleton occupancy component attached to a pseudo-entity
        occ_entity = world.create_entity()
        occ_store[occ_entity] = TileOccupancy()
    occ = occ_store[occ_entity]
    # Initialize occupants if empty
    if not occ.occupants:
        faces_store = world.get_component(DieFaces)
        for eid, pos in pos_store.items():
            if eid in faces_store:  # only track dice entities
                occ.occupants.setdefault((pos.i, pos.j), []).append(eid)
    faces_store = world.get_component(DieFaces)
    remaining = []
    for ev in world.event_queue:
        if ev.type == MOVE_COMPLETE and ev.entity in pos_store and ev.entity in faces_store:
            # Remove from all tiles first (entity should occupy only one)
            for k, lst in list(occ.occupants.items()):
                if ev.entity in lst:
                    lst.remove(ev.entity)
                    if not lst:
                        occ.occupants.pop(k, None)
            pos = pos_store.get(ev.entity)
            if pos:
                occ.occupants.setdefault((pos.i, pos.j), []).append(ev.entity)
            # Consume event for occupancy (leave for orientation system already processed earlier)
            remaining.append(ev)
        else:
            remaining.append(ev)
    world.event_queue = remaining


def ai_walker_system(world: World, dt: float):
    """Deprecated random walker (left in place for compatibility but does nothing)."""
    return


def enemy_planning_system(world: World, dt: float):
    """Deterministic planning using Patrol components.

    For each enemy (AIWalker + Patrol) during planning phase:
    - Attempt to move in its patrol (di,dj) direction.
    - If blocked by barrier or bounds, reverse (di,dj) on the Patrol component and attempt once.
    - If still blocked, no move is planned this turn.
    - Only plan if TurnState.planned is empty (one planning pass per phase).
    """
    turn_store = world.get_component(TurnState)
    if not turn_store:
        return
    turn = next(iter(turn_store.values()))
    if turn.phase != 'planning' or turn.planned:
        return
    pos_store = world.get_component(Position)
    ai_store = world.get_component(AIWalker)
    patrol_store = world.get_component(Patrol)
    barrier_store = world.get_component(Barrier)
    barrier_positions = world.get_component(Position)
    GRID_LIMIT = 8
    for eid in ai_store.keys():
        if eid not in patrol_store:
            continue
        pos = pos_store.get(eid)
        patrol = patrol_store.get(eid)
        if not pos or not patrol:
            continue
        attempts = 0
        planned = None
        while attempts < 2:
            di, dj = patrol.di, patrol.dj
            ti = pos.i + di; tj = pos.j + dj
            blocked = False
            # Bounds
            if not (0 <= ti < GRID_LIMIT and 0 <= tj < GRID_LIMIT):
                blocked = True
            # Barriers
            if not blocked and barrier_store:
                for b_eid in barrier_store.keys():
                    b_pos = barrier_positions.get(b_eid)
                    if b_pos and b_pos.i == ti and b_pos.j == tj:
                        blocked = True
                        break
            if blocked:
                # Reverse direction and try once more
                patrol.di *= -1
                patrol.dj *= -1
                attempts += 1
                continue
            planned = {'entity': eid, 'di': di, 'dj': dj, 'ti': ti, 'tj': tj}
            break
        if planned:
            turn.planned.append(planned)


def turn_advance_system(world: World, dt: float):
    """When executing phase and all moves resolved, return to planning phase and clear planned list."""
    turn_store = world.get_component(TurnState)
    if not turn_store:
        return
    turn = next(iter(turn_store.values()))
    if turn.phase != 'executing':
        return
    move_store = world.get_component(GridMove)
    anim_store = world.get_component(TumbleAnim)
    # If no pending movement / animations, advance turn
    if not move_store and not anim_store:
        turn.phase = 'planning'
        turn.planned.clear()
        turn.planning_elapsed = 0.0


def player_turn_commit_system(world: World, dt: float):
    """Consume PLAYER_MOVE_INTENT during planning phase and commit player + enemy moves.

    Mirrors logic previously embedded in window.on_key_press.
    Rules:
    - If target tile is barrier or claimed by enemy planned move, cancel (stay in planning).
    - Otherwise emit MOVE_REQUEST for player and all enemy planned moves; set phase to executing.
    """
    turn_store = world.get_component(TurnState)
    if not turn_store:
        return
    turn = next(iter(turn_store.values()))
    if turn.phase != 'planning':
        return
    # Accumulate planning elapsed time for preview visibility gating
    turn.planning_elapsed += dt
    # Disallow intents while previous execution cleanup (shouldn't happen since phase != planning) or if any moves/animations lingering
    move_store = world.get_component(GridMove)
    anim_store = world.get_component(TumbleAnim)
    if move_store or anim_store:
        return
    pos_store = world.get_component(Position)
    barrier_store = world.get_component(Barrier)
    remaining = []
    MIN_PREVIEW_TIME = 0.05  # require at least 50ms in planning so previews can render
    for ev in world.event_queue:
        if ev.type == PLAYER_MOVE_INTENT and ev.entity is not None:
            # Require at least enemy planning pass (if enemies exist) before accepting input
            ai_store = world.get_component(AIWalker)
            if ai_store and not turn.planned:
                # Enemy not yet planned this frame; defer intent by keeping event in queue for next frame
                remaining.append(ev)
                continue
            # Ensure previews have been visible long enough this planning phase
            if turn.planning_elapsed < MIN_PREVIEW_TIME:
                remaining.append(ev)
                continue
            di = ev.data.get('di', 0); dj = ev.data.get('dj', 0)
            p_pos = pos_store.get(ev.entity)
            if not p_pos:
                continue
            intended_ti = p_pos.i + di
            intended_tj = p_pos.j + dj
            enemy_targets = {(plan.get('ti'), plan.get('tj')) for plan in turn.planned if plan.get('ti') is not None}
            # Barrier check
            blocked = False
            if barrier_store:
                barrier_positions = world.get_component(Position)
                for b_eid in barrier_store.keys():
                    b_pos = barrier_positions.get(b_eid)
                    if b_pos and b_pos.i == intended_ti and b_pos.j == intended_tj:
                        blocked = True
                        break
            player_cancelled = blocked or (intended_ti, intended_tj) in enemy_targets
            if player_cancelled:
                # Stay in planning; do not emit moves
                continue
            # Emit player move
            world.emit(ECSEvent(type=MOVE_REQUEST, entity=ev.entity, data={'di': di, 'dj': dj}))
            # Emit enemy planned moves
            for plan in turn.planned:
                world.emit(ECSEvent(type=MOVE_REQUEST, entity=plan['entity'], data={'di': plan['di'], 'dj': plan['dj']}))
            turn.phase = 'executing'
        else:
            remaining.append(ev)
    world.event_queue = remaining


def attack_effect_system(world: World, dt: float):
    """Trigger attack effects when a die finishes movement based on its top face.

    Supports both legacy single-face AttackSide and new per-face AttackSet.

    Workflow:
    - Listen for MOVE_COMPLETE events.
    - After orientation_system has updated DieFaces, read the entity's 'top' face id.
    - Resolve an AttackEffect either from AttackSet.effects[top_id] or an AttackSide whose face_id == top_id.
    - Apply effect targeting (currently only 'forward-single').
    - (Future) Emit damage events / visual feedback.
    """
    faces_store = world.get_component(DieFaces)
    pos_store = world.get_component(Position)
    hp_store = world.get_component(HP)
    attack_side_store = world.get_component(AttackSide)
    attack_set_store = world.get_component(AttackSet)
    remaining = []
    for ev in world.event_queue:
        if ev.type == MOVE_COMPLETE and ev.entity in faces_store and ev.entity in pos_store:
            top_face = faces_store[ev.entity].sides.get('top')
            if not top_face:
                # Consume if orientation already done to avoid perpetual event retention
                if ev.data.get('orientation_done'):
                    # Drop event
                    continue
                remaining.append(ev)
                continue
            # Resolve all effects via utility (supports multiple patterns per face)
            effects = get_attack_effects(world, ev.entity)
            if not effects:
                if ev.data.get('orientation_done'):
                    continue
                remaining.append(ev)
                continue
            # Multi-effect handling (each pattern applied once)
            di = ev.data.get('di', 0)
            dj = ev.data.get('dj', 0)
            pos = pos_store.get(ev.entity)
            if not pos:
                if ev.data.get('orientation_done'):
                    continue
                remaining.append(ev)
                continue
            targets_map = get_attack_targets(world, ev.entity, di, dj, pos.i, pos.j)
            for eff in effects:
                tiles = targets_map.get(eff.target_type, [])
                for (ti, tj) in tiles:
                    for target_eid, tpos in pos_store.items():
                        if target_eid == ev.entity:
                            continue
                        if tpos.i == ti and tpos.j == tj and target_eid in hp_store:
                            hp_comp = hp_store[target_eid]
                            hp_comp.current = max(0, hp_comp.current - eff.strength)
            # Consume MOVE_COMPLETE entirely after attack processed
            continue
        else:
            remaining.append(ev)
    world.event_queue = remaining
