@tool
class_name UIButton
extends Button
## A Unity UI Button with its Image: the image (a sprite, Unity's rounded
## "UISprite", or a plain rectangle) is tinted by the button's color block.
##
## [member button_enabled] mirrors toggling the Button component: when off the
## button ignores clicks and shows its normal tint, as Unity does.

@export var texture: Texture2D:
	set(value):
		texture = value
		_refresh()
@export var rounded := false:
	set(value):
		rounded = value
		_refresh()
@export var image_color := Color.WHITE:
	set(value):
		image_color = value
		_refresh()
@export var image_enabled := true:
	set(value):
		image_enabled = value
		_refresh()
@export var normal_color := Color.WHITE:
	set(value):
		normal_color = value
		_refresh()
@export var highlighted_color := Color(0.9607843, 0.9607843, 0.9607843):
	set(value):
		highlighted_color = value
		_refresh()
@export var pressed_color := Color(0.78431374, 0.78431374, 0.78431374):
	set(value):
		pressed_color = value
		_refresh()
@export var button_enabled := true:
	set(value):
		button_enabled = value
		disabled = not value
		_refresh()


func _init() -> void:
	focus_mode = Control.FOCUS_NONE
	_refresh()


func _refresh() -> void:
	add_theme_stylebox_override("normal", _make_style(normal_color))
	add_theme_stylebox_override("hover", _make_style(highlighted_color))
	add_theme_stylebox_override("pressed", _make_style(pressed_color))
	add_theme_stylebox_override("hover_pressed", _make_style(pressed_color))
	add_theme_stylebox_override("disabled", _make_style(normal_color))
	add_theme_stylebox_override("focus", StyleBoxEmpty.new())


func _make_style(tint: Color) -> StyleBox:
	if not image_enabled:
		return StyleBoxEmpty.new()
	var color := image_color * tint
	if texture:
		var style := StyleBoxTexture.new()
		style.texture = texture
		style.modulate_color = color
		return style
	var flat := StyleBoxFlat.new()
	flat.bg_color = color
	if rounded:
		flat.set_corner_radius_all(6)
		flat.anti_aliasing = true
	return flat
