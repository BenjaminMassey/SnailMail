// Port of Unity's Skybox/Panoramic (latitude-longitude) shader.
// Directions are converted back to Unity's left-handed space before mapping so
// the panorama is not mirrored.
shader_type sky;

uniform sampler2D tex : source_color, filter_linear, repeat_enable;
uniform vec4 tint : source_color = vec4(0.5, 0.5, 0.5, 0.5);
uniform float exposure = 1.0;
uniform float rotation_degrees = 0.0;

void sky() {
	vec3 dir = normalize(vec3(EYEDIR.x, EYEDIR.y, -EYEDIR.z));
	float r = radians(rotation_degrees);
	dir.xz = mat2(vec2(cos(r), -sin(r)), vec2(sin(r), cos(r))) * dir.xz;
	float latitude = acos(dir.y);
	float longitude = atan(dir.z, dir.x);
	vec2 uv = vec2(0.5 - longitude / (2.0 * PI), latitude / PI);
	// Unity multiplies by the tint, doubled in gamma space, and the exposure.
	COLOR = texture(tex, uv).rgb * tint.rgb * 2.0 * exposure;
}
