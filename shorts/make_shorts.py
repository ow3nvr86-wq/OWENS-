#!/usr/bin/env python3
"""make_shorts.py - turn a long video into captioned, vertical Shorts.

Pipeline:
  1. Transcribe the video with Whisper (word-level timestamps, cached).
  2. Pick clips: the timestamps you pass with --clips, or the best moments
     found automatically (--auto N).
  3. For each clip: trim, reframe to 9:16 (1080x1920), burn in captions in
     the Shorts style, optionally add a hook title, and write an .mp4.
  4. Write a notes file with suggested titles, descriptions and hashtags.

Quick start:
  python shorts/make_shorts.py my_video.mp4 --list            # see transcript
  python shorts/make_shorts.py my_video.mp4 --auto 3          # best 3 moments
  python shorts/make_shorts.py my_video.mp4 --clips "1:05-1:40,4:10-4:55"

Requires ffmpeg on PATH and `pip install faster-whisper`.
Run with --help for every option.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

OUT_W, OUT_H = 1080, 1920

HOOK_WORDS = {
    "how", "why", "what", "never", "always", "secret", "best", "worst",
    "nobody", "everyone", "stop", "mistake", "wrong", "crazy", "insane",
    "actually", "truth", "trick", "hack", "biggest", "only", "first",
    "imagine", "listen", "watch", "look", "here's", "this", "you",
}

COLORS = {  # ASS colours are &HAABBGGRR
    "yellow": "&H0000FFFF",
    "green": "&H0000FF66",
    "cyan": "&H00FFFF00",
    "red": "&H003C3CFF",
    "pink": "&H00B469FF",
    "orange": "&H0000A5FF",
    "white": "&H00FFFFFF",
}


# --------------------------------------------------------------------------
# Data types
# --------------------------------------------------------------------------

@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)


@dataclass
class Clip:
    start: float
    end: float
    score: float = 0.0
    title: str | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_time(value: str) -> float:
    """'83', '83.5', '1:23', '1:02:03.5' -> seconds."""
    value = value.strip()
    if not value:
        raise ValueError("empty time")
    parts = value.split(":")
    if len(parts) > 3:
        raise ValueError(f"bad time: {value}")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m}:{s:04.1f}"


def ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ass_escape(text: str) -> str:
    return text.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        die(f"ffprobe could not read {path}:\n{out.stderr.strip()}")
    info = json.loads(out.stdout)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        die(f"{path} has no video stream")
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    return {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "duration": float(info["format"].get("duration", 0) or 0),
        "has_audio": has_audio,
    }


# --------------------------------------------------------------------------
# 1. Transcription
# --------------------------------------------------------------------------

def transcribe(video: Path, cache: Path, model_name: str, language: str | None) -> list[Segment]:
    if cache.exists():
        data = json.loads(cache.read_text())
        if data.get("model") == model_name and data.get("language_opt") == language:
            print(f"Using cached transcript: {cache}")
            return [
                Segment(s["start"], s["end"], s["text"], [Word(**w) for w in s["words"]])
                for s in data["segments"]
            ]

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("faster-whisper is not installed. Run:  pip install faster-whisper")

    import numpy as np

    # Decode with ffmpeg ourselves: 16 kHz mono float, what Whisper expects.
    # This avoids faster-whisper's own decoder breaking on newer PyAV releases.
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-f", "f32le", "-"],
        capture_output=True,
    )
    if pcm.returncode != 0:
        die(f"ffmpeg could not read the audio:\n{pcm.stderr.decode(errors='replace').strip()}")
    audio = np.frombuffer(pcm.stdout, dtype=np.float32)
    if audio.size == 0:
        print("No audio track found, so there are no captions.")
        return []

    print(f"Transcribing with Whisper '{model_name}' (first run downloads the model)...")
    model = WhisperModel(model_name, device="auto", compute_type="int8")
    raw_segments, info = model.transcribe(
        audio, language=language, word_timestamps=True, vad_filter=True,
    )
    segments: list[Segment] = []
    for seg in raw_segments:
        words = [Word(float(w.start), float(w.end), w.word.strip())
                 for w in (seg.words or []) if w.word.strip()]
        segments.append(Segment(float(seg.start), float(seg.end), seg.text.strip(), words))
        print(f"  [{fmt_time(seg.start)}] {seg.text.strip()}")

    cache.write_text(json.dumps({
        "model": model_name,
        "language_opt": language,
        "language": info.language,
        "segments": [
            {"start": s.start, "end": s.end, "text": s.text,
             "words": [w.__dict__ for w in s.words]}
            for s in segments
        ],
    }, indent=1))
    print(f"Saved transcript: {cache}")
    return segments


def write_transcript_txt(segments: list[Segment], path: Path) -> None:
    lines = [f"[{fmt_time(s.start)} - {fmt_time(s.end)}] {s.text}" for s in segments]
    path.write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# 2. Clip selection
# --------------------------------------------------------------------------

def parse_clip_item(item: str, duration: float) -> Clip:
    """'1:05-1:40' or '1:05-1:40 | Hook title' -> Clip."""
    rng, _, title = item.partition("|")
    rng = rng.strip()
    if "-" not in rng:
        die(f"clip '{item}' must look like START-END, e.g. 1:05-1:40")
    a, b = rng.split("-", 1)
    try:
        start, end = parse_time(a), parse_time(b)
    except ValueError as exc:
        die(f"clip '{item}': {exc}")
    if duration:
        end = min(end, duration)
    if end <= start:
        die(f"clip '{item}' ends before it starts")
    return Clip(start, end, title=title.strip() or None)


def parse_clips(spec: str, duration: float) -> list[Clip]:
    return [parse_clip_item(i, duration) for i in spec.split(",") if i.strip()]


def parse_clips_file(path: Path, duration: float) -> list[Clip]:
    """One clip per line: START-END | optional title. Blank lines and # comments are skipped."""
    if not path.exists():
        die(f"no such clips file: {path}")
    clips = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            clips.append(parse_clip_item(line, duration))
    if not clips:
        die(f"{path} has no clips in it")
    return clips


