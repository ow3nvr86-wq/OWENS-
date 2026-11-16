"""PORT HOLLOW (dystopian town Short): ONE continuous camera move, no cuts. The 3D town, the tower and the floor-9 hallway
are rendered by tools/town_oneshot.py into oneshot/ (frames + camera.json with the camera and the 2D actors' tracks).
Every time below comes from a cue word in work/words.json (same resolver as the Blender script), so a new voiceover
only needs: align -> this script -> re-render. Writes script.json.  FICTION: Port Hollow is made up (see story_notes.txt)."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = ['nobody', 'live', 'people', 'one', 'store', 'school', 'hall', 'never', 'good', 'cant', 'night', 'speakers', 'sealing', 'return', 'then',
        'slam', 'window', 'whiteout', 'bay', 'nobody', 'inside', 'man', 'later', 'smiling', 'name', 'lock', 'tunnel', 'shuts', 'morning', 'counts',
        'seventy', 'single', 'except', 'counted', 'seventyone', 'somebody', 'empty', 'next', 'yours']
KEYS = ['hook', 'live', 'people', 'one', 'store', 'school', 'hall', 'never', 'good', 'cant', 'night', 'speakers', 'sealing', 'ret', 'then',
        'slam', 'window', 'whiteout', 'bay', 'nobody2', 'inside', 'man', 'later', 'smiling', 'name', 'lock', 'tunnel', 'shuts', 'morning', 'counts',
        'seventy', 'single', 'except', 'counted', 'seventyone', 'somebody', 'empty', 'next', 'yours']
b = {}; wi = 0; ws = WORDS['words']
for key, cue in zip(KEYS, CUES):
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d

FH = 3.1; Z9 = FH * 8; SPEAKER = [0.0, 0.0, Z9 + 2.62]; SIGN = [0.0, -8.98, FH * 14 + 2.6]

chars = [
  dict(id='you', cast='you', track='hero', autoGait=True, mood='neutral', lookAt='camera',
       keys=[K(b['never'] - 0.4, mood='neutral', lookAt='camera'), K(b['good'], mood='smug'), K(b['cant'], mood='worried', lookAt='camera'),
             K(b['night'] + 0.2, mood='worried', lookAt='up'), K(b['speakers'], mood='scared', lookAt='up'), K(b['sealing'], mood='scared', lookAt='camera')]),
] + [dict(id='res%d' % i, cast='res%d' % i, track='res%d' % i, autoGait=True, mood='neutral', lookAt='camera' if i % 2 else 'left',
          keys=[K(b['speakers'] + 0.1 * i, mood='worried', lookAt='up'), K(b['ret'] + 0.05 * i, mood='scared', lookAt='right')]) for i in range(6)] + [
  dict(id='man', cast='man', track='man', autoGait=False, mood='creepy', lookAt='camera', blink=0,
       keys=[K(b['name'] - 0.2, lookAt='left'), K(b['name'] + 0.5, lookAt='camera')], nodAt=[b['name'] + 0.1]),
]

fx = [
  dict(type='snow', keys=[dict(at=0.0, a=1.0), dict(at=b['one'] + 0.5, a=1.0), dict(at=b['one'] + 0.8, a=0.0), dict(at=b['then'] + 0.8, a=0.0), dict(at=b['then'] + 1.2, a=1.0),
                          dict(at=b['inside'], a=0.6), dict(at=b['morning'], a=0.5), dict(at=b['morning'] + 1.5, a=1.0), dict(at=b['empty'] - 0.4, a=1.0), dict(at=b['empty'] - 0.1, a=0.0)]),
  dict(type='fog', keys=[dict(at=b['whiteout'] + 1.0, a=0.0), dict(at=b['nobody2'], a=0.35), dict(at=b['inside'], a=0.7), dict(at=b['man'] + 0.4, a=0.55),
                         dict(at=b['lock'], a=0.45), dict(at=b['tunnel'] + 0.2, a=0.2), dict(at=b['morning'], a=0.15), dict(at=b['morning'] + 1.2, a=0.0)]),
  dict(type='silhouette', world=[2.2, -21.0, 0.0], rW=2.5, keys=[dict(at=b['nobody2'], a=0.0), dict(at=b['nobody2'] + 0.7, a=0.75), dict(at=b['inside'] + 0.6, a=0.8), dict(at=b['man'], a=0.0)]),
  dict(type='waves', at=b['speakers'], dur=3.6, world=SPEAKER),
  dict(type='pa', at=b['sealing'] - 0.25, dur=0.95, x=0.5, y=0.2, dy=0, text='DOORS SEALING'),
  dict(type='pa', at=b['ret'] - 0.1, dur=1.4, x=0.5, y=0.2, dy=0, text='RETURN TO YOUR FLOOR', size=48),
  dict(type='nametag', of='man', at=b['name'] - 0.1, untilAt=b['tunnel']),
  dict(type='counter', at=b['counts'] - 0.3, world=SIGN, rW=9.0, glitchAt=b['counted'] + 0.2, redAt=b['seventyone'],
       keys=[dict(at=b['counts'] - 0.3, n=0), dict(at=b['seventy'], n=270, count=True), dict(at=b['seventyone'], n=271)]),
  dict(type='flicker', at=b['counted'] + 0.2, dur=0.6), dict(type='flicker', at=b['seventyone'], dur=0.5),
  dict(type='blast', at=b['slam'], world=[0.0, 0.0, 30.0], r=1, only=['nobody'], shake=14, hidden=True),
  dict(type='blast', at=b['lock'], world=[0.0, -8.0, 1.0], r=1, only=['nobody'], shake=10, hidden=True),
  dict(type='blast', at=b['shuts'], world=[0.0, 0.0, 0.0], r=1, only=['nobody'], shake=16, hidden=True),
  dict(type='blast', at=b['seventyone'], world=[0.0, 0.0, 0.0], r=1, only=['nobody'], shake=18, hidden=True),
  dict(type='eyes', at=END - 1.0, world=[-2.05, -1.9, Z9 + 1.62], rW=0.6),
  dict(type='darken', keys=[dict(at=END - 0.55, a=0.0), dict(at=END - 0.05, a=1.0)]),
]

sfx = [dict(type='wind', at=0.0, dur=8.5, gain=0.6), dict(type='gust', at=b['one'] - 0.9, dur=1.6, gain=0.8), dict(type='whoosh', at=b['store'] - 0.4, gain=0.7),
       dict(type='hum', at=b['store'], dur=7.0, gain=0.35), dict(type='ting', at=b['night'], gain=0.4), dict(type='crackle', at=b['speakers'], dur=1.4, gain=0.8),
       dict(type='alarm', at=b['sealing'] - 0.2, dur=2.2, gain=0.45), dict(type='whoosh', at=b['then'] + 0.2, gain=0.6), dict(type='slams', at=b['slam'] - 0.15, dur=1.9, gain=0.9),
       dict(type='wind', at=b['window'], dur=9.0, gain=0.7), dict(type='gust', at=b['whiteout'], dur=3.0, gain=0.9), dict(type='gust', at=b['nobody2'], dur=2.5, gain=0.7),
       dict(type='lock', at=b['lock'] - 0.02, gain=1.0), dict(type='slam', at=b['shuts'] - 0.05, gain=0.9), dict(type='alarm', at=b['shuts'] + 0.2, dur=0.9, gain=0.3),
       dict(type='counter', at=b['counts'] - 0.2, dur=1.6, gain=0.6), dict(type='beep', at=b['seventy'], gain=0.7), dict(type='glitch', at=b['counted'] + 0.2, gain=0.8),
       dict(type='beep', at=b['seventyone'] - 0.02, gain=0.8), dict(type='boom', at=b['seventyone'], gain=0.6), dict(type='glitch', at=b['seventyone'] + 0.05, dur=0.5, gain=0.6),
       dict(type='whoosh', at=b['somebody'] + 0.4, gain=0.7), dict(type='hum', at=b['empty'], dur=4.0, gain=0.25), dict(type='creak', at=END - 1.35, dur=1.3, gain=0.9)]

jump = lambda col, num, **k: dict(costume='jumpsuit', num=num, **k)
S_ = dict(title='Port Hollow', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.72, caption_case='lower', caption_size=78, grade='brightness(1.02) saturate(1.08) contrast(1.06)', thumbnail_cue=b['seventyone'] + 0.3,
  music=dict(level_db=-18, segments=[dict(style='dread', bpm=64, fadeIn=1.0, fadeOut=1.2, **{'from': 0.0, 'to': b['except'] + 0.4}),
                                     dict(style='reveal', bpm=60, fadeIn=0.05, fadeOut=0.8, **{'from': b['seventyone'] - 0.05, 'to': END})]),
  cast=dict(you=dict(costume='jumpsuit', num='9-14', hat='beanie', mood='neutral', hair='#3a2618'),
            res0=jump(0, '9-03', hat='none', hair='#2a1a10'), res1=jump(0, '9-07', hat='cap', hair='#6a4a2a'), res2=jump(0, '9-10', hat='none', hair='#c9a35a'),
            res3=jump(0, '9-17', hat='none', hair='#1a1a1a', facial='moustache'), res4=jump(0, '9-18', hat='cap', hair='#8a5a3a'), res5=jump(0, '9-21', hat='none', hair='#5a3a2a'),
            man=dict(costume='jumpsuit_snow', num='9-??', hat='none', mood='creepy', hair='#4a3a2a')),
  scenes=[dict(cue='Nobody', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
