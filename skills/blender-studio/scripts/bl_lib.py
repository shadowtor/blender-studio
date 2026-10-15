"""blender-studio helpers. They run INSIDE Blender (send them with execute_blender_code or blender_mcp.py).

    import sys; sys.path.insert(0, r"<skill>/scripts")
    import importlib, bl_lib; importlib.reload(bl_lib); from bl_lib import *

Units: 1 Blender unit = 1 metre, so every size is written through mm(): mm(55) is 55 mm.
Real scale keeps glTF, STL, USD and AR exports correct without rescaling.
"""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector

PI = math.pi


def mm(x):
    return x / 1000.0


# ---------------------------------------------------------------- scene

def is_default_scene():
    """True for Blender's untouched startup scene (Cube, Light, Camera, no file)."""
    return not bpy.data.filepath and {o.name for o in bpy.data.objects} <= {"Cube", "Light", "Camera"}


def is_ours():
    """True for a scene fresh_scene() emptied earlier in this session, which may be rebuilt freely."""
    return bool(bpy.context.scene.get("blender_studio"))


def fresh_scene(force=False):
    """Empty the scene. Refuses when the user has their own content, unless force=True (save theirs first)."""
    if not force and not (is_default_scene() or is_ours()):
        raise RuntimeError("Scene holds the user's work. Ask first, or save a copy and pass force=True.")
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
                 bpy.data.images, bpy.data.actions, bpy.data.collections):
        for d in list(coll):
            coll.remove(d)
    sc = bpy.context.scene
    sc.unit_settings.system, sc.unit_settings.scale_length, sc.unit_settings.length_unit = "METRIC", 1.0, "MILLIMETERS"
    sc.frame_start, sc.frame_end, sc.frame_current = 1, 1, 1
    sc["blender_studio"] = True
    return sc


def render_setup(w=1920, h=1080, engine="EEVEE", samples=64, transparent=False, fps=30, frames=None, view="Standard"):
    """engine: EEVEE (fast, good for previews and most product shots) or CYCLES (best glass and shadows).
    view 'Standard' keeps brand colours true; 'AgX' is the filmic default and dulls flat artwork."""
    sc = bpy.context.scene
    r = sc.render
    r.engine = "CYCLES" if engine.upper() == "CYCLES" else "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.film_transparent = transparent
    r.fps = fps
    if r.engine == "CYCLES":
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
    else:
        sc.eevee.taa_render_samples = samples
    sc.view_settings.view_transform = view
    if frames:
        sc.frame_start, sc.frame_end = 1, frames
    return sc


def _link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def _bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type in {"MESH", "CURVE"} for c in o.bound_box]
    lo = Vector((min(p[i] for p in pts) for i in range(3)))
    hi = Vector((max(p[i] for p in pts) for i in range(3)))
    return lo, hi


# ---------------------------------------------------------------- materials

_SOCKETS = {"transmission": "Transmission Weight", "ior": "IOR", "coat": "Coat Weight", "coat_rough": "Coat Roughness",
            "emission": "Emission Strength", "emission_color": "Emission Color", "alpha": "Alpha",
            "sheen": "Sheen Weight", "spec": "Specular IOR Level"}


