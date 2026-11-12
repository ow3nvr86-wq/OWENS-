"""Build the map data for the WW2 Shorts: Europe with the borders of September 1939 and the lines of 1939-41, plus
the land of the northern hemisphere from the Atlantic to Hawaii (for the move to Pearl Harbor).

Sources: Natural Earth 1:50m countries and land (public domain). The 1939 borders are built from the modern country
shapes plus historical lines drawn here by hand from the positions of border towns (approximate, to about 20-30 km):
  - Germany of 1939: Germany + Austria + the Czech lands + its eastern territories of the time (Pomerania, Silesia,
    East Brandenburg, East Prussia with Danzig and Memel)
  - Poland of 1939: the 1921 border with the USSR (the Riga line) and with Lithuania (Vilnius in Poland)
  - the German-Soviet line through Poland of 28 Sept 1939; the demarcation line in France of June 1940 (Vichy);
    the front line in the USSR of early December 1941

  python tools/build_map.py <dir with ne_50m_admin_0_countries.geojson and ne_50m_land.geojson>
  -> assets/map/ww2_map.json   (rings in world units: x = (lon-15)*cos(50)*30, y = -(lat-50)*30)
"""
import json
import math
import os
import sys

from shapely import affinity
from shapely.geometry import shape, Polygon, MultiPolygon, box
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K, LON0, LAT0 = 30.0, 15.0, 50.0
CLAT = math.cos(math.radians(50.0))

# ---- hand-drawn historical lines (lon, lat) -------------------------------------------------------------
GER_POL = [(18.07, 55.2), (18.07, 54.78), (17.75, 54.4), (17.4, 54.05), (17.3, 53.7), (16.95, 53.12), (16.6, 52.9), (16.0, 52.65),
           (15.85, 52.3), (16.05, 52.0), (16.3, 51.8), (16.7, 51.62), (17.2, 51.5), (17.7, 51.3), (18.2, 51.05), (18.65, 50.8),
           (18.85, 50.5), (18.8, 50.3), (18.45, 50.15), (18.35, 50.02), (18.3, 49.9), (18.3, 49.3)]
EAST_PRUSSIA = [(18.56, 55.0), (18.56, 54.47), (18.35, 54.3), (18.5, 54.05), (18.85, 53.95), (18.88, 53.68), (19.3, 53.6),
                (19.75, 53.58), (20.0, 53.4), (20.1, 53.3), (20.9, 53.35), (21.6, 53.45), (22.3, 53.6), (22.8, 54.3), (22.8, 54.36),
                (22.6, 54.95), (22.0, 55.05), (21.3, 55.3), (21.25, 55.7), (21.08, 55.92), (20.5, 56.1), (19.0, 56.1)]
POL_LIT = [(23.5, 53.93), (24.0, 54.05), (24.4, 54.35), (24.75, 54.72), (25.0, 55.0), (25.5, 55.2), (26.0, 55.35), (26.6, 55.68)]
RIGA = [(28.2, 55.95), (28.15, 55.5), (28.2, 55.2), (27.95, 54.85), (27.5, 54.4), (27.3, 54.15), (27.05, 53.75), (26.95, 53.4),
        (26.85, 53.07), (27.0, 52.8), (27.4, 52.5), (27.65, 52.2), (27.6, 51.9), (27.5, 51.5), (27.45, 51.25), (27.3, 50.9),
        (27.3, 50.6), (26.7, 50.3), (26.2, 50.0), (26.2, 49.5), (26.3, 49.0), (26.4, 48.55)]
POL_SOUTH = [(26.4, 48.55), (25.75, 48.6), (25.55, 48.4), (25.15, 48.2), (24.95, 47.95), (24.6, 48.05), (24.3, 48.35), (23.6, 48.7),
             (22.9, 49.0), (22.7, 49.1)]
