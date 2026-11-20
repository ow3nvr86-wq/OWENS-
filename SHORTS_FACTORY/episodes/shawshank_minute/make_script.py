"""MOVIES IN A MINUTE: THE SHAWSHANK REDEMPTION (1994). ONE continuous camera move (white flashes hide the jumps).
The 3D prison, tunnel, sewer pipe, storm and beach are rendered by tools/shawshank_oneshot.py into oneshot/ (frames +
camera.json with the camera and every 2D actor's track). Every time below comes from a cue word in work/words.json
(same resolver as the Blender script), so a new voiceover only needs: align -> this script -> re-render.
Plot facts: sources.txt. Original characters, poster and music; no film footage, audio, logos or dialogue."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, 'script.json')
WORDS = json.load(open(os.path.join(HERE, 'work', 'words.json')))
norm = lambda w: re.sub(r"[^a-z0-9]", '', w.lower())
CUES = [('then', 'then'), ('empty', 'empty'), ('y1947', '1947'), ('two', 'two'), ('innocent', 'innocent'), ('shawshank', 'shawshank'), ('befriends', 'befriends'),
        ('anything', 'anything'), ('asks', 'asks'), ('rock', 'rock'), ('later', 'later'), ('poster', 'poster'), ('years', 'years'), ('taxes', 'taxes'),
        ('library', 'library'), ('launders', 'launders'), ('warden', 'warden'), ('then2', 'then'), ('inmate', 'inmate'), ('really', 'really'),
        ('warden2', 'warden'), ('killed', 'killed'), ('tells', 'tells'), ('mexico', 'mexico'), ('next', 'next'), ('roll', 'roll'), ('gone', 'gone'),
        ('furious', 'furious'), ('throws', 'throws'), ('rock2', 'rock'), ('rips', 'rips'), ('behind', 'behind'), ('tunnel', 'tunnel'),
        ('nineteen2', 'nineteen'), ('crawls', 'crawls'), ('sewer', 'sewer'), ('takes', 'takes'), ('money', 'money'), ('mails', 'mails'), ('newspaper', 'newspaper'),
        ('red2', 'red'), ('forty', 'forty'), ('follows', 'follows'), ('finds', 'finds'), ('beach2', 'beach'), ('would', 'would')]
b = {}; wi = 0; ws = WORDS['words']
for key, cue in CUES:
    j = wi
    while norm(ws[j]['word']) != cue: j += 1
    b[key] = round(ws[j]['start'], 3); wi = j + 1
END = WORDS['duration'] + 1.2
b['vanish'] = b['then'] + 0.5; b['hit'] = b['rips']; b['flashC'] = b['red2'] - 0.12; b['flashD'] = b['finds'] - 0.2
BOLTS = [b['takes'] - 0.05, b['money'] + 0.6, b['mails'] + 0.5, b['newspaper'] + 0.4, b['flashC'] - 0.2]
def K(t, **k): d = dict(k); d['cue'] = round(t, 3); return d
NF = [0.45, 1.1]

chars = [
  dict(id='andy', cast='andy', track='andy', autoGait=True, rollTrack=True, mood='sad', lookAt='camera', nearFade=NF,
       keys=[K(0.0, action='idle', mood='sad', lookAt='camera'), K(b['then'] - 0.1, mood='determined', lookAt='right'),
             K(b['shawshank'] + 0.3, mood='worried', lookAt='left'), K(b['asks'], action='talk', mood='neutral', lookAt='left'),
             K(b['rock'] + 0.55, action='idle', prop='rockhammer', mood='happy'), K(b['poster'] + 0.35, prop='poster', mood='smug'),
             K(b['years'] - 0.2, prop='', mood='neutral', lookAt='right'), K(b['taxes'] - 0.4, prop='papers', mood='happy'),
             K(b['library'] + 0.2, prop='book', mood='happy'), K(b['launders'] + 0.7, prop='papers', mood='worried'),
             K(b['then2'] - 0.15, prop='', action='idle', mood='neutral', lookAt='right'), K(b['really'] + 0.1, mood='shocked'),
             K(b['shot'] if 'shot' in b else b['killed'], action='sit', mood='happy', lookAt='right'),
             K(b['crawls'] - 0.75, action='skydive', mood='determined', lookAt='camera'),
             K(b['takes'] - 0.1, action='cheer', mood='happy', lookAt='up')]),
  dict(id='andy_suit', cast='andy_suit', track='andy_suit', autoGait=True, mood='worried', lookAt='camera', nearFade=NF,
       keys=[K(b['innocent'] - 0.2, mood='sad', lookAt='camera')]),
  dict(id='arr1', cast='arr1', track='arr1', autoGait=True, mood='sad', lookAt='left', nearFade=NF),
  dict(id='arr2', cast='arr2', track='arr2', autoGait=True, mood='worried', lookAt='left', nearFade=NF),
  dict(id='red', cast='red', track='red', autoGait=True, mood='smug', lookAt='right', nearFade=NF,
       keys=[K(b['rock'] - 0.3, action='hold', prop='rockhammer'), K(b['rock'] + 0.55, action='idle', prop=''),
             K(b['later'], action='hold', prop='poster'), K(b['poster'] + 0.35, action='idle', prop=''),
             K(b['killed'], action='sit', mood='neutral', lookAt='left'), K(b['mexico'], mood='happy')]),
  dict(id='red_free', cast='red_free', track='red_free', autoGait=True, mood='neutral', lookAt='camera', nearFade=NF,
       keys=[K(b['forty'], mood='happy'), K(b['flashD'], mood='worried', lookAt='right'), K(b['finds'] + 0.3, mood='happy'), K(b['beach2'], action='cheer', mood='happy')]),
  dict(id='andy_beach', cast='andy_beach', track='andy_beach', autoGait=False, mood='neutral', lookAt='left', nearFade=NF,
       keys=[K(0.0, action='hold', prop='sander'), K(b['finds'], action='idle', prop='', mood='shocked'), K(b['beach2'], action='cheer', mood='happy')]),
  dict(id='warden', cast='warden', track='warden', autoGait=True, mood='smug', lookAt='left', nearFade=[0.6, 1.3],
       keys=[K(b['launders'], action='hold', prop='papers'), K(b['then2'], action='idle', prop=''), K(b['warden2'], mood='angry', lookAt='left'),
             K(b['furious'] - 0.4, mood='angry', lookAt='right', prop='rock'), K(b['throws'] + 0.35, action='punch'), K(b['rock2'] - 0.05, prop=''),
             K(b['rips'] + 0.1, action='idle', mood='shocked')]),
  dict(id='guard1', cast='guard', track='guard1', autoGait=True, mood='angry', lookAt='camera', nearFade=NF,
       keys=[K(0.0, action='hold', prop='rifle'), K(b['years'] - 0.2, action='idle', prop='', mood='happy', lookAt='right'),
             K(b['warden2'] - 1.0, action='aim', prop='rifle', mood='angry', lookAt='left'), K(b['next'], action='idle', prop='', mood='neutral', lookAt='right'),
             K(b['gone'], mood='shocked')]),
  dict(id='guard2', cast='guard2', track='guard2', autoGait=True, mood='happy', lookAt='left', nearFade=NF,
       keys=[K(b['next'], mood='neutral'), K(b['gone'], mood='shocked', lookAt='right')]),
  dict(id='tommy', cast='tommy', track='tommy', autoGait=False, mood='worried', lookAt='left', nearFade=NF,
       keys=[K(b['inmate'], action='talk'), K(b['really'] + 0.7, action='idle', mood='scared')]),
]
for k, n in enumerate(['inm1', 'inm2', 'inm3', 'inm4']):
    chars.append(dict(id=n, cast=n, track=n, autoGait=False, mood='neutral', lookAt=['left', 'right', 'right', 'left'][k], nearFade=NF,
                      keys=[K(b['next'], mood='sad'), K(b['gone'] + 0.1 * k, mood='shocked', lookAt='camera')]))

fx = [
  dict(type='callout', at=0.35, dur=1.9, x=0.5, y=0.17, text='19 YEARS', sub="FOR A MURDER HE DIDN'T COMMIT", size=74),
  dict(type='flash', at=b['vanish'] - 0.08, dur=0.35, amount=0.85),
  dict(type='callout', at=b['empty'] - 0.1, dur=0.9, x=0.5, y=0.17, text='EMPTY', size=80, edge='#ff5a4a'),
  dict(type='callout', at=b['y1947'] - 0.05, dur=1.4, x=0.5, y=0.17, text='1947', sub='PORTLAND, MAINE', size=84),
  dict(type='callout', at=b['two'] - 0.1, dur=1.9, x=0.5, y=0.17, text='TWO LIFE SENTENCES', sub='WIFE AND HER LOVER', size=60, edge='#ff5a4a'),
  dict(type='callout', at=b['innocent'] - 0.05, dur=1.1, x=0.5, y=0.17, text='INNOCENT', size=76, edge='#6ad17a'),
  dict(type='speedlines', at=b['shawshank'], dur=1.6, x=0.5, y=0.5),
  dict(type='tag', at=b['befriends'] + 0.2, untilAt=b['asks'] + 0.4, of='red', text='RED', bg='#ff7a5a'),
  dict(type='tag', at=b['asks'] - 0.3, untilAt=b['rock'] - 0.2, of='andy', text='ANDY'),
  dict(type='callout', at=b['rock'] - 0.05, dur=1.0, x=0.5, y=0.17, text='ROCK HAMMER', size=64),
  dict(type='callout', at=b['poster'] - 0.5, dur=1.0, x=0.5, y=0.17, text='MOVIE-STAR POSTER', size=56),
  dict(type='years', at=b['years'] - 0.1, untilAt=b['then2'] - 0.35, x=0.5, y=0.13, keys=[dict(at=b['years'], n=1949), dict(at=b['then2'] - 0.6, n=1965)], label='YEARS PASS', size=84),
  dict(type='callout', at=b['taxes'] - 0.1, dur=1.2, x=0.5, y=0.27, text="THE GUARDS' TAXES", size=44, edge='#9ad0ff'),
  dict(type='callout', at=b['library'] - 0.05, dur=1.0, x=0.5, y=0.27, text='PRISON LIBRARY', size=44, edge='#9ad0ff'),
  dict(type='callout', at=b['launders'] - 0.05, dur=1.3, x=0.5, y=0.27, text="WARDEN'S DIRTY MONEY", size=44, edge='#9ad0ff'),
  dict(type='tag', at=b['warden'] - 0.3, untilAt=b['then2'] - 0.4, of='warden', text='THE WARDEN', bg='#d8d8e0'),
  dict(type='tag', at=b['inmate'] - 0.1, untilAt=b['warden2'] - 0.5, of='tommy', text='NEW INMATE', bg='#9ad0ff'),
  dict(type='callout', at=b['really'] - 0.05, dur=1.3, x=0.5, y=0.17, text='HE KNOWS THE REAL KILLER', size=46, edge='#ff5a4a'),
  dict(type='flash', at=b['killed'] - 0.02, dur=0.4, amount=1.0),
  dict(type='blast', at=b['killed'], world=[-10.5, -59.0, 9.0], r=1, only=['nobody'], shake=14, hidden=True),
  dict(type='callout', at=b['mexico'] - 0.15, dur=1.6, x=0.5, y=0.17, text='ZIHUATANEJO, MEXICO', sub='A TOWN ON THE PACIFIC', size=56, edge='#5ad1ff'),
  dict(type='speedlines', at=b['killed'] + 0.15, dur=0.9, x=0.5, y=0.5),
  dict(type='callout', at=b['gone'] - 0.15, dur=1.0, x=0.5, y=0.17, text='GONE', size=96, edge='#ff5a4a'),
  dict(type='speedlines', at=b['throws'] + 0.3, dur=1.3, x=0.5, y=0.45),
  dict(type='impactframe', at=b['hit'], dur=0.12),
  dict(type='blast', at=b['hit'], world=[0.0, 2.8, 1.45], r=1, only=['nobody'], shake=12, hidden=True),
  dict(type='years', at=b['nineteen2'] - 0.1, untilAt=b['crawls'] - 0.3, x=0.5, y=0.13, keys=[dict(at=b['nineteen2'], n=0), dict(at=b['nineteen2'] + 1.4, n=19)], label='YEARS OF DIGGING', size=90),
  dict(type='speedlines', at=b['crawls'] - 0.35, dur=1.4, x=0.5, y=0.5),
  dict(type='rain', keys=[dict(at=b['takes'] - 0.6, a=0.0), dict(at=b['takes'] - 0.25, a=1.0), dict(at=b['flashC'] - 0.01, a=1.0), dict(at=b['flashC'], a=0.0)]),
] + [dict(type='lightning', at=t0, x=[0.25, 0.7, 0.35, 0.62, 0.45][k], len=0.5) for k, t0 in enumerate(BOLTS)] + [
  dict(type='cash', at=b['money'] - 0.45, dur=2.0, x=0.5, y=0.45, count=36),
  dict(type='callout', at=b['money'] - 0.4, dur=1.4, x=0.5, y=0.17, text='OVER $370,000', sub="THE WARDEN'S DIRTY MONEY", size=66),
  dict(type='newspaper', at=b['mails'] + 0.05, dur=1.9, x=0.5, y=0.3, paper='THE DAILY NEWS', head='WARDEN EXPOSED', sub="SECRET BOOKS REVEAL HIS CRIMES"),
  dict(type='flash', at=b['flashC'] - 0.1, dur=0.45, amount=1.0),
  dict(type='callout', at=b['forty'] - 0.1, dur=1.5, x=0.5, y=0.17, text='40 YEARS', sub='RED IS FREE', size=84, edge='#6ad17a'),
  dict(type='flash', at=b['flashD'] - 0.1, dur=0.45, amount=1.0),
  dict(type='callout', at=b['finds'] + 0.2, dur=1.4, x=0.5, y=0.17, text='ZIHUATANEJO', size=70, edge='#5ad1ff'),
  dict(type='darken', keys=[dict(at=END - 0.5, a=0.0), dict(at=END - 0.05, a=1.0)]),
]
tint = [dict(at=0.0, col='#16244c', a=0.32), dict(at=b['vanish'], col='#ffb070', a=0.1), dict(at=b['y1947'] + 1.4, col='#ffd9a0', a=0.05),
        dict(at=b['shawshank'] + 0.6, col='#ffb060', a=0.1), dict(at=b['years'] + 0.4, col='#ffc890', a=0.08), dict(at=b['then2'] - 0.2, col='#14204a', a=0.42),
        dict(at=b['killed'], col='#6a7080', a=0.12), dict(at=b['roll'], col='#ffb070', a=0.12), dict(at=b['crawls'] - 0.8, col='#2f5a2a', a=0.3),
        dict(at=b['takes'], col='#1a2448', a=0.38), dict(at=b['flashC'], col='#ffe8c0', a=0.04), dict(at=b['flashD'], col='#ff9a50', a=0.16)]

sfx = [dict(type='hum', at=0.0, dur=4.6, gain=0.25), dict(type='sting', at=0.35, gain=0.5), dict(type='whoosh', at=b['vanish'] - 0.1, dur=0.5, gain=0.7),
       dict(type='ting', at=b['empty'], gain=0.4), dict(type='whoosh', at=b['y1947'] + 0.2, dur=1.4, gain=0.9), dict(type='gust', at=b['y1947'] + 0.8, dur=1.6, gain=0.6),
       dict(type='slam', at=b['two'], gain=0.6), dict(type='ting', at=b['innocent'], gain=0.4), dict(type='whoosh', at=b['shawshank'], dur=1.6, gain=0.9),
       dict(type='pop', at=b['befriends'] + 0.2, gain=0.5), dict(type='pop', at=b['rock'], gain=0.5), dict(type='pop', at=b['poster'] - 0.5, gain=0.5),
       dict(type='counter', at=b['years'], dur=6.4, gain=0.35), dict(type='whoosh', at=b['years'], dur=1.0, gain=0.6),
       dict(type='hum', at=b['then2'], dur=4.0, gain=0.3), dict(type='sting', at=b['really'], gain=0.45), dict(type='boom', at=b['killed'], gain=0.75),
       dict(type='slam', at=b['killed'] + 0.02, gain=0.5), dict(type='whoosh', at=b['killed'] + 0.15, dur=0.9, gain=0.7), dict(type='ting', at=b['mexico'], gain=0.35),
       dict(type='whoosh', at=b['next'] + 0.1, dur=1.0, gain=0.7), dict(type='alarm', at=b['roll'], dur=1.0, gain=0.3), dict(type='creak', at=b['gone'] - 0.6, dur=0.7, gain=0.6),
       dict(type='sting', at=b['gone'], gain=0.55), dict(type='scratch', at=b['furious'], dur=0.4, gain=0.4), dict(type='whoosh', at=b['throws'] + 0.35, dur=1.0, gain=0.8),
       dict(type='crash', at=b['hit'], gain=0.7), dict(type='slam', at=b['hit'], gain=0.5), dict(type='creak', at=b['behind'], dur=1.2, gain=0.5),
       dict(type='hum', at=b['tunnel'], dur=3.2, gain=0.35), dict(type='counter', at=b['nineteen2'], dur=1.4, gain=0.35), dict(type='scramble', at=b['crawls'] - 0.4, dur=1.6, gain=0.6),
       dict(type='whoosh', at=b['crawls'] - 0.35, dur=1.2, gain=0.9), dict(type='wind', at=b['takes'] - 0.4, dur=4.6, gain=0.6), dict(type='gust', at=b['takes'], dur=4.0, gain=0.5)] + \
      [dict(type='boom', at=t0, gain=0.6 - 0.05 * k) for k, t0 in enumerate(BOLTS)] + \
      [dict(type='tada', at=b['money'] - 0.4, gain=0.45), dict(type='whoosh', at=b['mails'] + 0.05, dur=0.6, gain=0.6), dict(type='slam', at=b['mails'] + 0.55, gain=0.5),
       dict(type='creak', at=b['red2'], dur=1.0, gain=0.5), dict(type='ting', at=b['forty'], gain=0.4), dict(type='whoosh', at=b['flashD'] - 0.1, dur=0.6, gain=0.6),
       dict(type='pop', at=b['finds'] + 0.2, gain=0.45), dict(type='tada', at=b['beach2'], gain=0.5), dict(type='pop', at=b['would'], gain=0.35)]

S_ = dict(title='Movies in a Minute: The Shawshank Redemption', fps=60, tail=1.2, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.765, caption_case='lower', caption_size=78, grade='brightness(1.02) saturate(1.1) contrast(1.06)', thumbnail_cue=b['hit'] + 0.25,
  music=dict(level_db=-24, segments=[dict(style='chill', bpm=96, fadeIn=0.6, fadeOut=0.4, **{'from': 0.0, 'to': b['then2'] - 0.2}),
                                     dict(style='dread', bpm=80, fadeIn=0.3, fadeOut=0.3, **{'from': b['then2'] - 0.2, 'to': b['rips']}),
                                     dict(style='chase', bpm=132, fadeIn=0.2, fadeOut=0.4, **{'from': b['rips'], 'to': b['flashC']}),
                                     dict(style='reveal', bpm=96, fadeIn=0.3, fadeOut=1.5, **{'from': b['flashC'], 'to': END})]),
  cast=dict(andy=dict(costume='inmate', num='437', mood='neutral', hair='#4a3426'),
            andy_suit=dict(costume='suit_grey', mood='neutral', hair='#4a3426', hat='fedora'),
            andy_beach=dict(costume='beach', mood='neutral', hair='#4a3426', hat='straw_hat'),
            arr1=dict(costume='coat_tan', mood='neutral', hair='#2a2420', hat='flat_cap'),
            arr2=dict(costume='suit_dark', mood='neutral', hair='#7a5a3a', hat='fedora'),
            red=dict(costume='inmate', num='237', mood='neutral', hair='#8a4a2a'),
            red_free=dict(costume='coat_tan', mood='neutral', hair='#8a4a2a', hat='fedora'),
            warden=dict(costume='suit_dark', mood='smug', hair='#9a9aa2'),
            guard=dict(costume='guard', mood='angry', hat='guard_cap'), guard2=dict(costume='guard', mood='neutral', hat='guard_cap'),
            tommy=dict(costume='inmate', num='602', mood='neutral', hair='#d8b45a'),
            inm1=dict(costume='inmate', num='118', hair='#2a2420'), inm2=dict(costume='inmate', num='351', hair='#6a4a2a'),
            inm3=dict(costume='inmate', num='509', hair='#1d1a18'), inm4=dict(costume='inmate', num='774', hair='#a07a4a')),
  scenes=[dict(cue='He', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx, charTint=tint)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx; end', round(END, 2))
