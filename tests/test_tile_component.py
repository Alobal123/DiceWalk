from dicewalk.main import DiceWalkGame
from ecs.components import Tile, Position

def test_tile_component_count():
    game = DiceWalkGame()
    tile_store = game.world.get_component(Tile)
    pos_store = game.world.get_component(Position)
    # Every tile entity should have Position and Tile but not DieFaces
    assert len(tile_store) == 8*8  # GRID_SIZE^2
    # Verify sample positions exist
    any_tile_positions = {(pos_store[eid].i, pos_store[eid].j) for eid in tile_store.keys() if eid in pos_store}
    assert (0,0) in any_tile_positions and (7,7) in any_tile_positions
