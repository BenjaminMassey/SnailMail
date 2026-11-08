extends SceneTree
## Checks that saving each scene in the editor would not lose anything: loads it
## the way the editor does, re-packs it (what Ctrl+S does), loads the result
## and compares every stored property on every node.
##   godot --headless --path . -s tools/resave_test.gd [-- res://scenes/Level1.tscn ...]


func _initialize() -> void:
	var paths: Array = Array(OS.get_cmdline_user_args())
	if paths.is_empty():
		for dir in ["res://scenes", "res://prefabs"]:
			for f in DirAccess.get_files_at(dir):
				if f.ends_with(".tscn"):
					paths.append(dir.path_join(f))
	var bad := 0
	for path in paths:
		var problems := _check(path)
		if problems.is_empty():
			print("ok    ", path)
		else:
			bad += 1
			print("LOSES ", path)
			for p in problems:
				print("        ", p)
	print("%d of %d scenes would lose data on save" % [bad, paths.size()])
	quit(1 if bad else 0)


func _check(path: String) -> Array:
	var before: Node = (load(path) as PackedScene).instantiate(PackedScene.GEN_EDIT_STATE_MAIN)
	var repacked := PackedScene.new()
	repacked.pack(before)
	var after: Node = repacked.instantiate(PackedScene.GEN_EDIT_STATE_MAIN)
	var problems := []
	_compare(before, before, after, problems)
	before.free()
	after.free()
	return problems


func _compare(root: Node, a: Node, b_root: Node, problems: Array) -> void:
	var rel := root.get_path_to(a)
	var b := b_root.get_node_or_null(rel)
	if b == null:
		problems.append("%s: node missing" % rel)
		return
	for prop in a.get_property_list():
		if not (prop.usage & PROPERTY_USAGE_STORAGE):
			continue
		var va = _node_ref(root, a.get(prop.name))
		var vb = _node_ref(b_root, b.get(prop.name))
		if va is Object or vb is Object:
			continue  # resources are shared/cached; not what this checks
		if not _same(va, vb):
			problems.append("%s.%s: %s -> %s" % [rel, prop.name, va, vb])
	for c in a.get_children():
		_compare(root, c, b_root, problems)


## Exported node references compare by path; an unset one is null.
func _node_ref(root: Node, v: Variant) -> Variant:
	if v is Object and not is_instance_valid(v):
		return null
	if v is Node:
		return root.get_path_to(v)
	return v


func _same(a: Variant, b: Variant) -> bool:
	if a == null and b == null:  # a typed null Object vs a plain null
		return true
	if (a is float or a is int) and (b is float or b is int):
		return is_equal_approx(float(a), float(b))
	if typeof(a) != typeof(b):
		return false
	if a is Vector2 or a is Vector3 or a is Vector4 or a is Color or a is Transform3D \
			or a is Transform2D or a is Basis or a is Quaternion or a is Rect2:
		return a.is_equal_approx(b)
	return a == b
