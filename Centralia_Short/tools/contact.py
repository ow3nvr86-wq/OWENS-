"""Contact sheet of still_*.png files: python contact.py DIR OUT [cols]"""
import os, sys
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
fs = sorted(f for f in os.listdir(d) if f.startswith('still_') and f.endswith('.png'))
ims = [Image.open(os.path.join(d, f)).convert('RGB') for f in fs]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, h * rows), (30, 30, 30))
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im.resize((w, h)), (x, y))
    ImageDraw.Draw(sheet).text((x + 4, y + 4), f[6:10], fill=(255, 255, 0))
sheet.save(out)
print(out, sheet.size)
