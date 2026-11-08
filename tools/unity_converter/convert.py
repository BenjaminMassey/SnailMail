"""Convert the SnailMail Unity project's scenes, prefabs and materials to Godot.

Usage (Python 3 with PyYAML and Pillow), from this directory:
    python convert.py
then let Godot import the new files and rebuild the derived meshes:
    godot --headless --path ../.. --import
    godot --headless --path ../.. -s tools/build_meshes.gd
On a fresh project, run convert.py once more afterwards so it sees the
up-to-date tools/models.json. Existing .import files are left alone; delete
one to have its settings regenerated.
"""
import json, os, re, shutil
from PIL import Image

from unityscene import UNITY, instantiate, guid_path, load_docs, Ref, v3, v2, q4, col
from mats import read_mat
from tscn import (Writer, Lit, V2, V3, V4, Col, T3D, NP, Ext, Sub, canon, unity_trs,
                  mat_mul, mat_inv, mat_vec, ROT_Y180)

GODOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

SCENES = ['LevelSelect', 'Controls', 'Credits'] + ['Level%d' % i for i in range(1, 21)] + ['End']

BUILTIN_MESH = {10202: 'Cube', 10206: 'Cylinder', 10207: 'Sphere', 10208: 'Capsule', 10209: 'Plane', 10210: 'Quad'}

# Unity script -> (gdscript file, class, {unity field: godot property})
SCRIPTS = {
    'Asteroid.cs': ('asteroid', 'Asteroid', {'orig_speed': 'orig_speed', 'wait_time': 'wait_time'}),
    'ButtonHandler.cs': ('button_handler', 'ButtonHandler', {}),
    'Collect.cs': ('collect', 'Collect', {'DingSound': 'ding_sound'}),
    'Controls.cs': ('controls', 'Controls', {}),
    'CorrectRadius.cs': ('correct_radius', 'CorrectRadius', {'offset': 'offset'}),
    'Credits.cs': ('credits', 'Credits', {}),
    'End.cs': ('end', 'End', {'Cheer': 'cheer', 'Aww': 'aww'}),
    'Face.cs': ('face', 'Face', {'Object_to_Face': 'object_to_face'}),
    'FaceCamera.cs': ('face_camera', 'FaceCamera', {}),
    'Kill.cs': ('kill', 'Kill', {'Puff': 'puff'}),
    'Launch.cs': ('launch', 'Launch', {'Boing': 'boing'}),
    'LevelSelectButton.cs': ('level_select_button', 'LevelSelectButton', {}),
    'LookAtCenter.cs': ('look_at_center', 'LookAtCenter', {'offset': 'offset'}),
    'Menu.cs': ('menu', 'Menu', {}),
    'Message.cs': ('message', 'Message', {}),
    'Move.cs': ('move', 'Move', {'MoveSpeed': 'move_speed', 'GravSpeed': 'grav_speed', 'world': 'world',
                                 'my_bottom': 'my_bottom', 'snail_obj': 'snail_obj'}),
    'Music.cs': ('music', 'Music', {}),
    'NextLevel.cs': ('next_level', 'NextLevel', {}),
    'PageHandler.cs': ('page_handler', 'PageHandler', {'page': 'page'}),
    'Reset.cs': ('reset', 'Reset', {}),
    'Unlocker.cs': ('unlocker', 'Unlocker', {}),
}
TRIGGER_SCRIPTS = {'Collect.cs', 'Kill.cs', 'End.cs'}

UI_SHADOW_SCRIPT = -900027084
UI_OUTLINE_SCRIPT = 1573420865

MODEL_INFO = json.load(open(os.path.join(GODOT, 'tools', 'models.json')))

warnings = []


def warn(msg):
    if msg not in warnings:
        warnings.append(msg)


# --- assets ----------------------------------------------------------------

def res_asset(rel):
    """Unity 'Assets/x/y' -> 'res://assets/x/y' (copying the file on first use)."""
    assert rel.startswith('Assets/')
    sub = rel[len('Assets/'):]
    dst = os.path.join(GODOT, 'assets', sub)
    src = os.path.join(UNITY, rel)
    ext = os.path.splitext(rel)[1].lower()
    if ext in ('.tif', '.tiff'):
        dst = os.path.splitext(dst)[0] + '.png'
        sub = os.path.splitext(sub)[0] + '.png'
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if ext in ('.png', '.jpg', '.jpeg', '.tif', '.tiff'):
            im = Image.open(src)
            if max(im.size) > 2048:  # Unity imported every texture at max size 2048
                k = 2048 / max(im.size)
                im = im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS)
                if ext in ('.jpg', '.jpeg'):
                    im.save(dst, quality=95)
                else:
                    im.save(dst)
            elif ext in ('.tif', '.tiff'):
                im.save(dst)
            else:
                shutil.copyfile(src, dst)
        elif ext == '.wav':
            open(dst, 'wb').write(plain_pcm_wav(open(src, 'rb').read()))
        else:
            shutil.copyfile(src, dst)
    return 'res://assets/' + sub


def plain_pcm_wav(data):
    """Rewrite a WAVE_FORMAT_EXTENSIBLE PCM file with a plain PCM header (Godot
    only reads format tags 1 and 3). The samples are unchanged."""
    import struct
    chunks, i = [], 12
    while i + 8 <= len(data):
        cid, size = data[i:i + 4], struct.unpack('<I', data[i + 4:i + 8])[0]
        chunks.append((cid, data[i + 8:i + 8 + size]))
        i += 8 + size + (size & 1)
    fmt = dict(chunks).get(b'fmt ')
    if fmt is None or struct.unpack('<H', fmt[:2])[0] != 0xFFFE:
        return data
    sub_format = struct.unpack('<H', fmt[24:26])[0]  # 1 = PCM, 3 = float
    out = b''
    for cid, body in chunks:
        if cid == b'fmt ':
            body = struct.pack('<H', sub_format) + body[2:16]
        elif cid != b'data':
            continue
        out += cid + struct.pack('<I', len(body)) + body + (b'\0' if len(body) & 1 else b'')
    return b'RIFF' + struct.pack('<I', 4 + len(out)) + b'WAVE' + out


def write_import(res_path, importer, type, params):
    path = os.path.join(GODOT, res_path[len('res://'):]) + '.import'
    if os.path.exists(path):  # keep Godot's completed import (delete it to apply new params)
        return
    lines = ['[remap]', '', 'importer="%s"' % importer, 'type="%s"' % type, '', '[params]', '']
    lines += ['%s=%s' % (k, v) for k, v in params.items()]
    open(path, 'w', newline='\n').write('\n'.join(lines) + '\n')


def texture(rel, normal=False):
    p = res_asset(rel)
    if normal:
        write_import(p, 'texture', 'CompressedTexture2D', {'compress/mode': 0, 'compress/normal_map': 1})
    return Ext(p, 'Texture2D')


_sounds = {}


def audio(rel, loop):
    p = res_asset(rel)
    if rel.lower().endswith('.mp3'):
        write_import(p, 'mp3', 'AudioStreamMP3', {'loop': 'true' if loop else 'false', 'loop_offset': 0})
    return Ext(p, 'AudioStream')


def font():
    return Ext(res_asset('Assets/Fonts/Chewy-Regular.ttf'), 'FontFile')


