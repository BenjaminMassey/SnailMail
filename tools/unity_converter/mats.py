"""Read Unity material (.mat) files."""
from unityscene import guid_path, load_docs


def read_mat(rel):
    """Shader, keywords, textures, colors and floats of the material at `rel`."""
    docs = load_docs(rel)
    for fid, d in docs.items():
        if d['cls'] != 21:
            continue
        m = d['data']
        sh = m.get('m_Shader', {})
        shp = guid_path(sh.get('guid')) or f"builtin:{sh.get('fileID')}"
        props = m.get('m_SavedProperties', {})
        tex = {}
        for e in props.get('m_TexEnvs', []) or []:
            (k, v), = e.items()
            if (v.get('m_Texture') or {}).get('guid'):
                tex[k] = (guid_path(v['m_Texture']['guid']), v.get('m_Scale'), v.get('m_Offset'))
        cols = {}
        for e in props.get('m_Colors', []) or []:
            (k, v), = e.items()
            cols[k] = tuple(round(float(x), 4) for x in v.values())
        fl = {}
        for e in props.get('m_Floats', []) or []:
            (k, v), = e.items()
            fl[k] = v
        return {'name': m.get('m_Name'), 'shader': shp, 'kw': m.get('m_ShaderKeywords'), 'tex': tex,
                'cols': cols, 'floats': fl, 'queue': m.get('m_CustomRenderQueue')}