def score_window(segs: list[Segment]) -> float:
    words = [w for s in segs for w in s.words]
    if not words:
        return 0.0
    duration = segs[-1].end - segs[0].start
    density = len(words) / max(duration, 1.0)              # talking, not dead air
    gaps = sum(max(0.0, b.start - a.end - 0.7) for a, b in zip(segs, segs[1:]))
    first = segs[0].text.lower()
    first_words = set(re.findall(r"[a-z']+", first)[:8])
    hook = len(first_words & HOOK_WORDS) * 0.4 + (0.8 if "?" in first else 0.0)
    if re.search(r"\d", first):
        hook += 0.3
    energy = sum(s.text.count("!") for s in segs) * 0.3 + sum(s.text.count("?") for s in segs) * 0.15
    clean_end = 0.5 if segs[-1].text.rstrip().endswith((".", "!", "?")) else 0.0
    clean_start = 0.3 if segs[0].text[:1].isupper() else 0.0
    return density + hook + energy + clean_end + clean_start - gaps * 0.5


def split_sentences(segments: list[Segment]) -> list[Segment]:
    """Re-cut Whisper's segments at sentence ends so clips never start mid-sentence."""
    sentences: list[Segment] = []
    current: list[Word] = []
    for seg in segments:
        if not seg.words:  # no word timings: keep the segment as one unit
            if current:
                sentences.append(_words_to_segment(current))
                current = []
            sentences.append(seg)
            continue
        for w in seg.words:
            if current and w.start - current[-1].end > 1.5:  # long pause = break
                sentences.append(_words_to_segment(current))
                current = []
            current.append(w)
            if w.text.endswith((".", "!", "?")):
                sentences.append(_words_to_segment(current))
                current = []
    if current:
        sentences.append(_words_to_segment(current))
    return sentences


def _words_to_segment(words: list[Word]) -> Segment:
    return Segment(words[0].start, words[-1].end, " ".join(w.text for w in words), list(words))


def auto_clips(segments: list[Segment], count: int, min_len: float, max_len: float,
               min_gap: float = 0.0) -> list[Clip]:
    segments = split_sentences(segments)
    candidates: list[Clip] = []
    for i in range(len(segments)):
        for j in range(i, len(segments)):
            length = segments[j].end - segments[i].start
            if length > max_len:
                break
            if length >= min_len:
                window = segments[i:j + 1]
                candidates.append(Clip(segments[i].start, segments[j].end, score_window(window)))

    if not candidates:  # video shorter than min_len, or one long segment
        if segments:
            start = segments[0].start
            return [Clip(start, min(segments[-1].end, start + max_len), 0.0)]
        return []

    candidates.sort(key=lambda c: c.score, reverse=True)
    picked: list[Clip] = []
    for cand in candidates:
        # keep picks apart so they come from different parts of the video
        if all(cand.end + min_gap <= p.start or cand.start >= p.end + min_gap for p in picked):
            picked.append(cand)
            if len(picked) == count:
                break
    return sorted(picked, key=lambda c: c.start)


