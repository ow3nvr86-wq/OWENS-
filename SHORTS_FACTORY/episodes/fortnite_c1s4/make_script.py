import json
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script.json')
hy = lambda sc, head=0.5: round(head + 0.1615 * sc, 3)          # feet y that puts the head centre at `head`
HERO = dict(id='hero', cast='hero')
def ch(**k): return k
def mv(f=None, **k):
    d = dict(k); d['from'] = f; return d
sc = []
# 1  You blink... (CU, sky)
sc.append(dict(cue='You', loc='b_sky', camera=dict(move='push', focus=[0.5, 0.42]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=hy(2.6, 0.42), scale=2.6, z='fg', mood='neutral', keys=[dict(cue='blink', mood='shocked', lookAt='left'), dict(cue='and', lookAt='camera')])],
  fx=[dict(type='rushclouds', at=0, z='near', n=5, dir=-0.15)], sfx=[dict(type='whoosh', at=0.0, gain=0.6)]))
# 2  and you're on the Battle Bus. (wide)
sc.append(dict(cue='and', loc='b_sky', camera=dict(move='pan_left', amount=1.4, focus=[0.5, 0.45]), transition='whip',
  props=[dict(type='bus', x=1.1, y=0.52, scale=0.8, z='mid', move=mv(x=0.5, f=0, to='Fortnite'))],
  characters=[ch(id='hero', cast='hero', x=1.1, y=0.52 - 0.0625, scale=0.42, z='mid', action='wave', mood='happy', move=mv(x=0.5, f=0, to='Fortnite'))],
  sfx=[dict(type='boing', at='Bus', gain=0.5)]))
# 3  Fortnite. Chapter 1, Season 4. (skydive)
sc.append(dict(cue='Fortnite', loc='b_sky', camera=dict(move='tilt_down', amount=1.5, focus=[0.5, 0.5]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.66, scale=1.5, z='fg', action='skydive', mood='happy', bodyRot=-1.0, lookAt='down', keys=[dict(cue='Chapter', mood='determined')])],
  fx=[dict(type='rushclouds', at=0, z='near', n=9, dir=-1)], sfx=[dict(type='whoosh', at=0.0)]))
# 4  A comet just flattened Dusty Depot...
sc.append(dict(cue='A comet', loc='b_sky', camera=dict(move='pull', focus=[0.72, 0.75]), transition='cut',
  fx=[dict(type='comet', at='comet', from_=None, z='mid', dur=1.3), dict(type='blast', at='Dusty', x=0.78, y=0.8, r=110, z='far', shake=26), dict(type='flash', at='Dusty', dur=0.3, amount=0.7)],
  sfx=[dict(type='whoosh', at='comet'), dict(type='boom', at='Dusty')]))
sc[-1]['fx'][0].pop('from_'); sc[-1]['fx'][0].update({'from': [1.25, -0.15], 'to': [0.78, 0.79]})
# 5  and ninety-nine players want you gone. (crowd skydiving at every depth)
sc.append(dict(cue='and', loc='b_sky', camera=dict(move='push', amount=1.3, focus=[0.5, 0.5]), transition='whip',
  crowds=[dict(cast=['p1', 'p2', 'p3', 'p4'], count=70, area=[0.0, 0.05, 1.0, 1.0], scale=[0.12, 0.75], z=[400, 50], action='skydive', mood='angry', dy=-0.03, seed=4)],
  sfx=[dict(type='charge', at='players', gain=0.7)]))
# 6  You drop into Tilted Towers.
sc.append(dict(cue='You drop', loc='b_town', camera=dict(move='tilt_down', amount=1.8, focus=[0.5, 0.6]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.86, scale=0.95, z='fg', action='glide', prop='glider', mood='happy', air=[dict(at=0, h=0.75), dict(at='Towers', h=0.0)], keys=[dict(cue='Towers', action='idle', prop=None)])],
  sfx=[dict(type='whoosh', at=0.0)]))
