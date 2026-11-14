"""Shot plan v2 (illustrated-history style): rc characters, human-scale 3D sets, 3D prop sprites, close wide-lens framing,
lowercase captions. Writes script.json.  Official logo files can be dropped in as props/logo_fortnite.png and
props/logo_victory.png; until then the logo slots show styled text."""
import json, os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script.json')
HD = 468                                           # rc character: feet-to-head-centre in body units
def feet(scale, head_y): return round(head_y + HD * scale / 1920, 3)
def mv(f=None, **k): d = dict(k); d['from'] = f; return d
sc = []
def S(**k): sc.append(k)

# 1  You blink... : inside the bus, close on the hero in the aisle
S(cue='You', loc='b2_bus', camera=dict(move='push', focus=[0.5, 0.36]), transition='cut',
  characters=[dict(id='p2', cast='p2', x=0.32, y=0.7, scale=0.55, z='mid', mood='neutral', lookAt='hero'),
              dict(id='p3', cast='p3', x=0.7, y=0.68, scale=0.5, z='mid', flip=True, mood='neutral', lookAt='hero'),
              dict(id='hero', cast='hero', x=0.5, y=feet(2.1, 0.36), scale=2.1, z='fg', mood='sad', keys=[dict(cue='blink', mood='shocked', lookAt='left'), dict(cue='and', lookAt='right')])],
  sfx=[dict(type='whoosh', at=0.0, gain=0.5)])
# 2  and you're on the Battle Bus : the bus in the sky (3D sprite)
S(cue='and', loc='b_sky', camera=dict(move='push', amount=1.2, focus=[0.5, 0.45]), transition='whip',
  props=[dict(type='bus', x=1.2, y=0.62, scale=1.9, z='fg', move=mv(x=0.52, f=0, to='Fortnite'))],
  sfx=[dict(type='boing', at='Bus', gain=0.4)])
# 3  Fortnite. Chapter 1, Season 4. : the title, the hero skydiving under it
S(cue='Fortnite', loc='b_sky', camera=dict(move='tilt_down', amount=1.0, focus=[0.5, 0.5]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=0.82, scale=1.4, z='fg', action='skydive', mood='happy', bodyRot=-0.9, lookAt='down', keys=[dict(cue='Chapter', mood='determined')])],
  fx=[dict(type='logo', at='Fortnite', img='props/logo_fortnite.png', text='FORTNITE', size=150, x=0.5, y=0.18, w=0.8),
      dict(type='logo', at='Chapter', text='CHAPTER 1 · SEASON 4', size=58, x=0.5, y=0.27), dict(type='rushclouds', at=0, z='near', n=8, dir=-1)],
  sfx=[dict(type='whoosh', at=0.0), dict(type='sting', at='Fortnite', gain=0.6)])
# 4  A comet just flattened Dusty Depot...
S(cue='A comet', loc='b_sky', camera=dict(move='pull', focus=[0.5, 0.68]), transition='cut',
  fx=[dict(type='comet', at='comet', z='mid', dur=1.3, **{'from': [1.25, -0.15], 'to': [0.5, 0.71]}), dict(type='blast', at='Dusty', x=0.5, y=0.72, r=110, z='far', shake=26), dict(type='flash', at='Dusty', dur=0.3, amount=0.7)],
  sfx=[dict(type='whoosh', at='comet'), dict(type='boom', at='Dusty')])
# 5  and ninety-nine players want you gone. : back inside, every passenger turns to glare
S(cue='and', loc='b2_bus', camera=dict(move='pull', focus=[0.5, 0.55]), transition='whip',
  characters=[dict(id=f'g{i}', cast=['p1', 'p2', 'p3', 'p4'][i % 4], x=x, y=y, scale=s, z=z, flip=x > 0.5, mood='neutral', lookAt='hero',
                   keys=[dict(cue='want', mood='angry', lookAt='camera')]) for i, (x, y, s, z) in enumerate([(0.3, 0.74, 0.62, 'mid'), (0.7, 0.73, 0.6, 'mid'), (0.4, 0.66, 0.45, 'mid'), (0.6, 0.655, 0.43, 'mid'), (0.46, 0.6, 0.3, 'far'), (0.55, 0.595, 0.28, 'far')])]
             + [dict(id='hero', cast='hero', x=0.5, y=feet(1.5, 0.46), scale=1.5, z='fg', mood='worried', lookAt='left', keys=[dict(cue='gone', mood='scared', lookAt='right')])],
  sfx=[dict(type='sting', at='players', gain=0.7)])
