class_name Music
extends Component
## Keeps the background music playing across scene loads (Unity's
## DontDestroyOnLoad): the first music object moves itself out of the scene,
## later copies remove themselves.


func _ready() -> void:
	super()
	var count := get_tree().get_nodes_in_group("Music").size()
	if count > 1:
		game_object.queue_free()
		return
	_dont_destroy_on_load.call_deferred()


func _dont_destroy_on_load() -> void:
	game_object.reparent(get_tree().root)
