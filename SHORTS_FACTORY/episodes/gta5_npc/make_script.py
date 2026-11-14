"""GTA 5 NPC Short: ONE continuous camera move (no cuts). The 3D city and the camera are rendered by tools/gta_oneshot.py
into oneshot/ (frames + camera.json with the camera and every actor's world track). Here the 2D cast is pinned to those
tracks, so they walk, run, drive and fly with the 3D world. Times are seconds (= the voice's word times). Writes script.json."""
import json, os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script.json')
def K(t, **k): d = dict(k); d['cue'] = t; return d
hop = lambda t: [dict(at=t - 0.01, h=0.0), dict(at=t + 0.22, h=0.75), dict(at=t + 0.5, h=0.0)]

chars = [
  dict(id='hero', cast='hero', track='hero', autoGait=True, mood='neutral', lookAt='camera',
       keys=[K(4.86, mood='sad'), K(5.48, mood='neutral', lookAt='right'), K(7.48, mood='worried', lookAt='camera'), K(8.46, mood='scared', lookAt='down'),
             K(10.0, mood='worried', lookAt='camera'), K(12.2, mood='shocked', lookAt='left'), K(13.6, lookAt='right'), K(14.77, mood='sad', lookAt='camera'),
             K(16.4, mood='shocked'), K(18.3, mood='worried', lookAt='up'), K(26.0, mood='scared', lookAt='camera'),
             K(44.18, mood='shocked', lookAt='right'), K(45.23, mood='scared', lookAt='camera'), K(47.96, mood='shocked', lookAt='left'), K(50.21, mood='happy')]),
  dict(id='heroCar', cast='hero', track='heroSeat', action='sit', clipDoor=True, rollTrack=True, autoFlip=False, flip=False, mood='scared', lookAt='camera',
       keys=[K(28.4, mood='determined', lookAt='right'), K(30.64, mood='scared', lookAt='left'), K(32.04, mood='worried', lookAt='camera'),
             K(35.07, mood='shocked', lookAt='right'), K(38.09, mood='determined'), K(40.07, action='cheer', mood='happy', lookAt='camera'),
             K(41.23, action='sit', mood='shocked'), K(42.74, mood='happy'), K(44.18, mood='worried', lookAt='right')]),
] + [dict(id='clone%d' % i, cast='hero', track='clone%d' % i, autoGait=True, mood='neutral', lookAt='camera',
          keys=[K(12.62, mood='happy', lookAt='camera')]) for i in range(5)] + [
  dict(id='mailman', cast='mailman', track='mailman', autoGait=True, mood='happy', lookAt='left', keys=[K(21.5, mood='shocked', lookAt='camera')]),
  dict(id='player', cast='player', track='player', autoGait=True, mood='smug', lookAt='camera',
       keys=[K(20.9, mood='angry', lookAt='left'), K(21.55, action='punch', mood='angry'), K(21.95, action='idle', mood='smug'),
             K(23.3, action='sit', mood='smug', lookAt='camera'), K(24.82, mood='angry', lookAt='camera'), K(28.4, mood='angry', lookAt='right'),
             K(46.0, action='idle', mood='shocked', lookAt='camera'), K(47.6, mood='scared', lookAt='left')]),
] + [dict(id='cop%d' % i, cast='cop', track='cop%d' % i, autoGait=True, mood='angry', lookAt='camera', airW=hop(45.25 + 0.06 * i),
          keys=[K(46.45, action='aim', prop='pistol', mood='angry'), K(47.37, action='idle', prop=None, lookAt='left'), K(49.3, mood='angry', lookAt='down')]
             + ([K(50.9, mood='neutral', lookAt='camera'), K(52.4, mood='happy', lookAt='camera')] if i == 1 else []),
          **({'nodAt': [52.5], 'talk': ['Same', 54.7]} if i == 1 else {})) for i in range(10)]

