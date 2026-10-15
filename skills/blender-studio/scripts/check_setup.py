#!/usr/bin/env python3
"""Check Python, the MCP for Blender socket, a Blender executable (background renders) and ffmpeg (GIF/MP4 only).
Exit 1 only when Blender cannot be reached."""
import os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_mcp
from render_bg import find_blender

bad = 0
print("OK   Python", sys.version.split()[0]) if sys.version_info >= (3, 8) else print("FAIL Python 3.8+ needed")
try:
    r = blender_mcp.call("get_addon_info", timeout=5)["result"]
    print("OK   Blender", r.get("blender_version"), "| add-on", ".".join(map(str, r.get("addon_version", []))))
except Exception as e:
    print(f"FAIL cannot reach Blender at {blender_mcp.HOST}:{blender_mcp.PORT} - {e}\n"
          "     Install the add-on (uvx mcp-for-blender install-addon), enable it, then N panel > MCP for Blender > Start MCP Server.")
    bad = 1
exe = find_blender()
print("OK   Blender executable", exe) if exe else print("WARN no Blender executable found; set BLENDER_EXE for background renders")
print("OK   ffmpeg", shutil.which("ffmpeg")) if shutil.which("ffmpeg") else print(
    "WARN ffmpeg not on PATH; needed only for GIF and web MP4 (winget install ffmpeg / brew install ffmpeg)")
sys.exit(bad)
