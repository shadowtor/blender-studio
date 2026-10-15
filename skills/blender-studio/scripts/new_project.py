#!/usr/bin/env python3
"""Create a blender-studio project folder.

  python new_project.py "Mochi keychain" --kind keychain --deliver model,render,animation,web [--dir projects]

Kinds: keychain | apparel | figurine | exploded | process | other.
Deliverables: model | render | animation | web. Makes <dir>/<slug>/{project.json,art/,build/,renders/,exports/}.
"""
import argparse, json, os, re

KINDS = ["keychain", "apparel", "figurine", "exploded", "process", "other"]
DELIVER = {
    "model": "GLB for web/AR, STL for printing, OBJ/FBX/USD for other tools, plus the .blend",
    "render": "PNG stills (transparent or on a backdrop)",
    "animation": "PNG sequence, MP4, GIF",
    "web": "GLB plus a model-viewer page",
}

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("name")
ap.add_argument("--kind", required=True, choices=KINDS)
ap.add_argument("--deliver", default="render", help="comma list of: " + ", ".join(DELIVER))
ap.add_argument("--dir", default=".")
a = ap.parse_args()
want = [d.strip() for d in a.deliver.split(",") if d.strip()]
bad = [d for d in want if d not in DELIVER]
if bad:
    raise SystemExit(f"unknown deliverable {bad}; use {list(DELIVER)}")

slug = re.sub(r"[^a-z0-9]+", "-", a.name.lower()).strip("-")
root = os.path.join(a.dir, slug)
for d in ("art", "build", "renders", "exports"):
    os.makedirs(os.path.join(root, d), exist_ok=True)
path = os.path.join(root, "project.json")
if os.path.exists(path):
    raise SystemExit(f"{path} exists, not overwriting")
json.dump({"name": a.name, "kind": a.kind, "deliverables": {d: DELIVER[d] for d in want},
           "artwork": [], "dimensions_mm": {}, "assumptions": [], "open_questions": [],
           "render": {"engine": "CYCLES", "size": [1920, 1080], "transparent": False, "fps": 30}},
          open(path, "w"), indent=2)
print("created", root)