fx = [dict(type='bubble', of='hero', at=10.56, dur=0.75, text='nice day!'), dict(type='bubble', of='hero', at=11.05, dur=0.75, text='hey!', dx=-0.25, rot=0.05),
      dict(type='bubble', of='hero', at=11.5, dur=0.8, text='watch it, pal!'),
      dict(type='tag', of='hero', at=16.4, text='NPC', untilAt=26.6)] + [dict(type='tag', of='clone%d' % i, at=16.55 + 0.08 * i, text='NPC', untilAt=26.4) for i in range(5)] + [
      dict(type='flash', at=18.6, dur=0.25, amount=0.35),
      dict(type='spawn', at=20.35, world=[-4.0, 42.0, 0.0]), dict(type='flash', at=20.56, dur=0.2, amount=0.5),
      dict(type='blast', at=21.7, actor='mailman', off=[0.7, -0.7, 0.9], rW=2.5, r=250, only=['mailman'], force=0.95, shake=18, hidden=True),
      dict(type='burst', at=21.7, actor='mailman', off=[0.3, -0.3, 1.3], dur=0.5), dict(type='impactframe', at=21.7),
      dict(type='stars', keys=[dict(at=28.4, n=1), dict(at=30.64, n=2), dict(at=32.04, n=3), dict(at=32.97, n=4), dict(at=33.55, n=5), dict(at=50.21, n=0)]),
      dict(type='speedlines', at=28.8, dur=1.6), dict(type='speedlines', at=31.0, dur=1.4), dict(type='speedlines', at=33.4, dur=1.2),
      dict(type='sirenglow', at=30.64, untilAt=50.1, amount=0.22),
      dict(type='speedlines', at=38.2, dur=0.9), dict(type='flash', at=38.6, dur=0.2, amount=0.4), dict(type='speedlines', at=39.9, dur=1.0),
      dict(type='blast', at=42.75, world=[3.0, 320.0, 0.0], r=1, only=['nobody'], shake=34, hidden=True), dict(type='impactframe', at=42.75), dict(type='flash', at=42.75, dur=0.2, amount=0.55),
      dict(type='blast', at=48.94, actor='player', off=[0.4, -0.4, 0.6], rW=3.0, r=300, only=['player'], force=0.42, shake=26, hidden=True, stay=True),
      dict(type='burst', at=48.94, actor='player', off=[0, 0, 0.8], dur=0.6), dict(type='impactframe', at=48.94),
      dict(type='flash', at=50.21, dur=0.25, amount=0.5), dict(type='title', at=50.21, untilAt=52.2, text='BUSTED', y=0.3, size=200)]

sfx = [dict(type='whoosh', at=0.0, gain=0.6), dict(type='siren', at=2.6, dur=2.2, gain=0.25), dict(type='ting', at=4.86, gain=0.5), dict(type='gulp', at=7.48, gain=0.6),
       dict(type='pop', at=10.56), dict(type='pop', at=11.05), dict(type='pop', at=11.5), dict(type='boing', at=12.62, gain=0.5), dict(type='sting', at=16.4, gain=0.7),
       dict(type='scratch', at=18.35, gain=0.8), dict(type='spawn', at=19.9, gain=0.8), dict(type='punch', at=21.68), dict(type='whoosh', at=21.75, gain=0.6),
       dict(type='engine', at=23.2, dur=1.4, gain=0.5), dict(type='whoosh', at=26.1, gain=0.7), dict(type='knock', at=27.0, gain=0.4), dict(type='engine', at=27.5, dur=2.6, gain=0.8),
       dict(type='skid', at=28.4, dur=0.8, gain=0.6), dict(type='siren', at=30.6, dur=5.4, gain=0.45), dict(type='ting', at=32.04, gain=0.5), dict(type='ting', at=32.97, gain=0.5),
       dict(type='ting', at=33.55, gain=0.6), dict(type='sting', at=35.93, gain=0.6), dict(type='engine', at=37.0, dur=1.8, gain=0.7), dict(type='whoosh', at=38.5, gain=0.8),
       dict(type='whoosh', at=40.3, gain=0.6), dict(type='whoosh', at=41.6), dict(type='whoosh', at=42.0, gain=0.8), dict(type='crash', at=42.74), dict(type='skid', at=42.95, dur=1.0, gain=0.8),
       dict(type='siren', at=44.1, dur=3.0, gain=0.55), dict(type='scramble', at=45.23, gain=0.8), dict(type='cuffs', at=46.5, gain=0.5), dict(type='scramble', at=47.4, gain=0.6),
       dict(type='punch', at=48.94), dict(type='boom', at=48.98, gain=0.5), dict(type='cuffs', at=49.7, gain=0.7), dict(type='sting', at=50.21, gain=0.9), dict(type='pop', at=52.5, gain=0.6)]

S_ = dict(title='Stuck in GTA 5 as an NPC', fps=60, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.72, caption_case='lower', caption_size=78, caption_swaps={'5.': '5.'}, grade='brightness(1.06) saturate(1.22) contrast(1.06)', thumbnail_cue=42.3,
  music=dict(level_db=-19, segments=[dict(style='chill', bpm=88, **{'from': 0.0, 'to': 18.36}), dict(style='chase', bpm=150, **{'from': 18.36, 'to': 50.18}),
                                     dict(style='chill', bpm=88, gain=0.8, fadeIn=0.6, **{'from': 51.0})]),
  cast=dict(hero=dict(costume='tee_white', hat='none', mood='neutral', hair='#3a2618'),
            player=dict(costume='flannel_red', hat='cap_back', facial='moustache', mood='smug', hair='#2a1a10'),
            mailman=dict(costume='mail', hat='mail_cap', mood='happy', hair='#6a6a6a'),
            cop=dict(costume='police', hat='police_cap', mood='angry', hair='#2a1a10', hatSpring=dict(freq=3.4, damping=0.2))),
  scenes=[dict(cue='You', bgseq=dict(dir='oneshot'), transition='cut', characters=chars, fx=fx, sfx=sfx)])
json.dump(S_, open(P, 'w'), indent=1); print('1 scene,', len(chars), 'characters,', len(fx), 'fx,', len(sfx), 'sfx')
