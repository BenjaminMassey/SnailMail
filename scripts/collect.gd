class_name Collect
extends Component
## Picks up letters the snail touches.

@export var ding_sound: AudioStreamPlayer


func _on_trigger_enter(other: Node3D) -> void:
	if other.is_in_group("Collectable"):
		ding_sound.play()
		other.queue_free()
