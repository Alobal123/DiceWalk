from __future__ import annotations
from typing import List
from ecs.world import World
from ecs.components import Position, GridMove, DieFaces, TumbleAnim, RenderCube, TileOccupancy, AIWalker, Tile
from ecs.events import MOVE_REQUEST, MOVE_STARTED, MOVE_COMPLETE, Event as ECSEvent

# (Removed placeholder position_sync_system & depth_sort; ordering handled in rendering.)


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
        if ev.type == MOVE_COMPLETE and ev.entity in faces_store:
            faces = faces_store[ev.entity].sides
            di = ev.data.get('di', 0)
            dj = ev.data.get('dj', 0)
            if di == 1:
                faces['top'], faces['east'], faces['bottom'], faces['west'] = faces['west'], faces['top'], faces['east'], faces['bottom']
            elif di == -1:
                faces['top'], faces['west'], faces['bottom'], faces['east'] = faces['east'], faces['top'], faces['west'], faces['bottom']
            elif dj == 1:
                faces['top'], faces['north'], faces['bottom'], faces['south'] = faces['south'], faces['top'], faces['north'], faces['bottom']
            elif dj == -1:
                faces['top'], faces['south'], faces['bottom'], faces['north'] = faces['north'], faces['top'], faces['south'], faces['bottom']
            # Orientation applied; remove tumble animation component if present
            anim_store.pop(ev.entity, None)
            # Consumed (not re-added)
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
    """Emit MOVE_REQUEST events for entities with AIWalker component at defined intervals.

    Chooses a random valid direction within bounds (0..7 for now) ignoring collisions.
    """
    pos_store = world.get_component(Position)
    ai_store = world.get_component(AIWalker)
    for eid, ai in ai_store.items():
        ai.timer += dt
        if ai.timer >= ai.interval:
            ai.timer = 0.0
            pos = pos_store.get(eid)
            if not pos:
                continue
            # Candidate directions
            dirs = [(1,0), (-1,0), (0,1), (0,-1)]
            import random
            random.shuffle(dirs)
            for di, dj in dirs:
                ni = pos.i + di; nj = pos.j + dj
                if 0 <= ni < 8 and 0 <= nj < 8:  # TODO: parameterize grid size
                    from ecs.events import Event as ECSEvent, MOVE_REQUEST
                    world.emit(ECSEvent(type=MOVE_REQUEST, entity=eid, data={'di': di, 'dj': dj}))
                    break