# 6  You drop into Tilted Towers.
S(cue='You drop', loc='b2_town', camera=dict(move='tilt_down', amount=1.0, focus=[0.5, 0.6]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=0.92, scale=1.0, z='fg', action='glide', prop='glider', mood='happy', air=[dict(at=0, h=0.65), dict(at='Towers', h=0.0)], keys=[dict(cue='Towers', action='idle', prop=None, mood='happy')])],
  sfx=[dict(type='whoosh', at=0.0)])
# 7  So does everyone else.
S(cue='So does', loc='b2_town', camera=dict(move='pull', focus=[0.5, 0.5]), transition='cut',
  crowds=[dict(cast=['p1', 'p2', 'p3', 'p4'], count=26, area=[0.05, -0.4, 0.95, 0.62], scale=[0.22, 0.5], z=[150, 50], action='glide', prop='glider', mood='angry', dy=0.34, seed=7)],
  characters=[dict(id='hero', cast='hero', x=0.5, y=feet(1.3, 0.58), scale=1.3, z='fg', mood='worried', lookAt='up', keys=[dict(cue='everyone', mood='scared')])],
  sfx=[dict(type='scramble', at='everyone')])
# 8  A guy with a shotgun is already waiting.
S(cue='A guy', loc='b2_town', camera=dict(move='push', focus=[0.62, 0.42]), transition='cut',
  characters=[dict(id='guy', cast='guy', x=0.64, y=feet(1.9, 0.36), scale=1.9, z='fg', flip=True, action='hold', prop='shotgun', mood='smug', lookAt='hero'),
              dict(id='hero', cast='hero', x=0.08, y=feet(1.6, 0.46), scale=1.6, z='fg', mood='shocked', lookAt='guy', keys=[dict(cue='waiting', mood='scared')])],
  sfx=[dict(type='sting', at='shotgun', gain=0.8)])
# 9  You panic-build.
S(cue='You', loc='b2_town', camera=dict(move='punch', amount=0.6, focus=[0.5, 0.4]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=feet(2.2, 0.4), scale=2.2, z='fg', action='build', mood='scared', lookAt='camera')],
  sfx=[dict(type='knock', at=0.1)])
# 10 A wall.   11 A ramp.   12 A staircase to nowhere.
S(cue='A wall', loc='b2_town', camera=dict(move='push', focus=[0.5, 0.6]), transition='cut',
  props=[dict(type='wall', x=0.66, y=0.95, scale=1.0, z='fg', at='wall', front=True)],
  characters=[dict(id='hero', cast='hero', x=0.24, y=0.95, scale=1.1, z='fg', action='build', mood='scared', lookAt='right')], sfx=[dict(type='knock', at='wall')])
S(cue='A ramp', loc='b2_town', camera=dict(move='push', focus=[0.5, 0.6]), transition='cut',
  props=[dict(type='wall', x=0.78, y=0.95, scale=0.85, z='fg'), dict(type='ramp', x=0.42, y=0.95, scale=0.85, z='fg', at='ramp')],
  characters=[dict(id='hero', cast='hero', x=0.16, y=0.95, scale=0.9, z='fg', action='run', mood='determined', move=mv(x=0.42, y=0.74, f='ramp', to=0.62))], sfx=[dict(type='knock', at='ramp')])
