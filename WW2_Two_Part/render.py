"""Render a part of the WW2 two-parter: every frame drawn in 2D with pycairo (one continuous map shot), finished with
numpy, titled and captioned with PIL, encoded with ffmpeg.

  python render.py part1 --stills 0.5,3,5.5     # look-dev stills -> part1/build/stills/
  python render.py part1                        # -> part1/final_video.mp4 (needs part1/audio/mix_with_voice.wav)
  python render.py part1 --no-voice             # music and sound only, no captions -> part1/final_video_no_voice.mp4
Options: --workers N (default 4), --no-captions.
"""
import argparse
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))
PART = next((a for a in sys.argv[1:] if a.startswith('part')), 'part1')
os.environ['WW2_PART'] = PART

import cairo  # noqa: E402
import numpy as np  # noqa: E402

from core import W, H, FPS, DURATION, NFRAMES, PART_DIR, new_surface, surf_array  # noqa: E402
import post  # noqa: E402
import text  # noqa: E402

scenes = __import__(PART)


def frame_rgb(t, os_, captions=True):
    s = new_surface(int(W * os_), int(H * os_))
    ctx = cairo.Context(s)
    look = scenes.scene_main(ctx, t, os_) or {}
    rgb = np.ascontiguousarray(post.finish(surf_array(s), os_, t, look))
    text.draw_titles(rgb, t, os_)
    if captions:
        text.draw_captions(rgb, t, os_)
    return rgb


def _render_chunk(args):
    f0, f1, os_, path, captions = args
    w, h = int(W * os_), int(H * os_)
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        pr.stdin.write(frame_rgb(f / FPS, os_, captions).tobytes())
    pr.stdin.close()
    pr.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('part', nargs='?', default='part1')
    ap.add_argument('--stills', default=None)
    ap.add_argument('--no-voice', action='store_true')
    ap.add_argument('--no-captions', action='store_true')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--scale', type=float, default=None)
    args = ap.parse_args()
    os_ = args.scale or (0.5 if args.stills else 1.0)
    captions = not (args.no_captions or args.no_voice)
    if args.stills:
        from PIL import Image
        d = os.path.join(PART_DIR, 'build', 'stills')
        os.makedirs(d, exist_ok=True)
        for s in args.stills.split(','):
            Image.fromarray(frame_rgb(float(s), os_, captions)).save(os.path.join(d, f'still_{float(s):06.2f}.png'))
        return
    seg = os.path.join(PART_DIR, 'build', 'segments')
    os.makedirs(seg, exist_ok=True)
    n = max(1, args.workers)
    per = math.ceil(NFRAMES / n)
    tag = 'nv' if args.no_voice else 'f'
    jobs = [(i * per, min(NFRAMES, (i + 1) * per), os_, os.path.join(seg, f'{tag}_{i:02d}.mp4'), captions) for i in range(n) if i * per < NFRAMES]
    t0 = time.time()
    with Pool(len(jobs)) as pool:
        paths = pool.map(_render_chunk, jobs)
    print(f'rendered {NFRAMES} frames in {time.time() - t0:.0f} s')
    lst = os.path.join(seg, f'{tag}_list.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in paths))
    out = os.path.join(PART_DIR, 'final_video_no_voice.mp4' if args.no_voice else 'final_video.mp4')
    audio = os.path.join(PART_DIR, 'audio', 'mix_no_voice.wav' if args.no_voice else 'mix_with_voice.wav')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst]
    if os.path.exists(audio):
        cmd += ['-i', audio]
    cmd += ['-vf', 'scale=1080:1920:flags=lanczos' if os_ != 1.0 else 'null', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19',
            '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p', '-r', str(FPS)]
    if os.path.exists(audio):
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest']
    subprocess.run(cmd + ['-movflags', '+faststart', out], check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
