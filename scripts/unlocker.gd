class_name Unlocker
extends Component
## Loads level progress and greys out locked level buttons.


func start() -> void:
	Unlocks.file_path = "user://snailmail.save"
	if not Unlocks.initialized:
		Unlocks.level_done[0] = true
		for i in range(1, Unlocks.num_levels):
			Unlocks.level_done[i] = false
		Unlocks.initialized = true
	Unlocks.load_data()
	update_buttons()


func update_buttons() -> void:
	var page_handler := GameObject.get_component(GameObject.find("Canvas"), PageHandler) as PageHandler
	var start_point := page_handler.page * 10
	var end_point := start_point + 10
	end_point = mini(Unlocks.num_levels, end_point)
	for i in range(start_point, end_point):
		var button_name := "Level" + str(i + 1) + " Button"
		var level_button := GameObject.find(button_name) as UIButton
		level_button.button_enabled = Unlocks.level_done[i]
		if Unlocks.level_done[i]:
			level_button.image_color = Color(1.0, 1.0, 1.0)
		else:
			level_button.image_color = Color(0.25, 0.25, 0.25)
			var text := GameObject.get_child(level_button, 0) as Label
			text.add_theme_color_override("font_color", Color(0, 0, 0))
