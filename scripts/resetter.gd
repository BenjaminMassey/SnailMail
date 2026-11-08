class_name Resetter
extends Object


static func reset() -> void:
	Buttons.up_button = false
	Buttons.right_button = false
	SceneManager.reload_active_scene()
