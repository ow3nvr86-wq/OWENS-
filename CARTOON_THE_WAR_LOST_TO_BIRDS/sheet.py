"""Contact sheet: python3 sheet.py <dir> <out.jpg> [cols]  (labels each still with its frame number)"""
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
fs = sorted(glob.glob(os.path.join(d, 'f*.jpg')))
ims = [Image.open(f).convert('RGB') for f in fs]
w = 300; h = int(w * 16 / 9)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * (h + 26)), (20, 20, 20))
g = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'fonts', 'Anton-Regular.ttf'), 20)
except Exception:
    font = None
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * (h + 26)
    sheet.paste(im.resize((w, h)), (x, y + 26))
    g.text((x + 6, y + 2), os.path.basename(f)[1:5], fill=(255, 210, 90), font=font)
sheet.save(out, quality=88)
print(out, len(ims))
