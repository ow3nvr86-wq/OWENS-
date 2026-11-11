"""Narration for "Rome Never Fell in 476": synthesises the script line by line with a local voice
(Kokoro-82M, Apache-2.0; American voice am_michael with the American phoneme set) and lays the lines end to end
with the pauses the brief asks for ("That's wrong." and "Then it cracked." get a short, punchy beat).

  $KOKORO_PY tools/voiceover.py            -> audio/narration.wav, build/vo_lines.json
  then: tools/words.py (offline speech recogniser) -> build/words.json, word-level times for captions and cues
"""
import argparse
import json
import os
import re
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
DURATION = 32.0
START = 0.12          # the voice starts almost at once: the hook must land inside the first second
SCALE = 0.84          # brisk, confident delivery (about 1.19x Kokoro's natural pace)

# (caption text, text the voice reads, pause after the line in seconds)
LINES = [
    ("You were taught Rome fell in 476.", "You were taught Rome fell in four seventy-six.", 0.18),
    ("That's wrong.", "That's wrong.", 0.50),
    ("At its peak, Rome ruled from Britain to Egypt:", "At its peak, Rome ruled from Britain to Egypt:", 0.16),
    ("three continents, and maybe one in four people on Earth.", "three continents, and maybe one in four people on Earth.", 0.34),
    ("In 117 AD, under Emperor Trajan, it hit its biggest size ever.", "In one seventeen AD, under Emperor Trajan, it hit its biggest size ever.", 0.34),
    ("Then it cracked.", "Then it cracked.", 0.46),
    ("Civil wars.", "Civil wars.", 0.14),
    ("Plague.", "Plague.", 0.14),
    ("Invaders on every border.", "Invaders on every border.", 0.22),
    ("So Rome split in two.", "So Rome split in two.", 0.40),
    ("In 476, the West collapsed.", "In four seventy-six, the West collapsed.", 0.16),
    ("But the East kept going.", "But the East kept going.", 0.36),
    ("For almost a thousand more years, until 1453.", "For almost a thousand more years, until fourteen fifty-three.", 0.34),
    ("So when did Rome really fall?", "So when did Rome really fall?", 0.0),
]


