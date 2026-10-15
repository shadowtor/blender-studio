#!/usr/bin/env python3
"""Render the 1280x640 social card (GitHub repo social preview, link previews) to site/social-card.png.

  python tools/make_social_card.py

Uses the two example hero renders and a headless Chromium-based browser (Chrome, Edge or Chromium). System fonts only,
nothing is downloaded. All content sits inside an 80 px safe area.
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, SAFE = 1280, 640, 80
OUT = os.path.join(ROOT, "site", "social-card.png")
uri = lambda *p: "file:///" + os.path.join(ROOT, *p).replace(os.sep, "/")


def browser():
    for p in (shutil.which("chrome"), shutil.which("msedge"), shutil.which("chromium"), shutil.which("google-chrome"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if p and os.path.exists(p):
            return p
    sys.exit("No Chromium-based browser found")


chips = "".join(f'<span class="chip{" on" if i == 0 else ""}">{t}</span>' for i, t in enumerate(["Model", "Render", "Animation", "Web"]))
html = f"""<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box}}html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#f3f1ee;color:#1a1714;font:400 24px/1.4 "Segoe UI","Helvetica Neue",Arial,sans-serif;position:relative}}
.safe{{position:absolute;left:{SAFE}px;top:{SAFE}px;right:{SAFE}px;bottom:{SAFE}px;display:grid;grid-template-columns:500px 1fr;gap:40px;align-items:center}}
.name{{font-weight:800;font-size:30px;letter-spacing:-.01em;margin-bottom:20px;color:#c2410c}}
h1{{margin:0;font-weight:800;font-size:50px;line-height:1.06;letter-spacing:-.02em}}
p{{margin:20px 0 0;color:#5a534c;font-size:23px;line-height:1.35}}
.chips{{display:flex;gap:10px;margin-top:24px;flex-wrap:wrap}}
.chip{{border:2px solid #1a1714;padding:3px 13px;font-weight:600;font-size:19px;background:#fff}}
.chip.on{{background:#c2410c;border-color:#c2410c;color:#fff}}
.tiles{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.tile{{height:380px;background:#e8ecf8;overflow:hidden;display:grid;place-items:center}}
.tile img{{width:150%;max-width:none}}
</style><body><div class="safe"><div>
<div class="name">blender-studio</div>
<h1>Describe the product. Get the model, the render and the GIF.</h1>
<p>Blender driven by your AI agent. An Agent Skill, tested with Claude Code.</p>
<div class="chips">{chips}</div></div>
<div class="tiles"><div class="tile"><img src="{uri('examples', 'acrylic-keychain', 'hero.png')}"></div>
<div class="tile"><img src="{uri('examples', 'vinyl-figurine', 'hero.png')}"></div></div></div></body>"""

with tempfile.TemporaryDirectory() as td:
    f = os.path.join(td, "card.html")
    open(f, "w", encoding="utf-8").write(html)
    subprocess.check_call([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                           f"--window-size={W},{H}", f"--screenshot={OUT}", "file:///" + f.replace(os.sep, "/")],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"wrote {OUT}  {os.path.getsize(OUT) / 1024:.0f} KB")
