class_name Kill
extends Component
## Salt and asteroids: touching them kills the snail and restarts the level.

@export var puff: AudioStreamPlayer


func _on_trigger_enter(other: Node3D) -> void:
	if LevelEnd.level_completed:
		return
	if other.name == "Character" or other.is_in_group("Player"):
		puff.play()
		var snail := GameObject.find("Snail")
		if snail:
			snail.queue_free()
		GameObject.get_component(other, Move).enabled = false
		MessageHandler.message("You died...", 1.0)
		_restart()


func _restart() -> void:
	await wait_for_seconds(1.0)
	Resetter.reset()
