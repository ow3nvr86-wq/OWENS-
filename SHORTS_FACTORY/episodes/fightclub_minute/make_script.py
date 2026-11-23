"""MOVIES IN A MINUTE: FIGHT CLUB (1999). ONE continuous camera move through one rainy night city (no cuts).
The 3D city, basement, office, hall, plane, house, high-rise and skyline are rendered by tools/fightclub_oneshot.py into
oneshot/ (frames + camera.json with the camera and every 2D actor's track). Every time below comes from a cue word in
work/words.json (same resolver as the Blender script), so a new voiceover only needs: align -> this script -> re-render.
Plot facts: sources.txt. Original characters and music; no film footage, audio, logos or likenesses."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('fight1', 'fight'), ('problem', 'problem'), ('exist', 'exist'), ('lonely', 'lonely'), ('sleep', 'sleep'), ('so', 'so'), ('support', 'support'),
        ('finally', 'finally'), ('sleeps', 'sleeps'), ('marla', 'marla'), ('faker', 'faker'), ('ruins', 'ruins'), ('flight', 'flight'), ('meets', 'meets'),
        ('tyler1', 'tyler'), ('soap1', 'soap'), ('then', 'then'), ('explodes', 'explodes'), ('calls', 'calls'), ('bar1', 'bar'), ('hit', 'hit'),
        ('fight2', 'fight'), ('soon', 'soon'), ('basement', 'basement'), ('rule', 'rule'), ('talk', 'talk'), ('move', 'move'), ('crumbling', 'crumbling'),
        ('tyler3', 'tyler'), ('soap2', 'soap'), ('fat', 'fat'), ('then2', 'then'), ('army', 'army'), ('project', 'project'), ('police', 'police'),
        ('kill', 'kill'), ('bob', 'bob'), ('shut', 'shut'), ('discovers', 'discovers'), ('truth', 'truth'), ('heis', 'he'), ('tyler4', 'tyler'),
        ('stop', 'stop'), ('shoots', 'shoots'), ('cheek', 'cheek'), ('gone', 'tylers'), ('bombs', 'bombs'), ('holds', 'holds'), ('hand', 'hand'),
        ('towers', 'towers'), ('fall', 'fall'), ('would', 'would')]
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
b['vanish'] = b['exist'] + 0.25; b['boom'] = b['explodes'] + 0.08; b['shotB'] = b['kill'] + 0.06; b['glitch'] = b['heis'] - 0.05
b['bang'] = b['cheek'] + 0.12; b['bomb0'] = b['bombs'] + 0.12; b['crash'] = b['towers'] - 0.5
HOOK1 = b['vanish'] + 0.45; CLUB0, CLUB1 = b['soon'] + 0.3, b['move'] + 0.2
BOMBS = [b['bomb0'] + k * 0.32 for k in range(5)]
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d
NF = [0.45, 1.1]

chars = [
  dict(id='narr', cast='narr', track='narr', autoGait=True, mood='worried', lookAt='right', nearFade=NF,
       keys=[K(0.0, action='idle', mood='worried', lookAt='right'), K(b['problem'], mood='sad', lookAt='camera'), K(b['vanish'], mood='shocked', lookAt='right'),
             K(HOOK1, action='sit', mood='sad', lookAt='camera'), K(b['so'] + 0.25, action='sit', mood='sad', lookAt='left'),
             K(b['sleeps'], mood='happy', lookAt='camera'), K(b['marla'] + 0.25, mood='shocked', lookAt='right'), K(b['ruins'], mood='angry'),
             K(b['ruins'] + 0.6, action='sit', mood='neutral', lookAt='right'), K(b['meets'] + 0.2, mood='worried'),
             K(b['then'] - 0.2, action='hold', prop='phone', mood='shocked', lookAt='camera'), K(b['calls'] + 0.45, action='idle', prop='', mood='worried', lookAt='left'),
             K(b['bar1'] + 0.4, mood='neutral', lookAt='left'), K(b['hit'] + 0.2, mood='shocked'), K(b['hit'] + 0.95, action='punch', mood='determined'),
             K(b['hit'] + 1.35, action='idle', mood='happy'), K(b['fight2'] + 0.35, mood='shocked'), K(b['fight2'] + 0.5, action='punch', mood='angry'),
             K(b['soon'] + 0.05, action='idle'), K(CLUB0, action='cheer', mood='happy', lookAt='left'), K(b['rule'], action='idle', mood='smug', lookAt='left'),
             K(CLUB1, action='hold', prop='soap', mood='neutral', lookAt='right'), K(b['fat'], mood='worried'),
             K(b['shut'] - 0.6, action='idle', prop='', mood='worried', lookAt='camera'), K(b['discovers'], mood='shocked', lookAt='right'),
             K(b['heis'], mood='scared'), K(b['stop'], mood='determined')]),
  dict(id='narr_b', cast='narr_b', track='narr_b', autoGait=False, mood='determined', lookAt='right', nearFade=NF,
       keys=[K(b['bang'], action='idle', mood='shocked', lookAt='camera'), K(b['gone'] + 0.2, mood='neutral', lookAt='right'),
             K(b['bombs'] + 0.1, mood='shocked', lookAt='camera'), K(b['holds'] + 0.3, mood='neutral', lookAt='right'), K(b['towers'], mood='sad', lookAt='camera')]),
  dict(id='tyler', cast='tyler', track='tyler', autoGait=False, mood='smug', lookAt='left', nearFade=NF,
       keys=[K(0.0, action='idle', mood='smug', lookAt='left'), K(b['problem'], lookAt='camera'),
             K(b['ruins'] + 0.6, action='sit', mood='smug', lookAt='left'), K(b['meets'], action='talk'), K(b['soap1'] - 0.15, action='hold', prop='soap', mood='happy'),
             K(b['then'] - 0.3, action='idle', prop=''),
             K(b['bar1'] - 0.6, action='idle', mood='smug', lookAt='right'), K(b['hit'] - 0.1, action='talk'), K(b['hit'] + 0.95, action='idle'),
             K(b['hit'] + 1.15, mood='shocked'), K(b['fight2'] + 0.05, action='punch', mood='happy'), K(b['fight2'] + 0.4, action='idle'),
             K(CLUB0, action='talk', mood='determined', lookAt='camera'), K(b['talk'] + 0.6, action='idle', mood='smug'),
             K(CLUB1, action='build', mood='happy', lookAt='left'), K(b['soap2'], action='hold', prop='soap'), K(b['then2'], action='idle', prop=''),
             K(b['discovers'] - 0.05, action='idle', mood='smug', lookAt='left'), K(b['heis'], mood='creepy', lookAt='camera'), K(b['stop'], mood='smug', lookAt='left'),
             K(b['bang'], mood='shocked')]),
  dict(id='bob', cast='bob', track='bob', autoGait=False, rollTrack=True, mood='sad', lookAt='right', nearFade=NF,
       keys=[K(0.0, action='sit', mood='sad', lookAt='right'), K(b['sleeps'], mood='happy'), K(b['marla'] + 0.3, mood='worried', lookAt='right'),
             K(CLUB0, action='cheer', mood='happy', lookAt='right'), K(b['then2'] + 1.6, action='idle', mood='determined', lookAt='right'),
             K(b['police'] - 0.1, mood='scared'), K(b['shotB'], action='fall', mood='shocked'), K(b['shotB'] + 0.45, action='idle', mood='sad')]),
  dict(id='marla', cast='marla', track='marla', autoGait=True, mood='smug', lookAt='right', nearFade=NF,
       keys=[K(b['marla'] - 0.3, action='idle', mood='smug', lookAt='left'), K(b['faker'], mood='smug', lookAt='camera'), K(b['ruins'], mood='happy', lookAt='left'),
             K(b['holds'] - 0.55, mood='neutral', lookAt='left'), K(b['hand'], mood='worried', lookAt='camera')]),
  dict(id='sg1', cast='sg1', track='sg1', autoGait=False, mood='sad', lookAt='left', nearFade=NF, keys=[K(0.0, action='sit'), K(b['marla'] + 0.3, lookAt='right', mood='worried')]),
  dict(id='sg2', cast='sg2', track='sg2', autoGait=False, mood='sad', lookAt='right', nearFade=NF, keys=[K(0.0, action='sit'), K(b['sleeps'], mood='neutral')]),
  dict(id='pat1', cast='pat1', track='pat1', autoGait=True, mood='shocked', lookAt='right', nearFade=NF, keys=[K(b['soon'] - 0.3, action='cheer', mood='happy')]),
  dict(id='pat2', cast='pat2', track='pat2', autoGait=True, mood='shocked', lookAt='right', nearFade=NF, keys=[K(b['soon'] - 0.2, action='cheer', mood='happy')]),
  dict(id='cop', cast='cop', track='cop', autoGait=False, mood='angry', lookAt='left', nearFade=NF,
       keys=[K(0.0, action='aim', prop='pistol', mood='angry', lookAt='left'), K(b['shotB'] + 0.3, mood='shocked')]),
]
PUNCH = [CLUB0 + 0.25 + 0.42 * k for k in range(int((CLUB1 - CLUB0 - 0.6) / 0.42))]
chars.append(dict(id='f1', cast='f1', track='f1', autoGait=False, mood='angry', lookAt='right', nearFade=NF,
                  keys=[K(t, action='punch' if k % 2 == 0 else 'idle', mood='angry' if k % 2 == 0 else 'shocked') for k, t in enumerate(PUNCH)]))
chars.append(dict(id='f2', cast='f2', track='f2', autoGait=False, mood='angry', lookAt='left', nearFade=NF,
                  keys=[K(t, action='idle' if k % 2 == 0 else 'punch', mood='shocked' if k % 2 == 0 else 'angry') for k, t in enumerate(PUNCH)]))
CROWD = ['tee_white', 'flannel_red', 'tee_blue', 'tee_black', 'tee_grey', 'jacket_purple', 'vest_orange', 'tee_red']
for k in range(8):
    look = 'right' if k < 3 or k == 6 else 'left'
    chars.append(dict(id='c%d' % k, cast='c%d' % k, track='c%d' % k, autoGait=False, mood='neutral', lookAt=look, nearFade=NF,
                      keys=[K(0.0, action='idle', mood='neutral'), K(b['exist'] + 0.1 * k, mood='worried'),
                            K(CLUB0 + 0.08 * k, action='cheer', mood='happy'), K(b['rule'] + 0.05 * k, action='idle', mood='determined', lookAt='camera'),
                            K(b['talk'] + 0.7 + 0.06 * k, action='cheer', mood='happy', lookAt=look)]))
for k in range(12):
    chars.append(dict(id='m%d' % k, cast='m%d' % (k % 4), track='m%d' % k, autoGait=True, mood='determined', lookAt='camera', nearFade=NF,
                      keys=[K(b['project'] + 0.05 * k, mood='angry')]))

fx = [
  dict(type='tag', at=0.35, untilAt=b['exist'] - 0.2, of='tyler', text='HIS BEST FRIEND', bg='#ff7a5a'),
  dict(type='callout', at=b['fight1'] - 0.05, dur=1.0, x=0.5, y=0.17, text='FIGHT CLUB', sub='(1999)', size=84),
  dict(type='callout', at=b['exist'] - 0.35, dur=1.1, x=0.5, y=0.17, text="DOESN'T EXIST", size=74, edge='#ff5a4a'),
  dict(type='flicker', at=b['vanish'] - 0.25, dur=0.5),
  dict(type='speedlines', at=b['exist'] + 0.5, dur=1.0, x=0.5, y=0.5),
  dict(type='callout', at=b['sleep'] - 0.5, dur=1.1, x=0.5, y=0.17, text='INSOMNIA', size=80, edge='#9adfb0'),
  dict(type='callout', at=b['support'] - 0.05, dur=2.4, x=0.5, y=0.17, text='SUPPORT GROUPS', sub="FOR DISEASES HE DOESN'T HAVE", size=66),
  dict(type='tag', at=b['support'] + 0.6, untilAt=b['finally'] - 0.1, of='bob', text='BOB', bg='#9ad0ff'),
  dict(type='bubble', at=b['sleeps'], dur=1.0, of='narr', text='Zzz', size=58),
  dict(type='tag', at=b['marla'] + 0.25, untilAt=b['ruins'] + 0.3, of='marla', text='MARLA', bg='#ff9ad0'),
  dict(type='callout', at=b['faker'] - 0.1, dur=0.95, x=0.5, y=0.17, text='ANOTHER FAKER', size=66, edge='#ff5a4a'),
  dict(type='speedlines', at=b['ruins'] + 0.55, dur=1.3, x=0.5, y=0.5),
  dict(type='tag', at=b['meets'] - 0.05, untilAt=b['soap1'] + 0.5, of='tyler', text='TYLER DURDEN', bg='#ff7a5a'),
  dict(type='callout', at=b['soap1'] - 0.1, dur=1.2, x=0.5, y=0.17, text='SOAP SALESMAN', size=64, edge='#ff9ad0'),
  dict(type='speedlines', at=b['then'] - 0.45, dur=0.9, x=0.5, y=0.5),
  dict(type='flash', at=b['boom'] - 0.03, dur=0.35, amount=0.8),
  dict(type='blast', at=b['boom'], world=[24.0, 5.5, 28.5], r=1, only=['nobody'], shake=16, hidden=True),
  dict(type='bubble', at=b['hit'] - 0.05, dur=1.0, of='tyler', text='HIT ME.', size=54),
  dict(type='impactframe', at=b['hit'] + 1.1, dur=0.1),
  dict(type='blast', at=b['hit'] + 1.1, world=[12.4, -3.5, 1.5], r=1, only=['nobody'], shake=9, hidden=True),
  dict(type='impactframe', at=b['fight2'] + 0.3, dur=0.1),
  dict(type='blast', at=b['fight2'] + 0.3, world=[13.0, -3.6, 1.5], r=1, only=['nobody'], shake=9, hidden=True),
  dict(type='speedlines', at=b['soon'] + 0.1, dur=1.2, x=0.5, y=0.5),
  dict(type='callout', at=b['basement'] - 0.1, dur=0.95, x=0.5, y=0.17, text='FIGHT CLUB', sub='A BAR BASEMENT', size=78),
  dict(type='callout', at=b['rule'] - 0.05, dur=1.9, x=0.5, y=0.17, text='RULE #1', sub="YOU DON'T TALK ABOUT IT", size=84, edge='#ff5a4a'),
] + [dict(type='blast', at=t + 0.12, world=[-0.35, 0.45, -2.6], r=1, only=['nobody'], shake=5, hidden=True) for k, t in enumerate(PUNCH) if k % 3 == 0] + [
  dict(type='speedlines', at=b['move'] + 0.1, dur=1.0, x=0.5, y=0.5),
  dict(type='callout', at=b['soap2'] - 0.1, dur=2.0, x=0.5, y=0.17, text='SOAP', sub='FROM STOLEN LIPOSUCTION FAT', size=88, edge='#ff9ad0'),
  dict(type='callout', at=b['project'] - 0.05, dur=1.5, x=0.5, y=0.17, text='PROJECT MAYHEM', size=70, edge='#ff3a2a'),
  dict(type='sirenglow', at=b['then2'] + 1.6, until=b['shut'] + 0.2, amount=0.26),
  dict(type='flash', at=b['shotB'] - 0.02, dur=0.2, amount=0.55),
  dict(type='blast', at=b['shotB'], world=[72.2, -9.4, 1.2], r=1, only=['nobody'], shake=10, hidden=True),
  dict(type='tag', at=b['bob'] - 0.25, untilAt=b['shut'] - 0.5, of='bob', text='BOB', bg='#9ad0ff'),
  dict(type='speedlines', at=b['shut'] - 0.6, dur=1.3, x=0.5, y=0.5),
  dict(type='callout', at=b['truth'] - 0.05, dur=0.8, x=0.5, y=0.17, text='THE TRUTH', size=76),
  dict(type='flicker', at=b['glitch'], dur=0.7),
  dict(type='callout', at=b['heis'] - 0.05, dur=1.15, x=0.5, y=0.17, text='HE IS TYLER', size=84, edge='#ff3a2a'),
  dict(type='flash', at=b['bang'] - 0.02, dur=0.45, amount=1.0),
  dict(type='blast', at=b['bang'], world=[85.1, 9.1, 59.6], r=1, only=['nobody'], shake=12, hidden=True),
  dict(type='callout', at=b['gone'], dur=1.1, x=0.5, y=0.17, text="TYLER'S GONE", size=76),
] + [dict(type='blast', at=t, world=[86.0, 30.0, 60.0], r=1, only=['nobody'], shake=5, hidden=True) for t in BOMBS] + [
  dict(type='tag', at=b['holds'] + 0.1, untilAt=b['towers'] - 0.5, of='marla', text='MARLA', bg='#ff9ad0'),
  dict(type='callout', at=b['towers'] - 0.4, dur=1.9, x=0.5, y=0.17, text='CREDIT CARD TOWERS', sub='ERASING THE DEBT RECORDS', size=56, edge='#ff8a3a'),
  dict(type='darken', keys=[dict(at=END - 0.5, a=0.0), dict(at=END - 0.05, a=1.0)]),
]
tint = [dict(at=0.0, col='#ffb060', a=0.12), dict(at=HOOK1, col='#9adfb0', a=0.14), dict(at=b['so'] + 0.25, col='#ffc890', a=0.07),
        dict(at=b['ruins'] + 0.6, col='#ffd9a8', a=0.06), dict(at=b['then'] - 0.2, col='#ff8a40', a=0.12), dict(at=b['bar1'] - 0.3, col='#ff9a4a', a=0.14),
        dict(at=CLUB0, col='#ffb060', a=0.12), dict(at=CLUB1, col='#ff9ac0', a=0.1), dict(at=b['then2'] - 0.2, col='#1c2a4a', a=0.3),
        dict(at=b['police'] - 0.3, col='#30306a', a=0.28), dict(at=b['shut'] - 0.6, col='#1c2848', a=0.3), dict(at=b['bomb0'], col='#ff8a50', a=0.16)]

sfx = [dict(type='hum', at=0.0, dur=4.6, gain=0.3), dict(type='sting', at=b['fight1'], gain=0.45), dict(type='glitch', at=b['vanish'] - 0.2, dur=0.6, gain=0.6),
       dict(type='whoosh', at=b['exist'] + 0.45, dur=1.0, gain=0.8), dict(type='hum', at=b['lonely'], dur=2.3, gain=0.25), dict(type='ting', at=b['sleep'], gain=0.3),
       dict(type='whoosh', at=b['so'] + 0.2, dur=0.8, gain=0.7), dict(type='pop', at=b['support'], gain=0.4), dict(type='pop', at=b['sleeps'], gain=0.35),
       dict(type='creak', at=b['marla'] - 0.35, dur=0.7, gain=0.5), dict(type='sting', at=b['faker'], gain=0.4), dict(type='whoosh', at=b['ruins'] + 0.45, dur=1.4, gain=0.9),
       dict(type='wind', at=b['ruins'] + 0.6, dur=1.2, gain=0.5), dict(type='engine', at=b['ruins'] + 1.6, dur=3.4, gain=0.3), dict(type='pop', at=b['tyler1'], gain=0.35),
       dict(type='pop', at=b['soap1'], gain=0.4), dict(type='whoosh', at=b['then'] - 0.5, dur=1.0, gain=0.9), dict(type='boom', at=b['boom'], gain=0.9),
       dict(type='crash', at=b['boom'] + 0.04, gain=0.6), dict(type='crackle', at=b['boom'] + 0.4, dur=6.0, gain=0.35), dict(type='beep', at=b['calls'], gain=0.25),
       dict(type='pop', at=b['hit'], gain=0.35), dict(type='punch', at=b['hit'] + 1.1, gain=0.85), dict(type='punch', at=b['fight2'] + 0.3, gain=0.85),
       dict(type='whoosh', at=b['soon'] + 0.1, dur=1.2, gain=0.8), dict(type='hum', at=b['basement'], dur=3.0, gain=0.25), dict(type='sting', at=b['rule'], gain=0.45)] + \
      [dict(type='punch', at=t + 0.12, gain=0.45) for t in PUNCH] + \
      [dict(type='whoosh', at=b['move'] + 0.1, dur=1.0, gain=0.8), dict(type='creak', at=b['crumbling'], dur=1.0, gain=0.45), dict(type='pop', at=b['soap2'], gain=0.4),
       dict(type='march', at=b['then2'] + 0.2, dur=2.8, gain=0.5), dict(type='sting', at=b['project'], gain=0.5), dict(type='siren', at=b['police'] - 0.4, dur=2.6, gain=0.35),
       dict(type='boom', at=b['shotB'], dur=0.6, gain=0.6), dict(type='slam', at=b['shotB'] + 0.01, gain=0.35), dict(type='whoosh', at=b['shut'] - 0.6, dur=1.2, gain=0.8),
       dict(type='hum', at=b['discovers'], dur=2.6, gain=0.3), dict(type='sting', at=b['truth'], gain=0.4), dict(type='glitch', at=b['glitch'], dur=0.7, gain=0.7),
       dict(type='boom', at=b['bang'], dur=0.8, gain=0.7), dict(type='slam', at=b['bang'] + 0.01, gain=0.45), dict(type='ting', at=b['gone'] + 0.1, gain=0.3)] + \
      [dict(type='boom', at=t, gain=0.75 - 0.06 * k) for k, t in enumerate(BOMBS)] + \
      [dict(type='crash', at=b['crash'] + 0.3, dur=1.6, gain=0.7), dict(type='crash', at=b['crash'] + 1.0, dur=1.6, gain=0.55), dict(type='gust', at=b['crash'] + 0.5, dur=3.2, gain=0.5),
       dict(type='pop', at=b['would'], gain=0.3)]

S_ = dict(title='Movies in a Minute: Fight Club', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.04) saturate(1.12) contrast(1.06)', thumbnail_cue=b['heis'] + 0.35,
  music=dict(level_db=-24, segments=[dict(style='dread', bpm=80, fadeIn=0.6, fadeOut=0.4, **{'from': 0.0, 'to': b['so']}),
                                     dict(style='chill', bpm=96, fadeIn=0.3, fadeOut=0.3, **{'from': b['so'], 'to': b['then'] - 0.3}),
                                     dict(style='chase', bpm=132, fadeIn=0.2, fadeOut=0.4, **{'from': b['then'] - 0.3, 'to': b['police'] - 0.4}),
                                     dict(style='dread', bpm=80, fadeIn=0.3, fadeOut=0.4, **{'from': b['police'] - 0.4, 'to': b['bombs']}),
                                     dict(style='reveal', bpm=96, fadeIn=0.3, fadeOut=1.5, **{'from': b['bombs'], 'to': END})]),
  cast=dict(narr=dict(costume='office_shirt', mood='neutral', hair='#4a3022'),
            narr_b=dict(costume='office_shirt', mood='neutral', hair='#4a3022', bandage=True),
            tyler=dict(costume='leather_red', mood='smug', hair='#c99a3a', shades='#6a2a1a'),
            bob=dict(costume='tee_grey', mood='sad', hair='#3a2a20', facial='beard'),
            marla=dict(costume='coat_black', mood='smug', hair='#1d1416', hairLong='#1d1416'),
            sg1=dict(costume='tee_blue', hair='#6a4a2a'), sg2=dict(costume='flannel_red', hair='#a07a4a'),
            pat1=dict(costume='tee_white', hair='#2a2420'), pat2=dict(costume='vest_orange', hair='#7a5a3a'),
            f1=dict(costume='tee_white', hair='#2a2420'), f2=dict(costume='tee_black', hair='#8a5a2a'),
            cop=dict(costume='police', hat='police_cap'),
            **{'c%d' % k: dict(costume=CROWD[k], hair=['#2a2420', '#6a4a2a', '#1d1a18', '#a07a4a', '#3a2a20', '#d8b45a', '#5a3a26', '#2a2420'][k]) for k in range(8)},
            **{'m%d' % k: dict(costume='tee_black', mood='determined') for k in range(4)}),
  scenes=[dict(cue='His', bgseq=dict(dir='oneshot_alex'), transition='cut', characters=chars, fx=fx, sfx=sfx, charTint=tint)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
