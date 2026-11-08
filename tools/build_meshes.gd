extends SceneTree
## Run headless after the first import:
##   godot --headless --path . -s tools/build_meshes.gd
## Builds Unity-equivalent primitive meshes and extracts model meshes that Unity
## scenes reference directly (MeshFilter -> model sub-mesh), then records the
## top-level node transforms of each imported FBX for the scene converter.

const MODELS := [
	"res://assets/Mailbox.FBX",
	"res://assets/Rocket.fbx",
	"res://assets/Stone.FBX",
	"res://assets/Fantasy House/Mesh/Fantasy_House_6.FBX",
]
## Models whose mesh Unity scenes use directly through a MeshFilter.
const EXTRACT_MESHES := [
	"res://assets/Stone.FBX",
	"res://assets/Fantasy House/Mesh/Fantasy_House_6.FBX",
]


func _init() -> void:
	DirAccess.make_dir_recursive_absolute("res://meshes")
	_build_unity_plane()
	var info := {}
	for path in MODELS:
		info[path] = _inspect_model(path)
	var f := FileAccess.open("res://tools/models.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(info, "\t"))
	quit()


## Unity's built-in Plane is 10x10 with UV (0, 0) at its (+X, +Z) corner. Unity's
## V axis starts at the bottom of the image and Godot's at the top, so in Godot
## space U runs along -X and V along -Z.
func _build_unity_plane() -> void:
	var plane := PlaneMesh.new()
	plane.size = Vector2(10, 10)
	plane.subdivide_width = 9
	plane.subdivide_depth = 9
	var arrays := plane.get_mesh_arrays()
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var uvs := PackedVector2Array()
	for v in verts:
		uvs.append(Vector2((5.0 - v.x) / 10.0, (5.0 - v.z) / 10.0))
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_TANGENT] = null
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	ResourceSaver.save(mesh, "res://meshes/Plane.res")


func _inspect_model(path: String) -> Dictionary:
	var scene: Node = (load(path) as PackedScene).instantiate()
	var tops := []
	for child in scene.get_children():
		if child is Node3D:
			var t: Transform3D = child.transform
			tops.append({
				"name": String(child.name),
				"basis": [t.basis.x.x, t.basis.x.y, t.basis.x.z, t.basis.y.x, t.basis.y.y, t.basis.y.z, t.basis.z.x, t.basis.z.y, t.basis.z.z],
				"origin": [t.origin.x, t.origin.y, t.origin.z],
			})
	var first_mesh := _first_mesh(scene)
	var mesh_path := ""
	if first_mesh and path in EXTRACT_MESHES:
		mesh_path = "res://meshes/%s.res" % path.get_file().get_basename()
		ResourceSaver.save(first_mesh.mesh.duplicate(true), mesh_path)
	scene.free()
	return {"tops": tops, "mesh": mesh_path}


func _first_mesh(n: Node) -> MeshInstance3D:
	if n is MeshInstance3D:
		return n
	for c in n.get_children():
		var m := _first_mesh(c)
		if m:
			return m
	return null
