"""Contact sheet of look-dev stills: python tools/contact.py out.jpg still1.png still2.png ..."""
import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
W, H = 270, 480
cols = min(len(files), 4)
rows = (len(files) + cols - 1) // cols
sh = Image.new('RGB', (cols * W, rows * (H + 18)), 'black')
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((W, H))
    x, y = (i % cols) * W, (i // cols) * (H + 18)
    sh.paste(im, (x, y + 18))
    ImageDraw.Draw(sh).text((x + 4, y + 3), f.split('/')[-1], fill='white')
sh.save(out, quality=88)
