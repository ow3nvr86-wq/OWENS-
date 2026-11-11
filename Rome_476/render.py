"""Render "Rome Never Fell in 476" (32 s, loops): every frame drawn in 2D with pycairo, finished with numpy,
captioned with PIL and encoded with ffmpeg.

  python render.py --stills 0.5,3,5.5          # look-dev stills -> build/stills/
  python render.py --preview                   # 540x960 frames, upscaled -> renders/preview.mp4
  python render.py                             # 1080x1920 -> final_video.mp4 (needs audio/mix_with_voice.wav)
  python render.py --no-voice                  # music and sound only, no captions -> renders/final_video_no_voice.mp4
  python render.py --range 0,6 --out build/s1.mp4   # one section
Options: --workers N (default 4), --no-captions.
"""
import argparse
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import cairo  # noqa: E402

from core import W, H, FPS, DURATION, NFRAMES, PAL, set_c, new_surface, surf_array, clamp, smooth, smoother, ease_out, ease_in, fbm2, ink_shape, hash01  # noqa: E402
import post  # noqa: E402
import text  # noqa: E402
import rome as scenes  # noqa: E402
from core import TIMING  # noqa: E402

# Scenes on the edit timeline (key, start, end) from scene_timing.json; each is drawn by rome.scene_<key>.
# Cuts are hard unless listed: the hook shatters into the map, and the last scene bleeds in as ink.
TIMELINE = [(sc['key'], sc['start'], sc['end'] if sc['key'] != 'end' else DURATION + 0.5) for sc in TIMING['scenes']]
TRANS = {'scale': ('shatter', 0.2), 'end': ('ink', 0.26)}


def bind():
    for i, e in enumerate(TIMELINE):
        if len(e) == 3:
            k, a, b = e
            TIMELINE[i] = (k, a, b, getattr(scenes, 'scene_' + k, None) or placeholder(k))


def placeholder(k):
    def fn(ctx, t, os_):
        set_c(ctx, PAL['parch2'])
        ctx.paint()
        return dict(dark=0.2)
    return fn


def render_scene(fn, t, os_):
    w, h = int(W * os_), int(H * os_)
    s = new_surface(w, h)
    ctx = cairo.Context(s)
    set_c(ctx, PAL['charcoal'])
    ctx.paint()
    look = fn(ctx, t, os_) or {}
    rgb = post.finish(surf_array(s), os_, t, look)
    return rgb


_NOISE = {}


def noise_tex(os_, seed=3, scale=110.0):
    key = (os_, seed)
    if key not in _NOISE:
        w, h = int(W * os_), int(H * os_)
        n = fbm2(h, w, seed, scale=scale * os_, octaves=5)
        _NOISE[key] = n
    return _NOISE[key]


