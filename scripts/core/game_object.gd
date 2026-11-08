class_name GameObject
extends Object
## Static helpers mirroring the parts of Unity's GameObject API the game uses.
##
## "Game objects" are the scene nodes converted from Unity GameObjects
## (Node3D / Control / CanvasLayer). Component nodes, collision shapes and audio
## players are children of those and are skipped by lookups. A game object is
## active when it can process (inactive ones are disabled via process_mode).


## GameObject.Find: first active game object with the given name, depth-first.
static func find(object_name: String) -> Node:
	var tree := Engine.get_main_loop() as SceneTree
	for child in tree.root.get_children():
		var found := _find_in(child, object_name, child == tree.current_scene)
		if found:
			return found
	return null


## GameObject.FindGameObjectsWithTag: tags are converted to node groups.
static func find_game_objects_with_tag(tag: String) -> Array[Node]:
	var tree := Engine.get_main_loop() as SceneTree
	var result: Array[Node] = []
	for node in tree.get_nodes_in_group(tag):
		if node.can_process():
			result.append(node)
	return result


## GetComponent<T>(): the first component node of the given script class.
static func get_component(game_object: Node, type: Script) -> Node:
	for child in game_object.get_children():
		if is_instance_of(child, type):
			return child
	return null


## transform.GetChild(index), counting only child game objects.
static func get_child(game_object: Node, index: int) -> Node:
	var i := 0
	for child in game_object.get_children():
		if is_game_object(child):
			if i == index:
				return child
			i += 1
	return null


## GameObject.SetActive.
static func set_active(game_object: Node, active: bool) -> void:
	if "visible" in game_object:
		game_object.visible = active
	game_object.process_mode = Node.PROCESS_MODE_INHERIT if active else Node.PROCESS_MODE_DISABLED


## The node that renders a game object's mesh (GetComponent<MeshRenderer>()).
static func get_mesh_renderer(game_object: Node) -> GeometryInstance3D:
	if game_object is MeshInstance3D:
		return game_object
	return game_object.get_node_or_null("Mesh") as GeometryInstance3D


## The game object's collider (GetComponent<Collider>()). Colliders that need
## their own uniformly scaled physics body live under a "Trigger" area.
static func get_collider(game_object: Node) -> CollisionShape3D:
	var collider := game_object.get_node_or_null("Collider") as CollisionShape3D
	if collider == null:
		collider = game_object.get_node_or_null("Trigger/Collider") as CollisionShape3D
	return collider


## Collider.bounds: the world-space axis-aligned box enclosing the collider.
static func get_collider_bounds(collider: CollisionShape3D) -> AABB:
	var local: AABB
	var shape := collider.shape
	if shape is BoxShape3D:
		local = AABB(-shape.size / 2.0, shape.size)
	elif shape is SphereShape3D:
		local = AABB(-Vector3.ONE * shape.radius, Vector3.ONE * shape.radius * 2.0)
	elif shape is CapsuleShape3D:
		var half := Vector3(shape.radius, shape.height / 2.0, shape.radius)
		local = AABB(-half, half * 2.0)
	else:
		return AABB(collider.global_position, Vector3.ZERO)
	return collider.global_transform * local


static func is_game_object(node: Node) -> bool:
	if node is CollisionShape3D or node is Component:
		return false
	return node is Node3D or node is Control or node is CanvasLayer


static func _find_in(node: Node, object_name: String, is_scene_root: bool) -> Node:
	if not node.can_process():
		return null
	if not is_scene_root and is_game_object(node) and node.name == object_name:
		return node
	for child in node.get_children():
		var found := _find_in(child, object_name, false)
		if found:
			return found
	return null
