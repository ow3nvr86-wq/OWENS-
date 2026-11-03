"""Word-by-word caption images for the edit (Pillow): build/captions/cap_NNNN.png + build/captions/index.json.

Anton, uppercase, white with a thick black outline and a soft shadow; the word being spoken is amber. At most three
words per chunk (chunks come from tools/voiceover.py), centred about 64% of the way down the 1080x1920 frame. Key moments (scene_timing.json "keys") replace the word-by-word
captions with one large amber phrase that pops in (EVERYONE IS GONE., THE ENTIRE WORLD IS YOURS., ...).

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


def render_key(text, path, size=150):
    lines = text.split('|')
    font = ImageFont.truetype(FONT, size)
    while max(font.getlength(l) for l in lines) > W - 140 and size > 70:
        size -= 6
        font = ImageFont.truetype(FONT, size)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(shadow)
    lh = size * 1.12
    y0 = CY - lh * (len(lines) - 1) / 2
    for i, l in enumerate(lines):
        y = y0 + i * lh
        ds.text((W / 2 + 7, y + 9), l, font=font, fill=(0, 0, 0, 180), anchor='mm', stroke_width=12, stroke_fill=(0, 0, 0, 180))
        d.text((W / 2, y), l, font=font, fill=AMBER, anchor='mm', stroke_width=11, stroke_fill=(0, 0, 0, 255))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    Image.alpha_composite(shadow, img).save(path, optimize=True)


def norm(w):
    return ''.join(ch for ch in w.lower() if ch.isalnum())


def key_windows(lines):
    with open(os.path.join(ROOT, 'scene_timing.json')) as fh:
        keys = json.load(fh).get('keys', [])
    words = [w for ln in lines for w in ln['words']]
    out = []
    for k in keys:
        if 'match' in k:
            target = [norm(x) for x in k['match'].split()]
            for i in range(len(words) - len(target) + 1):
                if [norm(w['w']) for w in words[i:i + len(target)]] == target:
                    out.append((words[i]['start'], words[i + len(target) - 1]['end'] + 0.45, k['text']))
                    break
            else:
                print('key caption not found in the narration:', k['match'])
        else:
            out.append((k['start'], k['end'], k['text']))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(ROOT, 'build', 'vo_timing.json')) as fh:
        lines = json.load(fh)['lines']
    keys = key_windows(lines)
    index = []
    n = 0
    for k, (a, b, text) in enumerate(keys):
        path = os.path.join(OUT, f'key_{k:02d}.png')
        render_key(text, path)
        index.append({'file': os.path.basename(path), 'start': round(a, 3), 'end': round(b, 3), 'text': text.replace('|', ' '), 'key': True})
    inkey = lambda t: any(a - 0.05 <= t < b for a, b, _ in keys)
    chunks = [c for ln in lines for c in ln['chunks'] if not inkey((c['start'] + c['end']) / 2)]
    for ci, c in enumerate(chunks):
        words = [w['w'].upper() for w in c['words']]
        nxt = chunks[ci + 1]['start'] if ci + 1 < len(chunks) else c['end'] + 0.5
        end = nxt if nxt - c['end'] < MAX_GAP else c['end'] + 0.1
        for k, w in enumerate(c['words']):
            t0 = w['start'] if k else c['start']
            t1 = c['words'][k + 1]['start'] if k + 1 < len(c['words']) else end
            for a, b, _ in keys:
                if t0 < a < t1:
                    t1 = a
            path = os.path.join(OUT, f'cap_{n:04d}.png')
            render(words, k, path)
            index.append({'file': os.path.basename(path), 'start': round(t0, 3), 'end': round(t1, 3), 'text': ' '.join(words)})
            n += 1
    with open(os.path.join(OUT, 'index.json'), 'w') as fh:
        json.dump(index, fh, indent=1)
    print('captions:', n, 'images in', OUT)


if __name__ == '__main__':
    main()
