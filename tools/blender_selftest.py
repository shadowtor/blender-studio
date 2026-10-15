"""Headless check of bl_lib: run with   blender -b --python tools/blender_selftest.py   (smoke_test.py does this for you).

Builds a keychain outline from the sample artwork, extrudes it, exports a GLB, and fails loudly on a wrong result.
"""
import os, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "skills", "blender-studio", "scripts"))
from bl_lib import *

fresh_scene()
cut = cutline(os.path.join(ROOT, "examples", "art", "mochi.png"), 55, offset_mm=2.5, hole_mm=4.5)
assert len(cut["loops"]) == 2, f"expected outline plus hole, got {len(cut['loops'])} loops"
assert cut["hole"] and abs(cut["hole"][2] - mm(2.25)) < 1e-9
slab = extrude_loops(cut["loops"], 3, "Slab", z_mm=1.5, bevel_mm=0.25)
d = slab.dimensions
assert 0.040 < d.x < 0.070 and 0.040 < d.y < 0.075 and abs(d.z - 0.003) < 1e-4, tuple(d)
dg = bpy.context.evaluated_depsgraph_get()
me = slab.evaluated_get(dg).to_mesh()
bm = bmesh.new()
bm.from_mesh(me)
open_edges = sum(1 for e in bm.edges if not e.is_manifold)
bm.free()
assert open_edges == 0, f"{open_edges} open edges"
out = export(os.path.join(tempfile.mkdtemp(), "t.glb"), [slab])
assert os.path.getsize(out) > 1000
print("blender_selftest ok: 2 loops, %.1f x %.1f x %.1f mm, 0 open edges, glb %d bytes"
      % (d.x * 1000, d.y * 1000, d.z * 1000, os.path.getsize(out)))