S(cue='A staircase', loc='b2_town', camera=dict(move='tilt_up', amount=1.0, focus=[0.5, 0.4]), transition='cut',
  props=[dict(type='stairs', x=0.5, y=0.97, scale=0.6, z='fg', at='staircase', steps=36, rate=0.03)],
  characters=[dict(id='hero', cast='hero', x=0.56, y=0.36, scale=0.32, z='fg', mood='happy', keys=[dict(cue='nowhere', mood='worried', lookAt='down')])],
  sfx=[dict(type='knock', at='staircase'), dict(type='pop', at='to'), dict(type='pop', at='nowhere')])
# 13 You jump off the top...
S(cue='You jump', loc='b_sky', camera=dict(move='tilt_down', amount=1.0, focus=[0.5, 0.5]), transition='whip',
  characters=[dict(id='hero', cast='hero', x=0.5, y=0.78, scale=1.5, z='fg', action='jump', mood='happy', keys=[dict(cue='top', action='fall', mood='shocked')])],
  fx=[dict(type='rushclouds', at='top', z='near', n=7, dir=-1)], sfx=[dict(type='boing', at='jump'), dict(type='whoosh', at='top')])
# 14 and land in the crater at Dusty Divot.
S(cue='and land', loc='b2_crater', camera=dict(move='push', focus=[0.45, 0.6]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.4, y=0.84, scale=0.9, z='fg', action='fall', mood='shocked', air=[dict(at=0, h=0.75), dict(at='crater', h=0.0, ease='linear')], keys=[dict(cue='crater', action='idle', mood='sad')])],
  fx=[dict(type='blast', at='crater', x=0.4, y=0.84, r=60, z='fg', shake=30)], sfx=[dict(type='boom', at='crater')])
# 15 The ground is covered in glowing purple rocks.
S(cue='The ground', loc='b2_crater', camera=dict(move='push', amount=1.2, focus=[0.5, 0.7]), transition='cut',
  props=[dict(type='hoprock', x=0.2, y=0.98, scale=2.2, z='near', seed=1), dict(type='hoprock', x=0.82, y=0.95, scale=1.7, z='near', seed=4)],
  characters=[dict(id='hero', cast='hero', x=0.48, y=0.9, scale=1.0, z='fg', mood='neutral', lookAt='down', keys=[dict(cue='glowing', mood='happy')])], sfx=[dict(type='ting', at='glowing')])
# 16 Hop Rocks.   17 You crush one.   18 Gravity? Gone.
S(cue='Hop', loc='b2_crater', camera=dict(move='push', focus=[0.5, 0.42]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.44, y=feet(2.3, 0.4), scale=2.3, z='fg', action='hold', prop='hoprock', mood='smug', lookAt='camera')], sfx=[dict(type='ting', at='Hop')])
S(cue='You crush', loc='b2_crater', camera=dict(move='punch', amount=0.7, focus=[0.56, 0.4]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.44, y=feet(2.3, 0.44), scale=2.3, z='fg', action='crush', mood='determined', lookAt='right', keys=[dict(cue='one', mood='happy')])],
  fx=[dict(type='burst', at='crush', x=0.62, y=0.3, z='fg', dur=0.8)], sfx=[dict(type='pop', at='crush'), dict(type='sting', at='one', gain=0.5)])
S(cue='Gravity', loc='b2_crater', camera=dict(move='tilt_up', amount=1.0, focus=[0.5, 0.5]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=0.9, scale=1.0, z='fg', action='float', mood='shocked', air=[dict(at=0, h=0.0), dict(at='You', h=0.34)], keys=[dict(cue='Gone', mood='happy')])],
  sfx=[dict(type='boing', at='Gravity', gain=0.6)])
# 19 You float across the map like a confused astronaut.
S(cue='You float', loc='b_sky', camera=dict(move='drift', amount=1.0, focus=[0.5, 0.5]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.3, y=0.66, scale=1.2, z='fg', action='float', mood='worried', move=mv(x=0.7, y=0.6, f=0, to='Then'), keys=[dict(cue='confused', lookAt='left'), dict(cue='astronaut', lookAt='camera')])],
  sfx=[dict(type='whoosh', at='float', gain=0.4)])
