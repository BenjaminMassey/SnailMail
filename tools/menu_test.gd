extends SceneTree
## Exercises the menu flow: music persistence, level select paging, progress
## saving/unlocking and "Next Level".
##   godot --headless --path . -s tools/menu_test.gd


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://snailmail.save"))
	await _load("LevelSelect")
	_report_music()
	print("level buttons: ", _level_buttons())

	var pages := GameObject.get_component(GameObject.find("Canvas"), PageHandler) as PageHandler
	pages.page_down()
	print("after page_down: ", _level_buttons())
	print("  up visible=", GameObject.find("Up Button") != null, " down visible=", GameObject.find("Down Button") != null)
	pages.page_up()
	print("after page_up: ", _level_buttons())

	# Beat level 1 the way End.gd does, then come back.
	await _load("Level1")
	_report_music()
	var end := GameObject.get_component(GameObject.find("Middle"), End) as End
	for n in get_nodes_in_group("Collectable"):
		n.free()
	end._on_trigger_enter(GameObject.find("Character"))
	await create_timer(2.0).timeout
	print("save file: ", FileAccess.get_file_as_string("user://snailmail.save"))
	var next := GameObject.find("NextLevel Button") as UIButton
	next.pressed.emit()
	await process_frame
	await process_frame
	print("after Next Level: ", current_scene.name)
	await _load("LevelSelect")
	_report_music()
	print("level buttons: ", _level_buttons())
	quit()


func _load(scene_name: String) -> void:
	change_scene_to_file("res://scenes/%s.tscn" % scene_name)
	for i in 5:
		await process_frame


func _report_music() -> void:
	var music := root.get_children().filter(func(n): return n.is_in_group("Music"))
	var playing := false
	for m in music:
		for c in m.get_children():
			if c is AudioStreamPlayer:
				playing = c.playing
	print("[%s] music objects at root: %d, playing: %s" % [current_scene.name, music.size(), playing])


func _level_buttons() -> String:
	var out := []
	for b in GameObject.find("Canvas").get_children():
		if b is UIButton and String(b.name).begins_with("Level") and String(b.name).ends_with(" Button") and b.name != "LevelSelect Button":
			out.append("%s%s" % [String(b.name).trim_suffix(" Button"), "" if b.button_enabled else "(locked)"])
	return ", ".join(out)
