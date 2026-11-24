"""MOVIES IN A MINUTE: THE MATRIX (1999). ONE continuous camera move (no cuts) through a green-tinted night city and the
dark real world under it. The 3D sets are rendered by tools/matrix_oneshot.py into oneshot/ (frames + camera.json with
the camera and every 2D actor's track). Every time below comes from a cue word in work/words.json (same resolver as
the Blender script). Plot facts: sources.txt. Original characters, set designs and music; no film footage, audio,
logos, character designs or likenesses."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
src = open(os.path.join(HERE, '..', '..', 'tools', 'matrix_oneshot.py')).read()
CUES = eval(src[src.index('CUES = ') + 7:src.index('B = {}')])
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
b['dive'] = b['red2'] + 0.12; b['shot'] = b['shoots'] + 0.1; b['freeze'] = b['stops'] + 0.05; b['dash'] = b['destroys'] + 0.02; b['burst'] = b['inside2'] + 0.05
OFFICE0 = b['find'] + 0.6; APT0 = b['day'] + 0.7; ROOM0 = b['neo1'] + 0.8; POD0 = b['wakes'] - 0.35; SHIP0 = b['ship'] - 0.9
KITCH0 = b['oracle'] - 0.75; REST0 = b['then'] - 0.05; CAPT0 = b['captured'] - 0.75; LOBBY0 = b['captured'] + 0.6; HALL0 = b['save'] + 0.3
SHOTS_L = [b['storm'] + 0.15 + 0.22 * k for k in range(8)]; SHOTS_H = [b['shot'] + 0.12 * k for k in range(4)]
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d
NF = [0.45, 1.1]

chars = [
  dict(id='neo', cast='neo', track='neo', autoGait=True, rollTrack=True, mood='neutral', lookAt='camera', nearFade=NF,
       keys=[K(0.0, action='idle', mood='neutral', lookAt='camera'), K(b['computer'], mood='shocked'), K(b['chose'], mood='determined', lookAt='right'),
             K(OFFICE0, action='sit', mood='sad', lookAt='camera'), K(b['day'], mood='neutral', lookAt='down'),
             K(APT0, action='sit', mood='determined', lookAt='left'), K(b['neo1'], mood='smug', lookAt='camera'), K(b['neo1'] + 0.5, lookAt='left'),
             K(ROOM0, action='sit', mood='worried', lookAt='left'), K(b['blue'], mood='neutral'), K(b['red1'], mood='determined'),
             K(b['takes'], action='hold', prop='pill_red', mood='determined', lookAt='camera'), K(b['red2'] + 0.05, action='idle', prop='', mood='shocked'),
             K(POD0, action='idle', mood='shocked', lookAt='camera'), K(b['countless'], mood='scared', lookAt='left'), K(b['energy'], mood='scared', lookAt='camera'),
             K(SHIP0, action='sit', mood='neutral', lookAt='camera'), K(b['kung'] + 0.1, mood='shocked'), K(b['brain'], mood='happy'),
             K(b['morpheus3'], mood='worried', lookAt='right'), K(b['one'], mood='shocked', lookAt='camera'),
             K(KITCH0, action='idle', mood='worried', lookAt='left'), K(b['isnt'], mood='sad', lookAt='camera'),
             K(LOBBY0, action='aim', prop='pistol', mood='determined', lookAt='right'),
             K(HALL0, action='idle', prop='', mood='determined', lookAt='left'), K(b['shot'], action='fall', mood='shocked'),
             K(b['wakes2'], action='idle', mood='determined', lookAt='left'), K(b['sees'], mood='smug'), K(b['stops'], action='present', mood='determined'),
             K(b['dash'], action='run', mood='angry'), K(b['burst'] + 0.1, action='idle', mood='smug', lookAt='camera'),
             K(b['would'], action='present', prop='pills', mood='smug', lookAt='camera')]),
  dict(id='mentor', cast='mentor', track='mentor', autoGait=True, mood='smug', lookAt='right', nearFade=NF,
       keys=[K(ROOM0, action='sit', mood='smug', lookAt='right'), K(b['pills'] - 0.1, action='present', prop='pills', mood='determined'),
             K(b['takes'] + 0.1, action='sit', prop='', mood='smug'), K(SHIP0, action='idle', mood='smug', lookAt='left'), K(b['morpheus3'], action='talk', mood='happy'),
             K(b['one'], action='idle', mood='determined'), K(CAPT0, action='idle', mood='angry', lookAt='left')]),
  dict(id='trinity', cast='trinity', track='trinity', autoGait=True, mood='neutral', lookAt='right', nearFade=NF,
       keys=[K(SHIP0, action='idle', mood='neutral', lookAt='right'), K(b['one'], mood='happy'), K(LOBBY0, action='aim', prop='pistol', mood='determined', lookAt='right')]),
  dict(id='oracle', cast='oracle', track='oracle', autoGait=False, mood='happy', lookAt='right', nearFade=NF,
       keys=[K(KITCH0, action='idle', mood='happy', lookAt='right'), K(b['oracle'], action='talk'), K(b['isnt'], action='idle', mood='smug')]),
  dict(id='cypher', cast='cypher', track='cypher', autoGait=False, mood='neutral', lookAt='left', nearFade=NF,
       keys=[K(SHIP0, action='idle', mood='neutral', lookAt='left'), K(REST0, action='sit', mood='smug', lookAt='right'), K(b['comfortable'], mood='happy')]),
  dict(id='smith', cast='smith', track='smith', autoGait=True, mood='smug', lookAt='left', nearFade=NF,
       keys=[K(REST0, action='sit', mood='smug', lookAt='left'), K(b['agents'], action='talk'), K(b['inside1'], action='sit'),
             K(CAPT0, action='idle', mood='angry', lookAt='left'), K(HALL0, action='aim', prop='pistol', mood='angry', lookAt='right'),
             K(b['destroys'], mood='shocked'), K(b['smith2'], mood='scared')]),
  dict(id='agent2', cast='agent2', track='agent2', autoGait=True, mood='angry', lookAt='right', nearFade=NF, keys=[K(CAPT0, action='idle', mood='angry', lookAt='right')]),
  dict(id='guard1', cast='guard1', track='guard1', autoGait=False, mood='neutral', lookAt='right', nearFade=NF,
       keys=[K(LOBBY0, action='idle', mood='neutral'), K(b['storm'] + 0.2, action='flail', mood='scared')]),
  dict(id='guard2', cast='guard2', track='guard2', autoGait=False, mood='neutral', lookAt='left', nearFade=NF,
       keys=[K(LOBBY0, action='idle', mood='neutral'), K(b['storm'] + 0.3, action='flail', mood='scared')]),
  dict(id='cow1', cast='cow1', track='cow1', autoGait=False, mood='sad', lookAt='camera', nearFade=NF, keys=[K(OFFICE0, action='sit', mood='sad')]),
  dict(id='cow2', cast='cow2', track='cow2', autoGait=False, mood='neutral', lookAt='left', nearFade=NF, keys=[K(OFFICE0, action='sit', mood='neutral')]),
  dict(id='walker1', cast='walker1', track='walker1', autoGait=True, mood='neutral', lookAt='right', nearFade=NF, keys=[K(b['computer'], mood='shocked')]),
  dict(id='walker2', cast='walker2', track='walker2', autoGait=True, mood='neutral', lookAt='left', nearFade=NF, keys=[K(b['computer'], mood='shocked')]),
]

fx = [
  dict(type='rain', keys=[dict(at=0.0, a=0.55), dict(at=b['morpheus1'], a=0.55), dict(at=b['morpheus1'] + 0.3, a=0.0), dict(at=b['captured'] - 0.6, a=0.0),
                          dict(at=b['captured'] - 0.3, a=0.5), dict(at=b['save'] + 0.6, a=0.5), dict(at=b['save'] + 1.0, a=0.0)]),
  dict(type='coderain', keys=[dict(at=b['computer'] - 0.05, a=0.0), dict(at=b['program'] + 0.15, a=0.85), dict(at=b['chose'] - 0.35, a=0.85), dict(at=b['chose'], a=0.0),
                              dict(at=b['sees'] - 0.1, a=0.0), dict(at=b['sees'] + 0.4, a=0.4), dict(at=b['burst'], a=0.4), dict(at=b['burst'] + 0.3, a=0.75), dict(at=END, a=0.6)]),
  dict(type='callout', at=0.25, dur=1.4, x=0.5, y=0.17, text='THE MATRIX', sub='(1999)', size=84, edge='#5aff7a'),
  dict(type='flicker', at=b['computer'] - 0.1, dur=0.4),
  dict(type='flicker', at=b['chose'] - 0.4, dur=0.4),
  dict(type='speedlines', at=b['find'] + 0.05, dur=0.9, x=0.5, y=0.5),
  dict(type='tag', at=b['thomas'], untilAt=b['day'] + 0.5, of='neo', text='THOMAS ANDERSON', bg='#9adfb0'),
  dict(type='callout', at=b['code'] - 0.1, dur=1.2, x=0.5, y=0.17, text='PROGRAMMER', sub='BY DAY', size=72, edge='#cfe8ff'),
  dict(type='callout', at=b['hacks'] - 0.05, dur=1.3, x=0.5, y=0.17, text='HACKER', sub='BY NIGHT', size=80, edge='#5aff7a'),
  dict(type='tag', at=b['neo1'] - 0.05, untilAt=b['neo1'] + 0.8, of='neo', text='NEO', bg='#5aff7a'),
  dict(type='speedlines', at=b['neo1'] + 0.75, dur=1.0, x=0.5, y=0.5),
  dict(type='tag', at=b['morpheus1'], untilAt=b['pills'] + 0.3, of='mentor', text='MORPHEUS', bg='#ff9a8a'),
  dict(type='callout', at=b['blue'] - 0.05, dur=2.4, x=0.5, y=0.17, text='BLUE PILL', sub='BACK TO NORMAL LIFE', size=80, edge='#4a8aff', subInk='#9ac0ff'),
  dict(type='callout', at=b['red1'] - 0.05, dur=2.1, x=0.5, y=0.17, text='RED PILL', sub='THE TRUTH', size=86, edge='#ff3a3a', subInk='#ff9a9a'),
  dict(type='flash', at=b['dive'] - 0.02, dur=0.7, amount=1.0),
  dict(type='speedlines', at=b['dive'], dur=0.7, x=0.5, y=0.5),
  dict(type='callout', at=b['wakes'] + 0.15, dur=1.4, x=0.5, y=0.17, text='THE REAL WORLD', size=70, edge='#ff6a8a'),
  dict(type='callout', at=b['energy'] - 0.4, dur=1.4, x=0.5, y=0.17, text='FARMED FOR ENERGY', size=60, edge='#ff6a8a'),
  dict(type='callout', at=b['fake'] - 0.1, dur=2.2, x=0.5, y=0.17, text='THE MATRIX', sub='A SIMULATED WORLD', size=80, edge='#5aff7a'),
  dict(type='speedlines', at=b['matrix1'] + 0.7, dur=1.2, x=0.5, y=0.5),
  dict(type='tag', at=b['ship'] + 0.4, untilAt=b['kung'] + 0.2, of='trinity', text='TRINITY', bg='#7ad8e0'),
  dict(type='callout', at=b['kung'], dur=2.0, x=0.5, y=0.17, text='KUNG FU', sub='UPLOADED TO HIS BRAIN', size=82, edge='#5aff7a'),
  dict(type='callout', at=b['one'] - 0.1, dur=0.9, x=0.5, y=0.17, text='THE ONE?', size=86, edge='#ffc95a'),
  dict(type='flicker', at=b['one'] + 0.3, dur=0.6),
  dict(type='flash', at=b['one'] + 0.45, dur=0.35, amount=0.6),
  dict(type='tag', at=b['oracle'] - 0.1, untilAt=b['isnt'] + 0.5, of='oracle', text='THE ORACLE', bg='#ffc95a'),
  dict(type='callout', at=b['isnt'] - 0.1, dur=0.95, x=0.5, y=0.17, text='NOT THE ONE?', size=74, edge='#ff5a4a'),
  dict(type='tag', at=b['cypher'] - 0.1, untilAt=b['agents'] + 0.3, of='cypher', text='CYPHER', bg='#d8b45a'),
  dict(type='tag', at=b['agents'], untilAt=b['comfortable'] - 0.1, of='smith', text='AGENT', bg='#9a9aa8'),
  dict(type='callout', at=b['comfortable'] - 0.1, dur=2.0, x=0.5, y=0.17, text='THE DEAL', sub='A COMFORTABLE LIFE, BACK INSIDE', size=78, edge='#ff5a4a'),
  dict(type='callout', at=b['captured'] - 0.1, dur=1.0, x=0.5, y=0.17, text='CAPTURED', size=80, edge='#ff5a4a'),
  dict(type='tag', at=b['captured'] - 0.3, untilAt=b['captured'] + 0.8, of='mentor', text='MORPHEUS', bg='#ff9a8a'),
  dict(type='tag', at=b['trinity1'], untilAt=b['save'], of='trinity', text='TRINITY', bg='#7ad8e0'),
] + [dict(type='impactframe', at=t, dur=0.06) for t in SHOTS_L[::3]] + \
    [dict(type='blast', at=t, world=[139.4, -2.0, 1.4], r=1, only=['nobody'], shake=4, hidden=True) for t in SHOTS_L] + [
  dict(type='tag', at=b['smith1'] - 0.1, untilAt=b['dead'], of='smith', text='AGENT SMITH', bg='#9a9aa8'),
  dict(type='impactframe', at=b['shot'], dur=0.08),
] + [dict(type='blast', at=t, world=[166.6, -0.6, 1.35], r=1, only=['nobody'], shake=7, hidden=True) for t in SHOTS_H] + [
  dict(type='bubble', at=b['loves'] - 0.35, dur=1.3, of='neo', text='♥', size=70),
  dict(type='flash', at=b['wakes2'] - 0.02, dur=0.3, amount=0.45),
  dict(type='callout', at=b['code2'] - 0.25, dur=1.2, x=0.5, y=0.17, text='HE SEES THE CODE', size=64, edge='#5aff7a'),
  dict(type='impactframe', at=b['freeze'] + 0.12, dur=0.06),
  dict(type='speedlines', at=b['dash'], dur=0.5, x=0.5, y=0.5),
  dict(type='flash', at=b['burst'] - 0.03, dur=0.6, amount=1.0),
  dict(type='blast', at=b['burst'], world=[166.9, -0.45, 1.2], r=1, only=['nobody'], shake=14, hidden=True),
  dict(type='callout', at=b['would'] - 0.05, dur=2.3, x=0.5, y=0.17, text='RED PILL', sub='OR BLUE?', size=86, edge='#ff3a3a', subInk='#9ac0ff'),
  dict(type='darken', keys=[dict(at=END - 0.5, a=0.0), dict(at=END - 0.05, a=1.0)]),
]
tint = [dict(at=0.0, col='#7dff9a', a=0.1), dict(at=OFFICE0, col='#e8fff0', a=0.05), dict(at=APT0, col='#5aff7a', a=0.16), dict(at=ROOM0, col='#ffb070', a=0.12),
        dict(at=POD0, col='#ff5a8a', a=0.2), dict(at=SHIP0, col='#7ab0ff', a=0.14), dict(at=KITCH0, col='#ffc070', a=0.1), dict(at=REST0, col='#ff7050', a=0.14),
        dict(at=CAPT0, col='#9adfb0', a=0.14), dict(at=LOBBY0, col='#e0ffe8', a=0.06), dict(at=HALL0, col='#ffb070', a=0.12), dict(at=b['sees'], col='#5aff7a', a=0.22)]

sfx = [dict(type='hum', at=0.0, dur=3.4, gain=0.3), dict(type='sting', at=0.3, gain=0.4), dict(type='glitch', at=b['computer'] - 0.1, dur=0.5, gain=0.7),
       dict(type='glitch', at=b['chose'] - 0.4, dur=0.4, gain=0.6), dict(type='whoosh', at=b['find'], dur=0.9, gain=0.8), dict(type='beep', at=b['code'], gain=0.25),
       dict(type='whoosh', at=b['day'] + 0.55, dur=0.8, gain=0.7), dict(type='beep', at=b['hacks'] + 0.2, gain=0.25), dict(type='beep', at=b['night'] + 0.3, gain=0.22),
       dict(type='whoosh', at=b['neo1'] + 0.7, dur=1.0, gain=0.8), dict(type='wind', at=b['stranger'] - 0.4, dur=2.0, gain=0.35), dict(type='creak', at=b['morpheus1'], dur=0.8, gain=0.4),
       dict(type='ting', at=b['pills'] + 0.1, gain=0.35), dict(type='pop', at=b['blue'], gain=0.35), dict(type='sting', at=b['red1'], gain=0.45), dict(type='gulp', at=b['red2'], gain=0.6),
       dict(type='whoosh', at=b['dive'], dur=0.9, gain=1.0), dict(type='glitch', at=b['dive'] + 0.1, dur=0.5, gain=0.6), dict(type='hum', at=b['wakes'], dur=7.5, gain=0.3),
       dict(type='engine', at=b['machines'] - 0.4, dur=3.0, gain=0.35), dict(type='charge', at=b['energy'] - 0.1, dur=0.8, gain=0.4), dict(type='sting', at=b['fake'], gain=0.4),
       dict(type='whoosh', at=b['matrix1'] + 0.6, dur=1.4, gain=0.9), dict(type='hum', at=b['ship'], dur=5.5, gain=0.25), dict(type='charge', at=b['kung'] - 0.1, dur=1.6, gain=0.5),
       dict(type='beep', at=b['uploaded'] + 0.5, gain=0.3), dict(type='sting', at=b['one'], gain=0.4), dict(type='glitch', at=b['one'] + 0.3, dur=0.6, gain=0.6),
       dict(type='whoosh', at=b['one'] + 0.35, dur=0.9, gain=0.9), dict(type='ting', at=b['oracle'], gain=0.3), dict(type='pop', at=b['isnt'], gain=0.3),
       dict(type='whoosh', at=b['then'] + 0.2, dur=0.7, gain=0.6), dict(type='sting', at=b['comfortable'], gain=0.4), dict(type='slam', at=b['captured'], gain=0.45),
       dict(type='cuffs', at=b['captured'] + 0.3, gain=0.4), dict(type='whoosh', at=b['trinity1'] - 0.2, dur=0.9, gain=0.8)] + \
      [dict(type='punch', at=t, gain=0.35) for t in SHOTS_L] + \
      [dict(type='whoosh', at=b['save'] + 0.4, dur=0.9, gain=0.8), dict(type='hum', at=b['smith1'], dur=4.5, gain=0.2)] + \
      [dict(type='punch', at=t, gain=0.55) for t in SHOTS_H] + \
      [dict(type='slam', at=b['shot'] + 0.35, gain=0.5), dict(type='pop', at=b['loves'], gain=0.35), dict(type='charge', at=b['wakes2'] - 0.2, dur=0.7, gain=0.5),
       dict(type='glitch', at=b['sees'] - 0.1, dur=0.6, gain=0.6), dict(type='hum', at=b['sees'], dur=6.0, gain=0.3)] + \
      [dict(type='ting', at=b['stops'] - 0.05 + 0.1 * k, gain=0.3) for k in range(4)] + \
      [dict(type='whoosh', at=b['dash'], dur=0.6, gain=0.9), dict(type='boom', at=b['burst'], gain=0.9), dict(type='crash', at=b['burst'] + 0.05, gain=0.5),
       dict(type='sting', at=b['would'], gain=0.45)]

S_ = dict(title='Movies in a Minute: The Matrix', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.04) saturate(1.1) contrast(1.06)', thumbnail_cue=b['red1'] + 0.6,
  music=dict(level_db=-24, segments=[dict(style='dread', bpm=84, fadeIn=0.6, fadeOut=0.4, **{'from': 0.0, 'to': b['dive']}),
                                     dict(style='dread', bpm=72, fadeIn=0.3, fadeOut=0.4, **{'from': b['dive'], 'to': b['ship'] - 0.6}),
                                     dict(style='chill', bpm=96, fadeIn=0.3, fadeOut=0.3, **{'from': b['ship'] - 0.6, 'to': b['then']}),
                                     dict(style='dread', bpm=84, fadeIn=0.3, fadeOut=0.3, **{'from': b['then'], 'to': b['storm'] - 0.3}),
                                     dict(style='chase', bpm=136, fadeIn=0.2, fadeOut=0.4, **{'from': b['storm'] - 0.3, 'to': b['sees']}),
                                     dict(style='reveal', bpm=96, fadeIn=0.3, fadeOut=1.5, **{'from': b['sees'], 'to': END})]),
  cast=dict(neo=dict(costume='hoodie_grey', mood='neutral', hair='#2a2420'),
            mentor=dict(costume='coat_wine', mood='smug', hair='#8a847c', facial='beard'),
            trinity=dict(costume='jacket_teal', mood='neutral', hair='#6a2a1a', hairLong='#6a2a1a'),
            oracle=dict(costume='cardigan_rose', mood='happy', hair='#d8d2c8'),
            cypher=dict(costume='sweater_crew', mood='smug', hair='#7a5a3a', facial='beard'),
            smith=dict(costume='suit_grey', mood='smug', hair='#3a3026'), agent2=dict(costume='suit_grey', mood='angry', hair='#2a2420'),
            guard1=dict(costume='police', hat='police_cap'), guard2=dict(costume='police', hat='police_cap'),
            cow1=dict(costume='office_shirt', hair='#6a4a2a'), cow2=dict(costume='tee_blue', hair='#a07a4a'),
            walker1=dict(costume='tee_white', hair='#2a2420'), walker2=dict(costume='flannel_red', hair='#d8b45a')),
  scenes=[dict(cue='Everything', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx, charTint=tint)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
