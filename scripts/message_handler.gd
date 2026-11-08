class_name MessageHandler
extends Object


static func message(text: String, time: float) -> void:
	var m := GameObject.get_component(GameObject.find("Text"), Message) as Message
	if m != null:
		m.message = text
		m.time = time
		m.send()
	else:
		print("FAILED VERY HARD TO SEND MESSAGE")