# --- materials ---------------------------------------------------------------

_mats = {}
UI_DEFAULT_MATS = set()


def write_tres(rel_out, type, props, script_class=None):
    w = Writer()
    text = w.resource_text(type, props, script_class)
    path = os.path.join(GODOT, rel_out[len('res://'):])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', newline='\n').write(text)


def material(guid):
    """Unity material guid -> Ext of converted Godot material."""
    rel = guid_path(guid)
    if rel is None or not rel.endswith('.mat'):
        return None
    if rel in _mats:
        return _mats[rel]
    m = read_mat(rel)
    name = os.path.splitext(os.path.basename(rel))[0]
    out = 'res://materials/%s.tres' % name
    sh = m['shader']
    cols, tex, fl, kw = m['cols'], m['tex'], m['floats'], (m['kw'] or '').split()

    def c(k, default=(1, 1, 1, 1)):
        return Col(*cols.get(k, default))

    def v4(k, default=(1, 1, 1, 1)):
        # For plain vec4 uniforms (no source_color): a Color value there is dropped
        # (saved as nil) when the material is converted to binary on export.
        return V4(*cols.get(k, default))

    if sh.endswith('TwoColors.shadergraph'):
        props = [('resource_name', name),
                 ('render_priority', 0),
                 ('shader', Ext('res://shaders/two_colors.gdshader', 'Shader')),
                 ('shader_parameter/color_a', v4('Color_2290612F', (0, 0, 0, 0))),
                 ('shader_parameter/color_b', v4('Color_CFBAD931', (0, 0, 0, 0)))]
        if 'Texture2D_895159E' in tex:
            props.append(('shader_parameter/shape_info', texture(tex['Texture2D_895159E'][0])))
        write_tres(out, 'ShaderMaterial', props)
    elif sh.endswith('SimpleMovement.shadergraph'):
        props = [('resource_name', name), ('render_priority', 0),
                 ('shader', Ext('res://shaders/simple_movement.gdshader', 'Shader')),
                 ('shader_parameter/color', c('Color_1A8E841E'))]
        write_tres(out, 'ShaderMaterial', props)
    elif sh == 'builtin:10770':  # UI/Default: unlit, alpha blended, double sided, no fog
        UI_DEFAULT_MATS.add(out)
        props = [('resource_name', name), ('transparency', 1), ('cull_mode', 2), ('shading_mode', 0),
                 ('disable_fog', True), ('albedo_color', c('_Color'))]
        if '_MainTex' in tex:
            props.append(('albedo_texture', texture(tex['_MainTex'][0])))
        write_tres(out, 'StandardMaterial3D', props)
    else:  # LWRP Lit
        props = [('resource_name', name)]
        surface = int(fl.get('_Surface', 0))
        if surface == 1:
            props.append(('transparency', 1))
        if int(fl.get('_Cull', 2)) == 0:
            props.append(('cull_mode', 2))
        if '_SPECULARHIGHLIGHTS_OFF' in kw:
            props.append(('specular_mode', 2))
        props.append(('albedo_color', c('_BaseColor')))
        if '_BaseMap' in tex:
            t, scale, off = tex['_BaseMap']
            props.append(('albedo_texture', texture(t)))
            if scale and (scale['x'], scale['y']) != (1, 1):
                props.append(('uv1_scale', V3(scale['x'], scale['y'], 1)))
            if off and (off['x'], off['y']) != (0, 0):
                props.append(('uv1_offset', V3(off['x'], off['y'], 0)))
        smooth = float(fl.get('_Smoothness', 0.5))
        if '_METALLICSPECGLOSSMAP' in kw and '_MetallicGlossMap' in tex:
            props += [('metallic', 1.0), ('metallic_texture', texture(tex['_MetallicGlossMap'][0])),
                      ('metallic_texture_channel', 0)]
        else:
            props.append(('metallic', float(fl.get('_Metallic', 0))))
        props += [('metallic_specular', 0.5 if int(fl.get('_WorkflowMode', 1)) == 1 else 0.0),
                  ('roughness', 1.0 - smooth)]
        if '_NORMALMAP' in kw and '_BumpMap' in tex:
            props += [('normal_enabled', True), ('normal_scale', float(fl.get('_BumpScale', 1))),
                      ('normal_texture', texture(tex['_BumpMap'][0], normal=True))]
        if '_OCCLUSIONMAP' in kw and '_OcclusionMap' in tex:
            props += [('ao_enabled', True), ('ao_texture', texture(tex['_OcclusionMap'][0]))]
        if '_EMISSION' in kw:
            props += [('emission_enabled', True), ('emission', c('_EmissionColor', (0, 0, 0, 1)))]
        write_tres(out, 'StandardMaterial3D', props)
    _mats[rel] = Ext(out, 'ShaderMaterial' if sh.endswith('.shadergraph') else 'StandardMaterial3D')
    return _mats[rel]


def skybox(guid):
    rel = guid_path(guid)
    m = read_mat(rel)
    name = os.path.splitext(os.path.basename(rel))[0]
    out = 'res://materials/sky/%s.tres' % name
    if m['shader'] == 'builtin:103':  # Skybox/Panoramic
        tint = m['cols'].get('_Tint', (0.5, 0.5, 0.5, 0.5))
        write_tres(out, 'ShaderMaterial', [
            ('resource_name', name), ('shader', Ext('res://shaders/panoramic_sky.gdshader', 'Shader')),
            ('shader_parameter/tex', texture(m['tex']['_Tex'][0])),
            ('shader_parameter/tint', Col(*tint)),
            ('shader_parameter/exposure', float(m['floats'].get('_Exposure', 1))),
            ('shader_parameter/rotation_degrees', float(m['floats'].get('_Rotation', 0)))])
        return Ext(out, 'ShaderMaterial')
    else:  # Skybox/Procedural, colors matched to the original game's rendering
        write_tres(out, 'ProceduralSkyMaterial', [
            ('resource_name', name),
            ('sky_top_color', Col(0.13, 0.24, 0.44)),
            ('sky_horizon_color', Col(0.72, 0.8, 0.84)),
            ('sky_curve', 0.12),
            ('ground_bottom_color', Col(0.6, 0.63, 0.65)),
            ('ground_horizon_color', Col(0.66, 0.7, 0.72)),
            ('sun_angle_max', 4.0)])
    return Ext(out, 'ProceduralSkyMaterial')


def builtin_meshes():
    defs = {
        'Cube': ('BoxMesh', []),
        'Sphere': ('SphereMesh', [('radius', 0.5), ('height', 1.0)]),
        'Capsule': ('CapsuleMesh', [('radius', 0.5), ('height', 2.0)]),
        'Cylinder': ('CylinderMesh', [('top_radius', 0.5), ('bottom_radius', 0.5), ('height', 2.0)]),
        'Quad': ('QuadMesh', []),
    }
    for name, (type, props) in defs.items():
        write_tres('res://meshes/%s.tres' % name, type, props)


def builtin_mesh(fid):
    name = BUILTIN_MESH[fid]
    if name == 'Plane':
        return Ext('res://meshes/Plane.res', 'ArrayMesh')
    return Ext('res://meshes/%s.tres' % name, {'Cube': 'BoxMesh', 'Sphere': 'SphereMesh', 'Capsule': 'CapsuleMesh',
                                               'Cylinder': 'CylinderMesh', 'Quad': 'QuadMesh'}[name])


