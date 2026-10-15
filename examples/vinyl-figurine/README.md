# Vinyl figurine with a printed face

Built end to end by the skill in Blender 5.2. The face is [`../art/mochi_face.png`](../art/mochi_face.png) projected onto the head with `decal()`.

| | |
|---|---|
| Brief | A designer-toy cat on a round base, glossy vinyl, brand face artwork, a full turn for a campaign GIF |
| Parts | Base, body, belly, head, ears, arms, feet, tail |
| Size | 68 x 73 x 95.6 mm overall, all 11 parts closed meshes (0 open edges) |
| Files | `figurine.glb` (0.5 MB), `figurine.blend`, `turntable.gif`, `hero.png` |
| Not proven | Moulding. This is a blockout of separate overlapping parts, not a union mesh with draft angles and wall thickness. It would need that work before an STL goes to a factory |

Rebuild: run `build.py` in a Blender with the MCP add-on running (see the keychain example for the two-line launcher).
Render the turn in the background and make the GIF:

```bash
python skills/blender-studio/scripts/render_bg.py examples/vinyl-figurine/figurine.blend --anim out/f_ --engine CYCLES --samples 20 --scale 55 --end 119 --step 2
python skills/blender-studio/scripts/make_gif.py "out/f_*.png" turntable.gif --fps 24 --width 440
```