def _principled(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, **kw):
    """Principled material. Extra inputs by short name: transmission, ior, coat, coat_rough, emission, alpha, sheen."""
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True  # deprecated in 5.x, harmless
    except Exception:
        pass
    p = _principled(m)
    p.inputs["Base Color"].default_value = (*color[:3], 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        p.inputs[_SOCKETS.get(k, k)].default_value = (*v[:3], 1) if isinstance(v, (tuple, list)) else v
    m.diffuse_color = (*color[:3], 1)
    return m


def acrylic(name="Acrylic", tint=(1, 1, 1), rough=0.03):
    return mat(name, tint, rough, transmission=1.0, ior=1.49)


def vinyl(name, color, rough=0.28):
    """Glossy moulded vinyl or PVC: soft sheen with a clear coat."""
    return mat(name, color, rough, coat=0.6, coat_rough=0.08, sheen=0.2)


def chrome(name="Chrome", color=(0.9, 0.9, 0.92), rough=0.12):
    return mat(name, color, rough, metal=1.0)


def image_mat(path, name=None, rough=0.45, alpha=True, emission=0.0):
    """Material showing an image on the UV map. alpha=True cuts out transparent pixels (PNG logos)."""
    img = bpy.data.images.load(path, check_existing=True)
    m = mat(name or os.path.splitext(os.path.basename(path))[0], rough=rough)
    p = _principled(m)
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.extension = "CLIP"
    m.node_tree.links.new(t.outputs["Color"], p.inputs["Base Color"])
    if alpha:
        m.node_tree.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    if emission:  # makes flat art survive any lighting; 0.2 to 0.4 is plenty
        m.node_tree.links.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emission
    return m


# ---------------------------------------------------------------- image to cut line (acrylic, stickers, die-cut)

def _march(f, level=0.5):
    """Marching squares over a 2D float field. Returns closed loops of (x, y) in pixel units."""
    H, W = f.shape
    inside = f > level
    code = (inside[:-1, :-1] * 1 + inside[:-1, 1:] * 2 + inside[1:, 1:] * 4 + inside[1:, :-1] * 8)
    table = {1: [("L", "B")], 2: [("B", "R")], 3: [("L", "R")], 4: [("R", "T")], 5: [("L", "B"), ("R", "T")],
             6: [("B", "T")], 7: [("L", "T")], 8: [("L", "T")], 9: [("B", "T")], 10: [("B", "R"), ("L", "T")],
             11: [("R", "T")], 12: [("L", "R")], 13: [("B", "R")], 14: [("L", "B")]}

    def key(e, i, j):  # an edge is shared by two cells, so give it one canonical id
        return {"B": ("h", i, j), "T": ("h", i + 1, j), "L": ("v", i, j), "R": ("v", i, j + 1)}[e]

    def pos(k):
        t, i, j = k
        (i2, j2) = (i, j + 1) if t == "h" else (i + 1, j)
        a, b = f[i, j], f[i2, j2]
        s = (level - a) / (b - a) if b != a else 0.5
        return (j + (j2 - j) * s, i + (i2 - i) * s)

    adj = {}
    for i, j in zip(*np.nonzero((code > 0) & (code < 15))):
        for e1, e2 in table[int(code[i, j])]:
            k1, k2 = key(e1, i, j), key(e2, i, j)
            adj.setdefault(k1, []).append(k2)
            adj.setdefault(k2, []).append(k1)
    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [], None, start
        while cur not in seen:
            seen.add(cur)
            loop.append(pos(cur))
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
        if len(loop) > 8:
            loops.append(loop)
    return loops


def _rdp(pts, eps):
    """Douglas-Peucker simplify for a closed loop."""
    pts = np.asarray(pts)

    def rec(a, b):
        p, q = pts[a], pts[b]
        d = q - p
        n = np.hypot(*d) or 1e-9
        dist = np.abs(d[0] * (pts[a + 1:b, 1] - p[1]) - d[1] * (pts[a + 1:b, 0] - p[0])) / n
        if len(dist) and dist.max() > eps:
            k = a + 1 + int(dist.argmax())
            return rec(a, k)[:-1] + rec(k, b)
        return [a, b]

    h = len(pts) // 2
    idx = rec(0, h)[:-1] + rec(h, len(pts) - 1)
    return pts[idx]


def _box(m):  # 3x3 box blur, edge padded
    p = np.pad(m, 1, mode="edge")
    return sum(p[i:i + m.shape[0], j:j + m.shape[1]] for i in range(3) for j in range(3)) / 9.0


def cutline(path, width_mm, offset_mm=2.0, hole_mm=0.0, wall_mm=2.0, smooth=3, max_px=500, threshold=0.5):
    """Trace the outline of a PNG's opaque pixels, grow it by offset_mm (the acrylic border), optionally add a
    keyring tab with a hole_mm hole at the top. Opaque images (no alpha) are keyed against the corner colour.
    Returns {"loops": [[(x, y) ...]], "w": art width m, "h": art height m, "hole": (x, y, r) or None}.
    Coordinates are metres, origin at the image centre, y up. Loops include the hole as an inner loop."""
    img = bpy.data.images.load(path, check_existing=True)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    a = px[..., 3]
    if a.min() > 0.99:  # no transparency: key out the background colour
        a = (np.abs(px[..., :3] - px[0, 0, :3]).sum(axis=2) > 0.12).astype(np.float32)
    k = max(1, int(math.ceil(max(w, h) / max_px)))  # shrink big images, contours do not need the pixels
    H, W = (h // k) * k, (w // k) * k
    a = a[:H, :W].reshape(H // k, k, W // k, k).mean(axis=(1, 3))
    mmpp = width_mm / a.shape[1]  # millimetres per (shrunk) pixel
    r_px = int(round(offset_mm / mmpp))
    pad = r_px + int(round((hole_mm / 2 + wall_mm) / mmpp)) * 2 + 8
    m = np.pad(a > threshold, pad).astype(np.float32)
    for n in range(r_px):  # octagon-ish grow: alternate cross and square dilation
        s = m.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if n % 2 else ()):
            s = np.maximum(s, np.roll(np.roll(m, dy, 0), dx, 1))
        m = s
    hole = None
    if hole_mm:
        rows = np.nonzero(m.max(axis=1))[0]
        top = rows.max()  # image rows run bottom-up, so the top is the largest index
        cols = np.nonzero(m[top - max(2, r_px):top + 1].max(axis=0))[0]
        cx = (cols.min() + cols.max()) / 2
        hr, tr = hole_mm / 2 / mmpp, (hole_mm / 2 + wall_mm) / mmpp
        yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
        cy = top + hr * 0.2  # start just above the art, then slide down until the tab really overlaps it
        while (m[np.hypot(xx - cx, yy - cy) <= tr] > 0).sum() < 0.3 * math.pi * tr * tr and cy > top - 4 * tr:
            cy -= 1
        d = np.hypot(xx - cx, yy - cy)
        m = np.maximum(m, (d <= tr).astype(np.float32))
        m = np.where(d <= hr, 0.0, m)
        hole = ((cx - m.shape[1] / 2) * mmpp, (cy - m.shape[0] / 2) * mmpp, hole_mm / 2)
    for _ in range(smooth):  # round off staircase corners; the 0.5 level then lands on a smooth curve
        m = _box(m)
    loops = []
    for lp in _march(m):
        lp = _rdp(lp + lp[:1], 0.35)[:-1]
        if len(lp) >= 4:
            loops.append([(mm((x - m.shape[1] / 2) * mmpp), mm((y - m.shape[0] / 2) * mmpp)) for x, y in lp])
    return {"loops": loops, "w": mm(width_mm), "h": mm(width_mm * h / w),
            "hole": tuple(mm(v) for v in hole) if hole else None}


def extrude_loops(loops, thickness_mm, name="Cut", z_mm=0.0, bevel_mm=0.25, material=None):
    """Flat solid from closed loops (inner loops become holes), centred on z_mm. Returns a mesh object."""
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions, cd.fill_mode, cd.extrude = "2D", "BOTH", mm(thickness_mm) / 2
    for pts in loops:
        sp = cd.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, (x, y) in zip(sp.points, pts):
            p.co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    o = _link(bpy.data.objects.new(name, cd))
    o.location.z = mm(z_mm)
    o = bake(o, name)
    if bevel_mm:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width, b.segments, b.limit_method, b.angle_limit = mm(bevel_mm), 2, "ANGLE", math.radians(40)
    if material:
        o.data.materials.append(material)
    return o


def bake(o, name=None):
    """Replace a curve (or any object with modifiers you want frozen) with a plain mesh object."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    bm = bmesh.new()  # curve-to-mesh leaves duplicate vertices along seams; weld them so the mesh is watertight
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    name, mw = name or o.name, o.matrix_world.copy()
    bpy.data.objects.remove(o, do_unlink=True)
    n = bpy.data.objects.new(name, me)
    n.matrix_world = mw
    return _link(n)


def art_plane(path, width_mm, z_mm=0.0, name="Art", material=None):
    """Flat quad of the artwork at true size (the print layer). Faces +Z, centred on the origin."""
    img = bpy.data.images.load(path, check_existing=True)
    w, h = mm(width_mm), mm(width_mm) * img.size[1] / img.size[0]
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, c in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = c
    o = _link(bpy.data.objects.new(name, me))
    o.location.z = mm(z_mm)
    o.data.materials.append(material or image_mat(path))
    return o


def split_ring(outer_mm=14, wire_mm=1.4, name="Split ring", material=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=mm(outer_mm / 2 - wire_mm / 2), minor_radius=mm(wire_mm / 2),
                                     major_segments=64, minor_segments=16)
    o = bpy.context.object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o


# ---------------------------------------------------------------- decals (apparel and merch mockups)

def decal(target, path, empty, size_mm=None, depth_mm=40):
    """Print an image onto an existing object's material, projected along an Empty's local -Z.
    Place and rotate the empty where the print goes (a flat PLAIN_AXES empty); scale it to the print size.
    The print shows only within depth_mm of the empty, so it does not bleed through to the back."""
    m = target.active_material
    p = _principled(m)
    n, l = m.node_tree.nodes, m.node_tree.links
    tc = n.new("ShaderNodeTexCoord")
    tc.object = empty
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0.5, 0.5, 0)
    mp.inputs["Scale"].default_value = (0.5, 0.5, 1)
    t = n.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    t.extension = "CLIP"
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], t.inputs["Vector"])
    z = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], z.inputs["Vector"])
    ab = n.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    l.new(z.outputs["Z"], ab.inputs[0])
    lt = n.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = mm(depth_mm) / max(empty.scale.z, 1e-6)
    l.new(ab.outputs[0], lt.inputs[0])
    mk = n.new("ShaderNodeMath")
    mk.operation = "MULTIPLY"
    l.new(t.outputs["Alpha"], mk.inputs[0])
    l.new(lt.outputs[0], mk.inputs[1])
    base = p.inputs["Base Color"].default_value[:]
    mix = n.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = base
    l.new(mk.outputs[0], mix.inputs[0])
    l.new(t.outputs["Color"], mix.inputs[7])
    l.new(mix.outputs[2], p.inputs["Base Color"])
    if size_mm:
        empty.scale = (mm(size_mm) / 2, mm(size_mm) / 2, empty.scale.z)
    return m


# ---------------------------------------------------------------- studio, camera

def stand(parts, name="Product"):
    """Parts are modelled lying flat (art facing +Z). Parent them to one empty tilted upright so the art faces the
    front camera (-Y). Keyframe the parts in local space and they still move along their own Z."""
    root = _link(bpy.data.objects.new(name, None))
    root.rotation_euler.x = PI / 2
    for o in parts:
        o.parent = root
    bpy.context.view_layer.update()
    return root


def studio(subject, bg=(0.93, 0.93, 0.95), floor=True, power=1.0, ambient=1.0):
    """Soft three-light product set. subject: an object, a list of objects, or a radius in metres."""
    if isinstance(subject, (int, float)):
        r, c = subject, Vector((0, 0, 0))
    else:
        lo, hi = _bounds(subject if isinstance(subject, (list, tuple)) else [subject])
        r, c = (hi - lo).length / 2, (hi + lo) / 2
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    cam_bg, amb = nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeBackground")
    cam_bg.inputs["Color"].default_value = amb.inputs["Color"].default_value = (*bg, 1)
    cam_bg.inputs["Strength"].default_value, amb.inputs["Strength"].default_value = 1.0, 0.3 * ambient
    lp, mx, out = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeOutputWorld")
    seen = nt.nodes.new("ShaderNodeMath")  # camera rays and the rays that continue through glass see the true backdrop
    seen.operation = "MAXIMUM"
    nt.links.new(lp.outputs["Is Camera Ray"], seen.inputs[0])
    nt.links.new(lp.outputs["Is Transmission Ray"], seen.inputs[1])
    nt.links.new(seen.outputs[0], mx.inputs[0])
    nt.links.new(amb.outputs[0], mx.inputs[1])
    nt.links.new(cam_bg.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    lights = {}
    for nm, (az, el, d, k, sz) in {"Key": (-40, 40, 3.2, 1.0, 2.2), "Fill": (50, 20, 3.5, 0.35, 3.0),
                                   "Rim": (170, 35, 3.5, 0.8, 1.6)}.items():
        L = bpy.data.lights.new(nm, "AREA")
        dist = r * d
        L.size = r * sz
        L.energy = 22 * k * power * dist ** 2  # constant exposure whatever the subject size
        o = _link(bpy.data.objects.new(nm, L))
        o.location = c + Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)),
                                 -math.cos(math.radians(az)) * math.cos(math.radians(el)),
                                 math.sin(math.radians(el)))) * dist
        con = o.constraints.new("TRACK_TO")
        con.target, con.track_axis, con.up_axis = _target(c), "TRACK_NEGATIVE_Z", "UP_Y"
        lights[nm] = o
    if floor:  # shadow catcher: the backdrop stays seamless and only the contact shadow shows (Cycles)
        objs = [] if isinstance(subject, (int, float)) else (subject if isinstance(subject, (list, tuple)) else [subject])
        z0 = _bounds(objs)[0].z if objs else 0
        bpy.ops.mesh.primitive_plane_add(size=r * 80, location=(c.x, c.y, z0))
        f = bpy.context.object
        f.name = "Floor"
        f.is_shadow_catcher = True
        lights["Floor"] = f
    return lights


def _target(c):
    t = bpy.data.objects.get("Target") or _link(bpy.data.objects.new("Target", None))
    t.location = c
    return t


def camera(subject, az=-30, el=18, lens=85, margin=1.2, name="Camera"):
    """Camera that frames the subject (object, list of objects) from azimuth/elevation degrees. az=0 is the front."""
    objs = subject if isinstance(subject, (list, tuple)) else [subject]
    lo, hi = _bounds(objs)
    c, r = (hi + lo) / 2, (hi - lo).length / 2
    sc = bpy.context.scene
    cd = bpy.data.cameras.new(name)
    cd.lens, cd.clip_start, cd.clip_end = lens, 0.001, 100
    aspect = sc.render.resolution_x / sc.render.resolution_y
    fov = 2 * math.atan(18 / lens * min(aspect, 1 / aspect))  # the narrower side decides how far back to stand
    dist = r * margin / math.sin(fov / 2)
    o = _link(bpy.data.objects.new(name, cd))
    a, e = math.radians(az), math.radians(el)
    o.location = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    con = o.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = _target(c), "TRACK_NEGATIVE_Z", "UP_Y"
    sc.camera = o
    return o


# ---------------------------------------------------------------- animation

def _interp(kind, fn):
    e = bpy.context.preferences.edit
    old = e.keyframe_new_interpolation_type
    e.keyframe_new_interpolation_type = kind
    try:
        fn()
    finally:
        e.keyframe_new_interpolation_type = old


def explode(parts, gap_mm=14, start=1, end=40, hold=0, axis=2, back=False):
    """Exploded view. parts: objects ordered in assembly order. Part i moves i*gap along the axis (centred on the
    middle part). Keys: assembled at `start`, exploded at `end`; back=True returns to assembled at end+hold+(end-start).
    Returns the last frame used."""
    mid = (len(parts) - 1) / 2
    for i, o in enumerate(parts):
        home = o.location.copy()
        far = home.copy()
        far[axis] += mm(gap_mm) * (i - mid)
        for f, loc in ((start, home), (end, far)) + (((end + hold, far), (end + hold + end - start, home)) if back else ()):
            o.location = loc
            o.keyframe_insert("location", frame=f)
        o.location = home
    last = end + (hold + end - start if back else 0)
    bpy.context.scene.frame_end = max(bpy.context.scene.frame_end, last)
    return last


def turntable(subject, frames=120, name="Turntable", spin_subject=True):
    """One full seamless turn. spin_subject=True rotates the subject under fixed lights (the gloss slides across it,
    best for vinyl and glass); False orbits the camera and lights around it."""
    objs = subject if isinstance(subject, (list, tuple)) else [subject]
    lo, hi = _bounds(objs)
    e = _link(bpy.data.objects.new(name, None))
    e.location = ((hi.x + lo.x) / 2, (hi.y + lo.y) / 2, lo.z) if spin_subject else ((hi + lo) / 2)
    movers = [o for o in objs if o.parent is None] if spin_subject else [
        o for o in bpy.data.objects if o.type in {"CAMERA", "LIGHT"} and o.parent is None]
    for o in movers:
        mw = o.matrix_world.copy()
        o.parent = e
        o.matrix_world = mw
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames

    def key():
        e.rotation_euler.z = 0
        e.keyframe_insert("rotation_euler", index=2, frame=1)
        e.rotation_euler.z = 2 * PI
        e.keyframe_insert("rotation_euler", index=2, frame=frames + 1)  # frame+1 is the same pose as 1: loop

    _interp("LINEAR", key)
    return e


def print_reveal(obj, start=1, end=120, name="PrintCut"):
    """Layer-by-layer 'being 3D printed' reveal: a box rises through the object and a Boolean keeps what is below it.
    Returns the cutter. Bake nothing: the Boolean stays live, so render in the background, not interactively."""
    lo, hi = _bounds([obj])
    pad = (hi - lo).length
    bpy.ops.mesh.primitive_cube_add(size=1)
    c = bpy.context.object
    c.name = name
    c.scale = (pad * 2, pad * 2, hi.z - lo.z)
    c.display_type = "WIRE"
    c.hide_render = True
    m = obj.modifiers.new("PrintReveal", "BOOLEAN")
    m.operation, m.solver, m.object = "INTERSECT", "EXACT", c
    z0 = lo.z - (hi.z - lo.z) / 2 - 1e-5
    z1 = hi.z - (hi.z - lo.z) / 2 + 1e-5
    c.location = ((hi.x + lo.x) / 2, (hi.y + lo.y) / 2, z0)
    c.keyframe_insert("location", index=2, frame=start)
    c.location.z = z1
    c.keyframe_insert("location", index=2, frame=end)
    bpy.context.scene.frame_end = max(bpy.context.scene.frame_end, end)
    return c


# ---------------------------------------------------------------- output

def still(path, w=None, h=None):
    """Render the current frame to path (PNG keeps transparency when film_transparent is on)."""
    r = bpy.context.scene.render
    if w:
        r.resolution_x, r.resolution_y = w, h or w
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA" if r.film_transparent else "RGB"
    r.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def save_copy(path):
    """Save the scene as a .blend without changing the user's open file, for background rendering.
    Artwork images are packed into the copy so it renders anywhere."""
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return path


def export(path, objs):
    """Export objs by extension: glb, gltf, stl, obj, fbx, usd/usdz, ply. Applies modifiers. Returns the path."""
    ext = os.path.splitext(path)[1].lower()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if ext in (".glb", ".gltf"):
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB" if ext == ".glb" else "GLTF_SEPARATE",
                                  use_selection=True, export_apply=True)
    elif ext == ".stl":
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, apply_modifiers=True)
    elif ext == ".obj":
        bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True, apply_modifiers=True)
    elif ext == ".fbx":
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True)
    elif ext in (".usd", ".usdc", ".usda", ".usdz"):
        bpy.ops.wm.usd_export(filepath=path, selected_objects_only=True)
    elif ext == ".ply":
        bpy.ops.wm.ply_export(filepath=path, export_selected_objects=True, apply_modifiers=True)
    else:
        raise ValueError("unsupported extension " + ext)
    return path


def report(objs=None):
    """Size in mm, triangles and non-manifold edges per object: the check before calling a model done."""
    out = []
    for o in objs or [o for o in bpy.data.objects if o.type == "MESH"]:
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bad = sum(1 for e in bm.edges if not e.is_manifold)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        bm.free()
        o.evaluated_get(dg).to_mesh_clear()
        d = o.dimensions
        out.append(f"{o.name}: {d.x * 1000:.1f} x {d.y * 1000:.1f} x {d.z * 1000:.1f} mm, {tris} tris, {bad} open edges")
    print("\n".join(out))
    return out