def combine(kind, A, B, u, os_, t):
    """Blend outgoing frame A into incoming frame B; u runs 0 -> 1 across the transition."""
    h, w = A.shape[:2]
    fa = A.astype(np.float32)
    fb = B.astype(np.float32)
    if kind == 'shatter':
        # the cracked frame breaks along its cracks; the shards fly out towards the camera, revealing the map
        k = clamp(u)
        sb = new_surface(w, h)
        c = cairo.Context(sb)
        c.set_source_surface(_arr_surface(fb), 0, 0)
        c.paint()
        if k < 1:
            sa = _arr_surface(fa)
            cells, _ = scenes.shards()
            ix, iy = scenes.IMPACT
            for i, cell in enumerate(cells):
                cx_, cy_ = cell[:, 0].mean(), cell[:, 1].mean()
                dx, dy = cx_ - ix, cy_ - iy
                dist = math.hypot(dx, dy) + 1
                delay = min(0.45, dist / 2600)
                kk = clamp((k - delay * 0.6) / (1 - delay * 0.6))
                e = kk ** 1.6
                vx, vy = dx / dist, dy / dist
                c.save()
                c.scale(os_, os_)
                c.translate(cx_ + vx * 900 * e, cy_ + vy * 900 * e + 500 * e * e)
                c.rotate((hash01(i, 3) - 0.5) * 2.4 * e)
                c.scale(1 + 0.7 * e, 1 + 0.7 * e)
                c.translate(-cx_, -cy_)
                c.new_path()
                c.move_to(*cell[0])
                for q in cell[1:]:
                    c.line_to(*q)
                c.close_path()
                c.clip_preserve()
                c.scale(1 / os_, 1 / os_)
                c.set_source_surface(sa, 0, 0)
                c.paint_with_alpha(1 - smooth(clamp((kk - 0.55) / 0.45)))
                c.scale(os_, os_)
                c.set_source_rgba(0.1, 0.08, 0.06, 0.9 * (1 - kk))
                c.set_line_width(4)
                c.stroke()
                c.restore()
        out = surf_array(sb)[..., [2, 1, 0]].astype(np.uint8)
        return np.ascontiguousarray(out)
    if kind == 'dissolve':
        k = smooth(u)
        return (fa * (1 - k) + fb * k).astype(np.uint8)
    if kind == 'flash':
        # a burst of white light: the outgoing picture burns out, the next one comes up out of the glare
        white = np.array([236, 226, 205], np.float32)
        if u < 0.5:
            k = smooth(u / 0.5)
            return np.clip(fa * (1 - k) + white * k, 0, 255).astype(np.uint8)
        k = smooth((u - 0.5) / 0.5)
        return np.clip(white * (1 - k) + fb * k, 0, 255).astype(np.uint8)
    if kind == 'ink':
        # ink spreading across the page: a noise field thresholded by a growing blot from the centre
        n = noise_tex(os_, 3)
        yy, xx = np.ogrid[:h, :w]
        r = np.sqrt(((xx - w * 0.5) / w) ** 2 + ((yy - h * 0.48) / h) ** 2 * 0.55) / 0.62
        field = 0.62 * r + 0.38 * n
        thr = -0.08 + 1.18 * smoother(u)
        m = np.clip((thr - field) / 0.035, 0, 1)
        edge = np.clip(1 - np.abs(thr - field) / 0.05, 0, 1) * (u < 0.995)
        out = fa * (1 - m[..., None]) + fb * m[..., None]
        ink = np.array([24, 19, 15], np.float32)
        out = out * (1 - 0.92 * edge[..., None]) + ink * 0.92 * edge[..., None]
        return np.clip(out, 0, 255).astype(np.uint8)
    if kind == 'tear':
        # the page tears from left to right along a ragged line and falls away
        k = smoother(u)
        xs = np.arange(w)
        jag = np.zeros(w, np.float32)
        for i, f in enumerate((0.011, 0.031, 0.09, 0.23)):
            jag += np.sin(xs / os_ * f + i * 1.7) * (26 - i * 6) * os_
        y_line = (h * (-0.25 + 1.5 * k) - xs * 0.35 + jag)[None, :]
        yy = np.arange(h)[:, None].astype(np.float32)
        m = (yy < y_line).astype(np.float32)
        out = fa * (1 - m[..., None]) + fb * m[..., None]
        fib = np.clip(1 - np.abs(yy - y_line - 7 * os_) / (7 * os_), 0, 1)
        n = noise_tex(os_, 5, 6.0)
        fib *= (0.6 + 0.4 * n)
        paper = np.array([232, 220, 194], np.float32)
        out = out * (1 - fib[..., None]) + paper * fib[..., None]
        sh = np.clip(1 - (y_line - yy) / (28 * os_), 0, 1) * (yy < y_line)
        out *= (1 - 0.45 * sh[..., None])
        return np.clip(out, 0, 255).astype(np.uint8)
    if kind == 'page':
        # an illustrated page turn: the fold sweeps right to left, the page's parchment back crosses over
        k = smoother(u)
        xf = w * (1.0 - 1.45 * k)
        flap = (w - xf) * 0.42
        xs = np.arange(w, dtype=np.float32)
        out = fa.copy()
        mB = (xs >= xf)[None, :]
        out = np.where(mB[..., None], fb, out)
        # shadow cast on the new page beside the fold
        sh = np.clip(1 - (xs - xf) / (90 * os_), 0, 1) * (xs >= xf)
        out *= (1 - 0.55 * sh[None, :, None])
        # the back of the page
        inflap = (xs >= xf - flap) & (xs < xf)
        g = np.clip((xf - xs) / max(flap, 1), 0, 1)
        back = np.array([214, 198, 166], np.float32)[None, :]
        shade = (0.72 + 0.28 * np.sin(g * math.pi * 0.9))[:, None]
        col = back * shade
        n = noise_tex(os_, 7, 40.0)
        flapimg = col[None, :, :] * (0.9 + 0.1 * n[..., None])
        out = np.where(inflap[None, :, None], flapimg, out)
        edge = np.clip(1 - np.abs(xs - (xf - flap)) / (3 * os_), 0, 1) * (flap > 2)
        out *= (1 - 0.7 * edge[None, :, None])
        return np.clip(out, 0, 255).astype(np.uint8)
    if kind == 'map':
        # the stage shrinks into its place on the city plan while the plan takes over
        from PIL import Image
        k = smoother(u)
        sc = 1.0 - 0.82 * k
        im = Image.fromarray(A).resize((max(2, int(w * sc)), max(2, int(h * sc))), Image.BILINEAR)
        a = np.asarray(im, np.float32)
        out = fb.copy()
        cx, cy = w * (0.5 + 0.06 * k), h * (0.5 + 0.05 * k)
        x0, y0 = int(cx - a.shape[1] / 2), int(cy - a.shape[0] / 2)
        al = 1 - smooth(clamp((u - 0.55) / 0.45))
        ys, xs_ = slice(max(0, y0), min(h, y0 + a.shape[0])), slice(max(0, x0), min(w, x0 + a.shape[1]))
        sub = a[ys.start - y0:ys.stop - y0, xs_.start - x0:xs_.stop - x0]
        out[ys, xs_] = out[ys, xs_] * (1 - al) + sub * al
        # an inked frame around the shrinking picture
        bw = max(2, int(6 * os_))
        for (yy0, yy1, xx0, xx1) in ((y0 - bw, y0, x0 - bw, x0 + a.shape[1] + bw), (y0 + a.shape[0], y0 + a.shape[0] + bw, x0 - bw, x0 + a.shape[1] + bw),
                                     (y0, y0 + a.shape[0], x0 - bw, x0), (y0, y0 + a.shape[0], x0 + a.shape[1], x0 + a.shape[1] + bw)):
            ys2, xs2 = slice(max(0, yy0), max(0, min(h, yy1))), slice(max(0, xx0), max(0, min(w, xx1)))
            out[ys2, xs2] = out[ys2, xs2] * (1 - al) + np.array([24, 19, 15], np.float32) * al
        return np.clip(out, 0, 255).astype(np.uint8)
    if kind == 'wipe':
        # a dark timber post sweeps across in the foreground; the cut hides behind it
        k = smoother(u)
        xe = w * (-0.35 + 1.7 * k)
        xs = np.arange(w, dtype=np.float32)
        m = (xs < xe)[None, :, None]
        out = np.where(m, fb, fa).astype(np.float32)
        half = 0.3 * w
        post_m = np.clip(1 - np.abs(xs - xe) / half, 0, 1)
        post_m = np.clip(post_m * 4, 0, 1)
        wood = np.array([40, 31, 24], np.float32)
        n = noise_tex(os_, 11, 14.0)
        grain = (0.75 + 0.5 * n[:, :])[..., None]
        out = out * (1 - post_m[None, :, None]) + (wood * grain) * post_m[None, :, None]
        return np.clip(out, 0, 255).astype(np.uint8)
    return B


