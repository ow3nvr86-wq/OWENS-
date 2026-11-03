"""Export the 2D illustration assets used in the Short as PNG sheets:
  assets/characters/*.png   model sheets: each principal character in several poses, and a crowd line-up
  assets/props/*.png        handcart, candle, rye with ergot, flask
  (the set layers are written by src/sets.py and src/sets2.py into assets/layers/; paper by src/post.py)

  python tools/export_assets.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import cairo  # noqa: E402

from core import PAL, new_surface, set_c  # noqa: E402
from figures import make_char, draw_figure  # noqa: E402
import poses  # noqa: E402
from props import handcart, candle  # noqa: E402
from scenes import DANCER  # noqa: E402
from scenes2 import VITUS, rye_ear  # noqa: E402


def sheet(name, items, s=2.6, w=2400, h=900, step=None):
    surf = new_surface(w, h)
    ctx = cairo.Context(surf)
    set_c(ctx, PAL['parch'])
    ctx.paint()
    step = step or (w - 200) / max(1, len(items) - 1)
    for i, (c, p, face) in enumerate(items):
        draw_figure(ctx, c, p, 100 + i * step, h - 80, s, face, boil_k=0)
    out = os.path.join(ROOT, 'assets', 'characters')
    os.makedirs(out, exist_ok=True)
    surf.write_to_png(os.path.join(out, name + '.png'))


def main():
    d = DANCER
    sheet('first_dancer', [(d, poses.idle(0, 1, turn=0.2), 1), (d, poses.dance('whirl', 0.0, 1518), 1), (d, poses.dance('whirl', 0.34, 1518), 1),
                           (d, poses.dance('whirl', 0.67, 1518), 1), (d, poses.dance('whirl', 1.0, 1518), 1), (d, poses.dance('whirl', 0.5, 1518, 0.8, 0.6), 1),
                           (d, poses.walk(0.3, 1), 1)], s=3.4, h=1000)
    dancers = [make_char(70 + i) for i in range(6)]
    sheet('dance_cycles', [(dancers[0], poses.dance('jig', 0.1, 70), 1), (dancers[1], poses.dance('jig', 0.5, 71), 1),
                           (dancers[2], poses.dance('convulse', 0.3, 72), 1), (dancers[3], poses.dance('convulse', 0.9, 73), -1),
                           (dancers[4], poses.dance('stomp', 0.2, 74), 1), (dancers[5], poses.dance('stomp', 0.7, 75), -1),
                           (dancers[0], poses.dance('sway', 0.4, 76, 1, 0.8), 1), (dancers[1], poses.dance('twirl', 0.3, 77), 1)])
    walkers = [make_char(210 + i) for i in range(4)]
    sheet('walk_cycle', [(walkers[0], poses.walk(k * 0.13, 210), 1) for k in range(8)])
    sheet('council_and_physicians', [(make_char(301, 'm', 'old', role='council'), poses.gesture('talk', 1.0, 301), 1),
                                     (make_char(302, 'm', 'adult', role='council', beard='short'), poses.gesture('chin', 1, 302), 1),
                                     (make_char(303, 'm', 'adult', role='physician'), poses.gesture('flask', 1.5, 303), 1),
                                     (make_char(304, 'm', 'old', role='physician', beard='full'), poses.gesture('book', 1, 304), -1),
                                     (make_char(305, 'm', 'adult', role='council'), poses.gesture('fold', 1, 305), -1),
                                     (make_char(306, 'm', 'young', role='council'), poses.gesture('write', 1, 306), -1)])
    sheet('musicians_and_saint', [(make_char(440, 'm', 'adult', coat=PAL['burg3']), poses.musician('drum', 0.1, 440), 1),
                                  (make_char(441, 'm', 'young'), poses.musician('shawm', 0.2, 441), 1),
                                  (make_char(442, 'm', 'old', beard='full'), poses.musician('bagpipe', 0.3, 442), 1),
                                  (make_char(443, 'm', 'adult'), poses.musician('fiddle', 0.4, 443), 1),
                                  (VITUS, dict(poses.idle(1, 501, turn=0.05), ua_f=0.4, fa_f=2.6, prop='palm'), 1),
                                  (make_char(801, 'm', 'old', role='priest', surplice=True), dict(poses.walk(0.2, 801), prop='cross', ua_f=1.2, fa_f=2.8), 1)])
    crowd = [make_char(20 + i) for i in range(12)]
    sheet('townspeople', [(c, poses.react(1.0, 0.0, c['seed'], ['stare', 'mouth', 'point', 'recoil', 'cross', 'whisper'][i % 6]), 1 if i % 2 else -1)
                          for i, c in enumerate(crowd)], s=2.2)
    out = os.path.join(ROOT, 'assets', 'props')
    os.makedirs(out, exist_ok=True)
    surf = new_surface(1800, 700)
    ctx = cairo.Context(surf)
    set_c(ctx, PAL['parch'])
    ctx.paint()
    handcart(ctx, 300, 600, 2.4, 1)
    for k in range(3):
        candle(ctx, 700 + k * 120, 600, 5.0, k * 0.3, seed=k)
    rye_ear(ctx, 1200, 640, 1.4, -0.1, 700, (5, 12, 19))
    rye_ear(ctx, 1450, 640, 1.4, 0.1, 701, (8, 15, 22, 27))
    surf.write_to_png(os.path.join(out, 'props.png'))
    print('exported assets/characters and assets/props')


if __name__ == '__main__':
    main()
