# Research report: the Great Molasses Flood (Boston, 1919)

## Why this topic

It sounds like a joke ("a wave of syrup"), but it was a real industrial disaster that killed 21 people. It has a strong visual hook (a brown wave through city streets), a clear cause-and-effect story (cut corners, then a weather change, then failure), and a surprising science payoff (cooling made the molasses deadlier, not the speed).

## Verified facts used in the script

| Claim (as used in the video) | Value used | Sources | Notes |
|---|---|---|---|
| Date and place | 15 January 1919, North End, Boston (Commercial Street) | [1] [2] [5] | The tank belonged to Purity Distilling, owned by US Industrial Alcohol (USIA). |
| Time of collapse | "around 12:40" | [2] [4] | Wikipedia [1] says about 12:30. History.com [2] and the Christian Science Monitor [4] say 12:40. I wrote "around". |
| Tank size | 50 ft tall, 90 ft wide ("five stories tall") | [1] [4] [5] | A History.com photo caption says 58 × 98 ft. The body text of [2] and the other sources say 50 ft. |
| Volume | 2.3 million US gallons | [1] [2] [4] [5] | Some sources say 2.5 million or "more than two million". 2.3 million is the most common figure. |
| Weight | ≈ 13,000 tons (on-screen only) | [1] | 13,000 short tons. NBC [5] gives 26 million lb (the same figure). |
| Deaths and injuries | 21 killed, about 150 injured | [1] [2] [4] [5] | Every source agrees. |
| Leaked from day one | Yes | [5] | Historian Stephen Puleo, quoted by NBC: the tank "starts leaking on Day 1". |
| Man in charge had no engineering experience | Arthur Jell, treasurer and project manager | [1] [5] | Puleo: "no technical experience, no architectural experience, no engineering experience." |
| Skipped a proper water test ("6 inches") | Filled with only 6 inches of water | [1] [5] | NBC [5] and Wikipedia [1] agree. |
| Painted brown to hide the leaks | Yes, in 1918 | [1] [5] | Wikipedia and NBC agree. |
| Cold snap, then above 40 °F | Low of 2 °F days earlier, then 40+ °F | [1] [2] [5] | Wikipedia: rose from 2 °F to 41 °F. History.com: "over 40 degrees". |
| Rivets like machine-gun fire | Witness description | [1] | Wikipedia cites witnesses describing a machine-gun-like sound as rivets shot out. |
| Wave height | "up to 25 feet" | [1] [5] | Estimates range from 15 to 40 ft. 25 ft is Puleo's figure (NBC) and Wikipedia's body text. I wrote "up to". |
| Wave speed | 35 mph | [1] [3] [5] | Wikipedia, Atlas Obscura and NBC. The CSM gives "more than 50 ft/s" (≈ 34 mph). |
| Knocked buildings off foundations; hit the elevated railway | Yes | [1] [6] | Wikipedia: buildings swept off their foundations, elevated railway girders damaged. |
| Viscosity rose as it cooled (≥ 4×) | "Scientists estimate at least four times" | [4] [7] | Sharp, Kennedy and Rubinstein, APS Division of Fluid Dynamics meeting, 2016 (a conference talk, not a journal paper). Nicole Sharp estimated a factor of four or more after the overnight drop below freezing. |
| About half the victims died because they were stuck | Rubinstein quote | [4] | Christian Science Monitor: Rubinstein said about half the victims "died basically because they were stuck". |
| Smelled sweet on hot days for decades | Residents' reports | [1] [2] | Wikipedia: residents reported the smell for decades. History.com caption: "The smell of molasses lingered for decades." |
| End card: fastest human sprint ≈ 28 mph | Usain Bolt's peak ≈ 12.4 m/s (≈ 27.8 mph), Berlin 2009 | [8] | Published peaks range from 12.2 to 12.4 m/s, so I show it as "≈ 28 mph". |

## Facts researched but not used (to keep under 60 s)

- 116 cadets from the training ship USS Nantucket were among the first rescuers [1].
- USIA blamed anarchist sabotage. In 1925 auditor Hugh W. Ogden found the company responsible, and USIA paid $628,000 in damages [1] [2].
- Afterwards, Boston required engineers' and architects' calculations to be filed and stamped. This later spread nationwide [5].
- Today the site is Langone Park, and a plaque marks it [1] [6].
- A 2014–2015 analysis by engineer Ronald Mayville found the steel was too thin and low in manganese, which made it brittle [1] [4].

## How the visuals relate to the facts (honesty notes)

- **The flood is simulated, not hand-animated.** `scripts/simulate_flood.py` solves the 2D shallow-water equations for an instantaneous dam break of 8,700 m³ (the tank's capacity) on a 1 m grid. Buildings act as walls. Bed friction and a viscosity that rises ×4 as the evening cools follow the 2016 estimate. The model is simplified: the street layout is illustrative, not a survey of 1919 Commercial Street, and the tank's real failure was not instantaneous.
- **The simulation gives a lower wave than eyewitnesses reported.** It peaks at about 4.5 m (15 ft) in the street and about 24 mph along it. In the wave shots, the renderer steepens the thin leading edge and exaggerates height by up to 1.5× (`WAVE_SHOTS` in `animation.py`), so the picture matches the historical "up to 25 ft / 35 mph" estimates the narration quotes. This is a stylistic choice, documented here and in the README. The on-screen numbers come from the historical sources, not from the simulation.
- **The 1915 and 1918 shots are flashbacks**, labelled on screen with their year.
- **The people are simple stylised mannequins.** They are not likenesses of the real victims or of Arthur Jell.

## Sources

1. Wikipedia, "Great Molasses Flood" — https://en.wikipedia.org/wiki/Great_Molasses_Flood
2. History.com (Evan Andrews), "The Great Molasses Flood of 1919" — https://www.history.com/news/the-great-molasses-flood-of-1919
3. Atlas Obscura, "100 Wonders: The Great Boston Molasses Flood" — https://www.atlasobscura.com/articles/5382
4. Christian Science Monitor (29 Nov 2016), "Scientists finally decode the Great Molasses Flood of 1919" — https://www.csmonitor.com/Science/2016/1129/Scientists-finally-decode-the-Great-Molasses-Flood-of-1919
5. NBC News (15 Jan 2019), "Great Boston Molasses Flood of 1919 killed 21 after 2 million gallons…" — https://www.nbcnews.com/news/us-news/great-boston-molasses-flood-1919-killed-21-after-2-million-n958326
6. NPR (13 Jan 2019), "After 100 Years, A Look Back At Boston's Great Molasses Flood Of 1919" — https://www.npr.org/2019/01/13/684894921/after-100-years-a-look-back-at-bostons-great-molasses-flood-of-1919
7. APS Division of Fluid Dynamics 2016, abstract L27.8, "In a sea of sticky molasses: The physics of the Boston Molasses Flood" (Sharp, Kennedy, Rubinstein) — https://archive.aps.org/dfd/2016/l27/8
8. ScienceABC, Usain Bolt's speed (≈ 12.4 m/s peak, Berlin 2009) — https://www.scienceabc.com/sports/science-usain-bolt-speed-height-age-body-structure-stride-length.html
