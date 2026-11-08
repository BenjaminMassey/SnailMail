// Port of the SimpleMovement shader graph: a pulsing tinted texture.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque;

uniform vec4 color : source_color = vec4(1.0, 0.966, 0.0, 0.0);
uniform sampler2D tex : source_color, hint_default_white;
uniform float speed = 1.0;

void fragment() {
	vec2 pulse = vec2(0.1) * sin(TIME) * speed;
	vec2 fade = (pulse - vec2(-0.11)) / (vec2(1.0) - vec2(-0.11));
	vec4 tinted = color * texture(tex, UV);
	vec2 result = fade * tinted.rg;
	ALBEDO = vec3(result, 0.0);
	ALPHA = result.x;
	EMISSION = color.rgb;
}
