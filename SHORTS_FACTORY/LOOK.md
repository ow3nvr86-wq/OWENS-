# The house colour look (default for every video)

Every Short uses the **Rick's Clips look**, `looks/ricks_clips.json`. The user asked for it on 2026-11-15 for this video and all future ones.

## How it was measured

- **Frames:** 144 real frames from 48 Shorts on the Rick's Clips channel (@RicksClips3000), YouTube's auto-captured frames at 25 / 50 / 75 % of each video, cropped to 9:16. No frames or assets are copied into our videos. Only colour statistics are matched.
- **Tool:** `tools/look_stats.py`, which reports luminance percentiles, saturation, shadow / mid / highlight tint, warmth and vignette.

| | Rick's Clips | Our GTA v1 (before) | Our frames graded with the look |
|---|---|---|---|
| luminance median (p50) | 0.455 | 0.571 | about 0.40-0.43 |
| dark tail (p10 / p25) | 0.144 / 0.263 | 0.355 / 0.474 | about 0.11 / 0.22 |
| share of deep shadow (L < 0.25) | 23 % | 6 % | about 25-29 % |
| mean saturation | 0.436 | 0.224 | about 0.42 |
| shadow colour | plum / warm (R > B > G) | neutral grey | plum / warm |
| vignette (edge / centre) | 0.81 | 0.96 | about 0.75 |

In words, the look has:
- rich, saturated colour;
- deep shadows that lean plum and brown, never grey;
- clean whites (the characters' heads stay white);
- darker edges.

## How it is applied

The look is a tone curve (fitted by matching luminance percentiles), saturation, split toning (shadow and highlight tint) and a vignette.
- **Shorts Factory engine:** `engine/look.js` applies it to every frame after motion blur and before the captions. It is on by default. Use `script.json` `"look": "<name>"` for another look, or `"none"` to turn it off.
- **Any other pipeline** (Blender-only, PIL post): `$SHORTS_PY SHORTS_FACTORY/tools/look.py apply SHORTS_FACTORY/looks/ricks_clips.json in.jpg out.jpg` gives the same maths in numpy. Apply it per frame before captions are drawn.
- **Re-fit or a new reference:**
  ```
  $SHORTS_PY tools/look.py fit "<our frames>" "<reference frames>" looks/<name>.json [--crop-vertical-ref]
  ```
  Then check a before / after / reference contact sheet. The fitted shadow and highlight tints were halved and cut to 30 % by eye, because at full strength white heads turned blue.

## Lighting to go with it

- Light the 3D world for contrast: a strong key (sun or a warm practical lamp) and real shadow areas.
- Warm practical lights (lamps, signs, windows) read well under this grade.
- Don't flatten the scene with fill light; the grade will not invent shadows that the render doesn't have.
