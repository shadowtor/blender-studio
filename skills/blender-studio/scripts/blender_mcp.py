#!/usr/bin/env python3
"""Tiny stdlib client for the MCP for Blender add-on socket (default 127.0.0.1:9876), for agents that do not load
the MCP tools. With the MCP tools loaded, use execute_blender_code instead.

  python blender_mcp.py ping
  python blender_mcp.py run build.py [--lib]     # --lib imports bl_lib first; HERE is set to the script's folder
  python blender_mcp.py code "print(bpy.app.version_string)" [--lib]

Set BLENDER_HOST / BLENDER_PORT to change the address. The socket has no authentication: keep it on localhost.
"""
import json, os, socket, sys

HOST, PORT = os.environ.get("BLENDER_HOST", "127.0.0.1"), int(os.environ.get("BLENDER_PORT", "9876"))
HERE = os.path.dirname(os.path.abspath(__file__))


def call(kind, params=None, timeout=300):
    with socket.create_connection((HOST, PORT), timeout=10) as s:
        s.settimeout(timeout)
        s.sendall(json.dumps({"type": kind, "params": params or {}}).encode())
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            try:
                return json.loads(buf)
            except ValueError:
                continue
    raise SystemExit("no complete reply from Blender")


def main(argv):
    if not argv or argv[0] not in ("ping", "run", "code"):
        sys.exit(__doc__)
    try:
        if argv[0] == "ping":
            r = call("get_addon_info")
            print(json.dumps(r.get("result", r), indent=2))
            return 0
        if argv[0] == "run":
            code = open(argv[1], encoding="utf-8").read()
            code = f'HERE = r"{os.path.dirname(os.path.abspath(argv[1]))}"\n' + code
        else:
            code = argv[1]
        if "--lib" in argv:
            code = f'import sys; sys.path.insert(0, r"{HERE}")\nfrom bl_lib import *\n' + code
        r = call("execute_code", {"code": code})
    except OSError as e:
        sys.exit(f"cannot reach Blender at {HOST}:{PORT} ({e}). Open Blender, press N in the 3D viewport, "
                 "MCP for Blender tab, Start MCP Server.")
    ok = r.get("status") == "success"
    print(r.get("result", r) if ok else "ERROR: " + str(r.get("message", r)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
