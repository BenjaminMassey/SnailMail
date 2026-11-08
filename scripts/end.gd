class_name End
extends Component
## The house: finishing the level once every letter has been collected.

@export var cheer: AudioStreamPlayer
@export var aww: AudioStreamPlayer

var _delay := 1.5

var _main_section: Control
var _results_section: Control
var _results_obj: Control

var _start_time: float


func start() -> void:
	_main_section = GameObject.find("MainSection")
	_results_section = GameObject.find("ResultsSection")
	_results_obj = GameObject.find("Results Info")

	_main_section.scale = Vector2.ONE
	_results_section.scale = Vector2.ZERO

	_start_time = _realtime_since_startup()


func _on_trigger_enter(other: Node3D) -> void:
	if other.name == "Character":
		var count := _num_collected()
		if count == 0:
			LevelEnd.level_completed = true
			cheer.play()
			MessageHandler.message("You delivered the mail!", _delay)
			_show_results()
		else:
			aww.play()
			var message := "You missed " + str(count) + " letter"
			if count == 1:
				message += "."
			else:
				message += "s."
			MessageHandler.message(message, _delay)
			_restart()


func _restart() -> void:
	GameObject.get_component(GameObject.find("Character"), Move).enabled = false
	await wait_for_seconds(_delay)
	Resetter.reset()


func _show_results() -> void:
	GameObject.get_component(GameObject.find("Character"), Move).enabled = false

	await wait_for_seconds(_delay)

	_main_section.scale = Vector2.ZERO
	_results_section.scale = Vector2.ONE

	var time := _realtime_since_startup() - (_start_time + _delay)
	time = roundf(time * 10.0) / 10.0
	var results := GameObject.get_child(_results_obj, 0) as Label
	results.text = results.text.replace("XXXX", _float_to_string(time))

	var level_str := SceneManager.get_active_scene_name()
	level_str = level_str.replace("Level", "")
	var level_num := level_str.to_int()
	if level_num < Unlocks.num_levels:
		Unlocks.level_done[level_num] = true

	Unlocks.save_data()


func _num_collected() -> int:
	var c := GameObject.find_game_objects_with_tag("Collectable")
	return c.size()


func _realtime_since_startup() -> float:
	return Time.get_ticks_msec() / 1000.0


## Formats like C#'s float.ToString(): whole numbers have no ".0".
func _float_to_string(value: float) -> String:
	if value == floorf(value):
		return str(int(value))
	return str(value)
