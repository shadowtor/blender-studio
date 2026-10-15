# Acrylic keychain from a PNG

Built end to end by the skill in Blender 5.2 from [`../art/mochi.png`](../art/mochi.png).

| | |
|---|---|
| Brief | Die-cut acrylic keychain: two 3 mm clear layers around a printed sheet, 2.5 mm border, 4.5 mm hole, chrome split ring, exploded view for a campaign page |
| Parts | Back acrylic, printed sheet (55 mm wide), front acrylic, split ring |
| Size | 51.0 x 51.7 x 3.0 mm per acrylic layer, 0 open edges |
| Files | `keychain.glb` (web, 0.3 MB), `keychain.blend`, `exploded.gif`, `exploded.mp4`, `hero.png` |
| Not proven | The look of real acrylic and printed colours. Get a manufacturer proof |

Rebuild it: open Blender with the MCP add-on running, then run

```python
HERE = r"<path to this folder>"
exec(open(HERE + "/build.py").read())
```

Parameters (`WIDTH_MM`, `BORDER_MM`, `HOLE_MM`, `ACRYLIC_MM`, `GAP_MM`) are at the top of `build.py`. Set `OUT` to a folder first to also save the `.blend` and GLB.

Render the animation without blocking Blender:

```bash
python skills/blender-studio/scripts/render_bg.py examples/acrylic-keychain/keychain.blend --anim out/f_ --engine CYCLES --samples 20 --scale 47
python skills/blender-studio/scripts/make_gif.py "out/f_%04d.png" exploded.gif --fps 24 --width 480 --hold 0.4
```

Swap `ART` for your own PNG with a transparent background and rebuild. Opaque images are keyed against the corner colour.
