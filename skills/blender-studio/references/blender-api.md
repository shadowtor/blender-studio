# Blender and bl_lib notes

Facts found building the examples in Blender 5.2. Prefer the live API: `bpy_api_lookup` and `describe_node_type` ride on the add-on, and Blender's Python console answers `dir()` faster than memory does.

## bl_lib functions

| Function | Does |
|---|---|
| `mm(x)` | Millimetres to metres. 1 Blender unit = 1 m so exports need no rescale |
| `fresh_scene(force=False)` | Empties the startup scene or a scene this skill built. Raises on user content |
| `render_setup(w, h, engine, samples, transparent, fps, frames, view)` | Engine `CYCLES` or `EEVEE`, size, film, fps, colour view (`Standard`) |
| `mat(name, color, rough, metal, **inputs)` | Principled. Extra: `transmission, ior, coat, coat_rough, emission, alpha, sheen` |
| `acrylic, vinyl, chrome, image_mat` | Clear acrylic, glossy vinyl, chrome, image (PNG alpha cut-out) |
| `cutline(png, width_mm, offset_mm, hole_mm, wall_mm)` | Outline loops of opaque pixels, grown by the border, with keyring tab and hole |
| `extrude_loops(loops, thickness_mm, name, z_mm, bevel_mm, material)` | Solid slab from loops, holes kept, welded mesh |
| `art_plane, split_ring, bake` | True-size artwork quad, ring, freeze a curve or modified object into a mesh |
| `decal(target, png, empty, size_mm, depth_mm)` | Print artwork onto an existing material, projected from an Empty |
| `stand(parts)` | Parent flat parts to an empty tilted upright (art faces -Y) |
| `studio(subject, bg, floor, power, ambient)` | Key, fill, rim area lights scaled to the subject, backdrop world, shadow-catcher floor |
| `camera(subject, az, el, lens, margin)` | Framed camera on a Track-To target |
| `explode, turntable, print_reveal` | Animation helpers (exploded view, 360 spin, layer reveal) |
| `still, save_copy, export, report` | Render a frame, save a copy for background render, export by extension, size and open-edge report |

## Gotchas that cost time

- **Fresh namespace per call.** Variables and imports do not survive between `execute_blender_code` calls. Re-import `bl_lib` each time. The scene itself persists.
- **Never `read_factory_settings`.** It resets add-ons, including the MCP add-on.
- **Glass needs Cycles.** In EEVEE the transmission material renders as an opaque grey slab. Cycles at 24 samples with the denoiser is enough for GIF frames (about 4 s a frame at 600 px on a CPU).
- **Glass and the backdrop.** Rays that refract through glass are no longer camera rays, so a world lit only for camera rays shows grey glass. `studio()` mixes in "Is Transmission Ray" so clear parts show the true backdrop colour.
- **Colours.** The default AgX view dulls flat artwork. `render_setup(view="Standard")` is the default here. Lower `studio(power=)` for glossy saturated materials, they clip to yellow quickly.
- **Floor.** `studio(floor=True)` adds a Cycles shadow catcher, so the backdrop is seamless and only the contact shadow shows. It does nothing in EEVEE.
- **Shader nodes by type, never by name.** Names are localised: `next(n for n in nodes if n.type == "BSDF_PRINCIPLED")`. Principled inputs are `Base Color, Roughness, Metallic, Transmission Weight, IOR, Coat Weight, Alpha, Emission Color, Emission Strength`.
- **Enums.** Read them: `bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items`. The engine list can under-report; assigning `"CYCLES"` in `try/except TypeError` is the test.
- **2D curve fill is the lazy way to extrude a shape with holes.** `dimensions="2D"`, `fill_mode="BOTH"`, `extrude=t/2` on a curve with several cyclic poly splines (inner loops are holes), then `bake()`. Curve-to-mesh leaves duplicate vertices, which makes STL and booleans fail: `bake()` welds them.
- **Keyframes.** Interpolation of new keys follows `preferences.edit.keyframe_new_interpolation_type`; `turntable()` switches it to LINEAR for the spin and restores it. Blender 5 changed the Action API (slots and layers), so do not walk `action.fcurves`.
- **Linear spin loops.** Key the last frame at `frames + 1` (same pose as frame 1) and render only `1..frames`.
- **Units.** 1 BU = 1 m. A 55 mm part is 0.055. A camera clip start of 1 mm (`0.001`) is set by `camera()`; the default 0.1 m clips tiny products.
- **Operators need context.** Prefer data API (`bpy.data`, `bmesh`). Where an operator is needed (`primitive_*_add`, `shade_smooth`, exports) it works from `execute_blender_code`.
- **Exports.** glTF: `export_apply=True` applies modifiers, KHR transmission carries the acrylic to web viewers, textures are embedded in GLB. STL: `bpy.ops.wm.stl_export`. OBJ: `wm.obj_export`. USD: `wm.usd_export`. FBX: `export_scene.fbx`.
- **Render in the foreground** blocks Blender and can time out the MCP socket. Use `render_bg.py` for animations and for anything over about a minute.
- **Eevee** setting names changed between versions. If a setting errors, read `dir(scene.eevee)`.
