class_name NextLevel
extends Component


func perform() -> void:
	LevelEnd.level_completed = false
	var level_str := SceneManager.get_active_scene_name()
	level_str = level_str.replace("Level", "")
	var level_num := level_str.to_int()
	var level_name := "Level" + str(level_num + 1)
	if level_num < Unlocks.num_levels:
		SceneManager.load_scene(level_name)
	else:
		SceneManager.load_scene("End")
