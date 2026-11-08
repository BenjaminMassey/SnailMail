extends SceneTree
## Loads each scene, runs it briefly, and reports which ones loaded.
##   godot --headless --path . -s tools/smoke_test.gd [-- Scene1 Scene2 ...]

const SCENES := ["LevelSelect", "Controls", "Credits", "End",
	"Level1", "Level2", "Level3", "Level4", "Level5", "Level6", "Level7", "Level8", "Level9", "Level10",
	"Level11", "Level12", "Level13", "Level14", "Level15", "Level16", "Level17", "Level18", "Level19", "Level20"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var scenes: Array = Array(OS.get_cmdline_user_args())
	if scenes.is_empty():
		scenes = SCENES
	for scene_name in scenes:
		print("=== ", scene_name)
		var err := change_scene_to_file("res://scenes/%s.tscn" % scene_name)
		if err != OK:
			print("  FAILED TO LOAD: ", error_string(err))
			continue
		for i in 120:
			await physics_frame
		print("  ok, nodes: ", current_scene.get_child_count() if current_scene else -1)
	quit()
