"""Part 2 narration with the channel's narrator George (Kokoro-82M, voice bm_george, Apache-2.0): each line is
synthesised in one pass and the lines are laid end to end with short pauses.

  $KOKORO_PY tools/george_vo.py part2 [--scale 0.80]   -> part2/voiceover/part2_george.wav
The result is then treated exactly like a supplied recording (tools/voice_prep.py, tools/words.py).
"""
import argparse
import os
import re
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
LINES = {'part2': [
    ("Part two.", 0.30),
    ("Hitler's empire looked unstoppable.", 0.28),
    ("Then, in one frozen city, it began to break.", 0.38),
    ("Stalingrad, nineteen forty-three.", 0.22),
    ("An entire German army surrenders.", 0.40),
    ("America fights back across the Pacific.", 0.40),
    ("June sixth, nineteen forty-four.", 0.20),
    ("D-Day.", 0.28),
    ("About a hundred and fifty-six thousand Allied troops land in Normandy in a single day.", 0.40),
    ("Germany is crushed from both sides.", 0.30),
    ("In May nineteen forty-five, with Soviet troops in Berlin, it surrenders.", 0.40),
    ("In August, two atomic bombs fall on Japan.", 0.32),
    ("By September, the war is over.", 0.40),
    ("An estimated seventy to eighty-five million people died.", 0.0),
]}


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




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('part', nargs='?', default='part2')
    ap.add_argument('--voice', default='bm_george')
    ap.add_argument('--scale', type=float, default=0.80)
    ap.add_argument('--kokoro-dir', default=os.environ.get('KOKORO_DIR', '/opt/shorts/kokoro'))
    args = ap.parse_args()
    v = KokoroVoice(args.kokoro_dir, args.voice)
    out, t = [np.zeros(int(0.08 * SR), np.float32)], 0.08
    for text, pause in LINES[args.part]:
        a = v.synth(text, args.scale)
        print(f'{t:6.2f}-{t + len(a) / SR:6.2f}  {text}\n          {v.phonemes(text)}')
        out += [a, np.zeros(int(pause * SR), np.float32)]
        t += len(a) / SR + pause
    y = np.concatenate(out)
    y *= 0.89 / max(np.abs(y).max(), 1e-6)
    d = os.path.join(ROOT, args.part, 'voiceover')
    os.makedirs(d, exist_ok=True)
    with wave.open(os.path.join(d, f'{args.part}_george.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f'total {len(y) / SR:.2f} s')


if __name__ == '__main__':
    main()
