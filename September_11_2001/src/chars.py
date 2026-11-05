"""The people of the film, all invented: Pripyat residents in 1980s Soviet dress, plant operators in white
coats and caps, firefighters in canvas suits and helmets, militia officers, evacuation officials and children
(some in school uniform with a Young Pioneer's red neckerchief). Built on the rig in figures.py."""
from core import PAL, hash01, mix, shade_c
from figures import make_char

COATS_M = [PAL['grey2'], PAL['brown'], PAL['umber'], PAL['charcoal2'], PAL['green3'], mix(PAL['grey'], PAL['brown2'], 0.5),
           mix(PAL['burg3'], PAL['brown'], 0.4), PAL['brown2']]
COATS_F = [mix(PAL['burg2'], PAL['brown2'], 0.3), PAL['green2'], PAL['parch3'], mix(PAL['grey3'], PAL['brown3'], 0.4), PAL['burg3'],
           mix(PAL['green'], PAL['grey'], 0.5), PAL['brown3'], mix(PAL['linen2'], PAL['grey3'], 0.5)]
TROUSERS = [PAL['charcoal2'], PAL['grey2'], PAL['umber'], mix(PAL['charcoal'], PAL['grey'], 0.4), PAL['brown']]


def person(kind, seed, **over):
    r = lambda k: hash01(seed, k, 77)
    if kind == 'man':
        c = make_char(seed, 'm', ['young', 'adult', 'adult', 'old'][int(r(1) * 4)], dress='modern', coat=COATS_M[int(r(2) * 8)],
                      hose=TROUSERS[int(r(3) * 5)], head=['none', 'none', 'flatcap', 'none'][int(r(4) * 4)],
                      cap=[PAL['grey2'], PAL['charcoal2'], PAL['brown']][int(r(5) * 3)], beard='short' if r(6) < 0.15 else None,
                      shoe=PAL['ink'])
        c['hose2'] = c['hose']
        c['hunch'] = 0.05 if c['age'] == 'old' else 0.0
    elif kind == 'woman':
        age = ['young', 'adult', 'adult', 'old'][int(r(1) * 4)]
        c = make_char(seed, 'f', age, gown=COATS_F[int(r(2) * 8)], apron=None, head='kerchief' if age == 'old' else 'none',
                      hem=30 + 8 * r(3), tights=mix(PAL['skin3'], PAL['brown'], 0.4), partlet=PAL['linen2'], shoe=PAL['ink'])
        c['hair'] = [PAL['hair_br'], PAL['hair_dk'], PAL['hair_bl'], mix(PAL['hair_br'], PAL['burg2'], 0.3)][int(r(4) * 4)] if age != 'old' else PAL['hair_gr']
        c['hunch'] = 0.06 if age == 'old' else 0.0
    elif kind == 'girl':
        c = make_char(seed, 'f', 'child', gown=mix(PAL['brown'], PAL['umber'], 0.5), apron=PAL['ink'] if r(1) < 0.5 else PAL['linen'],
                      head='none', hem=26, scarf=r(2) < 0.7, tights=PAL['linen2'], partlet=PAL['linen'], shoe=PAL['ink'])
        c['hair'] = [PAL['hair_br'], PAL['hair_bl'], PAL['hair_dk']][int(r(3) * 3)]
    elif kind == 'boy':
        c = make_char(seed, 'm', 'child', dress='modern', coat=mix(PAL['charcoal2'], PAL['grey2'], 0.5) if r(1) < 0.6 else PAL['green3'],
                      hose=PAL['charcoal2'], head='none', scarf=r(2) < 0.7, shoe=PAL['ink'])
        c['hose2'] = c['hose']
    elif kind == 'operator':
        c = make_char(seed, 'm', ['young', 'adult', 'adult'][int(r(1) * 3)], dress='robe', coat=PAL['linen'], sleeve=PAL['linen'],
                      fur=None, head='whitecap', hose=PAL['charcoal2'], hose2=PAL['charcoal2'], hem=36, shoe=PAL['ink'],
                      partlet=mix(PAL['grey3'], PAL['linen'], 0.5), beard=None)
        c['role'] = 'priest'          # an open-fronted coat drawn without fur
        c['surplice'] = False
    elif kind == 'fireman':
        canvas = mix(PAL['brown3'], PAL['grey'], 0.35 + 0.2 * r(1))
        c = make_char(seed, 'm', ['young', 'young', 'adult'][int(r(2) * 3)], dress='modern', coat=canvas, sleeve=canvas, hose=canvas,
                      head='firehelmet', cap=mix(PAL['burg2'], PAL['charcoal2'], 0.35), belt=PAL['ink'], shoe=PAL['ink'], beard=None,
                      reflect=None)
        c['hose2'] = c['hose']
    elif kind == 'militia':
        uni = mix(PAL['grey2'], PAL['green3'], 0.25)
        c = make_char(seed, 'm', 'adult', dress='modern', coat=uni, sleeve=uni, hose=shade_c(uni, -0.2), head='peaked', cap=uni,
                      band=PAL['burg2'], belt=PAL['ink'], shoe=PAL['ink'], beard=None)
        c['hose2'] = c['hose']
    elif kind == 'official':
        c = make_char(seed, 'm', 'adult', dress='modern', coat=PAL['charcoal2'], hose=PAL['charcoal2'], head='none', tie=PAL['burg3'],
                      shoe=PAL['ink'], beard=None)
        c['hose2'] = c['hose']
    else:
        raise ValueError(kind)
    c.update(over)
    return c


def crowd(n, seed, kinds=('man', 'woman', 'woman', 'man', 'girl', 'boy', 'woman', 'man')):
    return [person(kinds[(i + seed) % len(kinds)], seed * 100 + i) for i in range(n)]
