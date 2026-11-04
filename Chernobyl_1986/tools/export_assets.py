"""Export the 2D illustration assets used in the Short as PNG sheets:
  assets/characters/*.png   residents and children, plant operators, firefighters, militia and officials
  assets/props/*.png        the plant (intact, destroyed, under the arch), apartment block, vehicles, control-room
                            instruments, the Ferris wheel and swings
  (the background layers are written by src/sets.py into assets/layers/; paper by src/post.py)

  python tools/export_assets.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import cairo  # noqa: E402

from core import PAL, new_surface, set_c  # noqa: E402
from figures import draw_figure  # noqa: E402
from chars import person  # noqa: E402
import poses  # noqa: E402
import soviet as S  # noqa: E402


def sheet(name, items, s=3.4, w=2600, h=1000):
    surf = new_surface(w, h)
    ctx = cairo.Context(surf)
    set_c(ctx, PAL['parch'])
    ctx.paint()
    step = (w - 240) / max(1, len(items) - 1)
    for i, (c, p, face) in enumerate(items):
        draw_figure(ctx, c, p, 120 + i * step, h - 70, s, face, boil_k=0)
    out = os.path.join(ROOT, 'assets', 'characters')
    os.makedirs(out, exist_ok=True)
    surf.write_to_png(os.path.join(out, name + '.png'))


def main():
    sheet('pripyat_residents', [(person('man', 1), poses.walk(0.2, 1), 1), (person('woman', 2), poses.walk(0.5, 2), 1),
                                (person('woman', 13), dict(poses.idle(0, 3), prop='suitcase', ua_f=0.05, fa_f=0.05), 1),
                                (person('man', 11), dict(poses.idle(0, 11), prop='bag', ua_f=0.05, fa_f=0.05), -1),
                                (person('woman', 21, age='old'), poses.gesture('talk', 0.4, 21), 1), (person('girl', 4), poses.idle(0, 4), 1),
                                (person('boy', 5), poses.walk(0.3, 5, period=0.7), 1), (person('girl', 6), poses.walk(0.1, 6, period=0.7), -1)])
    sheet('operators', [(person('operator', 500 + i), p, 1) for i, p in enumerate(
        [poses.idle(0, 500, turn=0.4), dict(poses.gesture('write', 0.3, 501), prop='clipboard'), poses.gesture('fold', 0.2, 502),
         poses.react(1.0, 0.0, 503, 'recoil'), poses.react(1.0, 0.0, 504, 'stare')])], s=3.8)
    sheet('firefighters', [(person('fireman', 600 + i), p, 1) for i, p in enumerate(
        [poses.walk(0.1, 600, period=0.62, stride=1.25), dict(poses.idle(0, 601, turn=0.75), prop='hose', ua_f=1.0, fa_f=1.45, ua_b=0.9, fa_b=1.4,
                                                              arms_front=True, spray=1.0, prop_t=0.3),
         poses.gesture('point', 0.3, 602), poses.idle(0, 603, turn=0.3)])], s=3.8)
    sheet('militia_and_officials', [(person('militia', 31), poses.wave_hand(0.2, 31), 1), (person('militia', 33), poses.idle(0, 33, turn=0.3), 1),
                                    (person('official', 32), dict(poses.gesture('write', 0.2, 32), prop='clipboard'), 1),
                                    (person('official', 34), poses.walk(0.4, 34), 1)], s=3.8)
    out = os.path.join(ROOT, 'assets', 'props')
    os.makedirs(out, exist_ok=True)
    surf = new_surface(3000, 2400)
    ctx = cairo.Context(surf)
    set_c(ctx, PAL['parch'])
    ctx.paint()
    S.plant(ctx, 60, 700, 2.0, 0.3, state='intact')
    S.plant(ctx, 1000, 700, 2.0, 0.3, state='damaged', glow=1.0)
    S.plant(ctx, 1940, 700, 2.0, 0.3, state='nsc')
    S.panel_block(ctx, 60, 1400, 30, 9, 20, 1, laundry=0.5)
    S.car(ctx, 900, 1400, 60, 0.0, PAL['green2'])
    S.bus(ctx, 1350, 1400, 60, 0.0)
    S.fire_engine(ctx, 2050, 1400, 60, 0.0)
    S.dial(ctx, 2700, 1200, 160, 0.6, label='МВт')
    S.ferris_wheel(ctx, 400, 1900, 300, 0.0)
    S.swings(ctx, 1000, 2350, 80, 0.0)
    S.core_grid(ctx, 1500, 1950, 260, 0.0)
    S.street_lamp(ctx, 1950, 2350, 400)
    S.poplar(ctx, 2250, 2350, 600, 3)
    S.nsc(ctx, 2700, 2350, 1.5)
    surf.write_to_png(os.path.join(out, 'plant_city_vehicles_instruments.png'))
    print('exported assets/characters and assets/props')


if __name__ == '__main__':
    main()