# 7  So does everyone else.
sc.append(dict(cue='So does', loc='b_town', camera=dict(move='pull', focus=[0.5, 0.55]), transition='cut',
  crowds=[dict(cast=['p1', 'p2', 'p3', 'p4'], count=34, area=[0.05, -0.35, 0.95, 0.55], scale=[0.2, 0.45], z=[150, 50], action='glide', prop='glider', mood='angry', dy=0.33, seed=7),
          dict(cast=['p2', 'p4', 'p1'], count=14, area=[0.1, 0.7, 0.9, 0.95], scale=[0.3, 0.6], z=[150, 50], action='run', mood='angry', speed=0.18, wrap=True, seed=8)],
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.93, scale=1.1, z='fg', mood='worried', lookAt='up', keys=[dict(cue='everyone', mood='scared')])],
  sfx=[dict(type='scramble', at='everyone')]))
# 8  A guy with a shotgun is already waiting.
sc.append(dict(cue='A guy', loc='b_town', camera=dict(move='push', focus=[0.7, 0.55]), transition='cut',
  characters=[ch(id='guy', cast='guy', x=0.72, y=hy(1.6, 0.52), scale=1.6, z='fg', flip=True, action='hold', prop='shotgun', mood='smug', lookAt='hero'),
              ch(id='hero', cast='hero', x=0.2, y=hy(1.6, 0.54), scale=1.6, z='fg', mood='shocked', lookAt='guy', keys=[dict(cue='waiting', mood='scared')])],
  sfx=[dict(type='sting', at='shotgun', gain=0.8)]))
# 9  You panic-build.
sc.append(dict(cue='You', loc='b_town', camera=dict(move='punch', amount=0.6, focus=[0.5, 0.45]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=hy(2.4, 0.45), scale=2.4, z='fg', action='build', mood='scared', lookAt='camera')],
  sfx=[dict(type='knock', at=0.1)]))
# 10 A wall.  11 A ramp.  12 A staircase to nowhere.
sc.append(dict(cue='A wall', loc='b_town', camera=dict(move='push', focus=[0.45, 0.6]), transition='cut',
  props=[dict(type='wall', x=0.62, y=0.9, scale=1.25, z='fg', at='wall', front=True)],
  characters=[ch(id='hero', cast='hero', x=0.3, y=0.88, scale=1.15, z='fg', action='build', mood='scared', lookAt='right')],
  sfx=[dict(type='knock', at='wall')]))
sc.append(dict(cue='A ramp', loc='b_town', camera=dict(move='push', focus=[0.5, 0.6]), transition='cut',
  props=[dict(type='wall', x=0.78, y=0.9, scale=1.05, z='fg'), dict(type='ramp', x=0.42, y=0.9, scale=1.05, z='fg', at='ramp')],
  characters=[ch(id='hero', cast='hero', x=0.2, y=0.9, scale=0.95, z='fg', action='run', mood='determined', move=mv(x=0.5, y=0.7, f='ramp', to=0.62))],
  sfx=[dict(type='knock', at='ramp')]))
sc.append(dict(cue='A staircase', loc='b_town', camera=dict(move='tilt_up', amount=2.6, focus=[0.5, 0.35]), transition='cut',
  props=[dict(type='stairs', x=0.5, y=0.95, scale=0.62, z='fg', at='staircase', steps=60, rate=0.025)],
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.95 - 0.62 * 60 * 50 / 1920 + 0.01, scale=0.35, z='fg', mood='happy', action='idle', keys=[dict(cue='nowhere', mood='worried', lookAt='down')])],
  sfx=[dict(type='knock', at='staircase'), dict(type='pop', at='to'), dict(type='pop', at='nowhere')]))
