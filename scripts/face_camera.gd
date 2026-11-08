class_name FaceCamera
extends Component
## Billboards the object towards the gameplay camera.

var _cam: Node3D


func start() -> void:
	_cam = GameObject.find("Main Camera")


func _physics_process(_delta: float) -> void:
	if _cam == null:
		return
	UnityTransform.look_at(game_object, _cam.global_position)
