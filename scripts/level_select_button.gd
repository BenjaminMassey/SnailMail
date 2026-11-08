class_name LevelSelectButton
extends Component


func on_press() -> void:
	# Name will be "LevelX Button". Want to load "LevelX"
	var parts := String(game_object.name).split(" ")
	LevelEnd.level_completed = false
	SceneManager.load_scene(parts[0])
