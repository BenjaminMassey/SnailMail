class_name Unlocks
extends Object
## Which levels are unlocked, saved as a string of 0/1 characters.

static var initialized := false
static var num_levels := 20
static var level_done: Array[bool] = _new_progress()
static var file_path: String


static func save_data() -> void:
	print("Attempting save data (" + file_path + ")")
	var file := FileAccess.open(file_path, FileAccess.WRITE)
	if file == null:
		print(error_string(FileAccess.get_open_error()))
		return
	var data := ""
	for i in num_levels:
		data += "1" if level_done[i] else "0"
	file.store_string(data)


static func load_data() -> void:
	print("Attempting load data (" + file_path + ")")
	if FileAccess.file_exists(file_path):
		print("Succeeded file open: data collecting")
		var data := FileAccess.get_file_as_string(file_path)
		for i in mini(data.length(), num_levels):
			level_done[i] = data[i] == "1"
	else:
		print("Failed file open: creating new one")
		save_data()


static func reset_data() -> void:
	level_done[0] = true
	for i in range(1, num_levels):
		level_done[i] = false
	save_data()


static func _new_progress() -> Array[bool]:
	var progress: Array[bool] = []
	progress.resize(20)
	progress.fill(false)
	return progress
