# Interactive 3D on a website

## Fastest path: `<model-viewer>`

```bash
python scripts/make_viewer.py exports/keychain.glb exports/index.html --title "Mochi keychain" --rotate
```

Writes one HTML file that loads Google's `<model-viewer>` (pinned version, Subresource Integrity hash) and shows the GLB with orbit, zoom, soft shadow and an AR button on phones that support it. Embed the page in an `<iframe>` or copy the `<model-viewer>` tag into your own page. Useful attributes: `auto-rotate`, `camera-orbit="30deg 80deg auto"`, `exposure`, `shadow-intensity`, `poster` (an image shown while the model loads), `environment-image="neutral"`, `ar-modes`.

## Preparing the GLB

- Real scale in metres (the library does this), upright with +Y up in the file (the exporter converts).
- Under 5 MB. Textures at most 2048 px, JPEG for photos, PNG for artwork with alpha. Delete hidden geometry. Keep triangles under about 100 k.
- Transmission (acrylic) and clearcoat (vinyl) export as KHR extensions, which model-viewer renders. The look differs from Cycles: lit by an environment map, no path-traced caustics. Always judge the web version in the browser, not by the render.
- Smaller files: `npx @gltf-transform/cli optimize in.glb out.glb --texture-compress webp` (Draco or Meshopt for meshes). Run it only when asked, it needs Node.
- Do not ship licensed assets (Sketchfab, Poly Pizza) without checking their licence.

## When you need more than a viewer

Three.js with `GLTFLoader` gives custom explode controls, hotspots and scroll-driven animation. Export the parts as separate named nodes and move them in code, rather than baking an animation. Test on a phone-width viewport: touch orbit, load time on a slow connection, and `prefers-reduced-motion` (turn off `auto-rotate`).

## Checklist

1. Opens with the model centred, not clipped or tiny.
2. Orbit and zoom work with mouse and touch.
3. First load is under about 3 s on a normal connection (check the file size).
4. Console is clean, no failed requests.
5. A `poster` image is set so something shows immediately.
