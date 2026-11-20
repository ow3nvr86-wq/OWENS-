"""Map data for the Cuban Missile Crisis Short: the Caribbean, Florida and the Atlantic. Natural Earth 1:50m (public
domain). Same projection as the other maps.   python tools/build_map_cuba.py <dir with the Natural Earth geojson files>
-> assets/map/cuba_map.json"""
import json
import math
import os
import sys

from shapely import affinity
from shapely.geometry import shape, box
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K, LON0, LAT0 = 30.0, 15.0, 50.0
CLAT = math.cos(math.radians(50.0))


def main():
    src = sys.argv[1]
    bb = box(-105, 4, -12, 52)
    feats = json.load(open(os.path.join(src, 'ne_50m_admin_0_countries.geojson')))['features']
    by = {}
    for f in feats:
        by.setdefault(f['properties']['ADM0_A3'], []).append(shape(f['geometry']).buffer(0))
    by = {k: unary_union(v) for k, v in by.items()}
    land = unary_union([shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(src, 'ne_50m_land.geojson')))['features']]).intersection(bb)

    def pj(g):
        return affinity.affine_transform(g, [CLAT * K, 0, 0, -K, -LON0 * CLAT * K, LAT0 * K])

    R = {'LAND': land, 'CUBA': by['CUB'].intersection(bb), 'USA': by['USA'].intersection(bb), 'MEX': by['MEX'].intersection(bb),
         'BHS': by['BHS'].intersection(bb), 'HTI': unary_union([by['HTI'], by['DOM']]).intersection(bb), 'JAM': by['JAM']}
    out = {'proj': {'K': K, 'LON0': LON0, 'LAT0': LAT0, 'CLAT': CLAT}, 'regions': {}, 'lines': {}}
    for name, g in R.items():
        g = pj(g).simplify(0.25 if name != 'LAND' else 0.4)
        polys = []
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type != 'Polygon' or p.area < 0.8:
                continue
            polys.append([[[round(x, 2), round(y, 2)] for x, y in r.coords] for r in [p.exterior] + list(p.interiors) if len(r.coords) > 3])
        out['regions'][name] = polys
        print(name, len(polys), 'polygons')
    p = os.path.join(ROOT, 'assets', 'map', 'cuba_map.json')
    json.dump(out, open(p, 'w'), separators=(',', ':'))
    print('wrote', p, os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
