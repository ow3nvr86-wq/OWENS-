"""Finishing pass for the modern look: a cool filmic grade (soft S-curve, lifted navy blacks), a gentle bloom on
highlights, a vignette and subtle film grain. No paper texture."""
import numpy as np
from scipy import ndimage

from core import W, H

_CACHE = {}


def vignette(os_, strength):
    key = ('vig', os_)
    if key not in _CACHE:
        w, h = int(W * os_), int(H * os_)
        yy, xx = np.ogrid[:h, :w]
        dx = (xx - w / 2) / (w / 2)
        dy = (yy - h * 0.48) / (h / 2)
        r = np.sqrt(dx * dx * 0.8 + dy * dy * 0.7)
        _CACHE[key] = np.clip((r - 0.5) / 0.7, 0, 1) ** 1.8
    return 1 - strength * _CACHE[key]


def finish(bgra, os_, t, look):
    rgb = bgra[..., [2, 1, 0]].astype(np.float32) / 255.0
    bl = look.get('blur')
    if bl:
        # motion blur of a whip-pan: a box blur along the direction the camera travels
        bx, by = int(abs(bl[0]) * os_), int(abs(bl[1]) * os_)
        if bx > 2:
            rgb = ndimage.uniform_filter1d(rgb, bx, axis=1, mode='nearest')
        if by > 2:
            rgb = ndimage.uniform_filter1d(rgb, by, axis=0, mode='nearest')
    dark = look.get('dark', 0.0)
    lum = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11
    ds = look.get('desat', 0.08) + 0.25 * dark
    rgb = rgb * (1 - ds) + lum[..., None] * ds
    rgb *= np.array(look.get('tint', (0.98, 1.0, 1.04)), np.float32)
    rgb = np.clip(rgb * (1.0 - 0.3 * dark), 0, 1)
    # bloom: blur the highlights and add them back
    b = look.get('bloom', 0.25)
    if b > 0:
        hi = np.clip(rgb - 0.62, 0, 1)
        sm = hi[::4, ::4]
        sm = ndimage.gaussian_filter(sm, (6 * os_ + 2, 6 * os_ + 2, 0))
        sm = np.repeat(np.repeat(sm, 4, axis=0), 4, axis=1)[:rgb.shape[0], :rgb.shape[1]]
        rgb = rgb + b * sm
    # filmic S-curve, lifted navy blacks
    rgb = np.clip(rgb, 0, 1)
    rgb = rgb * rgb * (3 - 2 * rgb) * 0.4 + rgb * 0.6
    lift = np.array(look.get('lift', (0.02, 0.03, 0.05)), np.float32)
    rgb = lift + rgb * (1 - lift)
    rgb *= vignette(os_, look.get('vig', 0.45) + 0.2 * dark)[..., None]
    g = look.get('grain', 0.028)
    rng = np.random.default_rng(int(t * 30) * 7 + 1)
    h, w = rgb.shape[:2]
    rgb += (rng.random((h, w), np.float32)[..., None] - 0.5) * g
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