# 13 You jump off the top...
sc.append(dict(cue='You jump', loc='b_sky', camera=dict(move='tilt_down', amount=1.6, focus=[0.5, 0.5]), transition='whip',
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.7, scale=1.6, z='fg', action='jump', mood='happy', keys=[dict(cue='top', action='fall', mood='shocked')])],
  fx=[dict(type='rushclouds', at='top', z='near', n=7, dir=-1)], sfx=[dict(type='boing', at='jump'), dict(type='whoosh', at='top')]))
# 14 and land in the crater at Dusty Divot.
sc.append(dict(cue='and land', loc='b_crater', camera=dict(move='push', focus=[0.6, 0.7]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.62, y=0.76, scale=0.3, z='mid', action='fall', mood='shocked', air=[dict(at=0, h=0.7), dict(at='crater', h=0.0, ease='linear')], keys=[dict(cue='crater', action='idle', mood='sad')])],
  fx=[dict(type='blast', at='crater', x=0.62, y=0.76, r=60, z='mid', shake=30)], sfx=[dict(type='boom', at='crater')]))
# 15 The ground is covered in glowing purple rocks.
sc.append(dict(cue='The ground', loc='b_crater', camera=dict(move='push', amount=1.3, focus=[0.5, 0.7]), transition='cut',
  props=[dict(type='hoprock', x=0.22, y=0.97, scale=1.6, z='near', seed=1), dict(type='hoprock', x=0.8, y=0.93, scale=1.2, z='near', seed=4), dict(type='hoprock', x=0.62, y=0.86, scale=0.8, z='fg', seed=6)],
  characters=[ch(id='hero', cast='hero', x=0.42, y=0.84, scale=0.9, z='fg', mood='neutral', lookAt='down', keys=[dict(cue='glowing', mood='happy')])],
  sfx=[dict(type='ting', at='glowing')]))
# 16 Hop Rocks.
sc.append(dict(cue='Hop', loc='b_crater', camera=dict(move='push', focus=[0.5, 0.45]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.45, y=hy(2.5, 0.42), scale=2.5, z='fg', action='hold', prop='hoprock', mood='smug', lookAt='camera')],
  sfx=[dict(type='ting', at='Hop')]))
# 17 You crush one.
sc.append(dict(cue='You crush', loc='b_crater', camera=dict(move='punch', amount=0.7, focus=[0.55, 0.4]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.45, y=hy(2.5, 0.45), scale=2.5, z='fg', action='crush', mood='determined', lookAt='right', keys=[dict(cue='one', mood='happy')])],
  fx=[dict(type='burst', at='crush', x=0.62, y=0.3, z='fg', dur=0.8)], sfx=[dict(type='pop', at='crush'), dict(type='sting', at='one', gain=0.5)]))
# 18 Gravity? Gone.
sc.append(dict(cue='Gravity', loc='b_crater', camera=dict(move='tilt_up', amount=1.6, focus=[0.5, 0.5]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.82, scale=0.9, z='fg', action='float', mood='shocked', air=[dict(at=0, h=0.0), dict(at='You', h=0.32)], keys=[dict(cue='Gone', mood='happy')])],
  sfx=[dict(type='boing', at='Gravity', gain=0.6)]))
# 19 You float across the map like a confused astronaut.
sc.append(dict(cue='You float', loc='b_sky', camera=dict(move='pan_right', amount=1.6, focus=[0.5, 0.5]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.15, y=0.62, scale=1.3, z='fg', action='float', mood='worried', move=mv(x=0.8, y=0.56, f=0, to='Then'), keys=[dict(cue='confused', lookAt='left'), dict(cue='astronaut', lookAt='camera')])],
  sfx=[dict(type='whoosh', at='float', gain=0.4)]))
# 20 Then the storm closes in.
sc.append(dict(cue='Then the', loc='b_field', camera=dict(move='push', focus=[0.5, 0.6]), transition='whip',
  characters=[ch(id='hero', cast='hero', x=0.62, y=0.82, scale=0.6, z='fg', flip=True, action='run', mood='scared', move=mv(x=0.25, f=0.3, to='Health'))],
  fx=[dict(type='storm', at=0, z='mid', x0=1.0, x1=0.55, dur=1.8)], sfx=[dict(type='drums', at='storm', gain=0.7)]))