# --------------------------------------------------------------------------
# 3a. Captions (ASS subtitles)
# --------------------------------------------------------------------------

def words_in_clip(segments: list[Segment], clip: Clip) -> list[Word]:
    out = []
    for seg in segments:
        for w in seg.words:
            if w.start >= clip.start - 0.05 and w.start < clip.end - 0.1:
                out.append(Word(w.start - clip.start, min(w.end, clip.end) - clip.start, w.text))
    return out


def group_words(words: list[Word], per_line: int, max_chars: int) -> list[list[Word]]:
    groups: list[list[Word]] = []
    current: list[Word] = []
    for w in words:
        too_long = sum(len(x.text) + 1 for x in current) + len(w.text) > max_chars
        gap = current and w.start - current[-1].end > 0.6
        if current and (len(current) >= per_line or too_long or gap):
            groups.append(current)
            current = []
        current.append(w)
        if w.text.endswith((".", "!", "?", ",")) and len(current) >= 1:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def build_ass(words: list[Word], args: argparse.Namespace, clip_len: float, title: str | None) -> str:
    size = args.font_size
    caption_y = int(OUT_H * args.caption_pos)
    title_y = int(OUT_H * args.title_pos)
    hl = COLORS.get(args.highlight_color, args.highlight_color)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{args.font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,{max(3, size // 14)},3,5,70,70,0,1
Style: Title,{args.font},{int(size * 0.85)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{max(3, size // 12)},4,8,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    if title:
        events.append(
            f"Dialogue: 1,{ass_time(0)},{ass_time(clip_len)},Title,,0,0,0,,"
            f"{{\\pos({OUT_W // 2},{title_y})}}{ass_escape(title)}"
        )

    if args.style != "none":
        groups = group_words(words, args.words_per_line, args.max_chars)
        for gi, group in enumerate(groups):
            texts = [ass_escape(w.text.upper() if args.upper else w.text) for w in group]
            g_end = group[-1].end
            if gi + 1 < len(groups):
                nxt = groups[gi + 1][0].start
                if nxt - g_end < 1.0:      # hold through short pauses, no blinking
                    g_end = nxt
            else:
                g_end = min(clip_len, g_end + 0.4)
            pos = f"{{\\pos({OUT_W // 2},{caption_y})}}"

            if args.style == "plain":
                pop = "{\\fscx90\\fscy90\\t(0,80,\\fscx100\\fscy100)}"
                events.append(
                    f"Dialogue: 0,{ass_time(group[0].start)},{ass_time(g_end)},Caption,,0,0,0,,"
                    f"{pos}{pop}{' '.join(texts)}"
                )
                continue

            # highlight: one event per word, the spoken word is coloured
            for wi, w in enumerate(group):
                start = w.start if wi else group[0].start
                end = group[wi + 1].start if wi + 1 < len(group) else g_end
                if end <= start:
                    continue
                parts = [
                    f"{{\\c{hl}}}{t}{{\\c&H00FFFFFF&}}" if k == wi else t
                    for k, t in enumerate(texts)
                ]
                pop = "{\\fscx92\\fscy92\\t(0,80,\\fscx100\\fscy100)}" if wi == 0 else ""
                events.append(
                    f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,"
                    f"{pos}{pop}{' '.join(parts)}"
                )

    return header + "\n".join(events) + "\n"


# --------------------------------------------------------------------------
# 3b. Video: trim, reframe, burn captions
# --------------------------------------------------------------------------

def video_filter(args: argparse.Namespace) -> str:
    pre = f"crop={args.source_crop}," if args.source_crop else ""
    if args.layout == "crop":
        x = args.crop_x
        chain = (f"[0:v]{pre}scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,"
                 f"crop={OUT_W}:{OUT_H}:(iw-ow)*{x}:(ih-oh)/2,setsar=1[base]")
    elif args.layout == "fit":
        chain = (f"[0:v]{pre}scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
                 f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[base]")
    else:  # blur
        zoom = args.zoom
        fg_w = int(OUT_W * zoom) // 2 * 2
        chain = (
            f"[0:v]{pre}split=2[bgsrc][fgsrc];"
            f"[bgsrc]scale={OUT_W // 4}:{OUT_H // 4}:force_original_aspect_ratio=increase,"
            f"crop={OUT_W // 4}:{OUT_H // 4},boxblur=8:3,eq=brightness=-0.12:saturation=1.2,"
            f"scale={OUT_W}:{OUT_H}[bg];"
            f"[fgsrc]scale={fg_w}:-2[fgbig];"
            f"[fgbig]crop=min(iw\\,{OUT_W}):min(ih\\,{OUT_H})[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base]"
        )
    return chain + ";[base]ass=captions.ass[v]"


def render_clip(video: Path, clip: Clip, ass_text: str, out_path: Path,
                args: argparse.Namespace, has_audio: bool) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "captions.ass").write_text(ass_text, encoding="utf-8")
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-y",
            "-ss", f"{clip.start:.3f}", "-to", f"{clip.end:.3f}",
            "-i", str(video.resolve()),
            "-filter_complex", video_filter(args),
            "-map", "[v]",
        ]
        if has_audio:
            cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
        cmd += [
            "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
            "-pix_fmt", "yuv420p", "-r", str(args.fps),
            "-movflags", "+faststart",
            str(out_path.resolve()),
        ]
        # Run inside the temp dir so the subtitle path needs no escaping
        # (Windows drive letters break ffmpeg's filter syntax otherwise).
        result = subprocess.run(cmd, cwd=tmpdir)
        if result.returncode != 0:
            die(f"ffmpeg failed on clip {fmt_time(clip.start)}-{fmt_time(clip.end)}")


# --------------------------------------------------------------------------
# 4. Posting notes
# --------------------------------------------------------------------------

def suggest_title(text: str, limit: int = 80) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip())[0]
    sentence = sentence.rstrip(".")
    if len(sentence) > limit:
        sentence = sentence[:limit - 3].rsplit(" ", 1)[0] + "..."
    return sentence


def clip_text(segments: list[Segment], clip: Clip) -> str:
    return " ".join(w.text for w in words_in_clip(segments, clip))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Turn a long video into captioned vertical Shorts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("video", type=Path, help="input video file (.mp4, .mov, .mkv, ...)")

    pick = p.add_argument_group("choosing clips")
    pick.add_argument("--list", action="store_true",
                      help="only transcribe and print the transcript with timestamps")
    pick.add_argument("--clips", help='your own timestamps, e.g. "1:05-1:40,4:10-4:55". '
                      'Add a title per clip with |, e.g. "1:05-1:40|Wait for it"')
    pick.add_argument("--clips-file", type=Path,
                      help="text file with one clip per line: START-END | optional title "
                           "(best for long videos)")
    pick.add_argument("--auto", type=int, default=3, metavar="N",
                      help="when --clips is not given, pick the N best moments")
    pick.add_argument("--min-len", type=float, default=20, help="shortest auto clip (s)")
    pick.add_argument("--max-len", type=float, default=58, help="longest auto clip (s)")
    pick.add_argument("--min-gap", type=float, default=None,
                      help="auto: seconds to keep between picked clips; default "
                           "spreads them across the video")

    look = p.add_argument_group("framing")
    look.add_argument("--layout", choices=["blur", "crop", "fit"], default="blur",
                      help="blur: whole video over a blurred fill (best for screen "
                           "recordings); crop: fill the screen, cut the sides; "
                           "fit: whole video with black bars")
    look.add_argument("--zoom", type=float, default=1.0,
                      help="blur layout: scale the video wider than the screen, e.g. 1.4")
    look.add_argument("--crop-x", type=float, default=0.5,
                      help="crop layout: horizontal focus, 0 = left, 0.5 = centre, 1 = right")
    look.add_argument("--source-crop", metavar="W:H:X:Y",
                      help="cut browser bars/taskbar off the recording first, e.g. "
                           "1920:1080:0:120 keeps a 1920x1080 area starting 120px down")

    cap = p.add_argument_group("captions")
    cap.add_argument("--style", choices=["highlight", "plain", "none"], default="highlight",
                     help="highlight colours the word being spoken")
    cap.add_argument("--highlight-color", default="yellow",
                     help=f"{', '.join(COLORS)} or an ASS colour like &H0000FFFF")
    cap.add_argument("--font", default="Arial", help="any font installed on your computer")
    cap.add_argument("--font-size", type=int, default=84)
    cap.add_argument("--words-per-line", type=int, default=3)
    cap.add_argument("--max-chars", type=int, default=18, help="max characters per caption line")
    cap.add_argument("--no-upper", dest="upper", action="store_false",
                     help="keep normal case instead of ALL CAPS")
    cap.add_argument("--caption-pos", type=float, default=0.70,
                     help="caption height, 0 = top of screen, 1 = bottom")
    cap.add_argument("--title", help='hook text shown at the top, e.g. "He did NOT see that coming"')
    cap.add_argument("--auto-title", action="store_true",
                     help="use each clip's opening line as its on-screen title")
    cap.add_argument("--title-pos", type=float, default=0.14, help="title height, 0 = top, 1 = bottom")

    tech = p.add_argument_group("transcription and output")
    tech.add_argument("--model", default="base",
                      help="Whisper model: tiny, base, small, medium, large-v3 "
                           "(bigger = more accurate, slower)")
    tech.add_argument("--language", default=None, help="e.g. en; default detects it")
    tech.add_argument("--out", type=Path, default=Path("shorts/out"), help="output folder")
    tech.add_argument("--crf", type=int, default=20, help="video quality, lower = better")
    tech.add_argument("--preset", default="medium", help="x264 speed preset")
    tech.add_argument("--fps", type=int, default=30)
    return p


def main() -> None:
    args = build_parser().parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        die("ffmpeg is not installed or not on PATH. Get it from https://ffmpeg.org/download.html")
    if not args.video.exists():
        die(f"no such file: {args.video}")

    info = probe(args.video)
    args.out.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^\w\-]+", "_", args.video.stem).strip("_") or "video"

    segments = transcribe(args.video, args.out / f"{stem}.transcript.json", args.model, args.language)
    txt = args.out / f"{stem}.transcript.txt"
    write_transcript_txt(segments, txt)

    if args.list:
        print(txt.read_text())
        print(f"Transcript saved to {txt}. Pick timestamps and rerun with --clips "
              f"or --clips-file.")
        return

    if args.clips_file:
        clips = parse_clips_file(args.clips_file, info["duration"])
    elif args.clips:
        clips = parse_clips(args.clips, info["duration"])
    else:
        if not segments:
            die("no speech found, so there is nothing to auto-pick. Use --clips instead.")
        gap = args.min_gap
        if gap is None:  # spread picks out: up to 1/4 of an even share each, max 2 min
            gap = min(120.0, info["duration"] / max(args.auto, 1) / 4)
        clips = auto_clips(segments, args.auto, args.min_len, args.max_len, gap)
        print(f"Auto-picked {len(clips)} clip(s):")
        if len(clips) < args.auto:
            print(f"  (asked for {args.auto}; the video only has room for {len(clips)} "
                  f"well-spaced clips. Try a lower --min-gap or --min-len.)")
        for c in clips:
            print(f"  {fmt_time(c.start)} - {fmt_time(c.end)}  {suggest_title(clip_text(segments, c), 60)}")

    notes = [f"# Shorts from {args.video.name}\n"]
    for n, clip in enumerate(clips, 1):
        out_path = args.out / f"{stem}_short{n:02d}.mp4"
        print(f"\n[{n}/{len(clips)}] {fmt_time(clip.start)} - {fmt_time(clip.end)} "
              f"({clip.duration:.0f}s) -> {out_path}")
        words = words_in_clip(segments, clip)
        text = clip_text(segments, clip)
        title = clip.title or args.title
        if not title and args.auto_title and text:
            title = suggest_title(text, 50)
        ass_text = build_ass(words, args, clip.duration, title)
        render_clip(args.video, clip, ass_text, out_path, args, info["has_audio"])

        notes += [
            f"## {out_path.name}",
            f"- Source: {fmt_time(clip.start)} - {fmt_time(clip.end)} ({clip.duration:.0f}s)",
            f"- On-screen title: {title or '(none)'}",
            f"- Suggested title: {suggest_title(text) if text else '(add your own)'} #shorts",
            f"- Transcript: {text or '(no speech)'}",
            "- Hashtags: #shorts #fyp #viral",
            "",
        ]

    notes_path = args.out / f"{stem}_shorts.md"
    notes_path.write_text("\n".join(notes))
    print(f"\nDone. {len(clips)} short(s) in {args.out}/ - titles and captions in {notes_path}")


if __name__ == "__main__":
    main()
