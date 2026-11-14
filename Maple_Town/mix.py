"""Soundtrack for the Maple Town story: the narration over a light synthesised bed and effects (numpy; no samples).
  $SHORTS_PY mix.py -> audio/mix_with_voice.wav"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(ROOT, '..', 'WW2_Two_Part', 'audio.py')).read()
head = src[:src.index('def build_part1():')].replace("PDIR = os.path.join(ROOT, PART)", "PDIR = ROOT")
tail = src[src.index('def read_wav(path):'):src.index('def main():')]
g = {'__file__': os.path.join(ROOT, 'mix.py'), '__name__': 'maple'}
exec(compile(head + tail, 'audio_helpers', 'exec'), g)
globals().update({k: v for k, v in g.items() if not k.startswith('__')})
L = json.load(open(os.path.join(ROOT, 'build', 'lines.json')))
W = json.load(open(os.path.join(ROOT, 'build', 'words.json')))['words']


def at(word, n=1):
    k = 0
    for x in W:
        if x['w'].lower().strip('.,') == word:
            k += 1
            if k == n:
                return x['start']
    raise KeyError(word)


def main():
    mus = np.zeros((2, N))
    sfx = np.zeros((2, N))
    night0, rob, word, froze, owner, end = L[7]['start'], at('robbers'), at('word'), at('froze'), at('owner'), L[17]['start']
    # a soft, curious pulse; darker from the robbery; warm at the end
    t, k = 0.0, 0
    while t < DUR - 1.0:
        lv = 0.6 if t < night0 else (1.0 if t < owner else 0.5)
        if k % 4 == 0:
            place(mus, war_drum(k, 58), t, 0.5 * lv)
        place(mus, tick(k), t, 0.2 * lv, pan=0.3 if k % 2 else -0.3)
        t += 60 / 96.0 / 2
        k += 1
    for a, b, f in ((0, night0, 98.0), (night0, owner, 73.42), (owner, DUR, 110.0)):
        d = b - a
        place(mus, drone(f, d, int(a) + 1, 420) * env(tt(d), [(0, 0), (0.3, 1), (d - 0.3, 1), (d, 0)]), a, 0.34)
    place(mus, choir([220.0, 277.18, 329.63], DUR - end, 5), end, 0.2)
    place(sfx, boom(1.8, 60, 30, 1), 0.0, 0.7)
    place(sfx, whoosh(0.8, 2, 300, 2500, up=False), 0.0, 0.4)
    for i, x in enumerate(('hacker', 'cursed')):
        place(sfx, blip(10 + i, 420 - 60 * i), at(x), 0.4)
    ds = L[10]['start'] - night0
    place(sfx, siren(ds, 3, 600, 900, 0.7) * env(tt(ds), [(0, 0), (0.2, 1), (ds - 0.4, 1), (ds, 0)]), at('alarm'), 0.3)
    place(sfx, stamp_hit(4), rob, 0.9)
    place(sfx, boom(2.0, 55, 26, 5), rob, 0.8)
    place(sfx, stamp_hit(6), at('blocked'), 0.6)
    for i in range(8):
        place(sfx, stomp(20 + i), L[11]['start'] + i * 0.3, 0.3)
    place(sfx, blip(30, 880), word, 0.6)
    place(sfx, stamp_hit(7), word + 0.05, 0.5)
    place(sfx, stone_crack(8, 0.6), froze, 0.5)
    place(sfx, stamp_hit(9), at('dropped'), 0.7)
    place(sfx, whoosh(0.9, 10, 300, 3500), at('ran') - 0.1, 0.7)
    place(sfx, boom(2.6, 60, 26, 11), owner, 1.0)
    place(sfx, sparkle(1.6, 12, 30), owner, 0.4)
    place(mus, brass([110.0, 164.81, 220.0, 277.18], 1.8, 13), owner, 0.5)
    place(sfx, whoosh(0.6, 14, 400, 3000, up=False), end + 0.2, 0.4)
    for i in range(4):
        place(sfx, blip(40 + i, 520 + 80 * i), end + 0.9 + i * 0.12, 0.4)
    vo = read_wav(os.path.join(ROOT, 'audio', 'narration.wav'))
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    e = np.convolve(np.abs(vo), np.ones(int(0.12 * SR)) / (0.12 * SR), mode='same')
    duck = 1 - 0.5 * np.clip(e / (e.max() + 1e-9) * 3.0, 0, 1)
    m = mus / (np.abs(mus).max() + 1e-9)
    s = sfx / (np.abs(sfx).max() + 1e-9)
    vrms = np.sqrt(np.mean(vo[np.abs(vo) > 0.02] ** 2))
    fade = np.interp(np.arange(N) / SR, [0, DUR - 0.6, DUR], [1, 1, 0])
    mix = (m * (0.2 * vrms / np.sqrt(np.mean(m ** 2))) * duck[None, :] + s * 0.4 * (0.6 + 0.4 * duck[None, :])) * fade[None, :] + np.stack([vo, vo])
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    raw = os.path.join(ROOT, 'build', 'mix_raw.wav')
    out = os.path.join(ROOT, 'audio', 'mix_with_voice.wav')
    write_wav(raw, mix)
    loudnorm(raw, out, -13.1)
    trim_to(out)
    print('wrote', out)


main()
