class_name Reset
extends Component


func button_reset() -> void:
	Resetter.reset()


func button_reset_data() -> void:
	Unlocks.reset_data()
	(GameObject.get_component(GameObject.find("Canvas"), Unlocker) as Unlocker).update_buttons()
