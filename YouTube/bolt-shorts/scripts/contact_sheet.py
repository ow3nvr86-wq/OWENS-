"""Tile QC stills into a labelled contact sheet. usage: contact_sheet.py dir out.png [cols]"""
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
tw, th = 270, 480
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 26)), "white")
dr = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(os.path.join(d, f)).convert("RGB").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 26)
    sheet.paste(im, (x, y + 26))
    fr = int(f[1:4])
    dr.text((x + 6, y + 6), f"f{fr}  t={fr/30:.2f}s", fill="black")
sheet.save(out)
