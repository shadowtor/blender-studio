#!/usr/bin/env python3
"""Turn a PNG sequence or video into a GIF (Kickstarter pages, social posts) or a web MP4, through ffmpeg.

  python make_gif.py out/frame_%04d.png out/spin.gif --fps 24 --width 480
  python make_gif.py out/frame_%04d.png out/spin.mp4 --fps 30 --width 1080
  python make_gif.py "out/frame_*.png" out/spin.gif        # frames with gaps (render_bg.py --step 2) need the * form

GIF: two-pass palette (clean colours, small file). MP4/WebM: H.264 or VP9, yuv420p, plays everywhere.
Render GIF and MP4 frames with an opaque background (film_transparent off): GIF transparency looks jagged.
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("src", help="frame pattern like frame_%%04d.png, a glob like \"frame_*.png\", or a video file")
ap.add_argument("dst", help=".gif, .mp4 or .webm")
ap.add_argument("--fps", type=int, default=24)
ap.add_argument("--width", type=int, default=480)
ap.add_argument("--hold", type=float, default=0.0, help="seconds to hold the last frame before looping")
a = ap.parse_args()
ff = shutil.which("ffmpeg") or sys.exit("ffmpeg not found (winget install ffmpeg / brew install ffmpeg)")
if "*" in a.src:  # numbered with gaps: feed the sorted files through a concat list
    files = sorted(glob.glob(a.src)) or sys.exit("no frames match " + a.src)
    lst = os.path.join(tempfile.mkdtemp(), "frames.txt")
    with open(lst, "w") as fh:
        for f in files:
            fh.write("file '%s'\n" % os.path.abspath(f).replace("\\", "/"))
            fh.write("duration %f\n" % (1 / a.fps))
    inp = ["-f", "concat", "-safe", "0", "-i", lst]
else:
    inp = ["-framerate", str(a.fps), "-i", a.src] if "%" in a.src else ["-i", a.src]
ext = os.path.splitext(a.dst)[1].lower()
hold = f",tpad=stop_mode=clone:stop_duration={a.hold}" if a.hold else ""
if ext == ".gif":
    vf = f"[0:v]scale={a.width}:-2:flags=lanczos{hold},split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
    cmd = [ff, "-y", *inp, "-filter_complex", vf, "-loop", "0", a.dst]
elif ext in (".mp4", ".webm"):
    codec = (["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart"] if ext == ".mp4"
             else ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-pix_fmt", "yuv420p"])
    cmd = [ff, "-y", *inp, "-vf", f"scale={a.width}:-2:flags=lanczos{hold}", *codec, a.dst]
else:
    sys.exit("dst must end in .gif, .mp4 or .webm")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode:
    sys.exit(r.stderr[-1500:])
print(f"{a.dst}  {os.path.getsize(a.dst) / 1e6:.2f} MB")
