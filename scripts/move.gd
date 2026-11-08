class_name Move
extends Component
## Moves the snail forward/right along the planet surface and pulls it down.

@export var move_speed := 5.0
@export var grav_speed := 0.15

@export var world: Node3D
@export var my_bottom: Node3D
@export var snail_obj: Node3D

var gravity_on := false
var move_on := false

var _my_height: float
var _world_height: float
var _facing_up: bool


func start() -> void:
	_my_height = (game_object as Node3D).scale.y / 2.0
	_world_height = world.scale.y / 2.0

	_facing_up = true

	gravity_on = true
	move_on = true


func _process(delta: float) -> void:
	_handle_move(delta)
	_gravity(delta)


func _handle_move(delta: float) -> void:
	if not move_on:
		return
	var hor_inp := 0.0
	var ver_inp := 0.0
	if Buttons.right_button:
		hor_inp = 1.0
	if Buttons.up_button:
		ver_inp = 1.0

	if hor_inp + ver_inp == 2.0:
		hor_inp *= 0.66
		ver_inp *= 0.66

	var move := Vector3(hor_inp, 0.0, ver_inp)

	move *= delta * move_speed

	UnityTransform.translate(game_object, move)

	if hor_inp == 1.0 and _facing_up:
		UnityTransform.rotate(snail_obj, Vector3(0.0, 0.0, 90.0))
		_facing_up = false
	elif hor_inp == 0.0 and not _facing_up:
		UnityTransform.rotate(snail_obj, Vector3(0.0, 0.0, -90.0))
		_facing_up = true


func _gravity(delta: float) -> void:
	var body := game_object as Node3D
	UnityTransform.look_at(body, world.global_position)

	var p := my_bottom.global_position

	var r := p.length()

	if r > _world_height and gravity_on:
		var dist := r - _world_height
		if dist > grav_speed * delta:
			UnityTransform.translate(body, UnityTransform.FORWARD * grav_speed * delta)
		else:
			UnityTransform.translate(body, UnityTransform.FORWARD * dist)

	UnityTransform.rotate(body, Vector3(-90.0, 0.0, 0.0))