# 21 Health dropping.
sc.append(dict(cue='Health', loc='b_field', camera=dict(move='push', amount=1.2, focus=[0.5, 0.45]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=hy(2.2, 0.45), scale=2.2, z='fg', mood='worried', lookAt='down', keys=[dict(cue='dropping', mood='sad')])],
  fx=[dict(type='storm_tint', at=0), dict(type='hud', at=0, from_=0.7, to=0.22, dur=1.0)], sfx=[dict(type='gulp', at='dropping')]))
sc[-1]['fx'][1]['from'] = sc[-1]['fx'][1].pop('from_')
# 22 Someone at Risky Reels is dancing at you.
sc.append(dict(cue='Someone', loc='b_drivein', camera=dict(move='push', amount=1.4, focus=[0.45, 0.6]), transition='cut',
  characters=[ch(id='dancer', cast='dancer', x=0.435, y=0.617, scale=0.34, z='mid', action='dance', mood='happy', lookAt='camera'),
              ch(id='hero', cast='hero', x=0.2, y=hy(2.0, 0.52), scale=2.0, z='fg', mood='angry', lookAt='dancer', keys=[dict(cue='dancing', mood='angry')])],
  sfx=[dict(type='tada', at='dancing', gain=0.5)]))
# 23 Final circle. One player left.
sc.append(dict(cue='Final', loc='b_field', camera=dict(move='pull', focus=[0.5, 0.6]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.28, y=0.84, scale=0.55, z='fg', mood='determined', lookAt='sniper'),
              ch(id='sniper', cast='sniper', x=0.6, y=0.505, scale=0.15, z='mid', flip=True, mood='smug', lookAt='hero')],
  fx=[dict(type='storm', at=0, z='mid', x0=0.92, x1=0.86, dur=3), dict(type='glint', at='One', x=0.585, y=0.475, z='mid')],
  sfx=[dict(type='drums', at='Final', gain=0.6), dict(type='ting', at='One')]))
# 24 He has a Bolt-Action Sniper.
sc.append(dict(cue='He has', loc='b_field', camera=dict(move='push', focus=[0.6, 0.45]), transition='cut',
  characters=[ch(id='sniper', cast='sniper', x=0.6, y=hy(2.0, 0.47), scale=2.0, z='fg', flip=True, action='aim', prop='sniper', mood='smug', lookAt='left')],
  fx=[dict(type='glint', at='Sniper', x=0.33, y=0.38, z='fg')], sfx=[dict(type='ting', at='Sniper')]))
# 25 You have a shotgun... and one last Hop Rock.
sc.append(dict(cue='You have', loc='b_field', camera=dict(move='push', focus=[0.45, 0.45]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.42, y=hy(2.2, 0.46), scale=2.2, z='fg', action='hold', prop='shotgun', mood='determined', lookAt='right',
                 keys=[dict(cue='and one', prop='hoprock', mood='smug', lookAt='camera')])],
  sfx=[dict(type='knock', at='shotgun', gain=0.6), dict(type='ting', at='Hop')]))
# 26 You crush it. You jump.
sc.append(dict(cue='You crush', loc='b_field', camera=dict(move='tilt_up', amount=1.8, focus=[0.5, 0.5]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.45, y=0.85, scale=1.2, z='fg', action='crush', mood='determined', air=[dict(at=0, h=0), dict(at='jump', h=0), dict(at=1.65, h=0.38)], keys=[dict(cue='jump', action='jump', mood='happy')])],
  fx=[dict(type='burst', at='crush', x=0.53, y=0.52, z='fg')], sfx=[dict(type='pop', at='crush'), dict(type='boing', at='jump')]))
