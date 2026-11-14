# Video Agent: ChatGPT writes, Claude makes, your phone hears about it

An automatic loop that makes short vertical videos (TikTok, Reels, YouTube Shorts):

```
 ┌──────────────┐  script   ┌──────────────┐  scene plan  ┌──────────────┐
 │   ChatGPT    │ ────────▶ │    Claude    │ ───────────▶ │   Renderer   │──▶ 001-title.mp4
 │ (scriptwriter)│          │  (director)  │              │ voice + video│
 └──────────────┘           └──────────────┘              └──────┬───────┘
        ▲                          │                             │
        │   "Video #1 is done,     │                             ▼
        └──── here are my notes.   ◀─────────────────────  📱 notification
              Send the next script."
```

1. **ChatGPT** writes a script based on your series brief.
2. **Claude** turns it into a scene-by-scene plan: the voiceover words, the big on-screen headline, colours, and a social caption.
3. **The renderer** records the voiceover (OpenAI text-to-speech), draws a title card for each scene, adds a slow zoom and fades, and joins it all into one `.mp4`.
4. **Your phone** gets a notification that the video is ready.
5. **Claude reports back to ChatGPT** with what it made and notes on the script. That message is ChatGPT's signal to write the next script, and the loop goes around again.

ChatGPT keeps a memory of the whole series in `output/series.json`, so it never repeats a topic, even across separate runs.

> **What "Claude makes the video" means here.** Claude doesn't film or generate footage. It directs: it decides what each scene says and shows, and this code renders that into a narrated, animated title-card video. A clip generator (stock footage, AI video) could be added later as an extra step.

## Setup (once)

You need Python 3.10+, an **OpenAI API key** (https://platform.openai.com) and an **Anthropic API key** (https://platform.claude.com). A ChatGPT Plus subscription doesn't include API access; the API is billed separately.

```bash
cd video-agent
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Set your keys (Windows: use `set` instead of `export`):

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

### Phone notifications

1. Install the free **ntfy** app (iPhone or Android).
2. Tap **+** and subscribe to a topic name only you would guess, like `owen-videos-7f3k9`. Anyone who knows the name can read it.
3. Set the same name here:

```bash
export NTFY_TOPIC=owen-videos-7f3k9
```

If `NTFY_TOPIC` isn't set, everything still works and the notifications just print in the terminal.

## Run it

```bash
python pipeline.py --brief "wild history facts most people never learned"
```

That makes one video. The brief can be any topic: facts, money tips, motivation, storytime, product reviews, whatever your page is about. Describe the vibe and audience too (for example "funny, fast, for Gen Z"). If you leave `--brief` off the first time, it asks you. After that it remembers. More options:

```bash
python pipeline.py --count 5               # five videos back to back
python pipeline.py --count 3 --gap 30      # three videos, 30 minutes apart
python pipeline.py --forever --gap 60      # one an hour until you press Ctrl-C
python pipeline.py --voice cedar           # a different voice
python pipeline.py --new-series --brief "money tips for teens"   # start a fresh series
```

Everything lands in `output/`:

| File | What it is |
|---|---|
| `001-title.mp4` | The finished video, 1080×1920 |
| `001-title.caption.txt` | A caption with hashtags, ready to paste when you post |
| `001-title.script.txt` | ChatGPT's original script |
| `001-title.plan.json` | Claude's scene plan |
| `series.json` | The series memory: brief, count, and the ChatGPT conversation |

## Settings

| Variable | Default | What it does |
|---|---|---|
| `GPT_MODEL` | `gpt-5.5` | Which ChatGPT model writes the scripts |
| `TTS_MODEL` | `gpt-4o-mini-tts` | The OpenAI voice model. **OpenAI plans to shut this model down on Jan 6, 2027.** Set this to its replacement before then |
| `NTFY_TOPIC` | none | Your ntfy topic for phone notifications |
| `NTFY_SERVER` | `https://ntfy.sh` | Use your own ntfy server if you have one |
| `VIDEO_FONT` | DejaVu/Arial Bold | Path to a `.ttf` font for the on-screen text |

Claude runs as Claude Opus 5.5. Use `--effort` (`low` to `max`) to set how hard it thinks about each plan. If Claude's safety check ever declines a script, the request is retried automatically on a fallback model. If anything fails, you get a "Video pipeline stopped" notification with the error.

## Files

- `pipeline.py`: the loop and command-line options
- `writer.py`: ChatGPT, the scriptwriter, and its series memory
- `director.py`: Claude, the scene plan and the hand-off note back to ChatGPT
- `render.py`: voiceover, title cards and ffmpeg
- `notify.py`: phone notifications through ntfy

## Cost per video (roughly)

One ChatGPT script, one Claude plan (Opus 5.5: $4 / $20 per million input/output tokens) and about 45 seconds of text-to-speech. Expect a few cents per video; check each provider's pricing page for current rates.
