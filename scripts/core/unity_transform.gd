class_name UnityTransform
extends Object
## Unity Transform operations expressed in Unity's coordinate space.
##
## Scenes were converted from Unity's left-handed space by flipping Z, so a
## Unity vector (x, y, z) is (x, y, -z) here and Unity's "forward" (+Z) is
## Godot's -Z. These helpers take Unity-space arguments so the ported game code
## can keep the original numbers.

const FORWARD := Vector3(0, 0, 1)
const BACK := Vector3(0, 0, -1)


static func to_godot(v: Vector3) -> Vector3:
	return Vector3(v.x, v.y, -v.z)


## Quaternion.Euler(x, y, z) converted to Godot space (Unity applies Z, then X, then Y).
static func euler(degrees: Vector3) -> Quaternion:
	var qx := Quaternion(Vector3.RIGHT, deg_to_rad(-degrees.x))
	var qy := Quaternion(Vector3.UP, deg_to_rad(-degrees.y))
	var qz := Quaternion(Vector3.BACK, deg_to_rad(degrees.z))
	return qy * qx * qz


## transform.Translate(translation) in local space. Like Unity, the object's
## scale does not affect the distance moved.
static func translate(node: Node3D, translation: Vector3) -> void:
	var rotation := node.global_basis.orthonormalized()
	node.global_position += rotation * to_godot(translation)


## transform.Rotate(eulers) in local space.
static func rotate(node: Node3D, eulers: Vector3) -> void:
	node.quaternion = node.quaternion * euler(eulers)


## transform.LookAt(target): point forward at a world position with world up,
## keeping the object's scale.
static func look_at(node: Node3D, target: Vector3) -> void:
	var direction := target - node.global_position
	if direction.is_zero_approx():
		return
	direction = direction.normalized()
	var world_rotation: Quaternion
	if absf(direction.dot(Vector3.UP)) > 0.99999:
		world_rotation = Quaternion(Vector3.FORWARD, direction)
	else:
		world_rotation = Basis.looking_at(direction, Vector3.UP).get_rotation_quaternion()
	var parent := node.get_parent() as Node3D
	if parent:
		world_rotation = parent.global_basis.get_rotation_quaternion().inverse() * world_rotation
	node.quaternion = world_rotation
