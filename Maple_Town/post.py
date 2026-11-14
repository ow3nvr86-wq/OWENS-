"""Assemble the Short: rendered frames (15 fps, 540 x 960) -> 1080 x 1920 at 30 fps, with one-word captions (lowercase,
yellow, black outline) timed to the narration, and the soundtrack.   $SHORTS_PY post.py [--partial] -> final_video.mp4"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
DUR, FPS, RFPS = 38.0, 30, 15
W = json.load(open(os.path.join(ROOT, 'build', 'words.json')))['words']
FONT = ImageFont.truetype(os.path.join(ROOT, 'assets', 'Inter-Black.otf'), 104)
_C = {}


def caption(word):
    if word not in _C:
        d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
        b = d0.textbbox((0, 0), word, font=FONT, stroke_width=12)
        im = Image.new('RGBA', (b[2] - b[0] + 40, b[3] - b[1] + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((20 - b[0], 26 - b[1]), word, font=FONT, fill=(0, 0, 0, 150), stroke_width=12, stroke_fill=(0, 0, 0, 150))
        d.text((20 - b[0], 20 - b[1]), word, font=FONT, fill=(255, 221, 51, 255), stroke_width=12, stroke_fill=(10, 10, 14, 255))
        _C[word] = im
    return _C[word]


def main():
    fr = os.path.join(ROOT, 'build', 'frames')
    n = int(DUR * FPS)
    have = [os.path.exists(os.path.join(fr, f'f_{k:05d}.png')) for k in range(int(DUR * RFPS))]
    if not all(have) and '--partial' not in sys.argv:
        sys.exit(f'{sum(have)}/{len(have)} frames rendered; pass --partial to assemble anyway')
    out = os.path.join(ROOT, 'final_video.mp4')
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', str(FPS), '-i', '-',
                           '-i', os.path.join(ROOT, 'audio', 'mix_with_voice.wav'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
                           '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                           '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    last, base, kprev = None, None, -1
    for f in range(n):
        t = f / FPS
        k = min(int(t * RFPS), len(have) - 1)
        if k != kprev:
            p = os.path.join(fr, f'f_{k:05d}.png')
            if os.path.exists(p):
                base = Image.open(p).convert('RGB').resize((1080, 1920), Image.LANCZOS)
            elif base is None:
                base = Image.new('RGB', (1080, 1920))
            kprev = k
        im = base.copy()
        for i, w in enumerate(W):
            end = W[i + 1]['start'] if i + 1 < len(W) else w['end'] + 0.5
            if w['start'] <= t < min(end, w['end'] + 0.6):
                c = caption(w['w'].lower().strip('.,'))
                u = min(1.0, (t - w['start']) / 0.1)
                s = 1.18 - 0.18 * (1 - (1 - u) ** 3)
                c2 = c.resize((int(c.width * s), int(c.height * s)), Image.BILINEAR)
                im.paste(c2, (540 - c2.width // 2, 1210 - c2.height // 2), c2)
                break
        pr.stdin.write(np.asarray(im).tobytes())
    pr.stdin.close()
    pr.wait()
    print('wrote', out)


main()