# 27 He misses.
sc.append(dict(cue='He misses', loc='b_field', camera=dict(move='push', focus=[0.5, 0.45]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.45, y=0.66, scale=1.3, z='fg', action='float', mood='smug', air=[dict(at=0, h=0.2)], lookAt='right')],
  fx=[dict(type='tracer', at='misses', **{'from': [1.1, 0.6], 'to': [-0.1, 0.72]}, z='fg', dur=0.22)], sfx=[dict(type='whoosh', at='misses')]))
# 28 You don't.
sc.append(dict(cue="You don't", loc='b_field', camera=dict(move='push', focus=[0.55, 0.55]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.22, y=0.86, scale=1.3, z='fg', action='aim', prop='shotgun', mood='determined', lookAt='sniper'),
              ch(id='sniper', cast='sniper', x=0.62, y=0.505, scale=0.22, z='mid', flip=True, action='aim', prop='sniper', mood='smug', lookAt='hero', keys=[dict(cue="don't", mood='shocked')])],
  fx=[dict(type='flash', at="don't", dur=0.18, amount=0.6), dict(type='blast', at="don't", x=0.62, y=0.505, r=90, z='mid', shake=28, force=1.0)],
  sfx=[dict(type='boom', at="don't")]))
# 29 Victory Royale.
sc.append(dict(cue='Victory', loc='b_field', camera=dict(move='push', focus=[0.5, 0.45]), transition='zoom',
  characters=[ch(id='hero', cast='hero', x=0.5, y=hy(2.0, 0.5), scale=2.0, z='fg', action='cheer', mood='happy', lookAt='camera', talk=['Victory', 'Then'])],
  fx=[dict(type='confetti', at='Victory'), dict(type='badge', at='Victory', y=0.2)], sfx=[dict(type='tada', at='Victory')]))
# 30 Then you blink... and you're back in the lobby.
sc.append(dict(cue='Then you', loc='b_lobby', camera=dict(move='push', focus=[0.5, 0.62]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=0.75, scale=0.95, z='mid', mood='shocked', lookAt='left', keys=[dict(cue='blink', mood='neutral', lookAt='camera'), dict(cue='lobby', mood='happy', lookAt='right')])],
  sfx=[dict(type='ting', at='blink')]))
# 31 Ready up?
sc.append(dict(cue='Ready', loc='b_lobby', camera=dict(move='push', amount=1.2, focus=[0.5, 0.42]), transition='cut',
  characters=[ch(id='hero', cast='hero', x=0.5, y=hy(2.4, 0.42), scale=2.4, z='fg', mood='smug', lookAt='camera', action='wave', talk=['Ready', 3])],
  sfx=[dict(type='pop', at='up')]))
S = dict(title='Teleported into Fortnite (Chapter 1, Season 4)', fps=60,
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.68, caption_swaps={'ninety-nine': '99'}, grade='saturate(1.18) contrast(1.06)', thumbnail_cue='Victory',
  music=dict(style='bouncy', bpm=120, level_db=-20),
  cast=dict(hero=dict(costume='hoodie_green', hat='beanie', mood='neutral', hair='#4a2f1e', hatSpring=dict(freq=3.0, damping=0.18)),
            guy=dict(costume='jacket_purple', hat='cap', facial='moustache', mood='smug'),
            sniper=dict(costume='ghillie', hat='hood_leafy', mood='smug'),
            dancer=dict(costume='tracksuit_yellow', hat='bandana', mood='happy'),
            p1=dict(costume='tee_red', hat='cap', mood='angry'), p2=dict(costume='tee_blue', hat='headset', mood='angry'),
            p3=dict(costume='vest_orange', hat='beanie', mood='angry'), p4=dict(costume='jacket_purple', hat='bandana', mood='angry')),
  scenes=sc)
json.dump(S, open(P, 'w'), indent=1)
print(len(sc), 'scenes')
