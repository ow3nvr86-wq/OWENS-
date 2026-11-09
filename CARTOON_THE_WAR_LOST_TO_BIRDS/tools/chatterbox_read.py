"""Chatterbox (Resemble AI, MIT licence) reads the script line by line in the timbre of a reference clip.
Run with /opt/shorts/chatterbox-venv/bin/python: tools/chatterbox_read.py [only-these-names...]"""
import os, sys, time
import numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_common import HERE, LINES, pause_after, trim, write_wav, finish
UPBEAT = [l.strip() for l in open(os.path.join(HERE, 'script_read_upbeat.txt')) if l.strip()]
from chatterbox.tts import ChatterboxTTS

S = os.path.join(HERE, 'audio', 'voice_samples')
R = os.path.join(S, 'refs')
# name, reference clip (None = Chatterbox's own voice), exaggeration, cfg_weight[, temperature, lines]
CONFIG = [
    ('05b_gravel_upbeat',         'am_fenrir_upbeat', 0.85, 0.50, 0.80, UPBEAT),
    ('05c_gravel_extra_upbeat',   'am_fenrir_upbeat', 1.05, 0.55, 0.85, UPBEAT),
    ('02_george_expressive',      'bm_george',  0.55, 0.45),
    ('03_deep_documentary_us',    'am_onyx',    0.50, 0.40),
    ('04_warm_storyteller_us',    'am_michael', 0.55, 0.45),
    ('05_gravel_dramatic_us',     'am_fenrir',  0.65, 0.35),
    ('06_chatterbox_own_voice',   None,         0.55, 0.45),
    ('07_upbeat_social_female',   'af_bella',   0.75, 0.50),
    ('08_warm_female_us',         'af_heart',   0.55, 0.45),
    ('09_british_female',         'bf_emma',    0.55, 0.45),
    ('10_young_british_male',     'bm_fable',   0.60, 0.45),
]
only = sys.argv[1:]
m = ChatterboxTTS.from_pretrained(device='cpu')
for name, ref, ex, cfg, *rest in CONFIG:
    temp, lines = (rest + [0.75, LINES][len(rest):])[:2] if rest else (0.75, LINES)
    if only and not any(o in name for o in only):
        continue
    t0 = time.time()
    torch.manual_seed(7)
    m.prepare_conditionals(os.path.join(R, ref + '.wav'), exaggeration=ex) if ref else None
    parts = [np.zeros(2400, np.float32)]
    for i, line in enumerate(lines):
        w = m.generate(line, exaggeration=ex, cfg_weight=cfg, temperature=temp).squeeze(0).numpy().astype(np.float32)
        parts += [trim(w, m.sr), np.zeros(int(pause_after(i) * m.sr), np.float32)]
    a = np.concatenate(parts + [np.zeros(int(0.3 * m.sr), np.float32)])
    tmp = os.path.join(S, name + '.raw.wav')
    write_wav(tmp, a / np.abs(a).max() * 0.9, m.sr)
    finish(tmp, os.path.join(S, name + '.wav')); os.remove(tmp)
    print('%-28s %.2f s  (%.0f s to make)' % (name, len(a) / m.sr, time.time() - t0), flush=True)
