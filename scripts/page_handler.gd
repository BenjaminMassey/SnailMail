class_name PageHandler
extends Component
## Pages through the level select buttons, ten levels per page.

@export var page: int

var _buttons: Array[UIButton] = []

var _up_button: Node
var _down_button: Node

var _def_color: Color


func start() -> void:
	page = 0
	_buttons.resize(10)
	for i in 10:
		_buttons[i] = GameObject.find("Level" + str(i + 1) + " Button")
	_def_color = _buttons[0].normal_color

	_up_button = GameObject.find("Up Button")
	_down_button = GameObject.find("Down Button")

	_update_nav_buttons()


func page_down() -> void:
	page += 1
	@warning_ignore("integer_division")
	page = mini(Unlocks.num_levels / 10, page)
	_update_page()
	_update_nav_buttons()


func page_up() -> void:
	page -= 1
	page = maxi(0, page)
	_update_page()
	_update_nav_buttons()


func _update_page() -> void:
	for rel_num in 10:
		var num := (page * 10) + rel_num
		if num < Unlocks.num_levels:
			_new_button(num)
		else:
			_buttons[rel_num].name = "Non-Button"
			_buttons[rel_num].image_enabled = false
			_buttons[rel_num].button_enabled = false
			_button_text(rel_num).visible = false
	(GameObject.get_component(GameObject.find("Canvas"), Unlocker) as Unlocker).update_buttons()


func _new_button(num: int) -> void:
	var rel_num := num % 10
	var str_num := str(num + 1)
	_buttons[rel_num].name = "Level" + str_num + " Button"
	_button_text(rel_num).text = "Level " + str_num

	if num > 12: # Moon Levels Color
		_buttons[rel_num].normal_color = Color(0.4, 0, 0.4)
		_button_text(rel_num).add_theme_color_override("font_color", Color(1, 1, 1))
	else:
		_buttons[rel_num].normal_color = _def_color
		_button_text(rel_num).add_theme_color_override("font_color", Color(0, 0, 0))

	_buttons[rel_num].image_enabled = true
	_buttons[rel_num].button_enabled = true
	_button_text(rel_num).visible = true


func _update_nav_buttons() -> void:
	if page == 0:
		GameObject.set_active(_up_button, false)
	else:
		GameObject.set_active(_up_button, true)

	@warning_ignore("integer_division")
	if page == (Unlocks.num_levels / 10) - 1 or Unlocks.num_levels <= 10:
		GameObject.set_active(_down_button, false)
	else:
		GameObject.set_active(_down_button, true)


func _button_text(rel_num: int) -> Label:
	return GameObject.get_child(_buttons[rel_num], 0) as Label