# --- models ---------------------------------------------------------------

def model_default_materials(src):
    """Unity's per-model material remaps (externalObjects): material name -> Ext."""
    import yaml
    d = yaml.safe_load(open(os.path.join(UNITY, src + '.meta')))
    out = {}
    for e in d['ModelImporter'].get('externalObjects') or []:
        out[e['first']['name']] = material(e['second']['guid'])
    return out


OBJ_SURFACES = {}

# Unity gives each object of a multi-object OBJ its own renderer, identified by a
# hashed fileID; Godot imports them as surfaces of one mesh (sorted by material).
# Matched by geometry: the cap's dome is Material004, its brim Material_001.
OBJ_RENDERER_SURFACE = {
    ('Assets/lego cap.obj', -6359100828232346508): 0,  # Material004 (dome)
    ('Assets/lego cap.obj', -1361698509619221441): 1,  # Material_001 (brim)
    ('Assets/Mushroom.obj', -2416733968201007103): 0,  # mush
}


def obj_surfaces(src):
    if src not in OBJ_SURFACES:
        names = []
        for line in open(os.path.join(UNITY, src), encoding='utf-8', errors='replace'):
            if line.startswith('usemtl '):
                n = line.split(None, 1)[1].strip()
                if n not in names:
                    names.append(n)
        OBJ_SURFACES[src] = sorted(names)  # Godot orders OBJ surfaces by material name
    return OBJ_SURFACES[src]


_fbx_imports = set()


def fbx_import(src):
    p = res_asset(src)
    if src not in _fbx_imports:
        _fbx_imports.add(src)
        remaps = model_default_materials(src)
        if remaps:
            entries = ',\n'.join('"%s": {\n"use_external/enabled": true,\n"use_external/path": "%s"\n}' % (k, v.path)
                                 for k, v in remaps.items())
            write_import(p, 'scene', 'PackedScene', {'_subresources': '{\n"materials": {\n%s\n}\n}' % entries,
                                                     'fbx/importer': 0})
    return p


def model_wrapper_transform(res_path):
    """Transform for the imported model under its Unity GO: the handedness flip
    (180 degrees about Y), and for files whose single top node Unity collapsed into
    the root GO, that node's own transform cancelled."""
    info = MODEL_INFO.get(res_path)
    rows = ROT_Y180
    origin = (0, 0, 0)
    if info and len(info['tops']) == 1:
        t = info['tops'][0]
        b = t['basis']
        cols_ = [b[0:3], b[3:6], b[6:9]]
        m = [[cols_[j][i] for j in range(3)] for i in range(3)]
        inv = mat_inv(m)
        o = mat_vec(inv, t['origin'])
        rows = mat_mul(ROT_Y180, inv)
        origin = mat_vec(ROT_Y180, (-o[0], -o[1], -o[2]))
    return T3D(rows, origin)


# --- node specs ---------------------------------------------------------------

class Spec:
    def __init__(self, type=None, instance=None):
        self.type, self.instance = type, instance
        self.props = []
        self.groups = []

    def set(self, k, v):
        for i, (k2, _) in enumerate(self.props):
            if k2 == k:
                self.props[i] = (k, v)
                return
        self.props.append((k, v))


# Property values that need not be written for full nodes.
DEFAULTS = {'enabled': 'true', 'visible': 'true', 'process_mode': '0', 'self_modulate': 'Color(1, 1, 1, 1)',
            'scale': 'Vector2(1, 1)', 'rotation': '0', 'image_enabled': 'true', 'button_enabled': 'true',
            'image_color': 'Color(1, 1, 1, 1)', 'normal_color': 'Color(1, 1, 1, 1)',
            'highlighted_color': 'Color(0.9607843, 0.9607843, 0.9607843, 1)',
            'pressed_color': 'Color(0.7843137, 0.7843137, 0.7843137, 1)', 'rounded': 'false',
            'pivot_offset_ratio': 'Vector2(0, 0)', 'cast_shadow': '1'}


def script_info(d):
    p = guid_path((d.get('m_Script') or {}).get('guid'))
    if p and p.startswith('Assets/Scripts/'):
        return os.path.basename(p)
    return None


def ui_kind_of(d):
    if 'm_FontData' in d:
        return 'Text'
    if 'm_Sprite' in d and 'm_Type' in d:
        return 'Image'
    if 'm_OnClick' in d:
        return 'Button'
    if 'm_Delegates' in d:
        return 'EventTrigger'
    if 'm_EffectDistance' in d:
        return 'Outline' if (d.get('m_Script') or {}).get('fileID') == UI_OUTLINE_SCRIPT else 'Shadow'
    if 'm_Content' in d and 'm_Viewport' in d:
        return 'ScrollRect'
    if 'm_HandleRect' in d:
        return 'Scrollbar'
    if 'm_ShowMaskGraphic' in d:
        return 'Mask'
    if 'm_UiScaleMode' in d:
        return 'CanvasScaler'
    if 'm_BlockingObjects' in d:
        return 'GraphicRaycaster'
    if 'm_FirstSelected' in d:
        return 'EventSystem'
    if 'm_HorizontalAxis' in d:
        return 'InputModule'
    if 'sharedProfile' in d:
        return 'PPVolume'
    if 'volumeTrigger' in d:
        return 'PPLayer'
    return None


def ui_comp(go, kind):
    for c, d in go.comps:
        if c == 114 and ui_kind_of(d) == kind:
            return d
    return None


def snake(name):
    s = re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name)
    return s.lower()


def safe_name(n):
    return re.sub(r'[.:@/"%]', '_', n) or 'Node'


def is_skipped(go):
    if go.tcls != 224 and go.comp(223) is None and not go.children:
        kinds = [ui_kind_of(d) for c, d in go.comps if c == 114]
        if go.comps and all(c == 114 for c, _ in go.comps) and all(k in ('EventSystem', 'InputModule', 'PPVolume') for k in kinds):
            return True
    if ui_comp(go, 'Scrollbar') is not None:
        return True
    return False


class Plan:
    """Assigns Godot names/paths to the GameObjects of one emitted file."""

    def __init__(self):
        self.path = {}  # id(go) -> tuple
        self.comp_names = {}  # id(go) -> {id(compdata): name}
        self.children = {}  # id(go) -> emitted child GOs
        self.scroll_content = {}  # id(content go) -> True

    def assign(self, go, parent_path, used, is_root=False):
        name = safe_name(go.name)
        base, n = name, 2
        while name in used:
            name = '%s%d' % (base, n)
            n += 1
        used.add(name)
        path = () if is_root else parent_path + (name,)
        self.path[id(go)] = path
        names = {}
        cused = set()
        for c, d in go.comps:
            cn = None
            if c == 82:
                clip = guid_path((d.get('m_audioClip') or {}).get('guid'))
                cn = safe_name(os.path.splitext(os.path.basename(clip))[0]) if clip else 'AudioSource'
            elif c == 114 and script_info(d) in SCRIPTS:
                cn = SCRIPTS[script_info(d)][1]
            if cn:
                b, k = cn, 2
                while cn in cused:
                    cn = '%s%d' % (b, k)
                    k += 1
                cused.add(cn)
                names[id(d)] = cn
        self.comp_names[id(go)] = names
        kids = []
        scroll = ui_comp(go, 'ScrollRect')
        if scroll is not None:
            content = scroll.get('m_Content')
            if isinstance(content, Ref):
                kids = [content.go]
                self.scroll_content[id(content.go)] = True
        else:
            kids = [c for c in go.children if not is_skipped(c)]
        self.children[id(go)] = kids
        cu = set(cused)
        for k in kids:
            self.assign(k, path, cu)

    def ref_path(self, ref):
        g = ref.go
        base = self.path.get(id(g))
        if base is None:
            return None
        if ref.kind == 'comp' and ref.cls in (82, 114):
            cn = self.comp_names[id(g)].get(id(ref.comp))
            if cn:
                return base + (cn,)
        return base


