"""Synthesise the voiceover line by line with Piper TTS and build the master timeline.

Usage:  python scripts/voiceover.py --model /path/to/en_US-ljspeech-high.onnx

Writes audio/vo/Lxx.wav, audio/vo/voiceover.wav and build/timeline.json.
Every later stage (Blender shot lengths, captions, SFX, music) reads timeline.json,
so the animation always matches the real narration.
"""
import argparse, json, os, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 22050


def synth(voice, cfg, text, path):
    with wave.open(path, 'wb') as w:
        voice.synthesize_wav(text, w, syn_config=cfg)
    with wave.open(path, 'rb') as r:
        sr = r.getframerate()
        data = np.frombuffer(r.readframes(r.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    # trim leading/trailing near-silence so timing is tight
    idx = np.where(np.abs(data) > 0.01)[0]
    if len(idx):
        a, b = max(0, idx[0] - int(0.02 * sr)), min(len(data), idx[-1] + int(0.06 * sr))
        data = data[a:b]
    return data, sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--length-scale', type=float, default=0.77)
    args = ap.parse_args()
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(args.model)
    cfg = SynthesisConfig(length_scale=args.length_scale, noise_scale=0.6, noise_w_scale=0.75)
    spec = json.load(open(os.path.join(ROOT, 'scripts', 'script.json')))
    vo_dir = os.path.join(ROOT, 'audio', 'vo'); os.makedirs(vo_dir, exist_ok=True)
    t = spec['lead_in']; pieces = [np.zeros(int(t * SR), np.float32)]; lines = []
    for ln in spec['lines']:
        data, sr = synth(voice, cfg, ln['text'], os.path.join(vo_dir, ln['id'] + '_raw.wav'))
        assert sr == SR, sr
        os.remove(os.path.join(vo_dir, ln['id'] + '_raw.wav'))
        write_wav(os.path.join(vo_dir, ln['id'] + '.wav'), data)
        dur = len(data) / SR
        lines.append({**ln, 'start': round(t, 3), 'end': round(t + dur, 3),
                      'caption': spec['captions'].get(ln['id'], ln['text'])})
        pieces += [data, np.zeros(int(ln['pause'] * SR), np.float32)]
        t += dur + ln['pause']
    full = np.concatenate(pieces)
    write_wav(os.path.join(vo_dir, 'voiceover.wav'), full)
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    json.dump({'fps': 30, 'duration': round(len(full) / SR, 3), 'lines': lines},
              open(os.path.join(ROOT, 'build', 'timeline.json'), 'w'), indent=1)
    for l in lines:
        print(f"{l['id']} {l['start']:6.2f}-{l['end']:6.2f}  {l['text']}")
    print('TOTAL', round(len(full) / SR, 2), 's')


def write_wav(path, data):
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    main()