# 20 Then the storm closes in.   21 Health dropping.
S(cue='Then the', loc='b2_field', camera=dict(move='push', focus=[0.5, 0.6]), transition='whip',
  characters=[dict(id='hero', cast='hero', x=0.66, y=0.9, scale=0.75, z='fg', flip=True, action='run', mood='scared', move=mv(x=0.28, f=0.3, to='Health'))],
  fx=[dict(type='storm', at=0, z='mid', x0=1.0, x1=0.55, dur=1.8)], sfx=[dict(type='drums', at='storm', gain=0.7)])
S(cue='Health', loc='b2_field', camera=dict(move='push', amount=1.2, focus=[0.5, 0.42]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=feet(2.1, 0.42), scale=2.1, z='fg', mood='worried', lookAt='down', keys=[dict(cue='dropping', mood='sad')])],
  fx=[dict(type='storm_tint', at=0), dict(type='hud', at=0, to=0.22, dur=1.0, **{'from': 0.7})], sfx=[dict(type='gulp', at='dropping')])
# 22 Someone at Risky Reels is dancing at you.
S(cue='Someone', loc='b2_drivein', camera=dict(move='push', amount=1.4, focus=[0.72, 0.6]), transition='cut',
  characters=[dict(id='dancer', cast='dancer', x=0.82, y=0.618, scale=0.26, z='mid', action='dance', mood='happy', lookAt='camera'),
              dict(id='hero', cast='hero', x=0.2, y=feet(1.9, 0.5), scale=1.9, z='fg', mood='angry', lookAt='dancer')],
  sfx=[dict(type='tada', at='dancing', gain=0.5)])
# 23 Final circle. One player left.   24 He has a Bolt-Action Sniper.
S(cue='Final', loc='b2_field', camera=dict(move='pull', focus=[0.6, 0.55]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.24, y=0.94, scale=0.9, z='fg', mood='determined', lookAt='sniper'),
              dict(id='sniper', cast='sniper', x=0.72, y=0.505, scale=0.12, z='far', flip=True, mood='smug', lookAt='hero')],
  fx=[dict(type='storm', at=0, z='mid', x0=0.95, x1=0.88, dur=3), dict(type='glint', at='One', x=0.705, y=0.48, z='far')], sfx=[dict(type='drums', at='Final', gain=0.6), dict(type='ting', at='One')])
S(cue='He has', loc='b2_field', camera=dict(move='push', focus=[0.58, 0.42]), transition='cut',
  characters=[dict(id='sniper', cast='sniper', x=0.62, y=feet(1.9, 0.42), scale=1.9, z='fg', flip=True, action='aim', prop='sniper', mood='smug', lookAt='left')],
  fx=[dict(type='glint', at='Sniper', x=0.3, y=0.44, z='fg')], sfx=[dict(type='ting', at='Sniper')])
# 25 You have a shotgun... and one last Hop Rock.   26 You crush it. You jump.   27 He misses.   28 You don't.
S(cue='You have', loc='b2_field', camera=dict(move='push', focus=[0.45, 0.42]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.42, y=feet(2.1, 0.42), scale=2.1, z='fg', action='hold', prop='shotgun', mood='determined', lookAt='right', keys=[dict(cue='and one', prop='hoprock', mood='smug', lookAt='camera')])],
  sfx=[dict(type='knock', at='shotgun', gain=0.6), dict(type='ting', at='Hop')])
S(cue='You crush', loc='b2_field', camera=dict(move='tilt_up', amount=0.8, focus=[0.5, 0.5]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.46, y=0.94, scale=1.1, z='fg', action='crush', mood='determined', air=[dict(at=0, h=0), dict(at='jump', h=0), dict(at=1.65, h=0.36)], keys=[dict(cue='jump', action='jump', mood='happy')])],
  fx=[dict(type='burst', at='crush', x=0.54, y=0.52, z='fg')], sfx=[dict(type='pop', at='crush'), dict(type='boing', at='jump')])
