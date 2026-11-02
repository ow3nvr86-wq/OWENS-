# make_shorts.py: long video → captioned Shorts

Turns a recording into vertical **1080×1920** clips with **burned-in captions**,
ready for YouTube Shorts, TikTok and Instagram Reels.

> **Copyright:** only post clips of videos you own or have permission to use.
> Re-uploading someone else's YouTube video as a Short, screen-recorded or not,
> usually gets you copyright claims or strikes.

## One-time setup

1. Install **ffmpeg**:
   - Windows: `winget install ffmpeg`
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
2. Install **Python 3.9+**, then:

   ```bash
   pip install -r shorts/requirements.txt
   ```

The first run downloads the Whisper speech model (~150 MB for `base`).

## Usage

**Let it pick the best moments:**

```bash
python shorts/make_shorts.py "my recording.mp4" --auto 3
```

**See the transcript first, then choose your own timestamps:**

```bash
python shorts/make_shorts.py "my recording.mp4" --list
```

```bash
python shorts/make_shorts.py "my recording.mp4" --clips "1:05-1:40,4:10-4:55"
```

**Add a hook title at the top:**

```bash
python shorts/make_shorts.py "my recording.mp4" --clips "2:00-2:45" --title "He did NOT see that coming"
```

## Many Shorts from one long video

For an hour-long video, list your picks in a text file, one Short per line,
each with an optional on-screen title (lines starting with `#` are ignored):

```text
# START-END | on-screen title
12:05-12:40 | He did NOT see that coming
31:10-31:52 | The face at the end, though
48:00-48:35
```

```bash
python shorts/make_shorts.py "my 1 hour video.mp4" --clips-file clips.txt
```

Or let it pick. Automatic picks are spread across the whole video, and
`--auto-title` uses each clip's opening line as its hook:

```bash
python shorts/make_shorts.py "my 1 hour video.mp4" --auto 10 --auto-title
```

Everything lands in `shorts/out/`:

| File | What it is |
|---|---|
| `<name>_short01.mp4` … | the finished Shorts |
| `<name>_shorts.md` | suggested title, transcript and hashtags for each clip |
| `<name>.transcript.txt` | full transcript with timestamps |
| `<name>.transcript.json` | cache, so later runs skip transcribing |

## Screen recordings

Screen recordings often include the browser tabs, address bar or taskbar.
Cut them off with `--source-crop W:H:X:Y`, which keeps a W×H box starting X
pixels from the left and Y pixels from the top. For a 1920×1080 recording with
a 130px browser bar on top and a 50px taskbar at the bottom:

```bash
python shorts/make_shorts.py rec.mp4 --source-crop 1920:900:0:130 --auto 3
```

Tip: put the YouTube player in **full screen** before recording, then you
don't need this.

## Looks

| Option | Choices | Default |
|---|---|---|
| `--layout` | `blur`: whole video over a blurred fill · `crop`: fills the screen, cuts the sides · `fit`: black bars | `blur` |
| `--zoom` | blur layout: e.g. `1.4` makes the video bigger (cuts its edges) | `1.0` |
| `--crop-x` | crop layout focus: `0` left · `0.5` centre · `1` right | `0.5` |
| `--style` | `highlight`: current word coloured · `plain` · `none` | `highlight` |
| `--highlight-color` | `yellow` `green` `cyan` `red` `pink` `orange` `white` | `yellow` |
| `--font` / `--font-size` | any installed font, e.g. `"Arial Black"`, `Impact`, `Montserrat` | `Arial` / `84` |
| `--words-per-line` | words on screen at once | `3` |
| `--no-upper` | normal case instead of ALL CAPS | off |
| `--caption-pos` / `--title-pos` | height on screen, `0` top → `1` bottom | `0.70` / `0.14` |

Accuracy: `--model small` or `--model medium` transcribes more accurately but
more slowly. Use `--language en` to skip language detection.

Run `python shorts/make_shorts.py --help` for every option.
