class_name Asteroid
extends Component
## Falls towards the planet, shrinks away on impact, then repeats.

@export var orig_speed := 0.5
@export var wait_time := 0.5

var _speed: float

var _start_pos: Vector3
var _start_scale: Vector3
var _my_mesh_renderer: GeometryInstance3D
var _my_col: CollisionShape3D


func start() -> void:
	var body := game_object as Node3D
	_start_pos = body.global_position
	_start_scale = body.scale
	_my_mesh_renderer = GameObject.get_mesh_renderer(body)
	_my_col = GameObject.get_collider(body)

	var speed_random := randf_range(0.8, 1.2)
	_speed = orig_speed * speed_random

	_travel()


func _travel() -> void:
	var body := game_object as Node3D
	var start_random := randf_range(0.0, 0.5)
	await wait_for_seconds(start_random)

	while true:
		# Setup
		_my_mesh_renderer.visible = true
		_my_col.set_deferred("disabled", false)
		body.scale = _start_scale
		body.global_position = _start_pos
		UnityTransform.look_at(body, Vector3.ZERO) # Point at origin

		# Main movement
		var radius := body.global_position.length_squared()
		while radius > 30.0: # 25 is world radius, but want a little before
			UnityTransform.translate(body, UnityTransform.FORWARD * 0.1 * _speed)
			radius = body.global_position.length_squared()
			await wait_for_fixed_update()
		# Dissolve effect
		for _i in 20:
			body.scale *= 0.7
			UnityTransform.translate(body, UnityTransform.FORWARD * 0.1)
			await wait_for_fixed_update()

		# Wrap up + wait time. (Unity sets the scale to exactly zero; physics
		# needs an invertible transform, so use a vanishingly small one.)
		_my_col.set_deferred("disabled", true)
		body.scale = _start_scale * 0.00001
		_my_mesh_renderer.visible = false
		var wait_random := randf_range(0.8, 1.2)
		var waited := 0
		while waited < 50.0 * wait_time * wait_random:
			await wait_for_fixed_update()
			waited += 1
		var speed_random := randf_range(0.8, 1.2)
		_speed = orig_speed * speed_random
