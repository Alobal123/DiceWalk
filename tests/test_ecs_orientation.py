from dicewalk.main import DiceWalkGame
from ecs.events import Event as ECSEvent, MOVE_REQUEST, MOVE_COMPLETE
from ecs.components import DieFaces, Position

def test_orientation_faces_rotate():
    game = DiceWalkGame()
    # Capture initial top/east/north faces
    faces_store = game.world.get_component(DieFaces)
    player_faces = faces_store[game.player_entity].sides
    start_top = player_faces['top']
    start_west = player_faces['west']
    start_south = player_faces['south']

    # Issue east move
    game.world.emit(ECSEvent(type=MOVE_REQUEST, entity=game.player_entity, data={'di':1,'dj':0}))
    # Advance enough time to complete (duration 0.35)
    game.world.update(0.36)
    faces_after_east = faces_store[game.player_entity].sides
    # After east move: top becomes previous west
    assert faces_after_east['top'] is start_west
    # East move mapping: top<-west, east<-top, bottom<-east, west<-bottom (from original logic)

    # Issue north move
    game.world.emit(ECSEvent(type=MOVE_REQUEST, entity=game.player_entity, data={'di':0,'dj':1}))
    game.world.update(0.36)
    faces_after_north = faces_store[game.player_entity].sides
    # After north move: top becomes previous south (original south)
    assert faces_after_north['top'] is start_south

    # Ensure position advanced accordingly
    pos_store = game.world.get_component(Position)
    pos = pos_store[game.player_entity]
    # Started at (2,2) per main -> after east (3,2) -> after north (3,3)
    assert (pos.i, pos.j) == (3,3)
