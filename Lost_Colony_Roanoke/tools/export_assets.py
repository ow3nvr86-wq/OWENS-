"""Export the 2D illustration assets used in the Short as PNG sheets:
  assets/characters/*.png   model sheets: John White, the Dare family, colonists at work, soldier and sailors
  assets/props/*.png        ships, boat, cottage stages, the carved post, chests, barrels, campfire
  (the background layers are written by src/sets.py into assets/layers/; paper by src/post.py)

  python tools/export_assets.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import cairo  # noqa: E402

from core import PAL, new_surface, set_c  # noqa: E402
from figures import draw_figure, make_char  # noqa: E402
import poses  # noqa: E402
import world as Wd  # noqa: E402
from scenes import WHITE, ELEANOR, ANANIAS, SOLDIER, SAILORS, COLONISTS, TRUMPETER  # noqa: E402


def sheet(name, items, s=3.2, w=2600, h=1000):
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
    sheet('john_white', [(WHITE, poses.idle(0, 1, turn=0.1), 1), (WHITE, poses.idle(0, 1, turn=0.6), 1), (WHITE, poses.walk(0.2, 1), 1),
                         (WHITE, dict(poses.idle(0, 1, turn=0.7), prop='lantern', ua_f=0.9, fa_f=1.5), 1),
                         (WHITE, poses.react(1.0, 0.0, 1, 'stare', turn=0.5), 1)], s=3.8)
    sheet('the_dare_family', [(ELEANOR, poses.carry(poses.idle(0, 2, turn=0.3), 'baby'), 1), (ELEANOR, poses.carry(poses.idle(0, 2, turn=0.6), 'baby'), -1),
                              (ANANIAS, poses.idle(0, 3, turn=0.3), 1), (ANANIAS, poses.walk(0.4, 3), 1)], s=3.8)
    sheet('colonists_at_work', [(COLONISTS[5], poses.hammer(0.1, 5), 1), (COLONISTS[5], poses.hammer(0.5, 5), 1),
                                (COLONISTS[8], poses.carry(poses.walk(0.2, 8), 'log'), 1), (COLONISTS[0], poses.carry(poses.walk(0.4, 0), 'chest'), 1),
                                (COLONISTS[2], poses.carry(poses.walk(0.1, 2), 'sack'), 1),
                                (COLONISTS[12], dict(poses.walk(0.3, 12), prop='basket', ua_f=0.2, fa_f=1.4), 1),
                                (make_char(64, 'f', 'child'), poses.walk(0.2, 64, period=0.7), 1), (make_char(65, 'm', 'child'), poses.idle(0, 65), 1)])
    sheet('soldier_and_sailors', [(SOLDIER, dict(poses.idle(0, 30, turn=0.5), prop='musket', ua_f=0.35, fa_f=1.1), 1),
                                  (SAILORS[0], poses.row(0.2, 50), 1), (SAILORS[1], poses.row(0.9, 51), 1),
                                  (TRUMPETER, dict(poses.idle(0, 45, turn=0.5), prop='trumpet', ua_f=1.2, fa_f=2.2), 1),
                                  (SAILORS[3], poses.walk(0.2, 43), 1), (SAILORS[2], poses.wave_hand(0.3, 42), 1)])
    out = os.path.join(ROOT, 'assets', 'props')
    os.makedirs(out, exist_ok=True)
    surf = new_surface(2600, 1500)
    ctx = cairo.Context(surf)
    set_c(ctx, PAL['parch'])
    ctx.paint()
    Wd.ship(ctx, 420, 560, 1.2, 0.0, 1)
    Wd.ship(ctx, 1000, 560, 1.0, 0.0, 2, kind='pinnace')
    Wd.longboat(ctx, 1400, 540, 1.6, 0.3)
    Wd.carved_post(ctx, 1800, 620, 104, 430, 23)
    for k, st in enumerate((0.15, 0.35, 0.55, 0.8, 1.0)):
        Wd.cottage(ctx, 260 + k * 420, 1180, 330, 205, 32, st)
    Wd.sea_chest(ctx, 2150, 600, 1.6, 3, open_=1.0)
    Wd.barrel(ctx, 2350, 600, 1.6, 1)
    Wd.campfire(ctx, 2480, 600, 1.6, 0.5)
    Wd.palisade(ctx, 200, 2500, 1460, 220, 4, logw=30)
    surf.write_to_png(os.path.join(out, 'ships_houses_props.png'))
    print('exported assets/characters and assets/props')


if __name__ == '__main__':
    main()
