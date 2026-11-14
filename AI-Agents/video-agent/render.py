"""The renderer: builds the actual .mp4 from Claude's scene plan.

For each scene it records the voiceover (OpenAI text-to-speech), draws a
1080x1920 title card (Pillow), and animates it with a slow zoom and fades
(ffmpeg). Then it joins the scenes into one video.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import wave
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

from director import VideoPlan

W, H, FPS = 1080, 1920, 30
TTS_MODEL = os.environ.get("TTS_MODEL", "gpt-4o-mini-tts")
TAIL = 0.45  # seconds of silence after each scene's narration

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def ffmpeg_exe() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg  # pip-installed ffmpeg, so users don't need a system install
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args: list[str]) -> None:
    proc = subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.strip()[-800:]}")


# ------------------------------------------------------------------ audio
def make_voiceover(text: str, wav_path: Path, voice: str, style: str) -> float:
    """Record one scene's narration to a WAV file and return its length in seconds."""
    mp3 = wav_path.with_suffix(".mp3")
    with OpenAI().audio.speech.with_streaming_response.create(
        model=TTS_MODEL, voice=voice, input=text, instructions=style, response_format="mp3",
    ) as resp:
        resp.stream_to_file(mp3)
    # Re-encode through ffmpeg so the WAV header carries an exact length.
    _run(["-i", str(mp3), "-ar", "44100", "-ac", "1", str(wav_path)])
    mp3.unlink(missing_ok=True)
    with wave.open(str(wav_path)) as w:
        return w.getnframes() / w.getframerate()


# ------------------------------------------------------------------ pictures
def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in [os.environ.get("VIDEO_FONT", ""), *FONT_CANDIDATES]:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _hex(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else fallback


def _readable_bg(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """Darken a background until white text on it is comfortably readable."""
    def lum(c):
        def ch(v):
            v /= 255
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])
    while 1.05 / (lum(rgb) + 0.05) < 7 and max(rgb) > 0:
        rgb = tuple(int(v * 0.85) for v in rgb)
    return rgb


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + ([line] if line else [])


def draw_card(plan: VideoPlan, index: int, png_path: Path) -> None:
    scene = plan.scenes[index]
    bg = _readable_bg(_hex(scene.background, (15, 23, 42)))
    accent = _hex(scene.accent, (245, 158, 11))

    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    # Vertical gradient: background colour at the top, darker at the bottom.
    for y in range(H):
        t = y / H * 0.55
        draw.line([(0, y), (W, y)], fill=tuple(int(c * (1 - t)) for c in bg))

    margin = 96
    # Headline: as large as fits in at most 5 lines.
    for size in range(150, 60, -6):
        head_font = _font(size)
        head_lines = _wrap(draw, scene.headline.upper(), head_font, W - 2 * margin)
        if len(head_lines) <= 5:
            break
    sub_font = _font(52)
    sub_lines = _wrap(draw, scene.subtext, sub_font, W - 2 * margin) if scene.subtext.strip() else []

    head_h = len(head_lines) * int(head_font.size * 1.12)
    sub_h = len(sub_lines) * 68 + (60 if sub_lines else 0)
    y = (H - head_h - sub_h) // 2 - 60

    draw.rounded_rectangle([margin, y - 70, margin + 150, y - 48], radius=11, fill=accent)
    for line in head_lines:
        draw.text((margin, y), line, font=head_font, fill=(255, 255, 255))
        y += int(head_font.size * 1.12)
    y += 60
    for line in sub_lines:
        draw.text((margin, y), line, font=sub_font, fill=(226, 232, 240))
        y += 68

    small = _font(38)
    draw.text((margin, H - 190), plan.title[:48], font=small, fill=(203, 213, 225))
    counter = f"{index + 1}/{len(plan.scenes)}"
    draw.text((W - margin - draw.textlength(counter, font=small), H - 190), counter, font=small, fill=accent)
    # Progress bar along the bottom.
    draw.rectangle([0, H - 14, W, H], fill=tuple(int(c * 0.5) for c in bg))
    draw.rectangle([0, H - 14, int(W * (index + 1) / len(plan.scenes)), H], fill=accent)
    img.save(png_path)


# ------------------------------------------------------------------ video
def make_clip(png: Path, wav: Path, seconds: float, out: Path) -> None:
    total = seconds + TAIL
    frames = max(1, round(total * FPS))
    zoom = (
        f"scale={W * 2}:{H * 2},"
        f"zoompan=z='min(1+0.06*on/{frames},1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:s={W}x{H}:fps={FPS},"
        f"fade=t=in:st=0:d=0.25,fade=t=out:st={total - 0.25:.3f}:d=0.25,format=yuv420p"
    )
    _run([
        "-i", str(png), "-i", str(wav),
        "-filter_complex", f"[0:v]{zoom}[v];[1:a]apad=pad_dur={TAIL}[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "1",
        str(out),
    ])


def render(plan: VideoPlan, out_path: Path, voice: str = "marin",
           style: str = "Energetic, warm and confident, like a short-form video host.",
           voiceover=make_voiceover) -> float:
    """Render the whole video to out_path and return its length in seconds."""
    work = out_path.with_suffix("")  # a scratch folder next to the video
    work.mkdir(parents=True, exist_ok=True)
    clips, total = [], 0.0
    for i, scene in enumerate(plan.scenes):
        print(f"   scene {i + 1}/{len(plan.scenes)}: {scene.headline}")
        wav, png, clip = work / f"{i:02d}.wav", work / f"{i:02d}.png", work / f"{i:02d}.mp4"
        seconds = voiceover(scene.narration, wav, voice, style)
        draw_card(plan, i, png)
        make_clip(png, wav, seconds, clip)
        clips.append(clip)
        total += seconds + TAIL
    listing = work / "clips.txt"
    listing.write_text("".join(f"file '{c.name}'\n" for c in clips))
    _run(["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(out_path)])
    shutil.rmtree(work, ignore_errors=True)
    return total
