"""MOVIES IN A MINUTE: INTERSTELLAR (2014). ONE continuous camera move through a bright cel-shaded cartoon world with a
fully 3D cast and physics-driven motion (tools/interstellar_oneshot.py renders it into oneshot/ with camera.json). The
compositor adds only captions, callouts, name tags (which follow the 3D actors' tracks: ghost actors, nothing drawn),
flashes and speed lines. Every time comes from a cue word in work/words.json (same resolver as the Blender script).
Plot facts: sources.txt. Original characters, set designs and music; no film footage, audio, logos or likenesses."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
src = open(os.path.join(HERE, '..', '..', 'tools', 'interstellar_oneshot.py')).read()
CUES = eval(src[src.index('CUES = ') + 7:src.index('B = {}')])
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
b.update(space=b['goes'] + 0.55, miller0=b['millers'] - 0.05, hit=b['doyle'] - 0.1, lift=b['t23'] + 0.35, mann0=b['then'] - 0.05,
         shove=b['tries'] + 0.12, garg0=b['low'] - 0.08, sep=b['detaches'] + 0.1, tes0=b['inside'] - 0.02, push=b['ghost2'] - 0.35,
         watch0=b['ticks'] - 0.2, ark0=b['murph3'] - 0.3, sta0=b['cooper5'] - 0.12, room0=b['murph4'] - 0.55)
FLASH = [b['murph2'] - 0.1, b['space'] - 0.01, b['miller0'] - 0.04, b['mann0'] - 0.03, b['garg0'] - 0.03, b['tes0'] - 0.03,
         b['watch0'] - 0.03, b['sta0'] - 0.03, b['room0'] - 0.03]

# 3D actors: tracks only, for the tags (nothing is drawn by the compositor)
chars = [dict(id=k, cast='cobb', track=k, ghost=True, size=sz) for k, sz in
         (('cooper', 1.0), ('murphK', 0.72), ('brandP', 0.97), ('amelia', 0.94), ('doyle', 1.0), ('mann', 1.0), ('cooperS', 1.0), ('murphA', 0.94), ('murphO', 0.4))]

GOLD = '#ffc23a'
fx = [
  dict(type='callout', at=0.2, dur=1.7, x=0.5, y=0.17, text='INTERSTELLAR', sub='(2014)', size=80, edge='#8ac8ff'),
  dict(type='tag', at=b['leave'] - 0.6, untilAt=b['promised'] - 0.1, of='murphK', text='MURPH', bg='#a8e07a'),
  dict(type='tag', at=b['promised'] - 0.1, untilAt=b['earth1'] - 0.3, of='cooper', text='COOPER', bg='#8ab4ff'),
  dict(type='callout', at=b['dying'] - 0.1, dur=1.0, x=0.5, y=0.17, text='EARTH IS DYING', size=78, edge='#ffb86a'),
  dict(type='callout', at=b['dust1'] - 0.05, dur=1.7, x=0.5, y=0.17, text='DUST STORMS', sub='FAILING CROPS', size=80, edge='#e0a060'),
  dict(type='speedlines', at=b['cooper1'] - 0.35, dur=0.6, x=0.5, y=0.5),
  dict(type='tag', at=b['cooper1'] + 0.1, untilAt=b['finds'] - 0.1, of='cooper', text='COOPER', bg='#8ab4ff'),
  dict(type='callout', at=b['exnasa'] - 0.05, dur=1.1, x=0.5, y=0.17, text='EX-NASA PILOT', sub='NOW A FARMER', size=76, edge='#7ac8ff'),
  dict(type='speedlines', at=b['finds'], dur=0.7, x=0.5, y=0.5),
  dict(type='callout', at=b['code1'] - 0.05, dur=1.6, x=0.5, y=0.17, text='A CODE IN THE DUST', size=70, edge=GOLD),
  dict(type='tag', at=b['murphs1'] - 0.2, untilAt=b['calls'] - 0.1, of='murphK', text='MURPH', bg='#a8e07a'),
  dict(type='callout', at=b['ghost1'] - 0.1, dur=0.9, x=0.5, y=0.17, text='"A GHOST"', size=84, edge='#c8a0ff'),
  dict(type='speedlines', at=b['leads'] - 0.05, dur=1.2, x=0.5, y=0.5),
  dict(type='callout', at=b['secret'] - 0.05, dur=1.3, x=0.5, y=0.17, text='SECRET NASA BASE', size=74, edge='#7ac8ff'),
  dict(type='tag', at=b['base'] + 0.3, untilAt=b['wormhole'] - 0.2, of='brandP', text='PROF. BRAND', bg='#e0e0e8'),
  dict(type='callout', at=b['wormhole'] - 0.05, dur=1.5, x=0.5, y=0.17, text='A WORMHOLE', sub='NEAR SATURN', size=80, edge='#c8a0ff'),
  dict(type='callout', at=b['stay'] - 0.1, dur=1.0, x=0.5, y=0.17, text='"STAY"', size=96, edge='#a8e07a'),
  dict(type='callout', at=b['watch1'] - 0.1, dur=1.0, x=0.5, y=0.17, text='HIS WATCH', size=80, edge=GOLD),
  dict(type='speedlines', at=b['goes'] + 0.1, dur=0.9, x=0.5, y=0.5),
  dict(type='callout', at=b['millers'] + 0.05, dur=1.2, x=0.5, y=0.17, text="MILLER'S PLANET", size=74, edge='#7ae8f0'),
  dict(type='callout', at=b['hour'] - 0.15, dur=2.3, x=0.5, y=0.17, text='1 HOUR HERE', sub='= 7 YEARS ON EARTH', size=80, edge=GOLD),
  dict(type='tag', at=b['earth2'] - 0.2, untilAt=b['giant'] - 0.05, of='doyle', text='DOYLE', bg='#ffd8a8'),
  dict(type='callout', at=b['giant'] - 0.05, dur=1.2, x=0.5, y=0.17, text='A GIANT WAVE', size=80, edge='#7ae8f0'),
  dict(type='tag', at=b['giant'] + 0.2, untilAt=b['kills'] - 0.1, of='amelia', text='BRAND', bg='#c8d8ff'),
  dict(type='impactframe', at=b['hit'], dur=0.06),
  dict(type='callout', at=b['t23'] - 0.05, dur=1.5, x=0.5, y=0.17, text='23 YEARS', sub='GONE', size=96, edge='#ff8a7a'),
  dict(type='tag', at=b['mann'] - 0.1, untilAt=b['faked'] - 0.15, of='mann', text='DR. MANN', bg='#ffe08a'),
  dict(type='callout', at=b['faked'] - 0.05, dur=1.5, x=0.5, y=0.17, text='FAKED DATA', sub='TO GET RESCUED', size=80, edge='#ff6a5a'),
  dict(type='impactframe', at=b['shove'], dur=0.06),
  dict(type='callout', at=b['fuel'] - 0.3, dur=1.0, x=0.5, y=0.17, text='LOW ON FUEL', size=80, edge='#ff8a5a'),
  dict(type='callout', at=b['black'] - 0.05, dur=1.9, x=0.5, y=0.17, text='GARGANTUA', sub='A BLACK HOLE', size=84, edge=GOLD),
  dict(type='speedlines', at=b['make'], dur=0.6, x=0.5, y=0.5),
  dict(type='callout', at=b['bedroom'] - 0.1, dur=1.6, x=0.5, y=0.17, text='EVERY MOMENT', sub="OF MURPH'S ROOM", size=76, edge='#ffcc5a'),
  dict(type='callout', at=b['ghost2'] - 0.25, dur=0.95, x=0.5, y=0.17, text='HE WAS THE GHOST', size=72, edge='#c8a0ff'),
  dict(type='callout', at=b['morse'] - 0.1, dur=0.9, x=0.5, y=0.17, text='MORSE CODE', sub='. - - .', size=80, edge=GOLD),
  dict(type='tag', at=b['murph3'] - 0.2, untilAt=b['gravity'] - 0.1, of='murphA', text='MURPH', bg='#ffb89a'),
  dict(type='callout', at=b['gravity'] - 0.05, dur=1.1, x=0.5, y=0.17, text='GRAVITY: SOLVED', size=74, edge='#7aff9a'),
  dict(type='callout', at=b['station'] - 0.1, dur=1.3, x=0.5, y=0.17, text='A STATION', sub='BY SATURN', size=80, edge='#8ac8ff'),
  dict(type='tag', at=b['old'] - 0.1, untilAt=b['sends'] - 0.1, of='murphO', text='MURPH', bg='#ffb89a'),
  dict(type='callout', at=b['find'] - 0.1, dur=0.9, x=0.5, y=0.17, text='FIND BRAND', size=82, edge='#c8d8ff'),
  dict(type='callout', at=b['would'] - 0.05, dur=END - b['would'], x=0.5, y=0.17, text='WOULD YOU', sub='HAVE STAYED?', size=86, edge='#a8e07a'),
  dict(type='darken', keys=[dict(at=END - 0.45, a=0.0), dict(at=END - 0.05, a=1.0)]),
]
for ft in FLASH: fx.append(dict(type='flash', at=ft - 0.04, dur=0.32, amount=0.95))
tint = [dict(at=0.0, col='#ffe0c0', a=0.05)]

sfx = [dict(type='sting', at=0.25, gain=0.35), dict(type='wind', at=b['earth1'], dur=3.2, gain=0.5), dict(type='rumble', at=b['dust1'] - 0.2, dur=2.0, gain=0.5),
       dict(type='whoosh', at=b['cooper1'] - 0.4, dur=0.7, gain=0.6), dict(type='whoosh', at=b['finds'], dur=0.8, gain=0.7),
       dict(type='gust', at=b['code1'], dur=1.6, gain=0.35), dict(type='ting', at=b['code1'] + 0.2, gain=0.3), dict(type='knock', at=b['ghost1'] + 0.35, gain=0.6),
       dict(type='whoosh', at=b['leads'], dur=1.1, gain=0.8), dict(type='hum', at=b['base'], dur=2.4, gain=0.3), dict(type='charge', at=b['wormhole'] - 0.3, dur=0.9, gain=0.3),
       dict(type='whoosh', at=FLASH[0], dur=0.5, gain=0.7), dict(type='ting', at=b['watch1'], gain=0.35),
       dict(type='whoosh', at=b['goes'] + 0.2, dur=0.7, gain=0.9), dict(type='boom', at=FLASH[2], gain=0.5), dict(type='whoosh', at=FLASH[2] - 0.2, dur=0.5, gain=0.9),
       dict(type='tick', at=b['hour'], gain=0.6), dict(type='tick', at=b['hour'] + 0.5, gain=0.6), dict(type='tick', at=b['seven'], gain=0.6), dict(type='tick', at=b['seven'] + 0.5, gain=0.6),
       dict(type='rumble', at=b['earth2'], dur=2.6, gain=0.6), dict(type='crash', at=b['hit'], gain=0.6), dict(type='rumble', at=b['hit'], dur=1.4, gain=0.8),
       dict(type='engine', at=b['lift'], dur=1.3, gain=0.45), dict(type='whoosh', at=FLASH[3] - 0.15, dur=0.5, gain=0.8), dict(type='wind', at=b['mann0'], dur=3.4, gain=0.35),
       dict(type='beep', at=b['data1'], gain=0.3), dict(type='punch', at=b['shove'], gain=0.6), dict(type='slam', at=b['shove'] + 0.75, gain=0.5),
       dict(type='whoosh', at=FLASH[4] - 0.15, dur=0.5, gain=0.8), dict(type='hum', at=b['garg0'], dur=5.4, gain=0.35), dict(type='beep', at=b['fuel'], gain=0.25),
       dict(type='crackle', at=b['sep'] - 0.05, dur=0.3, gain=0.4), dict(type='whoosh', at=b['falls'], dur=1.2, gain=0.6), dict(type='rumble', at=b['hole'], dur=2.2, gain=0.5),
       dict(type='whoosh', at=b['make'] + 0.1, dur=0.6, gain=0.9), dict(type='boom', at=FLASH[5], gain=0.45), dict(type='hum', at=b['tes0'], dur=4.8, gain=0.3),
       dict(type='knock', at=b['push'] + 0.4, gain=0.5), dict(type='ting', at=b['ghost2'], gain=0.3)]
sfx += [dict(type='tick', at=b['watch0'] + 0.15 + k * 0.42, gain=0.7 if k % 3 else 0.9) for k in range(int((b['murph3'] - b['watch0']) / 0.42))]
sfx += [dict(type='sting', at=b['gravity'], gain=0.45), dict(type='rumble', at=b['ark0'] + 0.2, dur=3.2, gain=0.6), dict(type='engine', at=b['humanity2'], dur=1.6, gain=0.5),
        dict(type='whoosh', at=FLASH[7] - 0.15, dur=0.5, gain=0.8), dict(type='hum', at=b['sta0'], dur=1.8, gain=0.3), dict(type='whoosh', at=FLASH[8] - 0.1, dur=0.4, gain=0.6),
        dict(type='beep', at=b['old'] + 0.3, gain=0.18), dict(type='beep', at=b['old'] + 1.3, gain=0.18), dict(type='beep', at=b['old'] + 2.3, gain=0.18),
        dict(type='tada', at=b['would'] - 0.1, gain=0.0), dict(type='sting', at=b['would'], gain=0.4)]

S_ = dict(title='Movies in a Minute: Interstellar', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.02) saturate(1.06) contrast(1.04)', thumbnail_cue=b['hit'] - 0.6,
  music=dict(level_db=-24, segments=[dict(style='cosmic', bpm=72, fadeIn=0.8, fadeOut=0.4, **{'from': 0.0, 'to': b['earth2']}),
                                     dict(style='dread', bpm=76, fadeIn=0.3, fadeOut=0.4, **{'from': b['earth2'], 'to': b['low']}),
                                     dict(style='cosmic', bpm=72, fadeIn=0.4, fadeOut=0.3, **{'from': b['low'], 'to': b['ticks']}),
                                     dict(style='reveal', bpm=90, fadeIn=0.2, fadeOut=0.4, **{'from': b['ticks'], 'to': b['murph3']}),
                                     dict(style='cosmic', bpm=80, fadeIn=0.4, fadeOut=1.5, **{'from': b['murph3'], 'to': END})]),
  cast=dict(cobb=dict(costume='suit_navy', mood='neutral', hair='#4a3426')),
  scenes=[dict(cue='To', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=[s for s in sfx if s.get('gain', 1) > 0], charTint=tint)])
json.dump(S_, open(P, 'w'), indent=1, ensure_ascii=False); print('1 scene,', len(chars), 'ghost actors,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
