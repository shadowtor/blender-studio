"""Vinyl designer-toy figurine ("Mochi") with the brand artwork printed on the face, on a turntable.

Run inside Blender with HERE set to this folder, for example:
    HERE = r"F:/.../examples/vinyl-figurine"; exec(open(HERE + "/build.py").read())
Set OUT to a folder to also write keychain-style outputs (blend copy, GLB, STL).
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "skills", "blender-studio", "scripts"))
import importlib, bl_lib
importlib.reload(bl_lib)
from bl_lib import *

# --- parameters
FACE = os.path.join(ROOT, "examples", "art", "mochi_face.png")
HEAD_MM = (28, 25, 24)      # head radii x, y, z
BODY_MM = (16, 14, 20)
BASE_R_MM = 34
FACE_MM = 66                # printed face width (the PNG has a margin, so this is wider than the head)
RES = (1080, 1080)
FRAMES = 120


def blob(name, radii_mm, loc_mm, material, rot_deg=(0, 0, 0), subdiv=2):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=[mm(v) for v in loc_mm],
                                         rotation=[math.radians(v) for v in rot_deg])
    o = bpy.context.object
    o.name = name
    o.scale = [mm(v) for v in radii_mm]
    bpy.ops.object.transform_apply(scale=True, rotation=False)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    return o


fresh_scene()
render_setup(*RES, engine="CYCLES", samples=96, transparent=False, fps=30, frames=FRAMES)

orange = vinyl("Orange vinyl", (1.0, 0.43, 0.12))
cream = vinyl("Cream vinyl", (0.98, 0.86, 0.66))
pink = vinyl("Pink vinyl", (0.95, 0.42, 0.58))
base_m = vinyl("Base", (0.11, 0.09, 0.17), rough=0.2)

bpy.ops.mesh.primitive_cylinder_add(radius=mm(BASE_R_MM), depth=mm(5), vertices=96, location=(0, 0, mm(2.5)))
base = bpy.context.object
base.name = "Base"
base.data.materials.append(base_m)
bv = base.modifiers.new("Bevel", "BEVEL")
bv.width, bv.segments = mm(1.4), 3
bpy.ops.object.shade_smooth()

body = blob("Body", BODY_MM, (0, 4, 5 + BODY_MM[2] - 3), orange)
belly = blob("Belly", (11, 8, 14), (0, -6, 5 + BODY_MM[2] - 2), cream)
head_z = 5 + BODY_MM[2] * 2 - 8 + HEAD_MM[2] - 2
head = blob("Head", HEAD_MM, (0, 0, head_z), orange)
feet = [blob(f"Foot {s}", (8, 11, 5), (s * 9, -9, 8), cream) for s in (-1, 1)]
arms = [blob(f"Arm {s}", (5.5, 6.5, 12), (s * 17.5, -2, 5 + BODY_MM[2] + 2), orange, rot_deg=(0, -s * 16, 0)) for s in (-1, 1)]

ears = []
for s in (-1, 1):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=mm(11), radius2=mm(1.5), depth=mm(19),
                                    location=(mm(s * 17), mm(1), mm(head_z + HEAD_MM[2] - 1)),
                                    rotation=(0, math.radians(s * 28), 0))
    e = bpy.context.object
    e.name = f"Ear {s}"
    e.scale.y = 0.55
    e.data.materials.append(orange)
    e.modifiers.new("Subsurf", "SUBSURF").levels = 2
    bpy.ops.object.shade_smooth()
    ears.append(e)

cd = bpy.data.curves.new("Tail", "CURVE")
cd.dimensions, cd.bevel_depth, cd.bevel_resolution, cd.use_fill_caps = "3D", mm(4.2), 6, True
sp = cd.splines.new("BEZIER")
sp.bezier_points.add(3)
for p, (x, y, z) in zip(sp.bezier_points, ((0, 10, 12), (0, 30, 16), (0, 34, 38), (-7, 26, 52))):
    p.co = (mm(x), mm(y), mm(z))
    p.handle_left_type = p.handle_right_type = "AUTO"
tail_curve = bpy.data.objects.new("Tail", cd)
bpy.context.scene.collection.objects.link(tail_curve)
tail = bake(tail_curve)
tail.data.materials.append(orange)
bpy.context.view_layer.objects.active = tail
bpy.ops.object.shade_smooth()

# the face is the supplied artwork, printed onto the head along the camera axis
face = bpy.data.objects.new("Face print", None)
face.empty_display_type = "PLAIN_AXES"
face.empty_display_size = mm(10)
face.location = (0, -mm(HEAD_MM[1]), mm(head_z - 1))
face.rotation_euler.x = PI / 2
bpy.context.scene.collection.objects.link(face)
head.data.materials[0] = orange.copy()  # own material, so the decal does not spill onto the shared orange
decal(head, FACE, face, size_mm=FACE_MM, depth_mm=22)

parts = [base, body, belly, head, tail] + feet + arms + ears
studio(parts, bg=(0.80, 0.84, 0.94), floor=True, power=0.5, ambient=0.8)
camera(parts, az=-18, el=10, lens=100, margin=1.1)
spin = turntable(parts, FRAMES, spin_subject=True)
report([base, body, head, tail])

if "OUT" in globals():
    os.makedirs(OUT, exist_ok=True)
    bpy.context.scene.frame_set(1)
    save_copy(os.path.join(OUT, "figurine.blend"))
    # glTF cannot carry the projected decal, so the web copy gets the face baked flat onto the head's front
    import numpy as np
    src = bpy.data.images.load(FACE, check_existing=True)
    w, h = src.size
    px = np.array(src.pixels[:], dtype=np.float32).reshape(h, w, 4)
    orange_rgb = np.array(next(n for n in orange.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value[:3])
    rgb = px[..., :3] * px[..., 3:4] + orange_rgb * (1 - px[..., 3:4])
    tex = bpy.data.images.new("face_web", w, h)
    tex.pixels = np.dstack([rgb, np.ones((h, w), np.float32)]).ravel().tolist()
    tex.pack()
    web = vinyl("Head web", (1, 1, 1))
    t = web.node_tree.nodes.new("ShaderNodeTexImage")
    t.image, t.extension = tex, "EXTEND"
    web.node_tree.links.new(t.outputs["Color"], next(n for n in web.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"])
    uv = head.data.uv_layers.active
    old_uv = [d.uv.copy() for d in uv.data]
    for loop in head.data.loops:  # front projection; the back half is parked off the image so it stays plain orange
        p = head.matrix_world @ head.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (-1, -1) if p.y > 0 else (p.x / mm(FACE_MM) + 0.5, (p.z - mm(head_z - 1)) / mm(FACE_MM) + 0.5)
    keep = head.data.materials[0]
    head.data.materials[0] = web
    export(os.path.join(OUT, "figurine.glb"), parts)
    head.data.materials[0] = keep
    for d, o in zip(uv.data, old_uv):
        d.uv = o
