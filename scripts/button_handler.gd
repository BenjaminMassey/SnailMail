class_name ButtonHandler
extends Component
## Press/release handler for the Up and Right movement buttons.
##
## The first finger arrives as emulated mouse events through the button's
## button_down/button_up signals. Extra fingers are tracked here so both buttons
## can be held at once, as with Unity's multi-touch UI.

var _touches := {}


func start() -> void:
	Buttons.up_button = false
	Buttons.right_button = false


func on_press() -> void:
	if game_object.name.contains("Up"):
		Buttons.up_button = true
	if game_object.name.contains("Right"):
		Buttons.right_button = true


func on_release() -> void:
	if game_object.name.contains("Up"):
		Buttons.up_button = false
	if game_object.name.contains("Right"):
		Buttons.right_button = false


func _input(event: InputEvent) -> void:
	var touch := event as InputEventScreenTouch
	if touch == null or touch.index == 0:
		return
	if touch.pressed:
		if (game_object as Control).get_global_rect().has_point(touch.position):
			_touches[touch.index] = true
			on_press()
	elif _touches.erase(touch.index):
		on_release()