def _arr_surface(rgb):
    h, w = rgb.shape[:2]
    a = np.empty((h, w, 4), np.uint8)
    a[..., 0], a[..., 1], a[..., 2], a[..., 3] = rgb[..., 2], rgb[..., 1], rgb[..., 0], 255
    from core import array_surface
    return array_surface(a)


def frame_rgb(t, os_, captions=True):
    idx = None
    for i, (k, a, b, fn) in enumerate(TIMELINE):
        if a <= t < b:
            idx = i
            break
    if idx is None:
        idx = len(TIMELINE) - 1
    k, a, b, fn = TIMELINE[idx]
    rgb = None
    # incoming transition into this entry
    tr = TRANS.get(k)
    if tr and tr[1] > 0 and idx > 0 and t < a + tr[1]:
        pk, pa, pb, pfn = TIMELINE[idx - 1]
        u = (t - (a - tr[1])) / (2 * tr[1])
        rgb = combine(tr[0], render_scene(pfn, t, os_), render_scene(fn, t, os_), u, os_, t)
    # outgoing transition into the next entry
    if rgb is None and idx + 1 < len(TIMELINE):
        nk, na, nb, nfn = TIMELINE[idx + 1]
        tr = TRANS.get(nk)
        if tr and tr[1] > 0 and t >= na - tr[1]:
            u = (t - (na - tr[1])) / (2 * tr[1])
            rgb = combine(tr[0], render_scene(fn, t, os_), render_scene(nfn, t, os_), u, os_, t)
    if rgb is None:
        rgb = render_scene(fn, t, os_)
    # no fade-in from black (the hook hits on frame one) and no fade-out: the last frame matches the first
    rgb = np.ascontiguousarray(rgb)
    text.draw_titles(rgb, t, os_)
    if captions:
        text.draw_captions(rgb, t, os_)
    return rgb


