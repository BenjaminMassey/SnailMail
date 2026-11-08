extends SceneTree
## Renders a scene and saves screenshots (needs a window, not --headless).
##   godot --path . -s tools/screenshot.gd -- <Scene> <out_prefix> [options]
## Options: frames=N (default 90), shots=N (one every `frames`), up=1, right=1, auto=1,
##   noui=1 (hide CanvasLayers), size=WxH (window size, UI stretch set to expand).

const PlayTest = preload("res://tools/play_test.gd")

var _args := {}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var user := OS.get_cmdline_user_args()
	var scene_name: String = user[0]
	var out: String = user[1]
	for a in user.slice(2):
		var kv := a.split("=")
		_args[kv[0]] = kv[1]
	if _args.has("size"):
		var wh := (_args["size"] as String).split("x")
		root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
		DisplayServer.window_set_size(Vector2i(int(wh[0]), int(wh[1])))
	change_scene_to_file("res://scenes/%s.tscn" % scene_name)
	await process_frame
	await process_frame
	if _args.get("noui", "0") == "1":
		for n in current_scene.find_children("*", "CanvasLayer", true, false):
			if n.layer >= 0:
				n.visible = false
	if _args.has("cam"):
		# cam=x,y,z,tx,ty,tz in Unity coordinates: an extra camera looking at a target.
		var v := Array((_args["cam"] as String).split(",")).map(func(x): return float(x))
		var cam := Camera3D.new()
		current_scene.add_child(cam)
		cam.global_position = UnityTransform.to_godot(Vector3(v[0], v[1], v[2]))
		cam.look_at(UnityTransform.to_godot(Vector3(v[3], v[4], v[5])))
		cam.make_current()
	var frames := int(_args.get("frames", "90"))
	var shots := int(_args.get("shots", "1"))
	for s in shots:
		for i in frames:
			if _args.get("auto", "0") == "1":
				PlayTest.steer(current_scene)
			else:
				Buttons.up_button = _args.get("up", "0") == "1"
				Buttons.right_button = _args.get("right", "0") == "1"
			await process_frame
		var img := root.get_texture().get_image()
		img.save_png("%s_%d.png" % [out, s])
	quit()
