class_name Component
extends Node
## Base class for scripts ported from Unity MonoBehaviours.
##
## A component lives as a child node of the node it drives (its "game object"),
## so an object can carry several components just like in Unity. Disabling a
## component stops its per-frame callbacks; [method start] runs once, the first
## time the component is enabled inside the tree.

## Emitted every physics tick while the component is in the tree, regardless of
## [member enabled] (Unity keeps running coroutines on disabled components).
signal _fixed_update

@export var enabled := true:
	set(value):
		enabled = value
		_update_processing()

var game_object: Node:
	get:
		return get_parent()

var _started := false

func _ready() -> void:
	set_physics_process_internal(true)
	_update_processing()


func _notification(what: int) -> void:
	if what == NOTIFICATION_INTERNAL_PHYSICS_PROCESS:
		_fixed_update.emit()


## Called once before the first frame the component is enabled (Unity's Start).
func start() -> void:
	pass


## Equivalent of `yield return new WaitForSeconds(seconds)`. The timer belongs to
## this node, so a pending wait is dropped if the component is freed.
func wait_for_seconds(seconds: float) -> Signal:
	var timer := Timer.new()
	timer.one_shot = true
	timer.wait_time = maxf(seconds, 0.001)
	add_child(timer)
	timer.timeout.connect(timer.queue_free)
	timer.start()
	return timer.timeout


## Equivalent of `yield return new WaitForFixedUpdate()`. A pending wait is
## dropped if the component leaves the tree, like a coroutine on a destroyed object.
func wait_for_fixed_update() -> Signal:
	return _fixed_update


func _update_processing() -> void:
	if not is_inside_tree():
		return
	set_process(enabled)
	set_physics_process(enabled)
	set_process_input(enabled)
	if enabled and not _started:
		_started = true
		start()
