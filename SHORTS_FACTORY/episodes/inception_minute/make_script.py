"""MOVIES IN A MINUTE: INCEPTION (2010). ONE continuous camera move (no cuts) through a bright cel-shaded cartoon world:
a pastel dream street, then down through three dream levels and limbo, up to a plane and home to a spinning top. The 3D
sets are rendered by tools/inception_oneshot.py into oneshot/ (frames + camera.json with the camera and every 2D actor's
track). Every time below comes from a cue word in work/words.json (same resolver as the Blender script). Plot facts:
sources.txt. Original characters, set designs and music; no film footage, audio, logos, character designs or likenesses."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
src = open(os.path.join(HERE, '..', '..', 'tools', 'inception_oneshot.py')).read()
CUES = eval(src[src.index('CUES = ') + 7:src.index('B = {}')])
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
b['fold'] = b['dreams'] - 0.1; b['drop1'] = b['three'] + 0.1; b['bang'] = b['shoots'] + 0.12; b['kick'] = b['back'] - 0.05; b['up'] = b['wake'] - 0.25
SAFE0 = b['dom'] - 0.25; ROOF0 = b['client'] - 0.15; TERR0 = b['robert'] - 0.45; WORK0 = b['team'] - 0.3; HOTEL0 = b['hotel'] - 0.2
HOUSE0 = b['dead'] - 0.75; COURT0 = b['mal2'] - 0.25; LROOF0 = b['ariadne2'] - 0.3; VAULT0 = b['father'] - 0.45; CASTLE0 = b['saito2'] - 0.3
PLANE0 = b['up'] + 0.3; HOME0 = b['home2'] - 0.45
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d
NF = [0.45, 1.1]

chars = [
  dict(id='cobb', cast='cobb', track='cobb', autoGait=True, mood='smug', lookAt='camera', nearFade=NF,
       keys=[K(0.0, action='walk', mood='smug', lookAt='camera'), K(b['time'] - 0.2, action='idle', mood='determined'),
             K(b['leave'], action='hold', prop='idea', mood='smug', lookAt='camera'),
             K(SAFE0, action='hold', prop='idea', mood='determined', lookAt='up'), K(b['ideas'], mood='smug', lookAt='camera'),
             K(ROOF0, action='idle', prop='', mood='worried', lookAt='left'), K(b['home1'], mood='sad'), K(b['kids'], mood='happy', lookAt='left'),
             K(b['plants'], mood='determined', lookAt='camera'),
             K(WORK0, action='talk', mood='determined', lookAt='right'), K(b['architect'], action='idle', lookAt='right'), K(b['three'], action='sit', mood='neutral', lookAt='camera'),
             K(HOUSE0, action='idle', mood='sad', lookAt='right'), K(b['planted1'], mood='worried'), K(b['killed'], mood='sad', lookAt='down'),
             K(LROOF0, action='idle', mood='determined', lookAt='right'), K(b['dive'], action='point'), K(b['back'] + 0.2, action='idle', mood='worried', lookAt='down'),
             K(CASTLE0, action='idle', mood='worried', lookAt='right'), K(b['old'], mood='sad'),
             K(PLANE0, action='sit', mood='shocked', lookAt='camera'), K(b['saito3'], mood='neutral', lookAt='right'), K(b['call'] + 0.3, mood='happy', lookAt='camera'),
             K(HOME0, action='idle', prop='top', mood='happy', lookAt='camera'), K(b['spins'], action='present', prop='', mood='neutral', lookAt='down'),
             K(b['wait'] - 0.1, action='walk', mood='happy', lookAt='up')]),
  dict(id='saito', cast='saito', track='saito', autoGait=False, mood='smug', lookAt='right', nearFade=NF,
       keys=[K(ROOF0, action='talk', mood='smug', lookAt='right'), K(b['home1'], action='present'), K(b['plants'], action='point', mood='determined'),
             K(CASTLE0, action='sit', mood='sad', lookAt='left'), K(b['finds'], mood='shocked'), K(b['old'], mood='happy'),
             K(PLANE0, action='sit', mood='neutral', lookAt='left'), K(b['saito3'], action='hold', prop='phone', mood='smug', lookAt='camera'),
             K(b['home2'] - 0.4, action='sit', prop='', mood='happy')]),
  dict(id='fischer', cast='fischer', track='fischer', autoGait=False, rollTrack=True, mood='neutral', lookAt='camera', nearFade=NF,
       keys=[K(TERR0, action='crossed', mood='neutral', lookAt='camera'), K(b['break'], mood='shocked', lookAt='up'), K(b['dying1'], action='idle', mood='sad', lookAt='down'),
             K(COURT0, action='idle', mood='scared', lookAt='left'), K(b['bang'], action='fall', mood='shocked'),
             K(LROOF0, action='idle', mood='scared', lookAt='left'), K(b['kick'], action='flail', mood='shocked'),
             K(VAULT0, action='idle', mood='sad', lookAt='right'), K(b['live'], mood='happy'), K(b['planted2'], mood='determined', lookAt='camera')]),
  dict(id='mal', cast='mal', track='mal', autoGait=False, mood='neutral', lookAt='left', nearFade=NF,
       keys=[K(HOUSE0, action='idle', mood='sad', lookAt='left'), K(b['mal1'], mood='smug', lookAt='camera'), K(b['world'], mood='scared', lookAt='down'),
             K(COURT0, action='aim', prop='pistol', mood='angry', lookAt='right')]),
  dict(id='ariadne', cast='ariadne', track='ariadne', autoGait=False, mood='happy', lookAt='camera', nearFade=NF,
       keys=[K(WORK0, action='idle', mood='happy', lookAt='left'), K(b['ariadne1'], action='wave', lookAt='camera'), K(b['forger'], action='idle', lookAt='right'),
             K(b['three'], action='sit', mood='neutral', lookAt='camera'),
             K(LROOF0, action='idle', mood='determined', lookAt='right'), K(b['kick'] - 0.15, action='punch', mood='determined'), K(b['kick'] + 0.4, action='idle', lookAt='down')]),
  dict(id='eames', cast='eames', track='eames', autoGait=False, mood='smug', lookAt='left', nearFade=NF,
       keys=[K(WORK0, action='idle', mood='smug', lookAt='left'), K(b['forger'], action='present', lookAt='camera'), K(b['chemist'], action='idle', lookAt='right'),
             K(b['three'], action='sit', mood='neutral', lookAt='camera')]),
  dict(id='yusuf', cast='yusuf', track='yusuf', autoGait=False, mood='happy', lookAt='left', nearFade=NF,
       keys=[K(WORK0, action='idle', mood='happy', lookAt='left'), K(b['chemist'], action='present', lookAt='camera'), K(b['three'], action='sit', mood='neutral', lookAt='camera')]),
  dict(id='arthur', cast='arthur', track='arthur', autoGait=False, mood='neutral', lookAt='right', nearFade=NF,
       keys=[K(WORK0, action='crossed', mood='neutral', lookAt='right'), K(b['three'], action='sit', mood='neutral', lookAt='camera'),
             K(HOTEL0, action='float', mood='determined', lookAt='camera')]),
  dict(id='father', cast='father', track='father', autoGait=False, mood='sad', lookAt='left', nearFade=NF,
       keys=[K(VAULT0, action='sit', mood='sad', lookAt='left'), K(b['live'], action='talk', mood='happy'), K(b['life'] + 0.4, action='sit', mood='happy')]),
  dict(id='mark', cast='mark', track='mark', autoGait=False, mood='neutral', lookAt='down', nearFade=NF, keys=[K(SAFE0, action='sit', mood='neutral', lookAt='down')]),
  dict(id='walker1', cast='walker1', track='walker1', autoGait=True, mood='neutral', lookAt='right', nearFade=NF, keys=[K(b['steal'], mood='shocked', lookAt='left')]),
  dict(id='walker2', cast='walker2', track='walker2', autoGait=True, mood='neutral', lookAt='left', nearFade=NF, keys=[K(b['steal'], mood='shocked', lookAt='up')]),
  dict(id='kid1', cast='kid1', track='kid1', autoGait=False, mood='happy', lookAt='camera', nearFade=NF, keys=[K(HOME0, action='cheer', mood='happy')]),
  dict(id='kid2', cast='kid2', track='kid2', autoGait=False, mood='happy', lookAt='camera', nearFade=NF, keys=[K(HOME0, action='wave', mood='happy')]),
]

GOLD = '#ffc23a'
fx = [
  dict(type='callout', at=0.25, dur=1.5, x=0.5, y=0.17, text='INCEPTION', sub='(2010)', size=84, edge='#7ac8ff'),
  dict(type='speedlines', at=b['fold'], dur=1.4, x=0.5, y=0.45),
  dict(type='tag', at=b['dom'], untilAt=b['ideas'] + 0.6, of='cobb', text='DOM COBB', bg='#8ab4ff'),
  dict(type='callout', at=b['ideas'] - 0.1, dur=1.8, x=0.5, y=0.17, text='THE THIEF', sub='STEALS IDEAS IN DREAMS', size=80, edge='#ffe066'),
  dict(type='speedlines', at=ROOF0 + 0.1, dur=0.8, x=0.5, y=0.5),
  dict(type='tag', at=b['saito1'] - 0.1, untilAt=b['home1'] + 0.2, of='saito', text='SAITO', bg='#ffd8a8'),
  dict(type='callout', at=b['home1'] - 0.05, dur=1.2, x=0.5, y=0.17, text='A WAY HOME', sub='TO HIS KIDS', size=80, edge='#7aff9a'),
  dict(type='callout', at=b['plants'] - 0.05, dur=1.5, x=0.5, y=0.17, text='INCEPTION', sub='PLANT AN IDEA', size=84, edge=GOLD),
  dict(type='tag', at=b['robert'], untilAt=b['company'] + 0.4, of='fischer', text='ROBERT FISCHER', bg='#d8b0ff'),
  dict(type='callout', at=b['break'] - 0.05, dur=1.9, x=0.5, y=0.17, text='BREAK UP', sub="HIS DYING FATHER'S COMPANY", size=80, edge='#c88aff'),
  dict(type='impactframe', at=b['break'] + 0.05, dur=0.06),
  dict(type='tag', at=b['ariadne1'] - 0.3, untilAt=b['forger'] - 0.1, of='ariadne', text='ARIADNE  ·  ARCHITECT', bg='#ffd27a'),
  dict(type='tag', at=b['forger'] - 0.1, untilAt=b['chemist'] - 0.1, of='eames', text='FORGER', bg='#ffa08a'),
  dict(type='tag', at=b['chemist'] - 0.1, untilAt=b['three'], of='yusuf', text='CHEMIST', bg='#8ae8d8'),
  dict(type='flash', at=b['drop1'] - 0.02, dur=0.5, amount=0.7),
  dict(type='speedlines', at=b['drop1'], dur=0.8, x=0.5, y=0.5),
  dict(type='callout', at=b['van'] - 0.3, dur=0.95, x=0.5, y=0.17, text='LEVEL 1', sub='A VAN CHASE', size=80, edge='#7ac8ff'),
  dict(type='callout', at=b['hotel'] - 0.1, dur=0.85, x=0.5, y=0.17, text='LEVEL 2', sub='A HOTEL', size=80, edge='#ff9a6a'),
  dict(type='callout', at=b['snowy'] - 0.05, dur=1.5, x=0.5, y=0.17, text='LEVEL 3', sub='A SNOWY FORTRESS', size=80, edge='#8ae8d0'),
  dict(type='speedlines', at=b['hotel'] - 0.2, dur=0.5, x=0.5, y=0.5), dict(type='speedlines', at=b['snowy'] - 0.2, dur=0.5, x=0.5, y=0.5),
  dict(type='callout', at=b['sedative'] - 0.05, dur=1.6, x=0.5, y=0.17, text='DIE DOWN THERE?', sub='LOST IN LIMBO', size=74, edge='#ff8a7a'),
  dict(type='speedlines', at=b['dying2'] + 0.2, dur=1.4, x=0.5, y=0.5),
  dict(type='callout', at=b['limbo1'] - 0.05, dur=1.3, x=0.5, y=0.17, text='LIMBO', size=96, edge='#ffb86a'),
  dict(type='tag', at=b['mal1'] - 0.4, untilAt=b['planted1'], of='mal', text='MAL', bg='#f6e7c8'),
  dict(type='callout', at=b['planted1'] - 0.05, dur=2.4, x=0.5, y=0.17, text='HIS FIRST INCEPTION', sub="HER WORLD ISN'T REAL", size=68, edge='#ff8a9a'),
  dict(type='puff', at=b['killed'] + 0.45, world=[100.2, -3.5, -199.0], r=1.0),
  dict(type='speedlines', at=b['mal2'] - 0.4, dur=0.6, x=0.5, y=0.5),
  dict(type='impactframe', at=b['bang'], dur=0.08),
  dict(type='blast', at=b['bang'], world=[103.6, 5.6, -128.7], r=1, only=['nobody'], shake=8, hidden=True),
  dict(type='speedlines', at=LROOF0 + 0.05, dur=0.7, x=0.5, y=0.5),
  dict(type='callout', at=b['back'] - 0.05, dur=1.0, x=0.5, y=0.17, text='THE KICK', size=88, edge=GOLD),
  dict(type='speedlines', at=VAULT0 + 0.05, dur=0.6, x=0.5, y=0.5),
  dict(type='tag', at=b['father'] - 0.1, untilAt=b['live'] - 0.1, of='father', text='HIS FATHER', bg='#cfe0ff'),
  dict(type='bubble', at=b['live'] - 0.05, dur=1.4, of='father', text='\u2665', size=70),
  dict(type='callout', at=b['idea'] - 0.05, dur=1.4, x=0.5, y=0.17, text='IDEA PLANTED', size=84, edge='#a8ff7a'),
  dict(type='speedlines', at=CASTLE0 + 0.05, dur=0.7, x=0.5, y=0.5),
  dict(type='callout', at=b['old'] - 0.1, dur=1.0, x=0.5, y=0.17, text='OLD SAITO', size=80, edge='#ffb86a'),
  dict(type='flash', at=b['up'] - 0.02, dur=0.7, amount=1.0),
  dict(type='speedlines', at=b['up'], dur=0.6, x=0.5, y=0.5),
  dict(type='callout', at=b['call'] - 0.1, dur=1.1, x=0.5, y=0.17, text='ONE CALL', size=84, edge='#7aff9a'),
  dict(type='speedlines', at=b['home2'] - 0.3, dur=0.6, x=0.5, y=0.5),
  dict(type='callout', at=b['fall'] - 0.12, dur=END - b['fall'], x=0.5, y=0.17, text='DID IT FALL?', size=92, edge='#ff7a6b'),
  dict(type='darken', keys=[dict(at=END - 0.45, a=0.0), dict(at=END - 0.05, a=1.0)]),
]
fx = [f for f in fx if f]
tint = [dict(at=0.0, col='#ffe0f0', a=0.04), dict(at=b['drop1'] + 0.3, col='#9ad0ff', a=0.08), dict(at=HOTEL0, col='#ffb070', a=0.08),
        dict(at=b['snowy'], col='#e0fff6', a=0.05), dict(at=b['dying2'] + 0.5, col='#ffb070', a=0.1), dict(at=COURT0, col='#e0fff6', a=0.05),
        dict(at=LROOF0, col='#ffb070', a=0.1), dict(at=VAULT0, col='#e0fff6', a=0.05), dict(at=CASTLE0, col='#ffb070', a=0.1),
        dict(at=PLANE0, col='#ffffff', a=0.02), dict(at=HOME0, col='#ffe8c8', a=0.05)]

sfx = [dict(type='sting', at=0.3, gain=0.4), dict(type='whoosh', at=b['fold'], dur=1.6, gain=0.7), dict(type='rumble', at=b['fold'] + 0.2, dur=2.0, gain=0.4),
       dict(type='ting', at=b['leave'], gain=0.35), dict(type='whoosh', at=SAFE0, dur=0.8, gain=0.7), dict(type='creak', at=b['dom'] + 0.2, dur=0.8, gain=0.35),
       dict(type='ting', at=b['ideas'], gain=0.3), dict(type='whoosh', at=ROOF0, dur=0.9, gain=0.8), dict(type='engine', at=ROOF0 + 0.3, dur=4.2, gain=0.25),
       dict(type='pop', at=b['home1'], gain=0.3), dict(type='sting', at=b['plants'], gain=0.4), dict(type='whoosh', at=TERR0, dur=0.8, gain=0.7),
       dict(type='crash', at=b['break'] + 0.05, gain=0.55), dict(type='rumble', at=b['break'], dur=1.4, gain=0.45), dict(type='whoosh', at=WORK0, dur=0.9, gain=0.7),
       dict(type='pop', at=b['ariadne1'], gain=0.25), dict(type='pop', at=b['forger'], gain=0.25), dict(type='pop', at=b['chemist'], gain=0.25),
       dict(type='whoosh', at=b['drop1'], dur=0.9, gain=1.0), dict(type='engine', at=b['drop1'] + 0.5, dur=2.2, gain=0.45),
       dict(type='whoosh', at=b['hotel'] - 0.2, dur=0.6, gain=0.8), dict(type='hum', at=b['hotel'], dur=0.9, gain=0.3), dict(type='whoosh', at=b['snowy'] - 0.2, dur=0.6, gain=0.8),
       dict(type='wind', at=b['snowy'], dur=2.6, gain=0.4), dict(type='sting', at=b['sedative'], gain=0.35), dict(type='whoosh', at=b['dying2'] + 0.2, dur=1.6, gain=0.9),
       dict(type='hum', at=b['limbo1'] - 0.3, dur=7.0, gain=0.3), dict(type='wind', at=b['limbo1'], dur=3.0, gain=0.25), dict(type='ting', at=b['planted1'], gain=0.35),
       dict(type='sting', at=b['killed'], gain=0.35), dict(type='whoosh', at=b['mal2'] - 0.4, dur=0.7, gain=0.9), dict(type='punch', at=b['bang'], gain=0.6),
       dict(type='slam', at=b['bang'] + 0.4, gain=0.4), dict(type='whoosh', at=LROOF0, dur=0.8, gain=0.9), dict(type='whoosh', at=b['kick'], dur=1.0, gain=0.8),
       dict(type='whoosh', at=VAULT0, dur=0.7, gain=0.8), dict(type='beep', at=b['father'], gain=0.2), dict(type='beep', at=b['father'] + 1.0, gain=0.2),
       dict(type='charge', at=b['idea'] - 0.2, dur=0.9, gain=0.45), dict(type='ting', at=b['planted2'], gain=0.4),
       dict(type='whoosh', at=CASTLE0, dur=0.8, gain=0.9), dict(type='hum', at=b['finds'], dur=2.0, gain=0.25),
       dict(type='whoosh', at=b['up'], dur=0.9, gain=1.0), dict(type='boom', at=b['up'] + 0.05, gain=0.6), dict(type='engine', at=PLANE0, dur=3.0, gain=0.3),
       dict(type='beep', at=b['call'], gain=0.3), dict(type='whoosh', at=b['home2'] - 0.3, dur=0.8, gain=0.8),
       dict(type='spin', at=b['spins'] + 0.1, dur=END - b['spins'] - 0.6, gain=0.35), dict(type='sting', at=b['fall'], gain=0.45)]

S_ = dict(title='Movies in a Minute: Inception', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.02) saturate(1.08) contrast(1.04)', thumbnail_cue=b['break'] + 0.5,
  music=dict(level_db=-24, segments=[dict(style='chill', bpm=100, fadeIn=0.6, fadeOut=0.4, **{'from': 0.0, 'to': b['drop1']}),
                                     dict(style='chase', bpm=128, fadeIn=0.2, fadeOut=0.4, **{'from': b['drop1'], 'to': b['sedative']}),
                                     dict(style='dread', bpm=76, fadeIn=0.4, fadeOut=0.3, **{'from': b['sedative'], 'to': b['mal2'] - 0.3}),
                                     dict(style='chase', bpm=132, fadeIn=0.2, fadeOut=0.4, **{'from': b['mal2'] - 0.3, 'to': b['father'] - 0.3}),
                                     dict(style='reveal', bpm=90, fadeIn=0.3, fadeOut=0.4, **{'from': b['father'] - 0.3, 'to': b['up']}),
                                     dict(style='chill', bpm=96, fadeIn=0.3, fadeOut=1.5, **{'from': b['up'], 'to': END})]),
  cast=dict(cobb=dict(costume='suit_navy', mood='smug', hair='#4a3426'),
            saito=dict(costume='suit_cream', mood='smug', hair='#1f1a18'),
            fischer=dict(costume='suit_plum', mood='neutral', hair='#c89a5a'),
            mal=dict(costume='coat_cream', mood='neutral', hair='#3a2620', hairLong='#3a2620'),
            ariadne=dict(costume='jacket_mustard', mood='happy', hair='#6a3a24', hairLong='#6a3a24'),
            eames=dict(costume='shirt_coral', mood='smug', hair='#8a6a3a'),
            yusuf=dict(costume='vest_teal', mood='happy', hair='#1a1414'),
            arthur=dict(costume='suit_dark', mood='neutral', hair='#241c18'),
            father=dict(costume='pyjama_blue', mood='sad', hair='#e8e4dc'),
            mark=dict(costume='office_shirt', hair='#8a5a3a'),
            walker1=dict(costume='tee_red', hair='#2a2420'), walker2=dict(costume='jacket_purple', hair='#d8b45a'),
            kid1=dict(costume='tee_blue', hair='#e0b060'), kid2=dict(costume='tee_red', hair='#6a4a2a', hairLong='#6a4a2a')),
  scenes=[dict(cue='He', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx, charTint=tint)])
json.dump(S_, open(P, 'w'), indent=1, ensure_ascii=False); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
