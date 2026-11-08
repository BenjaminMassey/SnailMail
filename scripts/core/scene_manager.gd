class_name SceneManager
extends Object
## Unity's SceneManager: scenes are loaded by name from res://scenes.

const SCENE_DIR := "res://scenes/"


static func load_scene(scene_name: String) -> void:
	_tree().change_scene_to_file(SCENE_DIR + scene_name + ".tscn")


static func reload_active_scene() -> void:
	_tree().reload_current_scene()


static func get_active_scene_name() -> String:
	return _tree().current_scene.scene_file_path.get_file().get_basename()


static func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree
