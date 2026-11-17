"""THE LAST TOWN ON EARTH, PART 2: ONE continuous camera move, no cuts. The 3D town, the Tower, the floor-9 hallway and the
copy of your apartment are rendered by tools/town2_oneshot.py into oneshot/ (frames + camera.json with the camera and the
2D actors' tracks). Every time below comes from a cue word in work/words.json (same resolver as the Blender script), so a
new voiceover only needs: align -> this script -> re-render. Writes script.json.  FICTION (see story_notes.txt)."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('hook', 'never'), ('empty', 'empty'), ('nights', 'nights'), ('counted', 'counted'), ('seventyone', 'seventyone'), ('tonight', 'tonight'),
        ('knock', 'knock'), ('answers', 'answers'), ('door', 'door'), ('locked', 'locked'), ('inside', 'inside'), ('lamp', 'lamp'), ('bed', 'bed'),
        ('clock', 'clock'), ('fifteen', 'fifteen'), ('bed2', 'bed'), ('jumpsuit', 'jumpsuit'), ('folded', 'folded'), ('number', 'number'),
        ('yournum', 'your'), ('then', 'then'), ('speakers', 'speakers'), ('sealing', 'sealing'), ('ret', 'return'), ('run', 'run'), ('door2', 'door'),
        ('locked2', 'locked'), ('from', 'from'), ('through', 'through'), ('little', 'little'), ('window', 'window'), ('standing', 'standing'),
        ('wearing', 'wearing'), ('beanie', 'beanie'), ('smiling', 'smiling'), ('shutters', 'shutters'), ('slam', 'slam'), ('lights', 'lights'),
        ('die', 'die'), ('cold', 'cold'), ('six', 'six'), ('counts', 'counts'), ('seventy', 'seventy'), ('everyone', 'everyones'), ('home', 'home'),
        ('why', 'why'), ('snow', 'snow'), ('looking', 'looking'), ('own', 'own'), ('window2', 'window')]
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2; b['morning'] = b['six'] - 0.3
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d

FH = 3.1; Z9 = FH * 8; HW = 1.3; HERO_DOOR = 1.5; SIGN = [0.0, -8.98, FH * 14 + 2.6]; SPEAKER = [0.0, 0.0, Z9 + 2.62]
WINQ = [[HERO_DOOR - 0.16, -1.33, Z9 + 1.33], [HERO_DOOR + 0.16, -1.33, Z9 + 1.33], [HERO_DOOR + 0.16, -1.33, Z9 + 1.8], [HERO_DOOR - 0.16, -1.33, Z9 + 1.8]]
FACQ = [[HERO_DOOR - 0.8, -8.23, Z9 + 0.8], [HERO_DOOR + 0.8, -8.23, Z9 + 0.8], [HERO_DOOR + 0.8, -8.23, Z9 + 2.3], [HERO_DOOR - 0.8, -8.23, Z9 + 2.3]]

chars = [
  dict(id='you', cast='you', track='hero', autoGait=True, mood='worried', lookAt='left', nearFade=[0.6, 1.4],
       keys=[K(b['tonight'], mood='neutral', lookAt='left'), K(b['knock'] - 0.15, action='knock', lookAt='left'), K(b['answers'] + 0.35, action='idle', mood='worried'),
             K(b['door'], mood='scared', lookAt='left'), K(b['inside'] + 0.5, mood='worried', lookAt='camera'), K(b['jumpsuit'], mood='scared', lookAt='right'),
             K(b['speakers'], mood='scared', lookAt='up'), K(b['run'] - 0.1, mood='scared', lookAt='right'),
             K(b['locked2'] - 0.25, action='rattle', mood='scared', lookAt='left'), K(b['through'] - 0.1, action='idle', mood='scared', lookAt='left'),
             K(b['home'], action='idle', mood='worried', lookAt='up'), K(b['why'], mood='scared', lookAt='up')]),
  dict(id='double', cast='double', track='double', autoGait=False, mood='creepy', lookAt='camera', blink=0, clipQuad=WINQ, nodAt=[b['smiling'] + 0.05]),
  dict(id='double2', cast='double', track='double2', autoGait=False, size=0.75, mood='creepy', lookAt='camera', blink=0, clipQuad=FACQ,
       keys=[K(b['own'] - 0.1, action='wave')]),
]

fx = [
  dict(type='counter', at=0.0, world=[-0.6, HW - 0.14, Z9 + 2.15], rW=0.78, redAt=-1.0, untilAt=b['slam'] + 1.0, keys=[dict(at=0.0, n=271)]),
  dict(type='counter', at=b['counts'] - 0.3, world=SIGN, rW=9.0, keys=[dict(at=b['counts'] - 0.3, n=0), dict(at=b['seventy'], n=270, count=True)]),
  dict(type='snow', keys=[dict(at=0.0, a=0.0), dict(at=b['slam'] + 0.55, a=0.0), dict(at=b['slam'] + 0.9, a=1.0), dict(at=b['cold'], a=0.8),
                          dict(at=b['morning'], a=0.5), dict(at=b['morning'] + 1.5, a=1.0)]),
  dict(type='fog', keys=[dict(at=b['cold'] - 0.4, a=0.0), dict(at=b['cold'] + 0.8, a=0.65), dict(at=b['morning'], a=0.4), dict(at=b['morning'] + 1.4, a=0.0)]),
  dict(type='waves', at=b['speakers'], dur=3.0, world=SPEAKER),
  dict(type='pa', at=b['sealing'] - 0.25, dur=0.95, x=0.5, y=0.2, dy=0, text='DOORS SEALING'),
  dict(type='pa', at=b['ret'] - 0.1, dur=1.4, x=0.5, y=0.2, dy=0, text='RETURN TO YOUR FLOOR', size=48),
  dict(type='flicker', at=b['die'] - 0.1, dur=0.5),
  dict(type='blast', at=b['locked2'], world=[HERO_DOOR, -1.3, Z9 + 1.0], r=1, only=['nobody'], shake=8, hidden=True),
  dict(type='blast', at=b['slam'], world=[0.0, 0.0, 30.0], r=1, only=['nobody'], shake=14, hidden=True),
  dict(type='blast', at=b['own'], world=[0.0, 0.0, 0.0], r=1, only=['nobody'], shake=6, hidden=True),
  dict(type='darken', keys=[dict(at=END - 0.5, a=0.0), dict(at=END - 0.05, a=1.0)]),
]

sfx = [dict(type='hum', at=0.0, dur=7.0, gain=0.3), dict(type='knock', at=b['knock'] - 0.05, gain=1.0), dict(type='knock', at=b['knock'] + 0.2, gain=0.9),
       dict(type='knock', at=b['knock'] + 0.45, gain=0.9), dict(type='creak', at=b['door'] - 0.05, dur=1.3, gain=0.9), dict(type='hum', at=b['inside'], dur=10.5, gain=0.25),
       dict(type='ting', at=b['fifteen'], gain=0.3), dict(type='boom', at=b['yournum'], gain=0.5), dict(type='crackle', at=b['speakers'], dur=1.4, gain=0.8),
       dict(type='alarm', at=b['sealing'] - 0.2, dur=2.2, gain=0.45), dict(type='whoosh', at=b['run'], gain=0.6), dict(type='lock', at=b['locked2'] - 0.05, gain=1.0),
       dict(type='lock', at=b['locked2'] + 0.3, gain=0.8), dict(type='boom', at=b['smiling'], gain=0.45), dict(type='whoosh', at=b['shutters'], gain=0.8),
       dict(type='slams', at=b['slam'] - 0.15, dur=2.0, gain=0.9), dict(type='glitch', at=b['die'] - 0.1, dur=0.5, gain=0.6), dict(type='boom', at=b['die'] + 0.05, gain=0.5),
       dict(type='wind', at=b['slam'] + 0.6, dur=8.0, gain=0.6), dict(type='gust', at=b['cold'] - 0.3, dur=2.5, gain=0.9),
       dict(type='counter', at=b['counts'] - 0.2, dur=1.6, gain=0.6), dict(type='beep', at=b['seventy'], gain=0.7), dict(type='wind', at=b['home'], dur=7.0, gain=0.55),
       dict(type='boom', at=b['own'], gain=0.6)]

S_ = dict(title='The Last Town on Earth, Part 2', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.02) saturate(1.08) contrast(1.06)', thumbnail_cue=b['standing'] + 0.6,
  music=dict(level_db=-25, segments=[dict(file='music/six_forty_seven.mp3', offset=0.0, fadeIn=0.8, fadeOut=1.5, **{'from': 0.0, 'to': END})]),   # your track, kept light under the voice
  cast=dict(you=dict(costume='jumpsuit', num='9-14', hat='beanie', mood='neutral', hair='#3a2618'),
            double=dict(costume='jumpsuit', num='9-14', hat='beanie', mood='creepy', hair='#3a2618')),
  scenes=[dict(cue='Never', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
