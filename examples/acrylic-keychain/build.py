"""Acrylic keychain from a PNG: cut line, two clear layers around a printed sheet, split ring, exploded animation.

Run inside Blender with HERE set to this folder, for example:
    HERE = r"F:/.../examples/acrylic-keychain"; exec(open(HERE + "/build.py").read())
"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "skills", "blender-studio", "scripts"))
import importlib, bl_lib
importlib.reload(bl_lib)
from bl_lib import *

# --- parameters (measured, then fit, then derived)
ART = os.path.join(ROOT, "examples", "art", "mochi.png")
WIDTH_MM = 55        # artwork width on the keychain
ACRYLIC_MM = 3       # thickness of each clear layer
BORDER_MM = 2.5      # clear acrylic margin around the artwork
HOLE_MM = 4.5        # keyring hole diameter
RING_MM = 16         # split ring outer diameter
GAP_MM = 16          # exploded spacing between layers
RES = (1280, 1280)

fresh_scene()
render_setup(*RES, engine="CYCLES", samples=96, transparent=False, fps=30)

cut = cutline(ART, WIDTH_MM, offset_mm=BORDER_MM, hole_mm=HOLE_MM, wall_mm=2.5)
clear = acrylic("Clear acrylic", tint=(0.96, 0.99, 1.0))
back = extrude_loops(cut["loops"], ACRYLIC_MM, "Back acrylic", z_mm=ACRYLIC_MM / 2, material=clear)
art = art_plane(ART, WIDTH_MM, z_mm=ACRYLIC_MM + 0.1, name="Printed sheet", material=image_mat(ART, rough=0.35))
front = extrude_loops(cut["loops"], ACRYLIC_MM, "Front acrylic", z_mm=ACRYLIC_MM * 1.5 + 0.2, material=clear)
hx, hy, hr = cut["hole"]
ring = split_ring(RING_MM, 1.5, material=chrome())
ring.rotation_euler.y = PI / 2
rc = mm(RING_MM / 2 - 0.75)
ring.location = (hx, hy + hr - mm(0.75) + rc, mm(ACRYLIC_MM + 0.1))

parts = [back, art, front]
stand(parts + [ring])
studio(parts + [ring], bg=(0.80, 0.84, 0.94), floor=False)
cam = camera(parts + [ring], az=-24, el=14, lens=90, margin=1.45)

# exploded animation: layers fan out along Z, the ring lifts away, hold, then close up again
last = explode(parts, GAP_MM, start=1, end=45, hold=20, back=True)
ring.location = (hx, hy + hr - mm(0.75) + rc, mm(ACRYLIC_MM + 0.1))
for f, dy in ((1, 0), (45, 18), (65, 18), (109, 0)):
    ring.location.y = hy + hr - mm(0.75) + rc + mm(dy)
    ring.keyframe_insert("location", index=1, frame=f)
bpy.context.scene.frame_end = last
report(parts + [ring])

# --- outputs (set OUT to a folder to write them)
if "OUT" in globals():
    os.makedirs(OUT, exist_ok=True)
    save_copy(os.path.join(OUT, "keychain.blend"))
    bpy.context.scene.frame_set(1)  # exports use the assembled pose
    export(os.path.join(OUT, "keychain.glb"), parts + [ring])
