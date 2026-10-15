#!/usr/bin/env python3
"""Write a single-file interactive 3D page for a GLB (orbit, zoom, optional AR) using Google's <model-viewer>.

  python make_viewer.py exports/keychain.glb exports/index.html --title "Mochi keychain" [--poster renders/hero.png]
                        [--bg "#e8ecf8"] [--rotate] [--exposure 1.0]

The page references the GLB by its relative path, so keep the two files together. <model-viewer> loads from a pinned
jsDelivr URL with a Subresource Integrity hash; vendor the script into your site if you must not depend on a CDN. See references/web-3d.md.
"""
import argparse, html, os

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("glb")
ap.add_argument("out")
ap.add_argument("--title", default="3D model")
ap.add_argument("--poster")
ap.add_argument("--bg", default="#e8ecf8")
ap.add_argument("--rotate", action="store_true", help="slow auto-rotate until the visitor touches it")
ap.add_argument("--exposure", default="1")
a = ap.parse_args()

rel = lambda p: os.path.relpath(p, os.path.dirname(os.path.abspath(a.out))).replace(os.sep, "/")
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(a.title)}</title>
<script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js"
 integrity="sha256-d07doh4b4qCTTkYMpZQ68f4/iNoTCp+YvWqdYRV2ys8=" crossorigin="anonymous"></script>
<style>html,body{{margin:0;height:100%;background:{a.bg}}}model-viewer{{width:100%;height:100%;--poster-color:{a.bg}}}</style></head>
<body><model-viewer src="{rel(a.glb)}" alt="{html.escape(a.title)}" camera-controls touch-action="pan-y" shadow-intensity="1"
 exposure="{a.exposure}" environment-image="neutral" ar{" auto-rotate" if a.rotate else ""}{f' poster="{rel(a.poster)}"' if a.poster else ""}></model-viewer></body></html>
"""
open(a.out, "w", encoding="utf-8").write(page)
print("wrote", a.out)
