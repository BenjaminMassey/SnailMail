extends RichTextLabel
## Opens [url] links in the credits. Ignores taps that were really scroll drags.

const DRAG_THRESHOLD := 20.0

var _press_pos := Vector2.ZERO
var _dragged := false


func _ready() -> void:
	meta_clicked.connect(_on_meta_clicked)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		_press_pos = event.global_position
		_dragged = false
	elif event is InputEventMouseMotion and event.global_position.distance_to(_press_pos) > DRAG_THRESHOLD:
		_dragged = true


func _on_meta_clicked(meta: Variant) -> void:
	if _dragged:
		return
	OS.shell_open(str(meta))
