// Port of the TwoColors shader graph: the texture blends between two colors
// (ColorA where the texture is white, ColorB where it is black).
// The Unity project used gamma color space, so the blend happens on sRGB values.
shader_type spatial;

uniform sampler2D shape_info : hint_default_white;
uniform vec4 color_a = vec4(0.0);
uniform vec4 color_b = vec4(0.0);

vec3 srgb_to_linear(vec3 c) {
	return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

void fragment() {
	vec3 t = texture(shape_info, UV).rgb;
	vec3 albedo = color_a.rgb * t + color_b.rgb * (vec3(1.0) - t);
	ALBEDO = srgb_to_linear(clamp(albedo, 0.0, 1.0));
	METALLIC = 0.0;
	ROUGHNESS = 0.5;
}
