class_name Message
extends Component
## Shows a temporary message in the title text.

var time: float
var message: String

var _t: Control


func start() -> void:
	time = 1.0
	message = ""
	_t = game_object


func send() -> void:
	_t.text = message
	_t.visible = true
	await wait_for_seconds(time)
	_t.text = ""
	_t.visible = false
