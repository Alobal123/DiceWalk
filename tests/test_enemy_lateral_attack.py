from ecs.world import World
from ecs.components import Position, HP
from ecs.die_factory import create_enemy_die, create_player_die
from ecs.systems import movement_request_system, movement_progress_system, orientation_system, attack_effect_system
from ecs.events import Event as ECSEvent, MOVE_REQUEST as ECS_MOVE_REQUEST

def _setup_world():
	w = World()
	w.add_system(movement_request_system)
	w.add_system(movement_progress_system)
	w.add_system(orientation_system)
	w.add_system(attack_effect_system)
	return w

def test_enemy_forward_left_right_damage():
	w = _setup_world()
	# Enemy moves east (di=1) from (3,3) to (4,3).
	enemy = create_enemy_die(w, 3, 3, ai=False)
	# Forward tile beyond destination: (5,3)
	forward_victim = create_player_die(w, 5, 3)
	# Left of movement (moving east => left is south): (4,2)
	left_victim = create_player_die(w, 4, 2)
	# Right of movement (moving east => right is north): (4,4)
	right_victim = create_player_die(w, 4, 4)
	# Emit move
	w.emit(ECSEvent(type=ECS_MOVE_REQUEST, entity=enemy, data={'di':1,'dj':0}))
	total = 0.0
	while total < 0.5:
		w.update(0.1)
		total += 0.1
	hp_store = w.get_component(HP)
	assert hp_store[forward_victim].current == 9, f"Forward victim expected HP 9 got {hp_store[forward_victim].current}"
	assert hp_store[left_victim].current == 9, f"Left victim expected HP 9 got {hp_store[left_victim].current}"
	assert hp_store[right_victim].current == 9, f"Right victim expected HP 9 got {hp_store[right_victim].current}"
