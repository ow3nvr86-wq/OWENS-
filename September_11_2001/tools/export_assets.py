"""Export the 2D illustrations used in the Short as PNG sheets into assets/illustrations/.
  python tools/export_assets.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import cairo  # noqa: E402

import gfx as G  # noqa: E402
from gfx import C  # noqa: E402
from figures import draw_figure  # noqa: E402
from chars import person  # noqa: E402
import poses  # noqa: E402


def canvas(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(s)
    G.vgrad(c, 0, 0, w, h, [(0, C['navy1']), (1, C['navy2'])])
    return s, c


def main():
    out = os.path.join(ROOT, 'assets', 'illustrations')
    os.makedirs(out, exist_ok=True)
    s, c = canvas(1600, 1000)
    G.sky(c, 1600, 1000, 760)
    G.skyline(c, 0, 1600, 760, 1.1, 11, C['navy3'])
    G.twin_towers(c, 600, 760, 1.3, 0.0)
    s.write_to_png(os.path.join(out, 'skyline_twin_towers.png'))
    s, c = canvas(1200, 1000)
    G.twin_towers(c, 420, 900, 1.6, 0.0, outline=((*C['blue3'][:3], 0.9), 2.2), highlight=dict(tower='N', f0=93, f1=99, k=1.0))
    G.twin_towers(c, 420, 900, 1.6, 0.0, outline=((0, 0, 0, 0), 0.1), bands=False, highlight=dict(tower='S', f0=77, f1=85, k=1.0))
    s.write_to_png(os.path.join(out, 'towers_line_drawing.png'))
    s, c = canvas(1080, 1200)
    P = G.MapProj(39.75, -76.45, 190, 540, 600)
    G.draw_map(c, P, 0.0)
    for n, t0 in (('nyc', 0), ('dc', 0), ('shanksville', 0)):
        G.marker(c, *P.p(*G.PLACES[n]), 1.0, 0.0)
    G.pentagon_icon(c, 300, 1000, 90, lw=3)
    s.write_to_png(os.path.join(out, 'map_east_us.png'))
    s, c = canvas(1600, 900)
    G.fire_truck(c, 400, 760, 70, 0.0)
    for i, kind in enumerate(('fireman', 'fireman', 'man', 'woman')):
        ch = person(kind, 900 + i)
        p = poses.walk(0.3 * i, 900 + i) if kind == 'fireman' else poses.idle(0, 900 + i)
        G.silhouette(c, lambda cc, ch=ch, p=p, i=i: draw_figure(cc, ch, p, 900 + i * 160, 820, 2.4, 1, boil_k=None), C['char'],
                     G.mixc(C['warm'], C['white'], 0.5))
    s.write_to_png(os.path.join(out, 'responders_silhouettes.png'))
    s, c = canvas(1080, 1300)
    P = G.Persp(f=820, cx=540, hy=520, hcam=17.0)
    G.rect(c, 0, 520, 1080, 1300, G.mixc(C['grey2'], C['navy2'], 0.45))
    G.one_wtc(c, 760, 520, 1.0, G.mixc(C['navy3'], C['blue1'], 0.35), rim=C['blue3'])
    G.memorial_pool(c, P, 0.0, -15, 15, 17, 37, depth=7.0)
    s.write_to_png(os.path.join(out, 'memorial_pool.png'))
    s, c = canvas(1080, 1000)
    G.beams(c, 420, 660, 900, 0, 0.0)
    G.logo(c, 540, 600, 1.6)
    s.write_to_png(os.path.join(out, 'tribute_in_light_and_logo.png'))
    print('exported assets/illustrations')


if __name__ == '__main__':
    main()
