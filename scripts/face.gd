class_name Face
extends Component
## Keeps the object turned towards another object.

@export var object_to_face: Node3D


func _physics_process(_delta: float) -> void:
	UnityTransform.look_at(game_object, object_to_face.global_position)
