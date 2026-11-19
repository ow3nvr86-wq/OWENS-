"""WHAT IF YOU FELL INTO A HOLE THROUGH THE EARTH? ONE continuous camera move (two flashes hide set swaps). The 3D field,
cutaway Earth, tunnel, core and night ocean are rendered by tools/hole_oneshot.py into oneshot/ (frames + camera.json
with the camera, your track and your roll). Every time below comes from a cue word in work/words.json (same resolver as
the Blender script), so a new voiceover only needs: align -> this script -> re-render. Writes script.json.
Numbers on screen: sources.txt (42 min uniform Earth, 38 min real Earth, ~7.9 km/s at the centre, Kola 12 km, core
~5,200-5,400 C vs the Sun's surface ~5,500 C, 84-minute round trip). The tunnel itself is drawn compressed."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('hook', 'jump'), ('here', 'here'), ('minutes', 'minutes'), ('picture', 'picture'), ('tunnel', 'tunnel'), ('no', 'no'), ('step', 'step'),
        ('edge', 'edge'), ('fall', 'fall'), ('weightless', 'weightless'), ('under', 'under'), ('deepest', 'deepest'), ('twelve', 'twelve'),
        ('about', 'about'), ('center', 'center'), ('hot', 'hot'), ('eight', 'eight'), ('then', 'then'), ('flips', 'flips'), ('slows', 'slows'),
        ('rise', 'rise'), ('stop', 'stop'), ('top', 'top'), ('fortytwo', 'fortytwo'), ('really', 'really'), ('thirtyeight', 'thirtyeight'),
        ('jump2', 'jump'), ('us', 'us'), ('pop', 'pop'), ('indian', 'indian'), ('nobody', 'nobody'), ('fall2', 'fall'), ('forever', 'forever'),
        ('air', 'air'), ('stuck', 'stuck'), ('floating', 'floating'), ('would', 'would')]
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
b['flashA'] = b['picture'] + 0.42; b['flashB'] = b['step'] + 0.22; b['offEdge'] = b['edge'] + 0.15
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d

chars = [
  dict(id='you', cast='you', track='hero', autoGait=False, rollTrack=True, mood='neutral', lookAt='camera', nearFade=[0.7, 1.5],
       keys=[K(0.0, action='idle'), K(b['here'] - 0.15, action='wave'), K(b['minutes'] - 0.3, action='idle', lookAt='left'),
             K(b['flashB'], action='idle', mood='neutral', lookAt='camera'), K(b['edge'] - 0.05, action='jump', mood='shocked'),
             K(b['fall'], action='skydive', mood='scared'), K(b['weightless'], action='float', mood='neutral'),
             K(b['about'], action='skydive', mood='worried'), K(b['center'], action='float', mood='shocked'), K(b['eight'], mood='scared'),
             K(b['flips'] - 0.2, action='fall'), K(b['slows'], action='float', mood='worried'), K(b['stop'], action='float', mood='neutral'),
             K(b['pop'] - 0.1, action='cheer', mood='shocked'), K(b['pop'] + 0.9, action='float', mood='neutral'),
             K(b['nobody'], mood='worried'), K(b['fall2'], action='fall', mood='scared'), K(b['air'], action='skydive', mood='worried'),
             K(b['floating'], action='float', mood='worried'), K(b['would'], mood='neutral', lookAt='camera')]),
]

TAU = [dict(at=b['offEdge'], v=0), dict(at=b['weightless'], v=14), dict(at=b['under'], v=30), dict(at=b['twelve'], v=49.6),
       dict(at=b['about'], v=300), dict(at=b['center'], v=1266), dict(at=b['flips'] + 0.25, v=1268), dict(at=b['stop'], v=2532)]
fx = [
  dict(type='callout', at=b['minutes'] - 0.1, dur=1.0, x=0.5, y=0.12, text='42 MINUTES', size=70),
  dict(type='callout', at=b['tunnel'] - 0.1, dur=1.8, x=0.5, y=0.16, text='12,742 KM', sub='STRAIGHT THROUGH THE MIDDLE', size=66),
  dict(type='callout', at=b['no'] - 0.05, dur=1.0, x=0.5, y=0.16, text='NO AIR', size=72, edge='#5ad1ff'),
  dict(type='flash', at=b['flashA'] - 0.08, dur=0.4, amount=1.0), dict(type='flash', at=b['flashB'] - 0.08, dur=0.4, amount=1.0),
  dict(type='gauge', at=b['offEdge'], untilAt=b['jump2'] - 0.3, y=0.06, keys=TAU, T=2532, R=6371, fixAt=b['thirtyeight'] - 0.25, fixText='38:11', fixNote='REAL EARTH'),
  dict(type='gravity', at=b['fall'], untilAt=b['stop'] + 0.6, x=0.86, y=0.27, keys=[dict(at=b['flips'] - 0.2, a=0.0), dict(at=b['flips'] + 0.6, a=3.14159)]),
  dict(type='callout', at=b['hot'] - 0.15, dur=2.0, x=0.5, y=0.205, text='~5,200-5,400°C', sub="THE SUN'S SURFACE IS ~5,500°C", size=58, col='#3a0d06', edge='#ff7a2a'),
  dict(type='callout', at=b['eight'] - 0.1, dur=1.4, x=0.5, y=0.205, text='7.9 KM/S', sub='ABOUT 28,000 KM/H', size=70),
  dict(type='callout', at=b['indian'] - 0.1, dur=1.5, x=0.5, y=0.2, text='INDIAN OCEAN', sub='OPPOSITE MOST OF THE US', size=66, edge='#5ad1ff'),
  dict(type='callout', at=b['forever'] - 0.1, dur=1.2, x=0.5, y=0.2, text='FOREVER', sub='84 MINUTES THERE AND BACK', size=72),
  dict(type='callout', at=b['stuck'] - 0.05, dur=2.2, x=0.5, y=0.2, text='STUCK IN THE CENTER', sub='AIR SLOWS YOU DOWN EVERY TRIP', size=56, edge='#5ad1ff'),
  dict(type='speedlines', at=b['about'] + 0.4, dur=1.8, x=0.5, y=0.6), dict(type='speedlines', at=b['flips'] + 0.3, dur=1.2, x=0.5, y=0.45),
  dict(type='speedlines', at=b['air'] + 0.2, dur=1.6, x=0.5, y=0.6),
  dict(type='blast', at=b['center'], world=[0, 0, -900], r=1, only=['nobody'], shake=10, hidden=True),
  dict(type='darken', keys=[dict(at=END - 0.5, a=0.0), dict(at=END - 0.05, a=1.0)]),
]

sfx = [dict(type='wind', at=0.0, dur=3.6, gain=0.25), dict(type='pop', at=b['here'], gain=0.5), dict(type='ting', at=b['minutes'], gain=0.35),
       dict(type='whoosh', at=b['picture'] - 0.05, dur=0.6, gain=0.9), dict(type='boom', at=b['flashA'], gain=0.45), dict(type='ting', at=b['tunnel'], gain=0.3),
       dict(type='pop', at=b['no'], gain=0.5), dict(type='whoosh', at=b['step'] - 0.1, dur=0.5, gain=0.8), dict(type='boing', at=b['edge'], gain=0.4),
       dict(type='wind', at=b['fall'] - 0.3, dur=4.5, gain=0.5), dict(type='whoosh', at=b['under'], dur=0.5, gain=0.5), dict(type='ting', at=b['twelve'], gain=0.45),
       dict(type='whoosh', at=b['about'] + 0.3, dur=1.4, gain=0.9), dict(type='gust', at=b['about'] + 0.6, dur=2.2, gain=0.8),
       dict(type='crash', at=b['center'], gain=0.55), dict(type='crackle', at=b['center'] + 0.2, dur=4.6, gain=0.55), dict(type='hum', at=b['center'], dur=5.5, gain=0.3),
       dict(type='beep', at=b['eight'], gain=0.5), dict(type='spawn', at=b['flips'] - 0.2, dur=1.0, gain=0.5), dict(type='whoosh', at=b['flips'] + 0.3, dur=1.2, gain=0.9),
       dict(type='wind', at=b['slows'], dur=3.0, gain=0.4), dict(type='pop', at=b['stop'], gain=0.6), dict(type='wind', at=b['top'], dur=9.0, gain=0.2),
       dict(type='scratch', at=b['thirtyeight'] - 0.25, dur=0.4, gain=0.5), dict(type='ting', at=b['thirtyeight'], gain=0.4), dict(type='boing', at=b['pop'], gain=0.5),
       dict(type='whoosh', at=b['fall2'], dur=0.8, gain=0.8), dict(type='whoosh', at=b['air'] + 0.1, dur=1.6, gain=0.9), dict(type='gust', at=b['air'], dur=2.6, gain=0.9),
       dict(type='hum', at=b['stuck'], dur=4.5, gain=0.3), dict(type='crackle', at=b['floating'], dur=3.0, gain=0.35), dict(type='pop', at=b['would'], gain=0.4)]

S_ = dict(title='What If You Fell Into a Hole Through the Earth?', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.02) saturate(1.08) contrast(1.06)', thumbnail_cue=b['tunnel'] + 0.9,
  music=dict(level_db=-24, segments=[dict(style='chill', bpm=104, fadeIn=0.6, fadeOut=1.5, **{'from': 0.0, 'to': END})]),
  cast=dict(you=dict(costume='hoodie_green', mood='neutral', hair='#3a2618', hat='beanie')),
  scenes=[dict(cue='Jump', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
