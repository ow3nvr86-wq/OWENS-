"""Soundtrack for the Funny Town story: the narration over a light synthesised bed and effects (numpy; no samples).
  $SHORTS_PY mix.py -> audio/mix_with_voice.wav"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(ROOT, '..', 'WW2_Two_Part', 'audio.py')).read()
head = src[:src.index('def build_part1():')].replace("PDIR = os.path.join(ROOT, PART)", "PDIR = ROOT")
tail = src[src.index('def read_wav(path):'):src.index('def main():')]
g = {'__file__': os.path.join(ROOT, 'mix.py'), '__name__': 'funny'}
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
    end = L[12]['start']
    t, k = 0.0, 0
    while t < DUR - 1.0:                     # bouncy, cheerful pulse
        lv = 0.9 if t < end else 0.5
        if k % 4 == 0:
            place(mus, war_drum(k, 70), t, 0.35 * lv)
        place(mus, tick(k), t, 0.25 * lv, pan=0.3 if k % 2 else -0.3)
        t += 60 / 112.0 / 2
        k += 1
    for a, b, f in ((0, L[7]['start'], 130.8), (L[7]['start'], L[10]['start'], 98.0), (L[10]['start'], DUR, 146.8)):
        d = b - a
        place(mus, drone(f, d, int(a) + 1, 420) * env(tt(d), [(0, 0), (0.3, 1), (d - 0.3, 1), (d, 0)]), a, 0.3)
    place(sfx, whoosh(0.7, 2, 300, 2500, up=True), 0.0, 0.35)
    place(sfx, sparkle(1.4, 12, 30), at('dog'), 0.5)
    place(sfx, stamp_hit(3), at('dog'), 0.5)
    place(sfx, blip(10, 660), at('biscuit'), 0.5)
    place(sfx, blip(11, 880), at('sad'), 0.4)
    place(sfx, whoosh(0.8, 5, 400, 3500), at('banned') - 0.5, 0.5)
    place(sfx, stamp_hit(4), at('banned'), 0.7)
    place(sfx, blip(12, 300), at('obviously'), 0.5)
    place(sfx, blip(13, 740), at('snacks'), 0.4)
    place(sfx, stamp_hit(5), at('robber'), 0.5)
    place(sfx, stone_crack(6, 0.5), at('bank'), 0.3)
    for i in range(4):
        place(sfx, stomp(20 + i), at('walked') + i * 0.35, 0.25)
    place(sfx, stamp_hit(7), at('stared'), 0.5)
    place(sfx, blip(14, 520), at('begged'), 0.4)
    for i in range(3):
        place(sfx, blip(30 + i, 600 + 120 * i), at('belly') + i * 0.12, 0.4)
    place(sfx, sparkle(1.6, 15, 30), at('zero'), 0.5)
    place(sfx, boom(1.8, 60, 28, 9), at('zero'), 0.5)
    place(mus, brass([130.8, 196.0, 261.6, 329.6], 1.6, 13), at('zero'), 0.4)
    place(sfx, stamp_hit(8), at('cat'), 0.6)
    place(sfx, whoosh(0.6, 14, 400, 3000, up=False), end + 0.2, 0.4)
    for i in range(3):
        place(sfx, blip(40 + i, 400 - 60 * i), end + 1.4 + i * 0.15, 0.4)
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
