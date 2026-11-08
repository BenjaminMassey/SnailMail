extends SceneTree
## Plays a scene with a scripted input program and logs what happens.
##   godot --headless --path . -s tools/play_test.gd -- <Scene> <program>
## program: comma separated steps "<buttons>:<physics frames>", buttons being
## any of u (up), r (right) or - (none). Example: u:120,ur:30,u:200

var _last := {}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var user := OS.get_cmdline_user_args()
	var scene_name: String = user[0]
	change_scene_to_file("res://scenes/%s.tscn" % scene_name)
	await process_frame
	await process_frame
	var scene := current_scene
	var frame := 0
	for step in user[1].split(","):
		var parts := step.split(":")
		for i in int(parts[1]):
			if parts[0] == "auto":
				steer(current_scene)
			else:
				Buttons.up_button = parts[0].contains("u")
				Buttons.right_button = parts[0].contains("r")
			await physics_frame
			frame += 1
			if current_scene != scene:
				print("[%d] scene reloaded/changed -> %s" % [frame, current_scene.name if current_scene else "?"])
				quit()
				return
			_report(frame)
	quit()


func _report(frame: int) -> void:
	var state := {
		"letters": get_nodes_in_group("Collectable").filter(func(n): return not n.is_queued_for_deletion()).size(),
		"pads": current_scene.find_children("*Launch*", "", true, false).filter(
			func(n): return n.get_parent() == current_scene and not n.is_queued_for_deletion()).size(),
		"snail": GameObject.find("Snail") != null,
		"message": _message(),
		"results": _results_shown(),
	}
	for k in state:
		if not _last.has(k) or _last[k] != state[k]:
			var ch := current_scene.get_node_or_null("Character") as Node3D
			print("[%d] %s = %s   (character at %s)" % [frame, k, state[k], ch.global_position if ch else "?"])
	_last = state


## Head for the nearest letter (or the house once none are left) using only the
## forward and right buttons, like a player would.
static func steer(scene: Node) -> void:
	var ch := scene.get_node_or_null("Character") as Node3D
	if ch == null:
		return
	var target: Vector3
	var best := INF
	for n in scene.get_tree().get_nodes_in_group("Collectable"):
		if not n.is_queued_for_deletion() and ch.global_position.distance_to(n.global_position) < best:
			best = ch.global_position.distance_to(n.global_position)
			target = n.global_position
	if best == INF:
		target = (GameObject.find("Middle") as Node3D).global_position
	var local := ch.global_transform.affine_inverse() * target
	var right := local.x
	var forward := -local.z # Unity forward is Godot -Z
	Buttons.right_button = right > 0.3
	Buttons.up_button = forward > 0.3 or not Buttons.right_button


func _message() -> String:
	var text := GameObject.find("Text")
	return text.text if text and text.visible else ""


func _results_shown() -> bool:
	var results := GameObject.find("ResultsSection") as Control
	return results != null and results.scale.x > 0.5