S(cue='He misses', loc='b2_field', camera=dict(move='push', focus=[0.5, 0.45]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.45, y=0.7, scale=1.2, z='fg', action='float', mood='smug', air=[dict(at=0, h=0.2)], lookAt='right')],
  fx=[dict(type='tracer', at='misses', z='fg', dur=0.22, **{'from': [1.1, 0.55], 'to': [-0.1, 0.66]})], sfx=[dict(type='whoosh', at='misses')])
S(cue="You don't", loc='b2_field', camera=dict(move='push', focus=[0.6, 0.55]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.2, y=feet(1.5, 0.52), scale=1.5, z='fg', action='aim', prop='shotgun', mood='determined', lookAt='sniper'),
              dict(id='sniper', cast='sniper', x=0.74, y=0.62, scale=0.5, z='mid', flip=True, action='aim', prop='sniper', mood='smug', lookAt='hero', keys=[dict(cue="don't", mood='shocked')])],
  fx=[dict(type='flash', at="don't", dur=0.18, amount=0.6), dict(type='blast', at="don't", x=0.74, y=0.62, r=120, z='mid', shake=28)], sfx=[dict(type='boom', at="don't")])
# 29 Victory Royale.
S(cue='Victory', loc='b2_field', camera=dict(move='push', focus=[0.5, 0.45]), transition='zoom',
  characters=[dict(id='hero', cast='hero', x=0.5, y=feet(1.9, 0.52), scale=1.9, z='fg', action='cheer', mood='happy', lookAt='camera', talk=['Victory', 'Then'])],
  fx=[dict(type='confetti', at='Victory'), dict(type='logo', at='Victory', img='props/logo_victory.png', text='VICTORY|ROYALE', size=140, x=0.5, y=0.2, w=0.86)], sfx=[dict(type='tada', at='Victory')])
# 30 Then you blink... and you're back in the lobby.   31 Ready up?
S(cue='Then you', loc='b_lobby', camera=dict(move='push', focus=[0.5, 0.6]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=0.76, scale=0.75, z='mid', mood='shocked', lookAt='left', keys=[dict(cue='blink', mood='neutral', lookAt='camera'), dict(cue='lobby', mood='happy', lookAt='right')])],
  sfx=[dict(type='ting', at='blink')])
S(cue='Ready', loc='b_lobby', camera=dict(move='push', amount=1.2, focus=[0.5, 0.4]), transition='cut',
  characters=[dict(id='hero', cast='hero', x=0.5, y=feet(2.2, 0.4), scale=2.2, z='fg', mood='smug', lookAt='camera', action='wave', talk=['Ready', 3])],
  sfx=[dict(type='pop', at='up')])

S_ = dict(title='Teleported into Fortnite (Chapter 1, Season 4)', fps=60, charStyle='rc', sprites='props',
  features=dict(depth=True, motionBlur=True, rigV2=True, lipSync=True, crowdFX=True), motion_blur=dict(samples=8, shutter=0.5),
  caption_y=0.68, caption_case='lower', caption_size=78, caption_swaps={'ninety-nine': '99'}, grade='brightness(1.14) saturate(1.32) contrast(1.05)', thumbnail_cue='Victory',
  music=dict(style='bouncy', bpm=120, level_db=-20),
  cast=dict(hero=dict(costume='hoodie_green', hat='beanie', mood='neutral', hair='#4a2f1e', hatSpring=dict(freq=3.0, damping=0.18)),
            guy=dict(costume='jacket_purple', hat='cap', facial='moustache', mood='smug'),
            sniper=dict(costume='ghillie', hat='hood_leafy', mood='smug'),
            dancer=dict(costume='tracksuit_yellow', hat='bandana', mood='happy'),
            p1=dict(costume='tee_red', hat='cap', mood='neutral'), p2=dict(costume='tee_blue', hat='headset', mood='neutral', hair='#2a1a10'),
            p3=dict(costume='vest_orange', hat='beanie', mood='neutral'), p4=dict(costume='jacket_purple', hat='bandana', mood='neutral')),
  scenes=sc)
json.dump(S_, open(P, 'w'), indent=1); print(len(sc), 'scenes')
