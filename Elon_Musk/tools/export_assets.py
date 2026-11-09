"""Export the illustrations used in the Short as PNG sheets into assets/illustrations/."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
import cairo  # noqa: E402
import gfx as G  # noqa: E402
import journey as J  # noqa: E402
from portrait import portrait_duotone  # noqa: E402


def canvas(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(s)
    G.vgrad(c, 0, 0, w, h, [(0, G.C['navy1']), (1, G.C['navy0'])])
    return s, c


def main():
    out = os.path.join(ROOT, 'assets', 'illustrations')
    os.makedirs(out, exist_ok=True)
    s, c = canvas(1080, 1300)
    img, ox, oy, sc = portrait_duotone(2.0)
    c.translate(540, 560)
    c.scale(1.4 / sc, 1.4 / sc)
    c.translate(-ox * sc, -oy * sc)
    c.set_source_surface(img, 0, 0)
    c.paint()
    s.write_to_png(os.path.join(out, 'portrait.png'))
    s, c = canvas(1400, 400)
    for i, k in enumerate(('rocket', 'car', 'sat', 'chip')):
        J.icon(c, k, 200 + i * 330, 200, 90, G.C['white'])
    s.write_to_png(os.path.join(out, 'icons.png'))
    s, c = canvas(1400, 900)
    J.ev(c, 400, 600, 1.4, 0.0)
    J.rocket(c, 1050, 820, 1.0, 0.0, plume=0.8)
    s.write_to_png(os.path.join(out, 'car_and_rocket.png'))
    s, c = canvas(1080, 1080)
    J.earth(c, 540, 540, 380, 0.0)
    s.write_to_png(os.path.join(out, 'earth.png'))
    s, c = canvas(1080, 1920)
    J.draw_network(c, 23.0, 1.0, (540, 930), 1.0)
    s.write_to_png(os.path.join(out, 'network.png'))
    print('exported assets/illustrations')


if __name__ == '__main__':
    main()
