"""Genera l'icona PocketPSX-GUI: console 3DS + simboli PlayStation."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "assets"
SIZE = 512

# palette
BG = (27, 30, 38, 255)
PS_BLUE = (0, 55, 145, 255)
PS_TEAL = (0, 129, 145, 255)
SCREEN_TOP = (16, 20, 34, 255)
SCREEN_BOT = (10, 60, 70, 255)
GREEN = (0, 200, 120, 255)
RED = (230, 60, 90, 255)
BLUE = (60, 140, 255, 255)
PINK = (255, 110, 200, 255)
WHITE = (240, 244, 255, 255)
GREY = (150, 160, 180, 255)


def rrect(d, box, r, **kw):
    d.rounded_rectangle(box, radius=r, **kw)


img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# base console body
rrect(d, [16, 16, SIZE - 16, SIZE - 16], 90, fill=BG, outline=PS_BLUE, width=10)
# subtle inner border
rrect(d, [34, 34, SIZE - 34, SIZE - 34], 72, outline=(70, 90, 130, 255), width=3)

# ---- top screen (3DS upper) ----
rrect(d, [80, 70, SIZE - 80, 280], 28, fill=SCREEN_TOP, outline=PS_TEAL, width=6)
# glow line under top screen
d.line([110, 292, SIZE - 110, 292], fill=PS_TEAL, width=4)

# PS symbols on top screen: triangle, circle, cross, square
cx, cy, s = SIZE // 2, 175, 34
# triangle (green)
d.polygon([(cx - 150, cy + 28), (cx - 110, cy + 28), (cx - 130, cy - 8)], outline=GREEN, width=7)
# circle (red)
d.ellipse([cx - 45, cy - 28, cx + 15, cy + 32], outline=RED, width=7)
# cross (blue)
d.line([cx + 55, cy - 25, cx + 115, cy + 35], fill=BLUE, width=8)
d.line([cx + 55, cy + 35, cx + 115, cy - 25], fill=BLUE, width=8)
# square (pink)
d.rectangle([cx - 150, cy + 55, cx - 100, cy + 105], outline=PINK, width=7)

# ---- hinge ----
d.line([60, 310, SIZE - 60, 310], fill=(60, 70, 90, 255), width=10)

# ---- bottom screen (3DS lower, touch) ----
rrect(d, [110, 330, SIZE - 110, 440], 24, fill=SCREEN_BOT, outline=(120, 200, 210, 255), width=5)

# text on bottom screen
try:
    font = ImageFont.truetype("arialbd.ttf", 56)
    small = ImageFont.truetype("arial.ttf", 26)
except OSError:
    font = ImageFont.load_default()
    small = font
d.text((SIZE // 2, 372), "PSX", fill=WHITE, font=font, anchor="mm")
d.text((SIZE // 2, 412), "• 3DS •", fill=(170, 220, 230, 255), font=small, anchor="mm")

# side buttons (dpad left / ABXY right hints)
d.ellipse([48, 350, 88, 390], outline=GREY, width=5)          # left round button
d.ellipse([SIZE - 88, 350, SIZE - 48, 390], outline=GREY, width=5)  # right round button
d.ellipse([62, 364, 74, 376], fill=GREY)
d.ellipse([SIZE - 74, 364, SIZE - 62, 376], fill=GREY)

out_png = OUT / "icon.png"
img.save(out_png)
img.convert("RGB").save(OUT / "icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"OK: {out_png}")
