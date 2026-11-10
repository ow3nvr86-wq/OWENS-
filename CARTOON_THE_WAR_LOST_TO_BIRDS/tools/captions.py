"""Burn word-by-word captions onto the rendered frames (house style: Anton, uppercase, white with a black outline and a
soft shadow, the spoken word in amber, max 3 words / 17 characters per chunk, centred about 64 % down; numbers in
digits). Timing comes from work/words.json (Whisper word times snapped to the narration's pauses).
Run: $SHORTS_PY tools/captions.py [frames_in] [frames_out]   -> build/frames_cap/f0000.jpg ...
     $SHORTS_PY tools/captions.py --test 300,700           (writes a few frames to build/look/cap_test)"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
FONT = os.path.join(HERE, 'web', 'fonts', 'Anton-Regular.ttf')
W, H = 1080, 1920
SIZE = 100
Y_DEFAULT = 0.64
WHITE, AMBER, BLACK = (255, 255, 255), (255, 176, 32), (0, 0, 0)
# spoken numbers -> digits on screen (each entry: spoken words, caption token)
NUMBERS = [(['nineteen', 'thirty-two.'], '1932.'), (['Twenty', 'thousand'], '20,000'), (['ten', 'thousand'], '10,000'),
           (['two'], '2'), (['ten', 'bullets'], None)]
# shots whose middle of frame holds readable props (letters, map, notepad): captions drop lower there
LOW = [(183, 262), (441, 490), (619, 705), (1026, 1094), (1095, 1207)]
Y_LOW = 0.80


def tokens():
    """Caption tokens with start/end times: words, with spoken numbers merged into digits."""
    words = json.load(open(os.path.join(HERE, 'work', 'words.json')))['words']
    out, i = [], 0
    while i < len(words):
        w = words[i]
        merged = False
        for spoken, shown in NUMBERS:
            if shown and [x['word'] for x in words[i:i + len(spoken)]] == spoken:
                out.append(dict(text=shown, start=w['start'], end=words[i + len(spoken) - 1]['end'], line=w['line']))
                i += len(spoken); merged = True; break
        if merged: continue
        text = w['word']
        if text == 'ten' and i + 1 < len(words) and words[i + 1]['word'] == 'bullets': text = '10'
        out.append(dict(text=text, start=w['start'], end=w['end'], line=w['line']))
        i += 1
    return out


def chunks(toks):
    """Split each spoken phrase (ending at punctuation) into balanced chunks of <= 3 words / <= 17 characters."""
    phrases, cur = [], []
    for t in toks:
        cur.append(t)
        if re.search(r'[.,?!:]$', t['text']): phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    # glue a very short phrase ("so the farmers," is fine; "two guns," etc.) onto nothing - keep phrases as units
    out = []
    for ph in phrases:
        nw = len(ph); nc = len(' '.join(x['text'] for x in ph))
        k = max(-(-nw // 3), -(-nc // 17))
        while True:
            sizes = [nw // k + (1 if i < nw % k else 0) for i in range(k)]
            parts, i = [], 0
            for sz in sizes: parts.append(ph[i:i + sz]); i += sz
            if all(len(' '.join(x['text'] for x in p)) <= 17 for p in parts) or k >= nw: break
            k += 1
        out.extend(parts)
    # times: a chunk shows from its first word until the next chunk starts (or 0.35 s after its last word)
    res = []
    for k, c in enumerate(out):
        a = c[0]['start'] - 0.03
        nxt = out[k + 1][0]['start'] - 0.03 if k + 1 < len(out) else 1e9
        b = min(nxt, c[-1]['end'] + 0.35)
        res.append(dict(words=c, start=a, end=b))
    return res


FONT_OBJ = ImageFont.truetype(FONT, SIZE)


def draw_chunk(im, ch, t, y_frac):
    words = [w['text'].upper() for w in ch['words']]
    # active word: the last word whose start has passed
    act = max([k for k, w in enumerate(ch['words']) if w['start'] - 0.03 <= t] or [0])
    # pop-in: scale 0.82 -> 1 over the first 4 frames of the chunk
    age = (t - ch['start']) * FPS
    sc = 1.0 if age >= 4 else 0.82 + 0.18 * (1 - (1 - age / 4) ** 2)
    font = FONT_OBJ if sc >= 0.999 else ImageFont.truetype(FONT, max(10, int(SIZE * sc)))
    space = font.getlength(' ')
    widths = [font.getlength(w) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    x0 = (W - total) / 2
    y = int(H * y_frac)
    stroke = max(4, int(9 * sc))
    # soft shadow layer
    sh = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(sh)
    x = x0
    for w, ww in zip(words, widths):
        sd.text((x + 5, y + 7), w, font=font, fill=170, anchor='lm', stroke_width=stroke, stroke_fill=170)
        x += ww + space
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    im.paste((0, 0, 0), (0, 0), sh)
    d = ImageDraw.Draw(im)
    x = x0
    for k, (w, ww) in enumerate(zip(words, widths)):
        d.text((x, y), w, font=font, fill=AMBER if k == act else WHITE, anchor='lm', stroke_width=stroke, stroke_fill=BLACK)
        x += ww + space


def y_for(f):
    return Y_LOW if any(a <= f <= b for a, b in LOW) else Y_DEFAULT


def main():
    args = sys.argv[1:]
    test = None
    if args and args[0] == '--test':
        test = [int(v) for v in args[1].split(',')]; args = []
    src = args[0] if args else os.path.join(HERE, 'frames')
    dst = args[1] if len(args) > 1 else os.path.join(HERE, 'build', 'frames_cap')
    if test: dst = os.path.join(HERE, 'build', 'look', 'cap_test')
    os.makedirs(dst, exist_ok=True)
    CH = chunks(tokens())
    json.dump([dict(text=' '.join(w['text'] for w in c['words']), start=round(c['start'], 3), end=round(c['end'], 3)) for c in CH],
              open(os.path.join(HERE, 'work', 'caption_chunks.json'), 'w'), indent=1)
    n = len([f for f in os.listdir(src) if f.endswith('.jpg')])
    for f in (test or range(n)):
        t = f / FPS
        im = Image.open(os.path.join(src, 'f%04d.jpg' % f)).convert('RGB')
        for ch in CH:
            if ch['start'] <= t < ch['end']:
                draw_chunk(im, ch, t, y_for(f)); break
        im.save(os.path.join(dst, 'f%04d.jpg' % f), quality=95)
    print('captioned', len(test or range(n)), 'frames ->', dst, '|', len(CH), 'chunks')


if __name__ == '__main__':
    main()
