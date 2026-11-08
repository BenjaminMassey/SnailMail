// Port of the post-processing stack's classic Vignette (mode 0) as a
// multiplicative full-screen overlay.
shader_type canvas_item;
render_mode blend_mul, unshaded;

uniform vec3 vignette_color : source_color = vec3(0.0);
uniform vec2 center = vec2(0.5, 0.5);
uniform float intensity = 0.53;
uniform float smoothness = 0.4;
uniform float roundness = 0.0;

void fragment() {
	vec2 screen_size = 1.0 / SCREEN_PIXEL_SIZE;
	vec2 d = abs(SCREEN_UV - center) * intensity;
	d.x *= mix(1.0, screen_size.x / screen_size.y, roundness);
	float factor = pow(clamp(1.0 - dot(d, d), 0.0, 1.0), smoothness * 5.0);
	COLOR = vec4(mix(vignette_color, vec3(1.0), factor), 1.0);
}