def rel_path(frm, to):
    k = 0
    while k < min(len(frm), len(to)) and frm[k] == to[k]:
        k += 1
    parts = ['..'] * (len(frm) - k) + list(to[k:])
    return '/'.join(parts) or '.'


class Ctx:
    def __init__(self, plan, file):
        self.plan, self.file = plan, file


def local_scale_abs(go):
    scale = v3((go.transform or {}).get('m_LocalScale'), (1, 1, 1))
    return [abs(x) or 1.0 for x in scale]


def needs_split_trigger(go, c):
    """Jolt can't scale spheres/capsules non-uniformly, even when the shape node
    counter-scales, so such triggers get their own uniformly scaled Area3D child."""
    ax = local_scale_abs(go)
    return c in (135, 136) and max(ax) - min(ax) > 1e-6


def collider_spec(c, d, go, split=False):
    """Area3D collision shape child for a Unity collider. With split=True the shape
    sits under a Trigger area that already cancels the object's scale."""
    s = Spec('CollisionShape3D')
    center = v3(d.get('m_Center'))
    ax = local_scale_abs(go)
    if split:
        center = (center[0] * ax[0], center[1] * ax[1], center[2] * ax[2])
    pos = (center[0], center[1], -center[2])
    comp = [1.0, 1.0, 1.0] if split else ax
    if c == 65:
        size = v3(d.get('m_Size'), (1, 1, 1))
        s.set('transform', T3D([[1, 0, 0], [0, 1, 0], [0, 0, 1]], pos))
        s.set('shape', Sub('BoxShape3D', [('size', V3(*size))]))
    elif c == 135:
        # Unity scales a sphere collider uniformly by the largest axis; the shape
        # node cancels the object's own (possibly non-uniform) scale.
        r = float(d.get('m_Radius', 0.5)) * max(ax)
        s.set('transform', T3D([[1 / comp[0], 0, 0], [0, 1 / comp[1], 0], [0, 0, 1 / comp[2]]], pos))
        s.set('shape', Sub('SphereShape3D', [('radius', r)]))
    elif c == 136:
        direction = int(d.get('m_Direction', 1))
        others = [ax[i] for i in range(3) if i != direction]
        r = float(d.get('m_Radius', 0.5)) * max(others)
        h = max(float(d.get('m_Height', 2)) * ax[direction], 2 * r)
        rows = [[1 / comp[0], 0, 0], [0, 1 / comp[1], 0], [0, 0, 1 / comp[2]]]
        if direction == 0:
            rows = mat_mul(rows, [[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        elif direction == 2:
            rows = mat_mul(rows, [[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        s.set('transform', T3D(rows, pos))
        s.set('shape', Sub('CapsuleShape3D', [('radius', r), ('height', h)]))
    else:
        return None
    return s


def set_trigger_layers(spec, go, scripts):
    # The snail is on layer 2 and watches layer 1; everything else the reverse.
    player = go.tag == 'Player' or any(sc == 'Move.cs' for sc, _ in scripts)
    spec.set('collision_layer', 2 if player else 1)
    spec.set('collision_mask', 1 if player else 2)


def mesh_materials(spec, mr):
    mats = mr.get('m_Materials') or []
    ui_default = False
    for i, m in enumerate(mats):
        if isinstance(m, dict) and m.get('guid'):
            e = material(m['guid'])
            if e:
                spec.set('surface_material_override/%d' % i, e)
                ui_default |= e.path in UI_DEFAULT_MATS
    cast = int(mr.get('m_CastShadows', 1))
    spec.set('cast_shadow', 0 if ui_default else cast)


def go_specs(go, ctx):
    """Godot nodes for one GameObject: [(subpath, Spec)], [(signal, from, to, method)]."""
    if go.tcls == 224 or go.comp(223) is not None:
        if go.comp(20) is None:
            return ui_specs(go, ctx)
    plan = ctx.plan
    gpath = plan.path[id(go)]
    names = plan.comp_names[id(go)]
    t = go.transform or {}
    out, conns = [], []
    camera, light = go.comp(20), go.comp(108)
    mf, mr = go.comp(33), go.comp(23)
    scripts = [(script_info(d), d) for c, d in go.comps if c == 114 and script_info(d) in SCRIPTS]
    colliders = [(c, d) for c, d in go.comps if c in (65, 135, 136) and int(d.get('m_Enabled', 1))]
    trigger = bool(colliders) and (bool(scripts) or go.tag != 'Untagged')
    split = trigger and needs_split_trigger(go, colliders[0][0])
    area_path = gpath + ('Trigger',) if split else gpath
    mesh = None
    mesh_from_model = False
    if mf and mr and int(mr.get('m_Enabled', 1)):
        mm = mf.get('m_Mesh') or {}
        if mm.get('fileID') in BUILTIN_MESH and mm.get('guid', '').startswith('0000000000000000e'):
            mesh = builtin_mesh(mm['fileID'])
        elif mm.get('guid') and guid_path(mm['guid']):
            src = guid_path(mm['guid'])
            mesh = Ext('res://meshes/%s.res' % os.path.splitext(os.path.basename(src))[0], 'ArrayMesh')
            mesh_from_model = True

    if camera is not None:
        s = Spec('Camera3D')
        s.set('fov', float(camera.get('field of view', 60)))
        s.set('near', float(camera.get('near clip plane', 0.3)))
        s.set('far', float(camera.get('far clip plane', 1000)))
        if int(camera.get('m_Enabled', 1)) and go.active:
            s.set('current', True)
    elif light is not None:
        lt = int(light.get('m_Type', 1))
        s = Spec({0: 'SpotLight3D', 1: 'DirectionalLight3D', 2: 'OmniLight3D'}.get(lt, 'OmniLight3D'))
        s.set('light_color', Col(*col(light.get('m_Color'))))
        intensity = float(light.get('m_Intensity', 1))
        shadows = int((light.get('m_Shadows') or {}).get('m_Type', 0)) != 0
        if lt == 1:
            s.set('light_energy', intensity * LIGHT_DIRECTIONAL_SCALE)
            s.set('shadow_enabled', shadows)
        else:
            s.set('light_energy', intensity * LIGHT_LOCAL_SCALE)
            s.set('shadow_enabled', shadows)
            rng = float(light.get('m_Range', 10))
            if lt == 0:
                s.set('spot_range', rng)
                s.set('spot_attenuation', 2.0)
                s.set('spot_angle', float(light.get('m_SpotAngle', 30)) / 2.0)
            else:
                s.set('omni_range', rng)
                s.set('omni_attenuation', 2.0)
        if not int(light.get('m_Enabled', 1)):
            s.set('visible', False)
    elif trigger and not split:
        s = Spec('Area3D')
        set_trigger_layers(s, go, scripts)
    elif mesh is not None and not mesh_from_model:
        s = Spec('MeshInstance3D')
        s.set('mesh', mesh)
        mesh_materials(s, mr)
    else:
        s = Spec('Node3D')

    pos = v3(t.get('m_LocalPosition'))
    if go.tcls == 224 and (go.parent is None or go.parent.tcls != 224):
        # A RectTransform outside any canvas is placed by its anchored position.
        ap = v2(t.get('m_AnchoredPosition'))
        pos = (ap[0], ap[1], pos[2])
    s.set('transform', unity_trs(pos, q4(t.get('m_LocalRotation')), v3(t.get('m_LocalScale'), (1, 1, 1))))
    if not go.active:
        s.set('visible', False)
        s.set('process_mode', 4)
    if go.tag not in ('Untagged', None):
        s.groups.append(go.tag)
    out.append(((), s))

    if split:
        ts = Spec('Area3D')
        ax = local_scale_abs(go)
        ts.set('transform', T3D([[1 / ax[0], 0, 0], [0, 1 / ax[1], 0], [0, 0, 1 / ax[2]]], (0, 0, 0)))
        set_trigger_layers(ts, go, scripts)
        out.append((('Trigger',), ts))
        out.append((('Trigger', 'Collider'), collider_spec(colliders[0][0], colliders[0][1], go, split=True)))
    elif trigger:
        cs = collider_spec(colliders[0][0], colliders[0][1], go)
        if cs:
            out.append((('Collider',), cs))
    if mesh is not None and ((trigger and not split) or mesh_from_model):
        ms = Spec('MeshInstance3D')
        ms.set('mesh', mesh)
        if mesh_from_model:
            ms.set('transform', T3D(ROT_Y180, (0, 0, 0)))
        mesh_materials(ms, mr)
        out.append((('Mesh',), ms))

    if go.model:
        src = go.model
        ms = Spec()
        if src.lower().endswith('.obj'):
            ms.type = 'MeshInstance3D'
            p = res_asset(src)
            ms.set('transform', T3D(ROT_Y180, (0, 0, 0)))
            ms.set('mesh', Ext(p, 'ArrayMesh'))
            defaults = model_default_materials(src)
            surfaces = obj_surfaces(src)
            for i, sname in enumerate(surfaces):
                e = defaults.get(sname + 'Mat')
                if e:
                    ms.set('surface_material_override/%d' % i, e)
            for (target, slot), ref in go.model_mats.items():
                if isinstance(ref, dict) and ref.get('guid'):
                    surface = OBJ_RENDERER_SURFACE.get((src, target), slot)
                    ms.set('surface_material_override/%d' % surface, material(ref['guid']))
        else:
            p = fbx_import(src)
            ms.instance = Ext(p, 'PackedScene')
            ms.set('transform', model_wrapper_transform(p))
            if go.model_mats:
                warn('instance material overrides on FBX model %s ignored' % src)
        if not go.model_renderer_enabled:
            ms.set('visible', False)
        out.append((('Model',), ms))

    for c, d in go.comps:
        if c != 82:
            continue
        clip = guid_path((d.get('m_audioClip') or {}).get('guid'))
        a = Spec('AudioStreamPlayer')
        if clip:
            a.set('stream', audio(clip, bool(int(d.get('Loop', 0) or 0))))
        vol = float(d.get('m_Volume', 1))
        a.set('volume_db', Lit('%.4g' % (20 * __import__('math').log10(vol))) if vol > 0 else Lit('-80'))
        if float(d.get('m_Pitch', 1) or 1) != 1:
            a.set('pitch_scale', float(d['m_Pitch']))
        if int(d.get('m_PlayOnAwake', 0)) and int(d.get('m_Enabled', 1)):
            a.set('autoplay', True)
        out.append(((names[id(d)],), a))

    for sc, d in scripts:
        add_script(out, go, gpath, sc, d, names, ctx)
        if sc in TRIGGER_SCRIPTS and trigger:
            conns.append(('area_entered', area_path, gpath + (names[id(d)],), '_on_trigger_enter'))
    return out, conns


def add_script(out, go, gpath, sc, d, names, ctx):
    file, cls, fields = SCRIPTS[sc]
    cname = names[id(d)]
    s = Spec('Node')
    s.set('script', Ext('res://scripts/%s.gd' % file, 'Script'))
    s.set('enabled', bool(int(d.get('m_Enabled', 1))))
    spath = gpath + (cname,)
    for uf, gf in fields.items():
        if uf not in d:
            continue
        val = d[uf]
        if isinstance(val, Ref) or val is None or (isinstance(val, dict) and 'fileID' in val):
            tp = ctx.plan.ref_path(val) if isinstance(val, Ref) else None
            s.set(gf, NP(rel_path(spath, tp)) if tp else NP(''))
        elif isinstance(val, dict):
            s.set(gf, V3(*v3(val)))
        elif gf == 'page':
            s.set(gf, int(val))
        else:
            s.set(gf, float(val))
    out.append(((cname,), s))


# --- UI ---------------------------------------------------------------------

# Control.LayoutPreset values by (left, top, right, bottom) anchors.
LAYOUT_PRESETS = {(0, 0, 0, 0): 0, (1, 0, 1, 0): 1, (0, 1, 0, 1): 2, (1, 1, 1, 1): 3,
                  (0, .5, 0, .5): 4, (.5, 0, .5, 0): 5, (1, .5, 1, .5): 6, (.5, 1, .5, 1): 7,
                  (.5, .5, .5, .5): 8, (0, 0, 0, 1): 9, (0, 0, 1, 0): 10, (1, 0, 1, 1): 11,
                  (0, 1, 1, 1): 12, (0, .5, 1, .5): 13, (.5, 0, .5, 1): 14, (0, 0, 1, 1): 15}


def anchors_preset(anchors):
    for k, v in LAYOUT_PRESETS.items():
        if all(abs(a - b) < 1e-6 for a, b in zip(anchors, k)):
            return v
    return -1


def ui_layout(spec, go, ctx):
    t = go.transform or {}
    plan = ctx.plan
    if id(go) in plan.scroll_content:
        # Content of a scroll view: laid out by the ScrollContainer.
        spec.set('custom_minimum_size', V2(0, v2(t.get('m_SizeDelta'))[1]))
        spec.set('layout_mode', 2)
        spec.set('size_flags_horizontal', 3)
        spec.set('size_flags_vertical', 0)
        return
    amin, amax = v2(t.get('m_AnchorMin')), v2(t.get('m_AnchorMax'))
    pos, size = v2(t.get('m_AnchoredPosition')), v2(t.get('m_SizeDelta'))
    piv = v2(t.get('m_Pivot'), (0.5, 0.5))
    omin = (pos[0] - size[0] * piv[0], pos[1] - size[1] * piv[1])
    omax = (pos[0] + size[0] * (1 - piv[0]), pos[1] + size[1] * (1 - piv[1]))
    anchors = (amin[0], 1 - amax[1], amax[0], 1 - amin[1])
    spec.set('layout_mode', 1)
    # Godot derives anchors_preset from the anchors; if it isn't written, it reads
    # as changed and an editor save writes it into the scene, and setting a preset
    # on load resets the offsets. So write it, before the anchors and offsets.
    spec.set('anchors_preset', anchors_preset(anchors))
    spec.set('anchor_left', anchors[0])
    spec.set('anchor_top', anchors[1])
    spec.set('anchor_right', anchors[2])
    spec.set('anchor_bottom', anchors[3])
    spec.set('offset_left', omin[0])
    spec.set('offset_top', -omax[1])
    spec.set('offset_right', omax[0])
    spec.set('offset_bottom', -omin[1])
    spec.set('grow_horizontal', 2)
    spec.set('grow_vertical', 2)
    spec.set('pivot_offset_ratio', V2(piv[0], 1 - piv[1]))
    s = v3(t.get('m_LocalScale'), (1, 1, 1))
    spec.set('scale', V2(s[0], s[1]))
    q = q4(t.get('m_LocalRotation'))
    import math
    angle = 2 * math.atan2(q[2], q[3])
    spec.set('rotation', -angle)


def font_resource(style):
    f = font()
    if style == 0:
        return f
    props = [('base_font', f)]
    if style in (1, 3):
        props.append(('variation_embolden', 0.6))
    if style in (2, 3):
        props.append(('variation_transform', Lit('Transform2D(1, 0, 0.2, 1, 0, 0)')))
    return Sub('FontVariation', props)


RICH = re.compile(r'</?(b|i|color|size)(=[^>]*)?>')


def to_bbcode(text):
    def rep(m):
        tag, arg = m.group(1), m.group(2) or ''
        close = m.group(0).startswith('</')
        name = {'b': 'b', 'i': 'i', 'color': 'color', 'size': 'font_size'}[tag]
        return '[/%s]' % name if close else '[%s%s]' % (name, arg)
    return RICH.sub(rep, text)


CHEWY_LINE_HEIGHT = 117 / 90  # Godot's FontFile.get_height() per pixel of font size
_fonts = {}


def wrap_line_starts(plain, font, width, extra_advance=0.0):
    """Index where each line starts under word wrapping at the given width."""
    starts, line_start, last_space = [0], 0, -1
    for i, ch in enumerate(plain):
        if ch == '\n':
            line_start, last_space = i + 1, -1
            starts.append(line_start)
            continue
        if ch == ' ':
            last_space = i
        segment = plain[line_start:i + 1]
        if font.getlength(segment) + extra_advance * len(segment) > width and last_space > line_start:
            line_start, last_space = last_space + 1, -1
            starts.append(line_start)
    return starts


def truncate_lines(text, size, go, bold):
    """Unity's 'Truncate' vertical overflow drops whole lines that don't fit the
    rect. Godot lets them spill, so cut the text at conversion time instead."""
    from PIL import ImageFont
    t = go.transform or {}
    if v2(t.get('m_AnchorMin')) != v2(t.get('m_AnchorMax')) or not text:
        return text  # stretched rects depend on the parent's size
    width, height = v2(t.get('m_SizeDelta'))
    max_lines = int(height // (size * CHEWY_LINE_HEIGHT))
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(os.path.join(UNITY, 'Assets/Fonts/Chewy-Regular.ttf'), size)
    plain, index = '', []  # text without markup, and each plain char's index in `text`
    for m in re.finditer(r'<[^>]*>|.', text, re.S):
        if not RICH.fullmatch(m.group(0)):
            plain += m.group(0)
            index.append(m.start())
    # Chewy has no bold face; Unity emboldens it, widening each glyph by size / 24.
    starts = wrap_line_starts(plain, _fonts[size], width, size / 24 if bold else 0.0)
    if len(starts) <= max_lines:
        return text
    kept = text[:index[starts[max_lines]]]
    kept = re.sub(r'(\s|<(b|i|color|size)(=[^>]*)?>)+$', '', kept)  # drop tags opened at the cut
    open_tags = []
    for m in RICH.finditer(kept):
        if m.group(0).startswith('</'):
            if m.group(1) in open_tags:
                open_tags.remove(m.group(1))
        else:
            open_tags.append(m.group(1))
    return kept + ''.join('</%s>' % tag for tag in reversed(open_tags))


def text_specs(spec, go, d):
    fd = d.get('m_FontData') or {}
    text = (d.get('m_Text') or '').replace('\r\n', '\n')
    if int(fd.get('m_VerticalOverflow', 0)) == 0:
        text = truncate_lines(text, int(fd.get('m_FontSize', 14)), go, int(fd.get('m_FontStyle', 0)) in (1, 3))
    # Message texts are rich so scenes can override them with markup (e.g. End's title).
    has_message = any(script_info(sd) == 'Message.cs' for c, sd in go.comps if c == 114)
    rich = int(d.get('m_RichText', 1)) and (bool(RICH.search(text)) or has_message)
    style = int(fd.get('m_FontStyle', 0))
    size = int(fd.get('m_FontSize', 14))
    align = int(fd.get('m_Alignment', 0))
    color = Col(*col(d.get('m_Color')))
    halign, valign = align % 3, align // 3
    shadow = ui_comp(go, 'Shadow')
    outline = ui_comp(go, 'Outline')
    has_font = bool((fd.get('m_Font') or {}).get('guid'))
    if rich:
        spec.type = 'RichTextLabel'
        spec.set('bbcode_enabled', True)
        spec.set('text', to_bbcode(text))
        spec.set('scroll_active', False)
        if has_font:
            spec.set('theme_override_fonts/normal_font', font_resource(style))
            spec.set('theme_override_fonts/italics_font', font_resource(style | 2))
            spec.set('theme_override_fonts/bold_font', font_resource(style | 1))
            spec.set('theme_override_fonts/bold_italics_font', font_resource(3))
        for k in ('normal', 'italics', 'bold', 'bold_italics'):
            spec.set('theme_override_font_sizes/%s_font_size' % k, size)
        spec.set('theme_override_colors/default_color', color)
    else:
        spec.type = 'Label'
        spec.set('text', text)
        if has_font:
            spec.set('theme_override_fonts/font', font_resource(style))
        spec.set('theme_override_font_sizes/font_size', size)
        spec.set('theme_override_colors/font_color', color)
    spec.set('horizontal_alignment', halign)
    spec.set('vertical_alignment', 2 - valign)
    spec.set('autowrap_mode', 3 if int(fd.get('m_HorizontalOverflow', 0)) == 0 else 0)
    spec.set('mouse_filter', 2)
    for eff in (shadow, outline):
        if eff is not None and int(eff.get('m_Enabled', 1)):
            dist = v2(eff.get('m_EffectDistance'), (1, -1))
            ecol = Col(*col(eff.get('m_EffectColor')))
            if eff is shadow:
                spec.set('theme_override_colors/font_shadow_color', ecol)
                spec.set('theme_override_constants/shadow_offset_x', int(round(dist[0])))
                spec.set('theme_override_constants/shadow_offset_y', int(round(-dist[1])))
            else:
                spec.set('theme_override_colors/font_outline_color', ecol)
                spec.set('theme_override_constants/outline_size', int(round(abs(dist[0]) * 2)))
    if not int(d.get('m_Enabled', 1)):
        spec.set('visible', False)


def image_style(img):
    """StyleBoxFlat for an Image without a texture asset (plain or Unity built-in sprite)."""
    sp = (img.get('m_Sprite') or {})
    c = Col(*col(img.get('m_Color')))
    props = [('bg_color', c)]
    if sp.get('fileID') in (10905, 10907, 10917):
        props += [('corner_radius_top_left', 6), ('corner_radius_top_right', 6),
                  ('corner_radius_bottom_right', 6), ('corner_radius_bottom_left', 6)]
    return Sub('StyleBoxFlat', props)


def sprite_texture(img):
    sp = img.get('m_Sprite') or {}
    p = guid_path(sp.get('guid')) if sp.get('guid') else None
    if p and p.startswith('Assets/'):
        return texture(p)
    return None


def ui_specs(go, ctx):
    plan = ctx.plan
    gpath = plan.path[id(go)]
    names = plan.comp_names[id(go)]
    out, conns = [], []
    s = Spec('Control')
    if go.comp(223) is not None:
        s.type = 'CanvasLayer'
    else:
        text = ui_comp(go, 'Text')
        img = ui_comp(go, 'Image')
        btn = ui_comp(go, 'Button')
        scroll = ui_comp(go, 'ScrollRect')
        if scroll is not None:
            s.type = 'ScrollContainer'
            if img is not None and int(img.get('m_Enabled', 1)):
                s.set('theme_override_styles/panel', image_style(img))
            if not int(scroll.get('m_Horizontal', 1)):
                s.set('horizontal_scroll_mode', 0)
            if not int(scroll.get('m_Vertical', 1)):
                s.set('vertical_scroll_mode', 0)
        elif btn is not None:
            s.type = 'Button'
            s.set('focus_mode', 0)
            s.set('script', Ext('res://scripts/core/ui_button.gd', 'Script'))
            if img is not None:
                tex = sprite_texture(img)
                if tex:
                    s.set('texture', tex)
                elif (img.get('m_Sprite') or {}).get('fileID') in (10905, 10907):
                    s.set('rounded', True)
                s.set('image_color', Col(*col(img.get('m_Color'))))
                s.set('image_enabled', bool(int(img.get('m_Enabled', 1))))
            else:
                s.set('image_enabled', False)
            cb = btn.get('m_Colors') or {}
            if int(btn.get('m_Transition', 1)) == 1:
                s.set('normal_color', Col(*col(cb.get('m_NormalColor'))))
                s.set('highlighted_color', Col(*col(cb.get('m_HighlightedColor'))))
                s.set('pressed_color', Col(*col(cb.get('m_PressedColor'))))
            s.set('button_enabled', bool(int(btn.get('m_Enabled', 1))))
            for call in (btn.get('m_OnClick') or {}).get('m_PersistentCalls', {}).get('m_Calls') or []:
                c = ui_call(call, plan)
                if c:
                    conns.append(('pressed', gpath, c[0], c[1]))
            trig = ui_comp(go, 'EventTrigger')
            if trig is not None:
                for dl in trig.get('m_Delegates') or []:
                    sig = {2: 'button_down', 3: 'button_up'}.get(int(dl.get('eventID', -1)))
                    for call in (dl.get('callback') or {}).get('m_PersistentCalls', {}).get('m_Calls') or []:
                        c = ui_call(call, plan)
                        if c and sig:
                            conns.append((sig, gpath, c[0], c[1]))
                        elif c:
                            warn('unsupported EventTrigger id %s on %s' % (dl.get('eventID'), go.name))
        elif text is not None:
            text_specs(s, go, text)
        elif img is not None:
            tex = sprite_texture(img)
            if tex:
                s.type = 'TextureRect'
                s.set('texture', tex)
                s.set('expand_mode', 1)
                s.set('stretch_mode', 5 if int(img.get('m_PreserveAspect', 0)) else 0)
                s.set('self_modulate', Col(*col(img.get('m_Color'))))
            elif (img.get('m_Sprite') or {}).get('fileID'):
                s.type = 'Panel'
                s.set('theme_override_styles/panel', image_style(img))
            else:
                s.type = 'ColorRect'
                s.set('color', Col(*col(img.get('m_Color'))))
            if not int(img.get('m_Enabled', 1)):
                s.set('self_modulate', Col(1, 1, 1, 0))
            s.set('mouse_filter', 0 if int(img.get('m_RaycastTarget', 1)) else 2)
        else:
            s.set('mouse_filter', 2)
        ui_layout(s, go, ctx)
    if not go.active:
        s.set('visible', False)
        s.set('process_mode', 4)
    if go.tag not in ('Untagged', None):
        s.groups.append(go.tag)
    out.append(((), s))
    for c, d in go.comps:
        if c == 114 and script_info(d) in SCRIPTS:
            add_script(out, go, gpath, script_info(d), d, names, ctx)
    return out, conns


def ui_call(call, plan):
    target = call.get('m_Target')
    method = call.get('m_MethodName')
    if not isinstance(target, Ref) or not method:
        return None
    tp = plan.ref_path(target)
    if tp is None:
        return None
    return tp, snake(method)


# --- emission ---------------------------------------------------------------

# Unity rendered in gamma space; these bring Godot's linear lighting close to it.
LIGHT_DIRECTIONAL_SCALE = 1.1
LIGHT_LOCAL_SCALE = 1.1


def prefab_res(src):
    return 'res://prefabs/%s.tscn' % os.path.splitext(os.path.basename(src))[0]


def collect_specs(go, ctx, base, belongs):
    """Specs and connections for go's subtree (GOs where belongs(g)), keyed relative to base."""
    specs, conns = [], []

    def walk(g):
        if not belongs(g):
            return
        gp = ctx.plan.path[id(g)]
        sp, cs = go_specs(g, ctx)
        for sub, s in sp:
            specs.append((gp[len(base):] + sub, s))
        for sig, frm, to, method in cs:
            rel_to = to[len(base):] if to[:len(base)] == base else ('<outside>',) + to
            conns.append(((sig, frm[len(base):], rel_to, method), (sig, frm, to, method)))
        for k in ctx.plan.children[id(g)]:
            walk(k)
    walk(go)
    return specs, conns


class Emitter:
    def __init__(self, src, w, scene_name=None):
        self.src, self.w, self.scene_name = src, w, scene_name
        self.is_scene = scene_name is not None
        self.roots, _ = instantiate(src)
        self.plan = Plan()
        top = [r for r in self.roots if not is_skipped(r)]
        if self.is_scene:
            used = set()
            for r in top:
                self.plan.assign(r, (), used)
        else:
            top = top[:1]
            self.plan.assign(top[0], (), set(), is_root=True)
        self.top = top
        self.ctx = Ctx(self.plan, src)

    def parent_str(self, path):
        if not self.is_scene and not path:
            return None
        return '.' if len(path) <= 1 else '/'.join(path[:-1])

    @staticmethod
    def path_str(path):
        return '/'.join(path) if path else '.'

    def node_name(self, path, go=None):
        if path:
            return path[-1]
        return safe_name(go.name) if go is not None else self.scene_name

    def write_full(self, path, s, go=None):
        props = [(k, v) for k, v in s.props if DEFAULTS.get(k) != canon(v)]
        self.w.node(self.node_name(path, go), None if s.instance else s.type, self.parent_str(path),
                    s.instance, props, s.groups)

    def emit(self, g):
        gp = self.plan.path[id(g)]
        o = g.owners[-1] if g.owners else None
        if o and o[0] == self.src and o[2] is g and not g.model:
            self.emit_instance(g, o)
            return
        specs, conns = go_specs(g, self.ctx)
        for sub, s in specs:
            self.write_full(gp + sub, s, g if not sub else None)
        for sig, frm, to, method in conns:
            self.w.connection(sig, self.path_str(frm), self.path_str(to), method)
        for k in self.plan.children[id(g)]:
            self.emit(k)

    def emit_instance(self, g, o):
        _, fid, _, psrc = o
        gp = self.plan.path[id(g)]

        def belongs(x):
            return bool(x.owners) and x.owners[-1][0] == self.src and x.owners[-1][1] == fid

        inst_specs, inst_conns = collect_specs(g, self.ctx, gp, belongs)
        # The prefab on its own, to diff the instance against.
        p_roots, _ = instantiate(psrc)
        p_plan = Plan()
        p_plan.assign(p_roots[0], (), set(), is_root=True)
        p_specs, p_conns = collect_specs(p_roots[0], Ctx(p_plan, psrc), (), lambda x: True)
        pmap = dict(p_specs)

        def mark_editable(rel):
            # The instance itself, plus any prefab nested inside it on the way down.
            self.w.editable(self.path_str(gp))
            for i in range(1, len(rel)):
                nested = pmap.get(rel[:i])
                if nested is not None and nested.instance is not None:
                    self.w.editable(self.path_str(gp + rel[:i]))

        for rel, s in inst_specs:
            path = gp + rel
            ps = pmap.get(rel)
            if rel == ():
                pprops = {k: canon(v) for k, v in ps.props}
                props = [(k, v) for k, v in s.props if k == 'transform' or pprops.get(k) != canon(v)]
                self.w.node(self.node_name(path, g), None, self.parent_str(path),
                            Ext(prefab_res(psrc), 'PackedScene'), props, None)
            elif ps is None or ps.type != s.type or canon(ps.instance) != canon(s.instance):
                if ps is not None:
                    warn('%s: node %s replaced in instance of %s' % (self.src, '/'.join(rel), psrc))
                    mark_editable(rel)
                self.write_full(path, s)
            else:
                pprops = {k: canon(v) for k, v in ps.props}
                props = [(k, v) for k, v in s.props if pprops.get(k) != canon(v)]
                if props:
                    mark_editable(rel)
                    self.w.node(path[-1], None, self.parent_str(path), None, props, None)
        pconn = set(c[0] for c in p_conns)
        for rel, (sig, frm, to, method) in inst_conns:
            if rel not in pconn:
                self.w.connection(sig, self.path_str(frm), self.path_str(to), method)

        # GameObjects this file added under the instance.
        def added(x):
            for k in self.plan.children[id(x)]:
                if belongs(k):
                    added(k)
                else:
                    self.emit(k)
        added(g)

    def run(self):
        if self.is_scene:
            self.w.node(self.scene_name, 'Node3D', None, None, [], None)
        for r in self.top:
            self.emit(r)


def _active_in_hierarchy(g):
    while g is not None:
        if not g.active:
            return False
        g = g.parent
    return True


def scene_has_pp(roots):
    """True when the rendering camera has a PostProcessLayer."""
    for r in roots:
        for g in r.walk():
            cam = g.comp(20)
            if cam is not None and int(cam.get('m_Enabled', 1)) and _active_in_hierarchy(g):
                if any(c == 114 and ui_kind_of(d) == 'PPLayer' for c, d in g.comps):
                    return True
    return False


# Scenes whose fog is kept in the environment but switched off.
FOGLESS = re.compile(r'^Level(\d+|Select)$')


def environment(src, pp, fog=True):
    docs = load_docs(src)
    rs = next(d['data'] for d in docs.values() if d['cls'] == 104)
    props = [('background_mode', 2),
             ('sky', Sub('Sky', [('sky_material', skybox(rs['m_SkyboxMaterial']['guid']))])),
             ('ambient_light_source', 3),
             ('ambient_light_energy', float(rs.get('m_AmbientIntensity', 1))),
             ('reflected_light_source', 2)]
    if pp:  # Bloom + ACES tonemapping from the post-processing profile
        props += [('tonemap_mode', 3),
                  ('glow_enabled', True), ('glow_intensity', 0.6), ('glow_bloom', 0.05),
                  ('glow_hdr_threshold', 1.0), ('glow_blend_mode', 0)]
    if int(rs.get('m_Fog', 0)):
        # Unity's exponential-squared fog, 1 - exp(-(density * d)^2), is matched to
        # within a few percent over the distances the camera sees by Godot's depth
        # fog, (d / end)^curve, with end = 1.45 / density and curve = 1.35.
        density = float(rs.get('m_FogDensity', 0.01))
        props += [('fog_enabled', fog), ('fog_mode', 1),
                  ('fog_light_color', Col(*col(rs.get('m_FogColor')))),
                  ('fog_density', 1.0), ('fog_depth_begin', 0.0), ('fog_depth_end', 1.45 / density),
                  ('fog_depth_curve', 1.35), ('fog_sky_affect', 0.0), ('fog_sun_scatter', 0.0)]
    return Sub('Environment', props)


def emit_scene(name):
    src = 'Assets/Scenes/%s.unity' % name
    w = Writer()
    em = Emitter(src, w, name)
    em.run()
    pp = scene_has_pp(em.roots)
    w.node('WorldEnvironment', 'WorldEnvironment', '.', None, [('environment', environment(src, pp, fog=not FOGLESS.match(name)))])
    if pp:  # Vignette from the post-processing profile, drawn under the UI
        w.node('PostProcessVignette', 'CanvasLayer', '.', None, [('layer', -1)])
        w.node('Vignette', 'ColorRect', 'PostProcessVignette', None, [
            ('material', Sub('ShaderMaterial', [('shader', Ext('res://shaders/vignette.gdshader', 'Shader'))])),
            ('anchors_preset', 15), ('anchor_right', 1.0), ('anchor_bottom', 1.0),
            ('grow_horizontal', 2), ('grow_vertical', 2), ('mouse_filter', 2)])
    path = os.path.join(GODOT, 'scenes', name + '.tscn')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', newline='\n').write(w.scene_text())


def emit_prefab(src):
    w = Writer()
    Emitter(src, w).run()
    path = os.path.join(GODOT, prefab_res(src)[len('res://'):])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', newline='\n').write(w.scene_text())


def used_prefabs():
    seen = []

    def visit(path):
        for d in load_docs(path).values():
            if d['cls'] == 1001:
                p = guid_path(d['data']['m_SourcePrefab']['guid'])
                if p.endswith('.prefab') and p not in seen:
                    seen.append(p)
                    visit(p)
    for s in SCENES:
        visit('Assets/Scenes/%s.unity' % s)
    return seen


def main():
    builtin_meshes()
    for p in used_prefabs():
        roots, _ = instantiate(p)
        if not is_skipped(roots[0]):
            emit_prefab(p)
    for s in SCENES:
        emit_scene(s)
    for m in warnings:
        print('WARNING:', m)


if __name__ == '__main__':
    main()
