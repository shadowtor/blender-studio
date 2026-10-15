#!/usr/bin/env python3
"""Smoke test. Runs anywhere (CI included); the Blender steps run only when a Blender executable is found.

  python tools/smoke_test.py
"""
import json, os, py_compile, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills", "blender-studio")
S = os.path.join(SK, "scripts")
sys.path.insert(0, S)


def ok(msg):
    print("OK  ", msg)


def fail(msg):
    print("FAIL", msg)
    sys.exit(1)


# 1. SKILL.md frontmatter and referenced files
text = open(os.path.join(SK, "SKILL.md"), encoding="utf-8").read()
m = re.match(r"---\nname: (\S+)\ndescription: (.+)\n---\n", text)
if not m or m.group(1) != "blender-studio":
    fail("SKILL.md frontmatter")
ok("SKILL.md frontmatter")
for ref in re.findall(r"\]\((references/[^)]+)\)", text):
    if not os.path.exists(os.path.join(SK, ref)):
        fail("missing " + ref)
ok("SKILL.md links resolve")

# 2. every script compiles (bl_lib needs Blender's bpy, so it is compiled here and run in step 4)
for dirpath, _, files in os.walk(ROOT):
    if any(x in dirpath for x in (".git", "_work", "_site", "dist")):
        continue
    for f in files:
        if f.endswith(".py"):
            py_compile.compile(os.path.join(dirpath, f), cfile=os.path.join(tempfile.gettempdir(), "x.pyc"), doraise=True)
ok("python files compile")

# 3. project scaffold
with tempfile.TemporaryDirectory() as td:
    subprocess.check_call([sys.executable, os.path.join(S, "new_project.py"), "Smoke Part", "--kind", "keychain",
                           "--deliver", "model,web", "--dir", td], stdout=subprocess.DEVNULL)
    p = json.load(open(os.path.join(td, "smoke-part", "project.json")))
    if p["kind"] != "keychain" or set(p["deliverables"]) != {"model", "web"}:
        fail("new_project.py")
ok("new_project.py scaffolds a project")

# 4. headless Blender: the outline, extrusion and GLB export helpers work (optional)
from render_bg import find_blender
exe = find_blender()
if exe:
    r = subprocess.run([exe, "-b", "--factory-startup", "--python", os.path.join(ROOT, "tools", "blender_selftest.py")],
                       capture_output=True, text=True, timeout=300)
    if "blender_selftest ok" not in r.stdout:
        fail("blender_selftest:\n" + r.stdout[-1500:] + r.stderr[-800:])
    ok(next(l for l in r.stdout.splitlines() if "blender_selftest ok" in l))
else:
    print("SKIP headless Blender self-test (no Blender executable found; set BLENDER_EXE)")
print("smoke test passed")