CARPATHO = [(22.1, 48.4), (22.2, 49.1), (22.9, 49.0), (23.6, 48.7), (24.3, 48.35), (24.6, 48.05), (24.95, 47.95), (24.9, 47.6), (22.8, 47.9)]
SOVZ_1939 = [(23.55, 53.9), (22.8, 53.8), (21.85, 53.45), (21.88, 53.23), (21.6, 53.05), (22.3, 52.67), (22.9, 52.4), (23.2, 52.2),
             (23.65, 52.07), (23.65, 51.5), (23.95, 50.85), (24.05, 50.5), (23.6, 50.35), (22.6, 50.2), (22.7, 49.9), (22.77, 49.78),
             (22.4, 49.5), (22.3, 49.0)]
VICHY = [(6.2, 46.4), (5.5, 47.05), (4.85, 46.8), (3.35, 46.55), (2.4, 47.05), (1.9, 47.25), (0.95, 47.2), (0.6, 46.6), (0.35, 45.7),
         (-0.25, 44.6), (-0.5, 43.9), (-1.0, 43.3), (-1.2, 43.0)]
FRONT_DEC41 = [(29.7, 59.75), (29.7, 59.8), (30.4, 59.65), (31.0, 59.92), (32.3, 59.9), (31.9, 59.0), (31.3, 58.5), (31.5, 58.0),
               (32.5, 57.6), (33.1, 57.1), (35.9, 56.85), (37.2, 56.3), (37.4, 56.0), (36.9, 55.7), (36.7, 55.4), (37.2, 54.9),
               (37.3, 54.4), (38.6, 54.1), (38.3, 53.3), (38.0, 52.5), (37.3, 51.7), (36.8, 50.6), (37.0, 49.9), (37.0, 49.2),
               (38.5, 48.3), (38.9, 47.6), (38.95, 47.2), (38.0, 46.6), (36.6, 45.4), (36.7, 44.5), (36.7, 40.0)]
BORDER_JUN41 = [(21.0, 55.9), (22.6, 54.9), (22.8, 54.36), (23.5, 53.95), (22.8, 53.8), (21.85, 53.45), (21.88, 53.23), (22.3, 52.67),
                (23.65, 52.07), (23.95, 50.85), (24.05, 50.5), (22.6, 50.2), (22.77, 49.78), (22.7, 49.1), (24.6, 48.05), (26.3, 48.2),
                (28.1, 46.5), (28.2, 45.45), (29.7, 45.3)]


