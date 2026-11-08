"""Load Unity YAML scenes/prefabs and resolve prefab instances into a GameObject tree.

Every call to instantiate() builds a fresh tree. Object references ({fileID: N})
are resolved to Ref objects pointing at live GO/component instances, and every GO
created through a prefab instance records (file, instance id, instance root, source)
in `owners`, innermost first.
"""
import copy, os, re, yaml

# The Unity project sits next to the Godot project (override with SNAILMAIL_UNITY).
UNITY = os.environ.get('SNAILMAIL_UNITY', os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'SnailMail-Unity')))
MASK = 0x7FFFFFFFFFFFFFFF

CLASS = {1: 'GameObject', 4: 'Transform', 224: 'RectTransform', 20: 'Camera', 23: 'MeshRenderer',
         33: 'MeshFilter', 54: 'Rigidbody', 64: 'MeshCollider', 65: 'BoxCollider', 82: 'AudioSource',
         81: 'AudioListener', 108: 'Light', 114: 'MonoBehaviour', 135: 'SphereCollider',
         136: 'CapsuleCollider', 222: 'CanvasRenderer', 223: 'Canvas', 1001: 'PrefabInstance'}

GUIDS = {}
for root, _, files in os.walk(os.path.join(UNITY, 'Assets')):
    for f in files:
        if f.endswith('.meta'):
            p = os.path.join(root, f)
            with open(p, encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    if line.startswith('guid:'):
                        GUIDS[line.split()[1]] = os.path.relpath(p[:-5], UNITY).replace('\\', '/')
                        break


def guid_path(g):
    return GUIDS.get(g)


HDR = re.compile(r'^--- !u!(\d+) &(-?\d+)( stripped)?', re.M)
_cache = {}


def load_docs(path):
    if path in _cache:
        return _cache[path]
    raw = open(os.path.join(UNITY, path), 'rb').read()
    try:
        txt = raw.decode('utf-8')
    except UnicodeDecodeError:
        txt = raw.decode('latin-1')
    docs = {}
    ms = list(HDR.finditer(txt))
    for i, m in enumerate(ms):
        body = txt[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(txt)]
        data = yaml.safe_load(body)
        (_, d), = data.items()
        docs[int(m.group(2))] = {'cls': int(m.group(1)), 'data': d or {}, 'stripped': bool(m.group(3))}
    _cache[path] = docs
    return docs


class Ref:
    """Resolved object reference: kind is 'go', 'tr' or 'comp'."""

    def __init__(self, kind, go, comp=None, cls=None):
        self.kind, self.go, self.comp, self.cls = kind, go, comp, cls


class GO:
    def __init__(self, name):
        self.name = name
        self.active = True
        self.tag = 'Untagged'
        self.comps = []  # list of [cls, data]
        self.transform = None
        self.tcls = 4
        self.children = []
        self.parent = None
        self.model = None  # source model path when this GO is a model (fbx/obj) instance root
        self.model_mats = {}  # material slot -> material ref, from instance modifications
        self.model_renderer_enabled = True
        self.model_root_transform = None
        self.owners = []  # [(file, instance fileID, instance root GO, source path)], innermost first

    def comp(self, cls):
        for c, d in self.comps:
            if c == cls:
                return d
        return None

    def comps_of(self, cls):
        return [d for c, d in self.comps if c == cls]

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def set_path(obj, path, value):
    parts = path.split('.')
    cur = obj
    i = 0
    while i < len(parts):
        p = parts[i]
        if p == 'Array':
            nxt = parts[i + 1]
            if nxt == 'size':
                n = int(value)
                while len(cur) < n:
                    cur.append(None)
                del cur[n:]
                return
            idx = int(re.match(r'data\[(\d+)\]', nxt).group(1))
            while len(cur) <= idx:
                cur.append({})
            if i + 1 == len(parts) - 1:
                cur[idx] = value
                return
            if cur[idx] is None:
                cur[idx] = {}
            cur = cur[idx]
            i += 2
            continue
        if i == len(parts) - 1:
            cur[p] = value
            return
        if not isinstance(cur.get(p), (dict, list)):
            cur[p] = [] if (i + 1 < len(parts) and parts[i + 1] == 'Array') else {}
        cur = cur[p]
        i += 1


def _resolve_refs(obj, idmap):
    """Replace {fileID: N} (no guid) dicts inside component data with Ref objects."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, dict) and set(v.keys()) == {'fileID'} and v['fileID']:
                e = idmap.get(v['fileID'])
                obj[k] = Ref(*e) if e else None
            elif isinstance(v, dict) and set(v.keys()) == {'fileID'}:
                obj[k] = None
            else:
                _resolve_refs(v, idmap)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, dict) and set(v.keys()) == {'fileID'} and v['fileID']:
                e = idmap.get(v['fileID'])
                obj[i] = Ref(*e) if e else None
            elif isinstance(v, dict) and set(v.keys()) == {'fileID'}:
                obj[i] = None
            else:
                _resolve_refs(v, idmap)


def apply_model_mod(g, target, pp, m):
    """Apply a modification aimed at an object inside model instance g."""
    if pp == 'm_Name':
        g.name = str(m['value'])
    elif pp == 'm_IsActive':
        g.active = bool(int(m['value']))
    elif pp.startswith('m_Local') and target == g.model_root_transform:
        set_path(g.transform, pp, m['value'])
    elif pp.startswith('m_Materials.Array.data['):
        slot = int(re.search(r'\[(\d+)\]', pp).group(1))
        g.model_mats[(target, slot)] = m.get('objectReference')
    elif pp == 'm_Enabled':
        g.model_renderer_enabled = bool(int(m['value']))


def instantiate(path):
    """Return (roots, idmap); idmap maps local fileIDs -> (kind, GO, compdata, cls)."""
    docs = load_docs(path)
    idmap = {}
    gos = {}
    own_comps = []
    added_comps = []  # components this file adds to objects inside prefab instances
    for fid, doc in docs.items():
        if doc['stripped'] or doc['cls'] != 1:
            continue
        d = doc['data']
        g = GO(d.get('m_Name', ''))
        g.active = bool(d.get('m_IsActive', 1))
        g.tag = d.get('m_TagString', 'Untagged')
        gos[fid] = g
        idmap[fid] = ('go', g, None, 1)
    for fid, doc in docs.items():
        if doc['stripped'] or doc['cls'] in (1, 1001):
            continue
        d = copy.deepcopy(doc['data'])
        go = (d.get('m_GameObject') or {}).get('fileID')
        if go not in gos:
            if doc['cls'] not in (4, 224):
                added_comps.append((fid, doc['cls'], d, go))
            continue
        g = gos[go]
        if doc['cls'] in (4, 224):
            g.transform = d
            g.tcls = doc['cls']
            idmap[fid] = ('tr', g, d, doc['cls'])
        else:
            g.comps.append([doc['cls'], d])
            idmap[fid] = ('comp', g, d, doc['cls'])
            own_comps.append(d)

    # Prefab instances (modifications are applied after all ids are known)
    instances = {}
    for fid, doc in docs.items():
        if doc['cls'] != 1001:
            continue
        d = doc['data']
        src = guid_path(d['m_SourcePrefab']['guid'])
        if src.lower().endswith(('.fbx', '.obj')):
            g = GO(os.path.splitext(os.path.basename(src))[0])
            g.model = src
            g.transform = {'m_LocalPosition': {'x': 0, 'y': 0, 'z': 0},
                           'm_LocalRotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1},
                           'm_LocalScale': {'x': 1, 'y': 1, 'z': 1}}
            g.owners.append((path, fid, g, src))
            instances[fid] = (g, {}, d)
            # Objects inside the model are known only by the ids this file's
            # modifications use; register them so enclosing files can target them too.
            model_guid = d['m_SourcePrefab']['guid']
            for m in d['m_Modification'].get('m_Modifications') or []:
                t = m['target']
                if t.get('guid') == model_guid and t.get('fileID'):
                    idmap[(fid ^ t['fileID']) & MASK] = ('model', g, t['fileID'], None)
        else:
            roots, sub_idmap = instantiate(src)
            root = roots[0]
            for r in roots:
                for x in r.walk():
                    x.owners.append((path, fid, root, src))
            for lid, v in sub_idmap.items():
                idmap[(fid ^ lid) & MASK] = v
            instances[fid] = (root, sub_idmap, d)

    # Stripped objects -> the corresponding object inside the instance
    for fid, doc in docs.items():
        if not doc['stripped']:
            continue
        d = doc['data']
        pi = d['m_PrefabInstance']['fileID']
        so = d['m_CorrespondingSourceObject']['fileID']
        if pi not in instances:
            continue
        root, sub_idmap, _ = instances[pi]
        if so in sub_idmap:
            idmap[fid] = sub_idmap[so]
        elif root.model:
            kind = 'go' if doc['cls'] == 1 else ('tr' if doc['cls'] in (4, 224) else 'comp')
            idmap[fid] = (kind, root, root.transform if kind == 'tr' else None, doc['cls'])

    for fid, cls, d, go_fid in added_comps:
        e = idmap.get(go_fid)
        if e and e[0] == 'go':
            e[1].comps.append([cls, d])
            idmap[fid] = ('comp', e[1], d, cls)
            own_comps.append(d)

    def resolve_value(m):
        ref = m.get('objectReference') or {}
        if ref.get('guid'):
            return ref
        if ref.get('fileID'):
            e = idmap.get(ref['fileID'])
            return Ref(*e) if e else None
        return m['value']

    for fid, (root, sub_idmap, d) in instances.items():
        mods = d['m_Modification'].get('m_Modifications') or []
        if root.model:
            tcount = {}
            for m in mods:
                if m['propertyPath'].startswith('m_LocalPosition'):
                    t = m['target']['fileID']
                    tcount[t] = tcount.get(t, 0) + 1
            root_t = max(tcount, key=tcount.get) if tcount else None
            root.model_root_transform = root_t
            for m in mods:
                apply_model_mod(root, m['target']['fileID'], m['propertyPath'], m)
            continue
        for m in mods:
            tid = m['target'].get('fileID')
            if not tid or tid not in sub_idmap:
                continue
            kind, g, cd, _ = sub_idmap[tid]
            pp = m['propertyPath']
            val = resolve_value(m)
            if kind == 'model':
                apply_model_mod(g, cd, pp, m)
                continue
            if kind == 'go':
                if pp == 'm_Name':
                    g.name = str(val)
                elif pp == 'm_IsActive':
                    g.active = bool(int(val))
                elif pp == 'm_TagString':
                    g.tag = val
            else:
                set_path(cd, pp, val)
        for rc in (d['m_Modification'].get('m_RemovedComponents') or []):
            tid = rc.get('fileID')
            if tid in sub_idmap and sub_idmap[tid][0] == 'comp':
                _, g, cd, _ = sub_idmap[tid]
                g.comps = [c for c in g.comps if c[1] is not cd]

    for d in own_comps:
        _resolve_refs(d, idmap)
    for g in gos.values():
        _resolve_refs(g.transform, {})  # drop raw transform links

    # Hierarchy
    roots = []

    def parent_of(ref_fid):
        e = idmap.get(ref_fid)
        return e[1] if e else None

    for fid, doc in docs.items():
        if doc['stripped'] or doc['cls'] not in (4, 224):
            continue
        father = (doc['data'].get('m_Father') or {}).get('fileID', 0)
        g = gos.get(doc['data'].get('m_GameObject', {}).get('fileID'))
        if g is None:
            continue
        p = parent_of(father) if father else None
        if p:
            g.parent = p
            p.children.append(g)
        else:
            roots.append(g)
    for fid, (root, _, d) in instances.items():
        tp = (d['m_Modification'].get('m_TransformParent') or {}).get('fileID', 0)
        p = parent_of(tp) if tp else None
        if p:
            root.parent = p
            p.children.append(root)
        else:
            roots.append(root)

    def key(c):
        ro = (c.transform or {}).get('m_RootOrder')
        return int(ro) if ro is not None else 999

    def order(g):
        g.children.sort(key=key)
        for c in g.children:
            order(c)
    for r in roots:
        order(r)
    roots.sort(key=key)
    return roots, idmap


def v3(d, default=(0, 0, 0)):
    if not d:
        return default
    return (float(d.get('x', 0)), float(d.get('y', 0)), float(d.get('z', 0)))


def v2(d, default=(0, 0)):
    if not d:
        return default
    return (float(d.get('x', 0)), float(d.get('y', 0)))


def q4(d):
    if not d:
        return (0, 0, 0, 1)
    return (float(d.get('x', 0)), float(d.get('y', 0)), float(d.get('z', 0)), float(d.get('w', 1)))


def col(d, default=(1, 1, 1, 1)):
    if not d:
        return default
    return (float(d.get('r', 0)), float(d.get('g', 0)), float(d.get('b', 0)), float(d.get('a', 1)))