class KokoroVoice:
    def __init__(self, model_dir, name):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(os.path.join(model_dir, 'kokoro-v1.0.onnx'), os.path.join(model_dir, 'voices-v1.0.bin'))
        self.name = name
        self.lang = 'en-gb' if name[:1] == 'b' else 'en-us'

    # pronunciations the voice gets wrong, fixed in its phonemes before synthesis
    FIXES = [('pˈɛntaɡən', 'pˈɛntəɡən'),           # 'Pentagon' with a schwa: PEN-tuh-gon
             ('ᵻlˈɑːn', 'ˈiːlɑːn')]                 # 'Elon' as EE-lon, not ih-LON

    # Kokoro's American voices were trained on misaki's American phoneme set, but kokoro-onnx hands them raw
    # eSpeak IPA, which is partly British (non-rhotic 'ɜː' in learned/Earth/person, long marks) and splits
    # diphthongs. This is the conversion misaki itself applies to eSpeak output for American English.
    US = [('ʔn', 'tᵊn'), ('ʔ', 't'), ('aɪ', 'I'), ('aʊ', 'W'), ('eɪ', 'A'), ('ɔɪ', 'Y'), ('oʊ', 'O'),
          ('dʒ', 'ʤ'), ('tʃ', 'ʧ'), ('ɐ', 'ə'), ('ɚɹ', 'əɹ'), ('ɚ', 'əɹ'), ('ɜːɹ', 'ɜɹ'), ('ɜː', 'ɜɹ'), ('ɪə', 'iə'),
          ('r', 'ɹ'), ('ː', '')]

    # fixes in the American set, applied after the conversion
    POST = [('tɹˈæʤən', 'tɹˈAʤən'),            # 'Trajan' as TRAY-jun
            ('sˈɛvəntˌin', 'sˌɛvəntˈin')]        # 'one seventeen' with the stress on -TEEN

    def phonemes(self, text):
        ph = self.k.tokenizer.phonemize(text, self.lang)
        for bad, good in self.FIXES:
            ph = ph.replace(bad, good)
        if self.lang == 'en-us':
            for a, b in self.US:
                ph = ph.replace(a, b)
        for a, b in self.POST:
            ph = ph.replace(a, b)
        return ' '.join(ph.split())

    @staticmethod
    def tighten(a, sr, n_sentence_breaks, short=0.16, long=0.30, thr=0.004):
        """Shorten the silences inside a line: commas and hesitations to `short`, the breaks between sentences to
        `long`. Only true silence is cut (with short crossfades), so no word is touched."""
        e = np.convolve(np.abs(a), np.ones(int(0.01 * sr)) / (0.01 * sr), 'same')
        q = e < thr
        runs, i = [], 0
        while i < len(q):
            if q[i]:
                j = i
                while j < len(q) and q[j]:
                    j += 1
                if i > 0 and j < len(q) and (j - i) / sr > short:
                    runs.append((i, j))
                i = j
            else:
                i += 1
        keep_long = set(sorted(range(len(runs)), key=lambda k: runs[k][1] - runs[k][0], reverse=True)[:n_sentence_breaks])
        out, last = [], 0
        for k, (i, j) in enumerate(runs):
            target = int((long if k in keep_long else short) * sr)
            if j - i <= target:
                continue
            mid = i + target // 2
            out.append(a[last:mid])
            last = j - (target - target // 2)
        out.append(a[last:])
        return np.concatenate(out)

    def synth(self, text, scale):
        ph = self.phonemes(text)
        # the whole line in ONE pass of the model, so the intonation runs on across commas and full stops
        # (the library would otherwise synthesise each sentence separately and glue them together)
        try:
            a, _ = self.k._create_batch(ph, self.k.get_voice_style(self.name), 1.0 / scale, True)
            sr = 24000
        except Exception:
            a, sr = self.k.create(ph, voice=self.name, speed=1.0 / scale, lang=self.lang, is_phonemes=True,
                                  sentence_pause=0.14, clause_pause=0.05)
        a = np.asarray(a, np.float32)
        import re as _re
        a = self.tighten(a, sr, len(_re.findall(r'[.?!](?=\s)', text.strip())))
        # trim the lead-in and tail generously: soft first sounds ('th' in 'The', 'h' in 'He') sit below the
        # loudness of the vowel after them, and clipping them makes the line start sound chopped
        nz = np.nonzero(np.abs(a) > 0.003)[0]
        a = a[max(nz[0] - int(0.05 * sr), 0): nz[-1] + int(0.12 * sr)].copy()
        f = int(0.012 * sr)
        a[:f] *= np.linspace(0, 1, f)
        a[-f:] *= np.linspace(1, 0, f)
        n = int(len(a) * SR / sr)
        return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)


def write_wav(path, a):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', default='am_michael')
    ap.add_argument('--scale', type=float, default=SCALE)
    ap.add_argument('--kokoro-dir', default=os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro'))
    args = ap.parse_args()
    v = KokoroVoice(args.kokoro_dir, args.voice)
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True)
    track = np.zeros(int(DURATION * SR), np.float32)
    t, out = START, []
    for i, (cap, tts, pause) in enumerate(LINES):
        a = v.synth(tts, args.scale)
        s0 = int(t * SR)
        track[s0:s0 + len(a)] += a[:max(0, len(track) - s0)]
        out.append({'i': i, 'text': cap, 'tts': tts, 'phonemes': v.phonemes(tts), 'start': round(t, 3), 'end': round(t + len(a) / SR, 3)})
        print(f'{t:6.2f}-{t + len(a) / SR:6.2f}  {cap}')
        t += len(a) / SR + pause
    print(f'narration ends at {t:.2f} s of {DURATION}')
    track *= 0.89 / max(np.abs(track).max(), 1e-6)
    write_wav(os.path.join(ROOT, 'audio', 'narration.wav'), track)
    with open(os.path.join(ROOT, 'build', 'vo_lines.json'), 'w') as fh:
        json.dump({'voice': f'Kokoro-82M {args.voice}', 'scale': args.scale, 'lines': out}, fh, indent=1)


if __name__ == '__main__':
    main()
