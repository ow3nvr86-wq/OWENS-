"""Map data for the Short, from real geography:
  - coastlines: Natural Earth 1:50m land (public domain)
  - the Roman Empire at its greatest extent, AD 117: Ancient World Mapping Center (AWMC), ODbL, after the
    Barrington Atlas of the Greek and Roman World
  - Roman roads: AWMC (roads marked 'major')
The empire of AD 395 is the AD 117 extent minus the lands given up by then (Dacia, abandoned c. 271-275; the Agri
Decumates beyond the upper Rhine and Danube, c. 260; Mesopotamia and Armenia east of the Euphrates frontier, given
up in 363 and 387). The East-West line of 395 follows the boundary between the prefectures of Italy and Illyricum:
the Drina valley in the Balkans and the Altars of the Philaeni in Libya (about 19 degrees east).

Projection: equirectangular with true scale at 40 N; world units: 1 unit = 1 px at camera zoom 1.
"""
import json
import math
import os
import pickle

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPD = os.path.join(ROOT, 'assets', 'map')
CACHE = os.path.join(ROOT, 'build', 'mapdata.pkl')

K = 30.0                     # units per degree of latitude
LON0, LAT0 = 16.0, 40.0
CLAT = math.cos(math.radians(40.0))
BBOX = (-34.0, 4.0, 78.0, 76.0)   # lon0, lat0, lon1, lat1


def proj(lon, lat):
    return (np.asarray(lon) - LON0) * CLAT * K, -(np.asarray(lat) - LAT0) * K


def P(lon, lat):
    x, y = proj(lon, lat)
    return float(x), float(y)


PLACES = {
    'rome': (12.48, 41.89), 'constantinople': (28.98, 41.01), 'londinium': (-0.12, 51.51), 'alexandria': (29.92, 31.2),
    'carthage': (10.32, 36.85), 'antioch': (36.16, 36.2), 'ravenna': (12.2, 44.42), 'athens': (23.73, 37.98),
}

# the West/East line of AD 395 (lon, lat), from the Sahara to beyond the Danube
SPLIT_LINE = [(19.3, -30.0), (19.3, 16.0), (19.15, 29.0), (18.95, 30.35), (19.4, 33.5), (19.0, 37.5), (19.0, 40.5), (19.45, 41.85),
              (19.35, 42.6), (19.25, 43.5), (19.35, 44.4), (19.5, 44.95), (19.2, 45.6), (19.0, 47.5), (19.2, 62.0), (19.2, 100.0)]

LOST_BY_395 = [
    # Dacia, north of the lower Danube
    [(20.6, 45.5), (21.4, 45.1), (22.4, 44.75), (22.7, 44.2), (23.0, 43.82), (25.0, 43.62), (26.3, 44.05), (27.3, 44.1),
     (28.0, 44.6), (28.25, 45.3), (29.5, 45.45), (29.5, 49.5), (20.6, 49.5)],
    # Agri Decumates, between the upper Rhine and the upper Danube
    [(7.75, 47.62), (8.5, 47.96), (10.0, 48.42), (11.5, 48.78), (12.1, 49.05), (12.4, 51.5), (8.45, 51.5), (8.3, 50.0),
     (8.1, 49.1), (7.85, 48.3)],
    # Mesopotamia, Assyria and Armenia beyond the Euphrates frontier
    [(40.6, 28.0), (40.6, 36.6), (39.4, 38.4), (40.2, 42.2), (52.0, 42.2), (52.0, 28.0)],
]


def _load():
    from shapely.geometry import shape, Polygon, MultiPolygon, box, LineString
    from shapely.ops import unary_union, split
    from shapely import affinity

    def pj(geom):
        return affinity.affine_transform(geom, [CLAT * K, 0, 0, -K, -LON0 * CLAT * K, LAT0 * K])

    bb = box(*BBOX)
    land = []
    for f in json.load(open(os.path.join(MAPD, 'ne_50m_land.geojson')))['features']:
        g = shape(f['geometry']).intersection(bb)
        if g.is_empty:
            continue
        g = pj(g).simplify(0.6)
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type == 'Polygon' and p.area > 4:
                land.append(p)
    landu = unary_union(land)
    e117 = unary_union([shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(MAPD, 'roman_empire_ce_117_extent.geojson')))['features']])
    e117 = pj(e117).buffer(0.8).buffer(-0.8).simplify(0.5).intersection(landu.buffer(1.5))
    lost = unary_union([pj(Polygon(r)) for r in LOST_BY_395])
    e395 = e117.difference(lost).buffer(0)
    # the western side of the split line, as a polygon reaching far to the west
    sl = [P(*p) for p in SPLIT_LINE]
    west_poly = Polygon(sl + [P(-60, 100.0), P(-60, -30.0)]).buffer(0)
    west = e395.intersection(west_poly).buffer(0)
    east = e395.difference(west_poly).buffer(0)
    roads = []
    rome = np.array(P(*PLACES['rome']))
    for f in json.load(open(os.path.join(MAPD, 'roads.geojson')))['features']:
        if f['properties'].get('Major_or_M') != '1':
            continue
        for ln in shape(f['geometry']).geoms:
            ln = pj(ln).simplify(0.4)
            c = np.asarray(ln.coords)
            if len(c) < 2:
                continue
            d0, d1 = np.linalg.norm(c[0] - rome), np.linalg.norm(c[-1] - rome)
            if d1 < d0:
                c = c[::-1]
            seg = np.linalg.norm(np.diff(c, axis=0), axis=1)
            roads.append({'pts': c.astype(np.float32), 'd': float(min(d0, d1)), 'len': float(seg.sum())})
    roads.sort(key=lambda r: r['d'])

    def rings(g):
        out = []
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type != 'Polygon' or p.area < 2:
                continue
            out.append([np.asarray(p.exterior.coords, np.float32)] + [np.asarray(i.coords, np.float32) for i in p.interiors])
        return out

    return {'land': rings(landu), 'e117': rings(e117), 'e395': rings(e395), 'west': rings(west), 'east': rings(east),
            'roads': roads, 'split': np.array(sl, np.float32)}


_D = None


def data():
    global _D
    if _D is None:
        if os.path.exists(CACHE):
            _D = pickle.load(open(CACHE, 'rb'))
        else:
            _D = _load()
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            pickle.dump(_D, open(CACHE, 'wb'))
    return _D


if __name__ == '__main__':
    d = data()
    for k in ('land', 'e117', 'e395', 'west', 'east'):
        print(k, len(d[k]), 'polygons', sum(len(r) for poly in d[k] for r in poly), 'points')
    print('roads', len(d['roads']), 'segments')
