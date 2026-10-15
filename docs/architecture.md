# Architecture

```
agent --(MCP tools, or blender_mcp.py over a socket)--> MCP for Blender add-on (127.0.0.1:9876) --> Blender (bpy)
agent --(render_bg.py)--> background Blender process --> PNG frames --(make_gif.py, ffmpeg)--> GIF / MP4
```

The add-on exposes `execute_blender_code`, `look`, `get_scene_info`, `get_addon_status`, asset search and import, and `generate_3d`. The skill only needs the first four. Everything it builds goes through `execute_blender_code`.

| File | Runs | Job |
|---|---|---|
| `scripts/bl_lib.py` | inside Blender | Units, materials, PNG to outline, extrusion, decals, studio, camera, animation, exports, report |
| `scripts/blender_mcp.py` | on your machine | Socket client for agents without the MCP tools: ping, run a file, run a line |
| `scripts/render_bg.py` | on your machine | Background Blender render of a saved copy: still or animation |
| `scripts/make_gif.py` | on your machine | ffmpeg: PNG sequence to GIF or MP4 |
| `scripts/make_viewer.py` | on your machine | GLB to a single-file `<model-viewer>` page |
| `scripts/new_project.py`, `check_setup.py` | on your machine | Project folder, setup check |
| `references/*.md` | read by the agent | Recipes, Blender notes, output formats, web 3D |

Design choices:

- **Helpers, not one tool per operation.** The add-on takes whole scripts, so the skill gives the agent a small library and rules.
- **Real units.** 1 Blender unit is 1 metre and sizes are written through `mm()`, so GLB, STL and AR need no rescaling.
- **Never destroy the user's scene.** `fresh_scene()` refuses anything but Blender's startup scene or one it built. Copies are saved with `save_copy`.
- **Long renders run outside the session.** A background process keeps Blender usable and the socket from timing out.
- **The render is the check.** Numbers can all be right while the picture is wrong, so every step ends with a look.
