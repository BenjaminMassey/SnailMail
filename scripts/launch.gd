class_name Launch
extends Component
## Launch pads: when the snail is inside the pad's collider bounds it is pushed
## in the direction given by the pad's name, then the pad is used up.

@export var boing: AudioStreamPlayer

var _doing := false

var _direction: Vector3

var _character: Node3D
var _bottom: Node3D
var _col: CollisionShape3D


func start() -> void:
	_character = GameObject.find("Character")
	_bottom = GameObject.find("Bottom")


func _process(_delta: float) -> void:
	var char_pos := _character.global_position
	var bottom_pos := _bottom.global_position

	_col = GameObject.get_collider(game_object)
	var bounds := GameObject.get_collider_bounds(_col)

	if bounds.has_point(char_pos) or bounds.has_point(bottom_pos):
		_do()


func _do() -> void:
	# Directions are in Unity space (see UnityTransform).
	var pad_name := String(game_object.name)
	if pad_name.contains("Left"):
		_direction = Vector3.LEFT
	elif pad_name.contains("Right"):
		_direction = Vector3.RIGHT
	elif pad_name.contains("Up"):
		_direction = UnityTransform.FORWARD
	elif pad_name.contains("Down"):
		_direction = UnityTransform.BACK
	elif pad_name.contains("Jump"):
		_direction = Vector3.UP
	else:
		push_warning("Unknown Launch.cs container")
		game_object.queue_free()
	boing.play()
	_send()


func _send() -> void:
	if not _doing:
		_doing = true
		var character := GameObject.find("Character") as Node3D
		var mover := GameObject.get_component(character, Move) as Move
		var amount := 10
		var x := 1.0
		if _direction == Vector3.UP:
			amount = 30
			x = 0.6
			mover.gravity_on = false
		else:
			mover.move_on = false
		for i in amount:
			UnityTransform.translate(character, _direction * 0.4 * x)
			await wait_for_fixed_update()
		_doing = false
		mover.move_on = true
		mover.gravity_on = true
		game_object.queue_free()
