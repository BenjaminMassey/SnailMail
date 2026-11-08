class_name LookAtCenter
extends Component

## Extra rotation applied after facing the origin, as Unity Euler angles.
@export var offset := Vector3.ZERO


func start() -> void:
	UnityTransform.look_at(game_object, Vector3.ZERO)
	UnityTransform.rotate(game_object, offset)
