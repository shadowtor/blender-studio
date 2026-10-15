# Outputs: formats, sizes, presets

## Pick the file

| Need | File | Notes |
|---|---|---|
| Interactive web, AR, quick share | `.glb` | Embedded textures, materials carry over. Keep under 5 MB |
| 3D printing | `.stl` (single colour) or `.3mf` via a slicer import | Watertight, `report()` shows 0 open edges, metric scale is exact |
| Other 3D tools, game engines | `.fbx`, `.obj`, `.usd` | OBJ loses animation. FBX and USD keep it |
| Editable source | `.blend` | `save_copy()` so the user's session is not renamed |
| Still image | `.png` | Transparent when `render_setup(transparent=True)` |
| Video for a page or ad | `.mp4` H.264 | `make_gif.py` produces web-safe yuv420p |
| Looping clip for a Kickstarter page | `.gif` | 480 to 600 px wide, 15 to 24 fps, under 10 MB. MP4 is smaller and sharper where the platform accepts it |

## Resolution and time presets

| Use | Size | Engine and samples | Cost on a CPU (simple scene) |
|---|---|---|---|
| Check render | 700 x 700 | Cycles 24 | about 10 to 20 s |
| Hero still | 2048 x 2048 or 1920 x 1080 | Cycles 128 plus denoise | 1 to 4 min |
| GIF frames | 600 x 600 | Cycles 20 plus denoise | about 4 s a frame |
| MP4 1080p | 1920 x 1080 | Cycles 32 plus denoise | 15 to 40 s a frame, run in background |
| Social square | 1080 x 1080 | as hero | |
| Kickstarter header | 1600 x 900 (16:9) | as hero | |

A GPU cuts these a lot; set it in Preferences > System, the skill does not change preferences.

## Animation lengths

Exploded view: 1.5 s open, 0.7 s hold, 1.5 s close. Turntable: 4 to 6 s, 120 to 180 frames at 30 fps, seamless. Process clips: 8 to 15 s. Keep GIFs under 4 s unless asked.

## Transparent output

Transparent PNG stills: `render_setup(transparent=True)`. GIF has 1-bit transparency and looks jagged on soft edges, so render GIFs on a backdrop that matches the page. For video with transparency use WebM VP9 with alpha or an image sequence.

## Naming

`<product>_<view>_<size>.png`, `<product>_<action>.mp4`. Keep the project's `build/` script and the `.blend` with the outputs so any change is a re-run.
