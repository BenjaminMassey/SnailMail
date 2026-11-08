"""Godot text resource (.tscn/.tres) values and writer."""
import math


def fnum(x):
    if isinstance(x, bool):
        return 'true' if x else 'false'
    if isinstance(x, int):
        return str(x)
    if abs(x) < 1e-9:
        return '0'
    s = '%.7g' % x
    return s


class Val:
    def fmt(self, w):
        raise NotImplementedError

    def canon(self):
        return self.fmt(None)


class Lit(Val):
    def __init__(self, s):
        self.s = s

    def fmt(self, w):
        return self.s


class V2(Val):
    def __init__(self, x, y):
        self.v = (x, y)

    def fmt(self, w):
        return 'Vector2(%s, %s)' % tuple(fnum(float(a)) for a in self.v)


class V3(Val):
    def __init__(self, x, y, z):
        self.v = (x, y, z)

    def fmt(self, w):
        return 'Vector3(%s, %s, %s)' % tuple(fnum(float(a)) for a in self.v)


class V4(Val):
    def __init__(self, x, y, z, w_):
        self.v = (x, y, z, w_)

    def fmt(self, w):
        return 'Vector4(%s, %s, %s, %s)' % tuple(fnum(float(a)) for a in self.v)


class Col(Val):
    def __init__(self, r, g, b, a=1.0):
        self.v = (r, g, b, a)

    def fmt(self, w):
        return 'Color(%s, %s, %s, %s)' % tuple(fnum(float(a)) for a in self.v)


class T3D(Val):
    """rows: 3x3 basis rows, origin: 3-tuple."""

    def __init__(self, rows, origin):
        self.rows, self.origin = rows, origin

    def fmt(self, w):
        nums = [self.rows[i][j] for i in range(3) for j in range(3)] + list(self.origin)
        return 'Transform3D(%s)' % ', '.join(fnum(float(n)) for n in nums)


class NP(Val):
    def __init__(self, path):
        self.path = path

    def fmt(self, w):
        return 'NodePath("%s")' % self.path


class Ext(Val):
    def __init__(self, path, type):
        self.path, self.type = path, type

    def fmt(self, w):
        if w is None:
            return 'Ext(%s)' % self.path
        return 'ExtResource("%s")' % w.ext_id(self)


class Sub(Val):
    def __init__(self, type, props):
        self.type = type
        self.props = props  # ordered list of (key, value)

    def fmt(self, w):
        if w is None:
            return 'Sub(%s;%s)' % (self.type, ';'.join('%s=%s' % (k, fmt_value(v, None)) for k, v in self.props))
        return 'SubResource("%s")' % w.sub_id(self)


class Arr(Val):
    def __init__(self, items, typed=None):
        self.items, self.typed = items, typed

    def fmt(self, w):
        inner = ', '.join(fmt_value(v, w) for v in self.items)
        if self.typed:
            return '%s([%s])' % (self.typed, inner)
        return '[%s]' % inner


def fmt_value(v, w):
    if isinstance(v, Val):
        return v.fmt(w)
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return fnum(v)
    if isinstance(v, str):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if v is None:
        return 'null'
    raise TypeError(v)


def canon(v):
    return fmt_value(v, None)


class Writer:
    def __init__(self):
        self.exts = []  # (id, Ext)
        self.ext_by_path = {}
        self.subs = []  # (id, Sub, body)
        self.sub_by_canon = {}
        self.body = []
        self.conns = []
        # Instances whose children this file overrides. Godot only keeps such
        # overrides on save when the instance has "Editable Children" on.
        self.editables = []

    def ext_id(self, e):
        if e.path not in self.ext_by_path:
            i = '%d_%s' % (len(self.exts) + 1, ''.join(c for c in e.path.split('/')[-1] if c.isalnum())[:5].lower())
            self.ext_by_path[e.path] = i
            self.exts.append((i, e))
        return self.ext_by_path[e.path]

    def sub_id(self, s):
        c = canon(s)
        if c not in self.sub_by_canon:
            lines = ['%s = %s' % (k, fmt_value(v, self)) for k, v in s.props]  # registers nested resources first
            i = '%s_%d' % (s.type, len(self.subs) + 1)
            self.sub_by_canon[c] = i
            self.subs.append((i, s, lines))
        return self.sub_by_canon[c]

    def props(self, props):
        return ['%s = %s' % (k, fmt_value(v, self)) for k, v in props]

    def node(self, name, type=None, parent=None, instance=None, props=(), groups=None):
        attrs = ['name="%s"' % name]
        if type:
            attrs.append('type="%s"' % type)
        if parent is not None:
            attrs.append('parent="%s"' % parent)
        if instance is not None:
            attrs.append('instance=%s' % instance.fmt(self))
        node_paths = [k for k, v in props if isinstance(v, NP)]
        if node_paths:  # exported Node references are stored as paths
            attrs.append('node_paths=PackedStringArray(%s)' % ', '.join('"%s"' % k for k in node_paths))
        if groups:
            attrs.append('groups=[%s]' % ', '.join('"%s"' % g for g in groups))
        lines = self.props(props)
        self.body.append('[node %s]\n%s' % (' '.join(attrs), ''.join(l + '\n' for l in lines)))

    def editable(self, path):
        if path not in self.editables:
            self.editables.append(path)

    def connection(self, signal, frm, to, method):
        self.conns.append('[connection signal="%s" from="%s" to="%s" method="%s"]\n' % (signal, frm, to, method))

    def _header_resources(self):
        out = []
        for i, e in self.exts:
            out.append('[ext_resource type="%s" path="%s" id="%s"]\n' % (e.type, e.path, i))
        for i, s, lines in self.subs:
            out.append('[sub_resource type="%s" id="%s"]\n%s' % (s.type, i, ''.join(l + '\n' for l in lines)))
        return out

    def scene_text(self):
        head = '[gd_scene format=3]\n'
        conns = [''.join(self.conns)] if self.conns else []
        edits = [''.join('[editable path="%s"]\n' % p for p in self.editables)] if self.editables else []
        return '\n'.join([head] + self._header_resources() + self.body + conns + edits)

    def resource_text(self, type, props, script_class=None):
        lines = self.props(props)  # registers resources
        head = '[gd_resource type="%s"%s format=3]\n' % (type, ' script_class="%s"' % script_class if script_class else '')
        res = '[resource]\n' + ''.join(l + '\n' for l in lines)
        return '\n'.join([head] + self._header_resources() + [res])


# --- math -----------------------------------------------------------------

def quat_rows(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_vec(a, v):
    return tuple(sum(a[i][k] * v[k] for k in range(3)) for i in range(3))


def mat_inv(m):
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
            [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
            [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]]


def trs(pos, quat, scale):
    r = quat_rows(quat)
    rows = [[r[i][j] * scale[j] for j in range(3)] for i in range(3)]
    return T3D(rows, pos)


def unity_trs(p, q, s):
    """Unity local TRS (left-handed) -> Godot Transform3D (Z flipped)."""
    return trs((p[0], p[1], -p[2]), (-q[0], -q[1], q[2], q[3]), s)


ROT_Y180 = [[-1, 0, 0], [0, 1, 0], [0, 0, -1]]
