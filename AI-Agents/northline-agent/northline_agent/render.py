"""Draws slideshow images: 1080x1350 for Instagram/Facebook and 1080x1920 for TikTok."""

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .config import FONTS_DIR, PHOTOS_DIR, Config
from .content import Post

W = 1080
FORMATS = {
    # name: (height, top safe margin, bottom safe margin)
    "feed": (1350, 90, 110),
    # TikTok's caption and buttons cover the bottom and right edge.
    "tall": (1920, 170, 430),
}
SIDE = 90


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS_DIR / name), size)


def _hex(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _mix(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if font.getlength(candidate) <= width or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def _fit(text: str, font_name: str, width: int, max_height: int, start: int, floor: int, spacing: float):
    """Largest font size where the wrapped text fits the box."""
    size = start
    while True:
        font = _font(font_name, size)
        lines = _wrap(text, font, width)
        line_h = round(size * spacing)
        if len(lines) * line_h <= max_height or size <= floor:
            return font, lines, line_h
        size -= 4


def _photo_for(post_id: str) -> Path | None:
    photos = sorted(p for p in PHOTOS_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if not photos:
        return None
    index = int(hashlib.sha1(post_id.encode()).hexdigest(), 16) % len(photos)
    return photos[index]


def _background(size: tuple[int, int], bg: tuple, photo: Path | None) -> Image.Image:
    if photo is None:
        img = Image.new("RGB", size, bg)
        # Subtle vertical fade so flat slides don't look dead.
        shade = Image.linear_gradient("L").resize(size)
        return Image.composite(Image.new("RGB", size, _mix(bg, (0, 0, 0), 0.45)), img, shade)
    img = ImageOps.fit(Image.open(photo).convert("RGB"), size, Image.Resampling.LANCZOS)
    # Darken toward the bottom so white text stays readable on any photo.
    mask = Image.linear_gradient("L").resize(size).point(lambda v: 110 + v * 0.5)
    return Image.composite(Image.new("RGB", size, (0, 0, 0)), img, mask)


def _slide(
    cfg: Config,
    fmt: str,
    kind: str,
    headline: str,
    body: str,
    index: int,
    total: int,
    photo: Path | None,
) -> Image.Image:
    height, top, bottom = FORMATS[fmt]
    colors = cfg.brand["colors"]
    bg, fg, accent = _hex(colors["background"]), _hex(colors["text"]), _hex(colors["accent"])
    muted = _mix(fg, bg, 0.35)

    img = _background((W, height), bg, photo if kind == "cover" else None)
    d = ImageDraw.Draw(img)
    inner = W - 2 * SIDE

    # Header: wordmark on the left, slide counter on the right.
    mark = _font("BarlowCondensed-Bold.ttf", 40)
    d.rectangle([SIDE, top + 6, SIDE + 10, top + 44], fill=accent)
    d.text((SIDE + 26, top), cfg.brand["name"].upper(), font=mark, fill=fg)
    counter = _font("Inter-Medium.ttf", 32)
    label = f"{index} / {total}"
    d.text((W - SIDE - counter.getlength(label), top + 6), label, font=counter, fill=muted)

    # Footer: rule and handle.
    foot_y = height - bottom
    d.line([SIDE, foot_y, W - SIDE, foot_y], fill=_mix(fg, bg, 0.75), width=2)
    small = _font("Inter-Medium.ttf", 30)
    d.text((SIDE, foot_y + 22), cfg.brand["handle"], font=small, fill=muted)
    if kind == "cover":
        swipe = "SWIPE  →"
        f = _font("Inter-Bold.ttf", 30)
        d.text((W - SIDE - f.getlength(swipe), foot_y + 22), swipe, font=f, fill=accent)

    # Text block, vertically centred between header and footer.
    area_top, area_bottom = top + 120, foot_y - 60
    area_h = area_bottom - area_top
    start = {"cover": 176, "cta": 132, "slide": 124}[kind]
    head_font, head_lines, head_lh = _fit(
        headline.upper(), "BarlowCondensed-ExtraBold.ttf", inner, int(area_h * 0.62), start, 64, 0.98
    )
    body_font = _font("Inter-Medium.ttf", 44 if fmt == "tall" else 40)
    body_lines = _wrap(body, body_font, inner) if body else []
    body_lh = round(body_font.size * 1.38)

    extra = 0
    if kind == "cta":
        extra = 150
    gap = 44 if body_lines else 0
    block_h = len(head_lines) * head_lh + gap + len(body_lines) * body_lh + extra
    y = area_top + max(0, (area_h - block_h) // 2)
    if kind == "cover":
        y = max(y, area_top + int(area_h * 0.18))

    if kind == "slide":
        d.rectangle([SIDE, y - 34, SIDE + 90, y - 26], fill=accent)
    for line in head_lines:
        d.text((SIDE, y), line, font=head_font, fill=fg)
        y += head_lh
    y += gap
    for line in body_lines:
        d.text((SIDE, y), line, font=body_font, fill=muted)
        y += body_lh

    if kind == "cta":
        url = cfg.brand["store_url"].upper()
        pill_font = _font("BarlowCondensed-Bold.ttf", 52)
        pad_x, pill_h = 38, 96
        pill_w = int(pill_font.getlength(url)) + 2 * pad_x
        y += 46
        d.rounded_rectangle([SIDE, y, SIDE + pill_w, y + pill_h], radius=pill_h // 2, fill=accent)
        text_y = y + (pill_h - pill_font.size) // 2 - 6
        d.text((SIDE + pad_x, text_y), url, font=pill_font, fill=bg)

    return img


def render_post(cfg: Config, post: Post, post_id: str, out_dir: Path) -> dict[str, list[Path]]:
    """Writes every slide in both formats and returns the file paths per format."""
    out_dir.mkdir(parents=True, exist_ok=True)
    photo = _photo_for(post_id)
    frames = [("cover", post.hook, "")]
    frames += [("slide", s.headline, s.body) for s in post.slides]
    frames.append(("cta", post.cta.headline, post.cta.body))

    paths: dict[str, list[Path]] = {}
    for fmt in FORMATS:
        paths[fmt] = []
        for i, (kind, headline, body) in enumerate(frames, start=1):
            img = _slide(cfg, fmt, kind, headline, body, i, len(frames), photo)
            path = out_dir / f"{post_id}-{fmt}-{i:02d}.jpg"
            img.save(path, "JPEG", quality=90, optimize=True, progressive=False)
            paths[fmt].append(path)
    return paths
