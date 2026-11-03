"""Word-by-word caption images for the edit (Pillow): build/captions/cap_NNNN.png + build/captions/index.json.

Anton, uppercase, white with a thick black outline and a soft shadow; the word being spoken is amber. At most three
words per chunk (chunks come from tools/voiceover.py), centred about 64% of the way down the 1080x1920 frame.

    $SHORTS_PY tools/captions.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'captions')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'Anton-Regular.ttf')
W, H = 1080, 1920
CY = int(H * 0.64)
WHITE, AMBER = (255, 255, 255, 255), (255, 184, 36, 255)
MAX_GAP = 0.35


def render(words, active, path, size=104):
    font = ImageFont.truetype(FONT, size)
    sp = font.getlength(' ')
    widths = [font.getlength(w) for w in words]
    total = sum(widths) + sp * (len(words) - 1)
    while total > W - 120 and size > 60:
        size -= 6
        font = ImageFont.truetype(FONT, size)
        sp = font.getlength(' ')
        widths = [font.getlength(w) for w in words]
        total = sum(widths) + sp * (len(words) - 1)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(shadow)
    x = (W - total) / 2
    for i, (w, wd) in enumerate(zip(words, widths)):
        ds.text((x + 6, CY + 8), w, font=font, fill=(0, 0, 0, 170), anchor='lm', stroke_width=10, stroke_fill=(0, 0, 0, 170))
        d.text((x, CY), w, font=font, fill=AMBER if i == active else WHITE, anchor='lm', stroke_width=9, stroke_fill=(0, 0, 0, 255))
        x += wd + sp
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    Image.alpha_composite(shadow, img).save(path, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(ROOT, 'build', 'vo_timing.json')) as fh:
        lines = json.load(fh)['lines']
    chunks = [c for ln in lines for c in ln['chunks']]
    index = []
    n = 0
    for ci, c in enumerate(chunks):
        words = [w['w'].upper() for w in c['words']]
        nxt = chunks[ci + 1]['start'] if ci + 1 < len(chunks) else c['end'] + 0.5
        end = nxt if nxt - c['end'] < MAX_GAP else c['end'] + 0.1
        for k, w in enumerate(c['words']):
            t0 = w['start'] if k else c['start']
            t1 = c['words'][k + 1]['start'] if k + 1 < len(c['words']) else end
            path = os.path.join(OUT, f'cap_{n:04d}.png')
            render(words, k, path)
            index.append({'file': os.path.basename(path), 'start': round(t0, 3), 'end': round(t1, 3), 'text': ' '.join(words)})
            n += 1
    with open(os.path.join(OUT, 'index.json'), 'w') as fh:
        json.dump(index, fh, indent=1)
    print('captions:', n, 'images in', OUT)


if __name__ == '__main__':
    main()
