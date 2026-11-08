class_name CorrectRadius
extends Component
## Snaps an object onto the planet surface (offset above it) and, for launch
## pads, turns it to face along the surface.

@export var offset := 1.0


func start() -> void:
	var body := game_object as Node3D
	var world := GameObject.find("World") as Node3D
	var world_radius := world.scale.y / 2.0

	var orig_rot := body.quaternion

	UnityTransform.look_at(body, world.global_position)

	var p := body.global_position

	var r := p.length()

	var dist := (r - world_radius) - offset
	UnityTransform.translate(body, UnityTransform.FORWARD * dist)

	body.quaternion = orig_rot

	if body.name.contains("Jump"):
		_correct(Vector3(-35.0, -90.0, 90.0))
	elif body.name.contains("Launch"):
		_correct(Vector3(0.0, -90.0, 0.0))


func _correct(rot_amount: Vector3) -> void:
	var body := game_object as Node3D
	var world := GameObject.find("World") as Node3D

	UnityTransform.look_at(body, world.global_position)

	UnityTransform.rotate(body, rot_amount)
