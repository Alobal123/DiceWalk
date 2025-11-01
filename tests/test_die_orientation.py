from dicewalk.main import DiceWalkGame
from ecs.events import Event as ECSEvent, MOVE_REQUEST
from ecs.components import DieFaces

def _issue_move_and_advance(game: DiceWalkGame, di: int, dj: int):
    game.world.emit(ECSEvent(type=MOVE_REQUEST, entity=game.player_entity, data={'di': di, 'dj': dj}))
    game.world.update(0.36)  # > duration 0.35 to finish

def test_orientation_east():
    game = DiceWalkGame()
    faces_store = game.world.get_component(DieFaces)
    faces = faces_store[game.player_entity].sides
    start_top = faces['top']; start_west = faces['west']
    _issue_move_and_advance(game, 1, 0)
    # After east move top should become previous west
    assert faces_store[game.player_entity].sides['top'] is start_west
    assert faces_store[game.player_entity].sides['top'] is not start_top

def test_orientation_west():
    game = DiceWalkGame()
    faces_store = game.world.get_component(DieFaces)
    faces = faces_store[game.player_entity].sides
    start_top = faces['top']; start_east = faces['east']
    _issue_move_and_advance(game, -1, 0)
    # After west move top should become previous east
    assert faces_store[game.player_entity].sides['top'] is start_east
    assert faces_store[game.player_entity].sides['top'] is not start_top

def test_orientation_north():
    game = DiceWalkGame()
    faces_store = game.world.get_component(DieFaces)
    faces = faces_store[game.player_entity].sides
    start_top = faces['top']; start_south = faces['south']
    _issue_move_and_advance(game, 0, 1)
    assert faces_store[game.player_entity].sides['top'] is start_south
    assert faces_store[game.player_entity].sides['top'] is not start_top

def test_orientation_south():
    game = DiceWalkGame()
    faces_store = game.world.get_component(DieFaces)
    faces = faces_store[game.player_entity].sides
    start_top = faces['top']; start_north = faces['north']
    _issue_move_and_advance(game, 0, -1)
    assert faces_store[game.player_entity].sides['top'] is start_north
    assert faces_store[game.player_entity].sides['top'] is not start_top
