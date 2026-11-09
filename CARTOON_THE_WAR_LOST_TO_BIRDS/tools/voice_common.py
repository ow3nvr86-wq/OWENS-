"""Shared bits for the voice tools: the script lines, the pause plan and the 'produced narrator' finishing chain."""
import os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINES = [l.strip() for l in open(os.path.join(HERE, 'script.txt')) if l.strip()]


def pause_after(i):
    """Pause after script line i. Varied a little so the read doesn't tick like a metronome."""
    return [0.30, 0.34, 0.30, 0.26, 0.32, 0.36, 0.0][i] if i < 7 else 0.3


def trim(a, sr, thr=0.012, pad=0.035):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - int(pad * sr)): idx[-1] + int(pad * sr)]


def write_wav(path, a, sr):
    import wave
    pcm = (np.clip(a, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


# Gentle "voiceover booth" finish: rumble cut, a touch of chest warmth, presence for clarity on phone speakers,
# soft de-ess, light 2.5:1 compression, a very short room so it isn't bone-dry, then -16 LUFS for comparison.
FINISH = ('highpass=f=75,equalizer=f=180:t=q:w=1.0:g=1.5,equalizer=f=3200:t=q:w=1.2:g=2.0,'
          'deesser=i=0.35,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,'
          'aecho=0.9:0.9:14|23:0.05|0.03,loudnorm=I=-16:TP=-1.5:LRA=9')


def finish(src, dst):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', FINISH, '-ar', '48000', '-ac', '1', dst],
                   check=True)
