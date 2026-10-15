"""Draws the sample artwork used by the examples: Mochi, a cat head on a transparent background. Needs Pillow."""
import os
from PIL import Image, ImageDraw

S, K = 600, 4  # final size, supersampling
W = S * K
im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
k = lambda *v: [x * K for x in v]

CREAM, PINK, INK, ORANGE = (252, 238, 214, 255), (244, 143, 177, 255), (43, 33, 51, 255), (255, 167, 87, 255)
d.polygon(k(95, 250, 105, 70, 255, 150), fill=ORANGE)       # ears
d.polygon(k(505, 250, 495, 70, 345, 150), fill=ORANGE)
d.polygon(k(130, 215, 135, 112, 220, 165), fill=PINK)
d.polygon(k(470, 215, 465, 112, 380, 165), fill=PINK)
d.ellipse(k(50, 120, 550, 560), fill=CREAM)                   # head
d.pieslice(k(50, 120, 550, 560), 195, 345, fill=ORANGE)       # forehead patch
for x in (205, 395):                                          # eyes
    d.ellipse(k(x - 38, 290, x + 38, 380), fill=INK)
    d.ellipse(k(x - 20, 303, x - 2, 321), fill=(255, 255, 255, 255))
d.polygon(k(270, 392, 330, 392, 300, 424), fill=PINK)         # nose
d.arc(k(240, 400, 300, 460), 20, 160, fill=INK, width=5 * K)  # mouth
d.arc(k(300, 400, 360, 460), 20, 160, fill=INK, width=5 * K)
for y in (405, 435):                                          # whiskers
    d.line(k(70, y, 175, y + (y - 420) * .4), fill=INK, width=4 * K)
    d.line(k(530, y, 425, y + (y - 420) * .4), fill=INK, width=4 * K)
d.ellipse(k(120, 395, 175, 440), fill=(244, 143, 177, 150))   # blush
d.ellipse(k(425, 395, 480, 440), fill=(244, 143, 177, 150))

here = os.path.dirname(os.path.abspath(__file__))
im.resize((S, S), Image.LANCZOS).save(os.path.join(here, "mochi.png"))

# face only, no ears: this is what gets printed onto the vinyl figurine's head
face = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(face)
d.ellipse(k(50, 120, 550, 560), fill=CREAM)
d.pieslice(k(50, 120, 550, 560), 195, 345, fill=ORANGE)
face.alpha_composite(im.crop((0, 270 * K, W, W)), (0, 270 * K))  # eyes, nose, mouth, whiskers, blush
face.resize((S, S), Image.LANCZOS).save(os.path.join(here, "mochi_face.png"))
print("wrote mochi.png and mochi_face.png")
