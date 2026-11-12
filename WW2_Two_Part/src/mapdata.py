"""Map data for the WW2 Shorts (built by tools/build_map.py): regions as rings in world units, and helpers to draw them."""
import json
import os

import cairo
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_D = json.load(open(os.path.join(ROOT, 'assets', 'map', 'ww2_map.json')))
K, LON0, LAT0, CLAT = (_D['proj'][k] for k in ('K', 'LON0', 'LAT0', 'CLAT'))
R = {n: [[np.asarray(r, np.float32) for r in poly] for poly in polys] for n, polys in _D['regions'].items()}
LINES = {n: np.asarray(v, np.float32) for n, v in _D['lines'].items()}
BBOX = {}
for _n, _polys in R.items():
    _a = np.vstack([r for p in _polys for r in p])
    BBOX[_n] = (float(_a[:, 0].min()), float(_a[:, 1].min()), float(_a[:, 0].max()), float(_a[:, 1].max()))


def P(lon, lat):
    return (lon - LON0) * CLAT * K, -(lat - LAT0) * K


def PP(pts):
    return np.array([P(lo, la) for lo, la in pts], float)


def rings_path(ctx, rings):
    for poly in rings:
        for r in poly:
            ctx.move_to(float(r[0, 0]), float(r[0, 1]))
            for q in r[1:]:
                ctx.line_to(float(q[0]), float(q[1]))
            ctx.close_path()


def fill(ctx, name, col, alpha=None):
    ctx.new_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    rings_path(ctx, R[name])
    ctx.set_source_rgba(col[0], col[1], col[2], col[3] if alpha is None else alpha)
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


def stroke(ctx, name, col, lw, alpha=None):
    ctx.new_path()
    rings_path(ctx, R[name])
    ctx.set_source_rgba(col[0], col[1], col[2], col[3] if alpha is None else alpha)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def clip(ctx, names):
    ctx.new_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    for n in names:
        rings_path(ctx, R[n])
    ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
