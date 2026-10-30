"""Shared, deterministic layout of the 1919 North End waterfront (metres).

Both the flood simulation (plain Python + numpy) and the Blender scene import this,
so the molasses flows around exactly the buildings that get rendered.

Axes: +x east along Commercial Street, +y north (inland), z up. The harbour is to the south.
The tank site (today Langone Park) sat between Commercial Street and the water.
"""
import math
import random

# Tank: 50 ft tall, 90 ft diameter, 2.3 million US gallons (≈8,700 m³)
TANK_X, TANK_Y = 0.0, -19.0
TANK_R = 13.7            # 90 ft / 2
TANK_H = 15.2            # 50 ft
FILL_H = 8700.0 / (math.pi * TANK_R ** 2)   # ≈14.75 m of molasses

STREET_Y0, STREET_Y1 = 0.0, 18.0             # Commercial Street (south kerb, north kerb)
EL_Y = 9.0                                    # elevated railway centreline over the street
EL_COL_DY = 4.2                               # columns either side of centreline
EL_COL_SPACING = 12.0
SEAWALL_Y = -46.0                             # waterfront edge; harbour beyond
DOMAIN = (-130.0, 130.0, -72.0, 82.0)         # simulation / ground extent

# Cross streets running north from Commercial Street (x0, x1)
SIDE_STREETS = [(-74.0, -62.0), (30.0, 41.0)]

# House east of the tank that the wave shoves off its foundation (not an obstacle in the sim:
# it is pushed by the flow instead of blocking it).
PUSHED_HOUSE = dict(x0=27.0, x1=40.0, y0=-33.0, y1=-17.0, height=9.5)


def _row(rng, x0, x1, y0, depth_range, h_range, kinds):
    out, x = [], x0
    while x < x1 - 5:
        w = min(rng.uniform(8.0, 14.0), x1 - x)
        d = rng.uniform(*depth_range)
        out.append(dict(x0=x, x1=x + w, y0=y0, y1=y0 + d,
                        height=rng.choice(range(*h_range)) * 3.4 + rng.uniform(0.3, 1.2),
                        kind=rng.choice(kinds)))
        x += w + rng.choice([0.0, 0.0, 0.0, 0.6])
    return out


def buildings(seed=1919):
    """Return the list of solid buildings (axis-aligned boxes)."""
    rng = random.Random(seed)
    b = []
    # North side of Commercial Street: brick rowhouses and tenements, two rows deep
    blocks = [(-130.0, -74.0), (-62.0, 30.0), (41.0, 130.0)]
    for x0, x1 in blocks:
        b += _row(rng, x0, x1, STREET_Y1 + 2.0, (14, 20), (3, 6), ['brick', 'brick', 'brick_dark', 'stone'])
        b += _row(rng, x0, x1, STREET_Y1 + 26.0, (14, 22), (4, 7), ['brick', 'brick_dark', 'brick'])
    # Harbour side: freight sheds and warehouses either side of the tank yard
    b.append(dict(x0=-80.0, x1=-31.0, y0=-41.0, y1=-6.0, height=9.0, kind='shed'))
    b.append(dict(x0=50.0, x1=118.0, y0=-41.0, y1=-6.0, height=11.0, kind='warehouse'))
    b.append(dict(x0=-128.0, x1=-90.0, y0=-41.0, y1=-8.0, height=12.5, kind='warehouse'))
    return b


def el_columns():
    """Elevated-railway column footprints (x, y)."""
    cols = []
    x = DOMAIN[0] + 4
    while x < DOMAIN[1] - 4:
        cols.append((x, EL_Y - EL_COL_DY))
        cols.append((x, EL_Y + EL_COL_DY))
        x += EL_COL_SPACING
    return cols


# Debris carried by the flow: (name, kind, x, y, yaw)
DEBRIS = [
    ('barrel_a', 'barrel', 18.0, -2.5, 0.0),
    ('barrel_b', 'barrel', 21.0, -1.5, 0.7),
    ('barrel_c', 'barrel', -17.0, -3.0, 1.1),
    ('barrel_d', 'barrel', -20.0, -1.0, 2.0),
    ('crate_a', 'crate', 9.0, -1.0, 0.3),
    ('crate_b', 'crate', -9.0, 2.0, 1.2),
    ('crate_c', 'crate', -26.0, 4.5, 0.4),
    ('wagon', 'wagon', -34.0, 5.0, 0.0),
    ('truck', 'truck', 15.0, -39.0, 0.4),
    ('barrel_e', 'barrel', 8.0, -1.2, 0.2),
    ('crate_d', 'crate', 16.0, -1.8, 0.9),
]
