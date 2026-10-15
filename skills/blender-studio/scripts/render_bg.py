#!/usr/bin/env python3
"""Render a .blend in a background Blender process, so your open Blender stays usable and a long render cannot time out the MCP.

  python render_bg.py scene.blend --still out/hero.png [--frame 1]
  python render_bg.py scene.blend --anim out/frame_ [--start 1 --end 110 --step 2]   # writes out/frame_0001.png ...
  (--step 2 renders every second frame: half the time, the clip plays at half the frame count)
  options: --engine CYCLES|BLENDER_EEVEE  --samples N  --scale PERCENT

Save the scene first with bl_lib.save_copy(path). Blender is found through BLENDER_EXE, PATH or the usual install folders.
"""
import argparse, glob, os, shutil, subprocess, sys


def find_blender():
    for c in (os.environ.get("BLENDER_EXE"), shutil.which("blender")):
        if c and os.path.exists(c):
            return c
    pats = ["C:/Program Files/Blender Foundation/Blender */blender.exe", "/Applications/Blender.app/Contents/MacOS/Blender",
            "/usr/bin/blender", "/snap/bin/blender", os.path.expanduser("~/blender*/blender")]
    hits = sorted(h for p in pats for h in glob.glob(p))
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blend")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--still")
    g.add_argument("--anim")
    ap.add_argument("--frame", type=int, default=1)
    ap.add_argument("--start", type=int)
    ap.add_argument("--end", type=int)
    ap.add_argument("--step", type=int)
    ap.add_argument("--engine")
    ap.add_argument("--samples", type=int)
    ap.add_argument("--scale", type=int)
    a = ap.parse_args()
    exe = find_blender()
    if not exe:
        sys.exit("Blender executable not found. Set BLENDER_EXE.")
    out = os.path.abspath(a.still or a.anim)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    expr = ["import bpy; s = bpy.context.scene"]
    if a.samples:
        expr.append("s.cycles.samples = %d; s.eevee.taa_render_samples = %d" % (a.samples, a.samples))
    if a.scale:
        expr.append("s.render.resolution_percentage = %d" % a.scale)
    cmd = [exe, "-b", os.path.abspath(a.blend), "--python-expr", "; ".join(expr)]
    if a.engine:
        cmd += ["-E", a.engine]
    if a.still:
        cmd += ["-o", os.path.splitext(out)[0], "-F", "PNG", "-x", "1", "-f", str(a.frame)]
    else:
        cmd += ["-o", out + "####", "-F", "PNG", "-x", "1"]
        if a.start:
            cmd += ["-s", str(a.start)]
        if a.end:
            cmd += ["-e", str(a.end)]
        if a.step:
            cmd += ["-j", str(a.step)]
        cmd += ["-a"]
    print(" ".join(cmd))
    rc = subprocess.call(cmd)
    if a.still and rc == 0:  # Blender appends the frame number to a still's name; put it back to what was asked
        made = os.path.splitext(out)[0] + "%04d.png" % a.frame
        if os.path.exists(made):
            os.replace(made, out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
