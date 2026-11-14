"""Narration for the Maple Town story (Kokoro-82M am_michael, Apache-2.0).  $KOKORO_PY vo.py -> audio/narration.wav, build/lines.json"""
import json, os, re, wave
import numpy as np
ROOT = os.path.dirname(os.path.abspath(__file__))
SR = 48000
LINES = [
    ("Everyone in Maple Town knew one rule.", 0.22), ("Never talk to the kid in the grey hoodie.", 0.4),
    ("He moved into the empty house on Oak Street.", 0.25), ("He never spoke.", 0.22), ("He just walked the town, every night, alone.", 0.4),
    ("People said he was a hacker.", 0.2), ("People said he was cursed.", 0.4),
    ("Then, one night, the bank alarm went off.", 0.22), ("Robbers.", 0.25), ("They took everything, and blocked the only road out.", 0.4),
    ("Nobody moved.", 0.3), ("Except him.", 0.4),
    ("He walked straight up to them, and typed one word.", 0.55),
    ("The robbers froze.", 0.25), ("Then they dropped the money, and ran.", 0.45),
    ("Turns out the quiet kid was not a hacker.", 0.25), ("He was the owner of the game.", 0.5),
    ("And he had been watching how we treat new players.", 0.0),
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

if __name__ == '__main__':
    v = KokoroVoice(os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro'), 'am_michael')
    out, t, meta = [np.zeros(int(0.1 * SR), np.float32)], 0.1, []
    for text, pause in LINES:
        a = v.synth(text, 0.84)
        meta.append({'text': text, 'start': round(t, 3), 'end': round(t + len(a) / SR, 3)})
        out += [a, np.zeros(int(pause * SR), np.float32)]
        t += len(a) / SR + pause
    y = np.concatenate(out); y *= 0.89 / np.abs(y).max()
    os.makedirs(os.path.join(ROOT, 'audio'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    write_wav(os.path.join(ROOT, 'audio', 'narration.wav'), y)
    json.dump(meta, open(os.path.join(ROOT, 'build', 'lines.json'), 'w'), indent=1)
    for m in meta: print(m['start'], m['end'], m['text'])
    print('total', round(len(y) / SR, 2))
