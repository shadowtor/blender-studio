# Recipes

Each recipe says what to ask, how to build it, what to check. **Tested** means the example in `examples/` was built and rendered with this skill. **Untested** means the helper exists and was exercised briefly but no full example has shipped, so check the first result carefully.

## Acrylic keychain and other die-cut merch (tested: `examples/acrylic-keychain`)

Ask: artwork (PNG with transparency), printed width in mm, acrylic thickness (3 mm is common), border around the art, hole diameter, ring size, single or double layer, deliverables.

1. `cut = cutline(art, width_mm, offset_mm=border, hole_mm=hole, wall_mm=2.5)` traces the opaque pixels, grows them by the border and adds a keyring tab with the hole. Opaque images are keyed against the corner colour: say so and check the outline.
2. `extrude_loops(cut["loops"], thickness, ...)` makes each acrylic layer. `art_plane()` is the printed sheet at true size between layers. `split_ring()` plus `chrome()` is the ring; hang it so its lower arc passes through the hole.
3. `acrylic()` is clear (transmission 1, IOR 1.49). It only reads as acrylic in **Cycles**; EEVEE shows grey slabs unless raytracing is tuned.
4. `stand(parts)` tips the flat parts upright to face the camera. `explode(parts, gap_mm)` keys the layers apart and back.
5. Variants: epoxy dome (a lens-shaped top layer), holographic (add `mat(..., metal=1)` with an iridescent texture), glitter (noise texture into roughness), standee (extrude a base slot), magnet or pin back (add a small cylinder).

Check: outline hugs the art with no stray islands, hole is round and clear, layer order is back, art, front, no layer intersects another, `report()` shows 0 open edges.

## Vinyl figurine or designer toy (tested: `examples/vinyl-figurine`)

Ask: reference images or a description, height in mm, colours, pose, base or no base, face or markings (artwork), deliverables. For a character from a drawing, ask for front and side views; build blocky first, then refine.

1. Block it with scaled UV spheres and cones (`blob()` in the example), `shade_smooth`, Subdivision on small parts. Curves with a bevel make tails and cables; `bake()` freezes them.
2. `vinyl(name, colour, rough=0.28)` is the glossy moulded look. Keep colours slightly more saturated than the target: Standard view with strong lights washes them out, so lower `studio(power=0.5)`.
3. Printed details: `decal(head, art, empty, size_mm, depth_mm)` projects artwork from an Empty onto an existing material. Place the empty on the front surface, rotate it `x = 90 deg` to face the front camera. The artwork must not contain parts that should not print (ears), crop it to the area that is printed.
4. `turntable(parts, frames)` spins the subject under fixed lights so the highlight slides across the surface.
5. For a **printable** figurine: Boolean-union parts that touch, keep walls over 1.2 mm, check `report()` for 0 open edges, export STL. Describe orientation and supports; do not claim it prints.
6. For realism the user asks for beyond blockout, `search_assets` and `generate_3d` can supply a base mesh. Ask first (cost, third-party upload).

## Apparel and merch mockups (untested as an example; `decal()` is tested on the figurine)

Ask: the item (t-shirt, hoodie, cap, mug, tote, hang tag, label, packaging), colours, artwork files and print size and position, view angles, flat product shot or on a model.

- You need a mesh of the item. Sources: the user's file, `search_assets` (Poly Haven, Sketchfab, Poly Pizza), or `generate_3d`. Generated and downloaded models arrive at arbitrary scale and orientation: size them with `world_bounding_box`, then put them on the ground.
- Rigid merch (mug, tote board, tag, label, box, can, bottle) works well: `decal()` the artwork, keep the empty scaled to the real print size in mm, set `depth_mm` to just past the surface thickness.
- Garments: print with `decal()` on a flat-ish area (chest). Wrinkles come from the mesh, not from simulation. Avoid wrapping artwork around seams. Fabric look: Principled with `sheen`, high roughness, a tiling weave normal map.
- Show it the way it sells: front and back, flat lay on a plain backdrop (`studio(floor=True)`), a close-up of the print, a colourway row (duplicate the object, change one colour).
- Say clearly that colours on screen are not a print proof.

## Exploded view (tested, part of the keychain)

`explode(parts, gap_mm, start, end, hold, back=True)` offsets part `i` by `i * gap` around the middle part, in the parts' local Z. Put the parts under a root (`stand()`) first so local Z is the stacking direction. Camera at about 25 to 40 degrees azimuth so the gaps show; a straight-on camera hides depth. Add extra keys for loose hardware (the ring lifts along its own axis). Ease is Blender's default Bezier. Callouts and labels: ask, then add text objects (`bpy.data.curves.new(type="FONT")`) facing the camera.

## Process simulation, for example a 3D printer making a product (untested as an example)

Ask: the product, the machine (FDM gantry, resin, CNC, injection mould), duration, camera, whether sound or captions are wanted (not produced here).

- `print_reveal(obj, start, end)` keys a box rising through the object with a Boolean Intersect, so the part appears layer by layer from the bed up. Checked on one mesh: empty at the first frame, half height at the midpoint, whole at the end. The Boolean stays live and is slow in the viewport; render in the background.
- Build a plausible machine from primitives (frame, bed, gantry, nozzle). Key the nozzle to follow the cutter height plus a small circular XY motion. Add a faint emissive glow at the nozzle and a thin cylinder as filament.
- Add a glow plus a small point light at the nozzle tip for depth. Finish with a timelapse feel: ease out at the end, hold 1 s, then orbit the camera once.
- Do not claim the motion is a real toolpath. It is a visual stand-in.

## Interactive 3D website (tested: `examples/` page, see `site/`)

Build the model with textures at most 2048 px, no hidden geometry, a clear name per part. `export("exports/x.glb", objs)`, then `make_viewer.py`. Anything animated in Blender (explode, spin) does not need to be exported: model-viewer orbits the camera for free. If the page needs the explode itself, export animation (`export_animations`) or split into parts and animate in three.js. Details in [web-3d.md](web-3d.md).

## Rules for every recipe

- Dimensions come from the user. Name them at the top of the build script.
- Put the product in the centre, 0.2 mm bevels on acrylic and hard goods so edges catch light, soft three-light studio, Standard view transform for brand-true colours.
- One variation request should change one parameter and re-render, not restart.
