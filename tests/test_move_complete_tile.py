from game_objects.player_die import PlayerDie
from core.game_event import GameEventType

def test_move_complete_updates_tiles(game):
    # Subscribe game to MOVE_COMPLETE like main
    def on_event(ev):
        if ev.type == GameEventType.MOVE_COMPLETE:
            p = ev.payload or {}
            oi = p['old_i']; oj = p['old_j']; ni = p['new_i']; nj = p['new_j']
            mover = ev.source
            if mover in game.tiles[oi][oj].objects:
                game.tiles[oi][oj].remove(mover)
            if mover not in game.tiles[ni][nj].objects:
                game.tiles[ni][nj].add(mover)
    game.event_listener.subscribe(on_event, [GameEventType.MOVE_COMPLETE])

    die = PlayerDie(2,2)
    die.activate(game)  # subscribe (filters none)
    game.tiles[2][2].add(die)
    die.tumble(game, 1, 0)  # move east
    # Force finish without rendering (avoid arcade window dependency)
    die.anim_elapsed = die.anim_duration
    die.anim_type = 'tumble'
    die._commit_orientation()
    assert die.grid_i == 3 and die.grid_j == 2
    assert die in game.tiles[3][2].objects
    assert die not in game.tiles[2][2].objects