def main():
    src = sys.argv[1]
    feats = json.load(open(os.path.join(src, 'ne_50m_admin_0_countries.geojson')))['features']
    by = {}
    for f in feats:
        by.setdefault(f['properties']['ADM0_A3'], []).append(shape(f['geometry']).buffer(0))
    by = {k: unary_union(v) for k, v in by.items()}

    def C(*codes):
        return unary_union([by[c] for c in codes if c in by])

    def poly(pts, *closure):
        return Polygon(list(pts) + list(closure)).buffer(0)

    europe = box(-25, 30, 75, 73)
    A = poly(GER_POL, (12.0, 49.3), (12.0, 55.2))
    B = poly(EAST_PRUSSIA)
    PE = poly(POL_LIT + [(26.9, 55.95)] + RIGA + POL_SOUTH[1:], (22.0, 49.3), (22.0, 53.9))
    CU = poly(CARPATHO)
    SOVZ = poly(SOVZ_1939, (25.5, 49.0), (25.5, 54.0))
    VZ = poly(VICHY, (-1.4, 42.7), (-1.4, 40.5), (11.0, 40.5), (11.0, 46.5), (6.3, 46.5))
    WEST_OF_FRONT = poly(FRONT_DEC41, (15.0, 40.0), (15.0, 59.75))

    POL, RUS, LTU, BLR, UKR = C('POL'), C('RUS').intersection(box(0, 30, 180, 78)), C('LTU'), C('BLR'), C('UKR')
    ger_east = unary_union([POL.intersection(A), unary_union([POL, RUS, LTU]).intersection(B)])
    R = {}
    R['GER'] = unary_union([C('DEU', 'AUT', 'CZE'), ger_east])
    pol_w = POL.difference(A).difference(B)
    pol_e = unary_union([BLR, UKR, LTU]).intersection(PE)
    R['POL_GER'] = pol_w.difference(SOVZ)
    R['POL_SOV'] = unary_union([pol_e, pol_w.intersection(SOVZ)])
    cu = UKR.intersection(CU)
    R['USSR'] = unary_union([RUS.difference(B), BLR, UKR, C('GEO', 'ARM', 'AZE', 'KAZ', 'UZB', 'TKM', 'KGZ', 'TJK')]).difference(PE).difference(CU)
    R['LIT'] = LTU.difference(B).difference(PE)
    R['LAT'], R['EST'], R['FIN'], R['SWE'], R['DEN'] = C('LVA'), C('EST'), C('FIN', 'ALD'), C('SWE'), C('DNK')
    R['NOR'] = C('NOR').intersection(box(0, 55, 35, 72))
    R['NLD'], R['BEL'], R['LUX'] = C('NLD').intersection(europe), C('BEL'), C('LUX')
    fra = C('FRA', 'MCO').intersection(box(-6, 41, 10, 52))
    R['FRA_OCC'], R['FRA_VICHY'] = fra.difference(VZ), fra.intersection(VZ)
    R['GBR'], R['IRL'] = C('GBR', 'IMN', 'GGY', 'JEY').intersection(box(-12, 49, 3, 62)), C('IRL')
    R['ESP'] = C('ESP', 'AND').intersection(box(-10, 35.6, 5, 44.5))
    R['PRT'] = C('PRT').intersection(box(-10, 36, -6, 43))
    R['CHE'] = C('CHE', 'LIE')
    R['ITA'] = C('ITA', 'SMR', 'VAT', 'ALB', 'MLT')
    R['SVK'], R['HUN'] = C('SVK'), unary_union([C('HUN'), cu])
    R['ROU'] = C('ROU', 'MDA')
    R['YUG'] = C('SVN', 'HRV', 'BIH', 'SRB', 'MNE', 'MKD', 'KOS')
    R['GRC'], R['BGR'] = C('GRC'), C('BGR')
    R['TUR'] = C('TUR', 'CYP', 'CYN')
    R['OCC_EAST'] = unary_union([R['USSR'], R['POL_SOV'], R['LIT'], R['LAT'], R['EST']]).intersection(WEST_OF_FRONT)
    R['JPN'] = C('JPN', 'KOR', 'PRK', 'TWN')
    R['HAWAII'] = affinity.translate(C('USA').intersection(box(-161, 18.5, -154.5, 22.6)), xoff=360)

    # land from the Atlantic to Hawaii: longitudes west of -30 are moved 360 degrees east
    land = unary_union([shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(src, 'ne_50m_land.geojson')))['features']])
    east = land.intersection(box(-30, -5, 180, 78))
    west = affinity.translate(land.intersection(box(-180, -5, -110, 78)), xoff=360)
    R['LAND'] = unary_union([east, west])

    def pj(g):
        return affinity.affine_transform(g, [CLAT * K, 0, 0, -K, -LON0 * CLAT * K, LAT0 * K])

    out = {'proj': {'K': K, 'LON0': LON0, 'LAT0': LAT0, 'CLAT': CLAT}, 'regions': {}, 'lines': {}}
    for name, g in R.items():
        tol, amin = (0.45, 1.5) if name in ('LAND', 'JPN') else (0.16, 0.25)
        g = pj(g).simplify(tol)
        polys = []
        for p in getattr(g, 'geoms', [g]):
            if p.geom_type != 'Polygon' or p.area < amin:
                continue
            polys.append([[[round(x, 2), round(y, 2)] for x, y in r.coords] for r in [p.exterior] + list(p.interiors) if len(r.coords) > 3])
        out['regions'][name] = polys
        print(f'{name:10s} {len(polys):4d} polygons {sum(len(r) for p in polys for r in p):6d} points')
    for name, pts in (('front_dec41', FRONT_DEC41[1:-3]), ('border_jun41', BORDER_JUN41), ('vichy', VICHY), ('split39', SOVZ_1939)):
        out['lines'][name] = [[round((lo - LON0) * CLAT * K, 2), round(-(la - LAT0) * K, 2)] for lo, la in pts]
    os.makedirs(os.path.join(ROOT, 'assets', 'map'), exist_ok=True)
    p = os.path.join(ROOT, 'assets', 'map', 'ww2_map.json')
    json.dump(out, open(p, 'w'), separators=(',', ':'))
    print('wrote', p, os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