def _init():
    bind()


def _render_chunk(args):
    f0, f1, os_, path, captions = args
    bind()
    w, h = int(W * os_), int(H * os_)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        rgb = frame_rgb(f / FPS, os_, captions)
        pr.stdin.write(rgb.tobytes())
        if (f - f0) % 30 == 0:
            print(f'  frame {f} ({(time.time() - t0) / max(1, f - f0 + 1):.2f} s/frame)', flush=True)
    pr.stdin.close()
    pr.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stills', default=None)
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--no-voice', action='store_true')
    ap.add_argument('--no-captions', action='store_true')
    ap.add_argument('--range', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--scale', type=float, default=None)
    args = ap.parse_args()
    bind()
    os_ = args.scale or (0.5 if (args.preview or args.stills) else 1.0)
    captions = not (args.no_captions or args.no_voice)
    if args.stills:
        from PIL import Image
        d = os.path.join(ROOT, 'build', 'stills')
        os.makedirs(d, exist_ok=True)
        for s in args.stills.split(','):
            t = float(s)
            t0 = time.time()
            rgb = frame_rgb(t, os_, captions)
            Image.fromarray(rgb).save(os.path.join(d, f'still_{t:06.2f}.png'))
            print(f'still {t:.2f}s  {time.time() - t0:.2f}s')
        return
    f_a, f_b = 0, NFRAMES
    if args.range:
        a, b = [float(v) for v in args.range.split(',')]
        f_a, f_b = int(round(a * FPS)), int(round(b * FPS))
    seg_dir = os.path.join(ROOT, 'build', 'segments')
    os.makedirs(seg_dir, exist_ok=True)
    n = max(1, args.workers)
    per = math.ceil((f_b - f_a) / n)
    jobs = []
    tag = 'p' if args.preview else ('nv' if args.no_voice else 'f')
    for i in range(n):
        a, b = f_a + i * per, min(f_b, f_a + (i + 1) * per)
        if a < b:
            jobs.append((a, b, os_, os.path.join(seg_dir, f'{tag}_{i:02d}.mp4'), captions))
    t0 = time.time()
    with Pool(len(jobs)) as pool:
        paths = pool.map(_render_chunk, jobs)
    print(f'rendered {f_b - f_a} frames in {time.time() - t0:.0f} s')
    lst = os.path.join(seg_dir, f'{tag}_list.txt')
    with open(lst, 'w') as fh:
        for p in paths:
            fh.write(f"file '{p}'\n")
    if args.out:
        out = os.path.join(ROOT, args.out)
    elif args.preview:
        out = os.path.join(ROOT, 'renders', 'preview.mp4')
    elif args.no_voice:
        out = os.path.join(ROOT, 'renders', 'final_video_no_voice.mp4')
    else:
        out = os.path.join(ROOT, 'final_video.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    audio = os.path.join(ROOT, 'audio', 'mix_no_voice.wav' if args.no_voice else 'mix_with_voice.wav')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst]
    has_audio = os.path.exists(audio) and not args.range
    if has_audio:
        cmd += ['-i', audio]
    vf = 'scale=1080:1920:flags=lanczos' if os_ != 1.0 else 'null'
    cmd += ['-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-maxrate', '9M', '-bufsize', '18M',
            '-pix_fmt', 'yuv420p', '-r', str(FPS)]
    if has_audio:
        cmd += ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest']
    cmd += ['-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print('wrote', out)


if __name__ == '__main__':
    main()
