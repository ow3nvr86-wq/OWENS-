"""Build scene_timing.json from the measured narration: every cut, title, stamp, label and sound cue is placed on
the word it belongs to (build/words.json, from tools/words.py), and the word-by-word captions are written to
build/vo_timing.json.

  python tools/timing.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DURATION = 32.0

# caption words shown in gold: dates, numbers, and the twist
GOLD = {'476', 'WRONG', 'THREE', 'ONE', 'FOUR', '117', 'AD', 'TWO', 'THOUSAND', '1453'}
# short words that ride with the next word in the word-by-word captions
GLUE = {'you', 'in', 'to', 'at', 'its', 'the', 'a', 'on', 'it', 'so', 'of', 'and', 'for', 'but', 'did', 'were',
        "that's", 'then', 'from', 'under', 'until', 'more'}


def main():
    W = json.load(open(os.path.join(ROOT, 'build', 'words.json')))
    lines = json.load(open(os.path.join(ROOT, 'build', 'vo_lines.json')))['lines']

    def clean(w):
        return re.sub(r"[^a-z0-9']", '', w.lower())

    def at(word, n=1, after=0.0, key='start'):
        """Time of the n-th occurrence of `word` at or after `after`."""
        k = 0
        for x in W:
            if clean(x['w']) == word and x['start'] >= after - 1e-6:
                k += 1
                if k == n:
                    return round(x[key], 3)
        raise KeyError(word)

    L = {l['i']: l for l in lines}
    ev = {
        'drum0': 0.0,
        'stamp': at('476'),
        'slash': at('wrong'),
        'line1_end': L[1]['end'],
        'peak': at('peak'),
        'rome': at('rome', 1, 4.0), 'hispania': at('from', 1, 4.0), 'britain': at('britain'), 'egypt': at('egypt'),
        'continents': at('three'), 'crowd': at('one', 1, 7.0), 'quarter': at('four', 1, 7.0), 'earth': at('earth'),
        'y117': at('117'), 'ad': at('ad'), 'trajan': at('trajan'), 'biggest': at('biggest'), 'ever': at('ever'),
        'cracked': at('cracked'), 'civil': at('civil'), 'wars': at('wars'), 'plague': at('plague'),
        'invaders': at('invaders'), 'every': at('every'), 'border': at('border'),
        'so_split': at('so', 1, 19.0), 'split': at('split'), 'two': at('two'),
        'in476': at('476', 2), 'collapsed': at('collapsed'), 'but': at('but'), 'east': at('east'), 'going': at('going'),
        'for': at('for', 1, 25.0), 'thousand': at('thousand'), 'until': at('until'), 'y1453': at('1453'),
        'question': at('so', 1, 28.5), 'when': at('when'), 'fall': at('fall'), 'voice_end': L[len(L) - 1]['end'],
    }
    # cuts: between lines where there is a gap, or a beat before the word a new picture belongs to
    cuts = {
        'scale': round((L[1]['end'] + L[2]['start']) / 2, 3),        # the cracked frame shatters into the map
        'trajan': round((L[3]['end'] + L[4]['start']) / 2, 3),       # hard cut
        'clash': round(ev['civil'] - 0.08, 3),
        'plague': round(ev['plague'] - 0.08, 3),
        'divide': round(ev['invaders'] - 0.08, 3),
        'end': round(ev['question'] - 0.06, 3),                       # ink bleed back to the opening shot
    }
    order = ['hook', 'scale', 'trajan', 'clash', 'plague', 'divide', 'end']
    starts = [0.0] + [cuts[k] for k in order[1:]]
    ends = starts[1:] + [DURATION]
    names = {'hook': 'The hook', 'scale': 'The scale', 'trajan': 'The height of power', 'clash': 'The crack: civil wars',
             'plague': 'The crack: plague', 'divide': 'Invaders, the split, the fall of the West, the East to 1453',
             'end': 'The question (loops to the opening frame)'}
    scenes = [{'id': i + 1, 'key': k, 'name': names[k], 'start': round(a, 3), 'end': round(b, 3)}
              for i, (k, a, b) in enumerate(zip(order, starts, ends))]
    titles = [
        {'start': ev['continents'] + 0.05, 'end': ev['crowd'] - 0.05, 'style': 'gold', 'text': '3 CONTINENTS', 'y': 0.175},
        {'start': ev['quarter'] - 0.1, 'end': cuts['trajan'], 'style': 'gold', 'text': '~1 IN 4 PEOPLE|ON EARTH', 'y': 0.19},
        {'start': ev['y117'], 'end': ev['ever'] + 0.55, 'style': 'slam', 'text': '117 AD|PEAK EXPANSION', 'y': 0.19},
        {'start': ev['split'] + 0.06, 'end': ev['in476'] - 0.08, 'style': 'slam', 'text': '395 AD|THE SPLIT', 'y': 0.19},
        {'start': ev['in476'], 'end': ev['but'] - 0.06, 'style': 'slam_red', 'text': '476 AD|WESTERN ROME FALLS', 'y': 0.19},
        {'start': ev['but'] + 0.05, 'end': ev['for'] - 0.05, 'style': 'slam_purple', 'text': 'THE EAST|SURVIVES', 'y': 0.19},
        {'start': ev['question'] + 0.08, 'end': DURATION - 0.45, 'style': 'question', 'text': 'WHEN DID ROME|REALLY FALL?', 'y': 0.215},
    ]
    T = {'title': 'Rome Never Fell in 476', 'duration': DURATION, 'scenes': scenes, 'events': ev, 'cuts': cuts,
         'titles': titles, 'lines': [{'scene': None, 'text': l['text'], 'start': l['start'], 'end': l['end']} for l in lines]}
    json.dump(T, open(os.path.join(ROOT, 'scene_timing.json'), 'w'), indent=1)

    # word-by-word captions (short words ride with the next one); the final question is shown as a title instead
    caps = []
    i = 0
    last_line = len(L) - 1
    while i < len(W):
        g = [W[i]]
        while clean(g[-1]['w']) in GLUE and i + 1 < len(W) and W[i + 1]['line'] == W[i]['line'] and len(g) < 3:
            i += 1
            g.append(W[i])
        i += 1
        if g[0]['line'] == last_line:
            continue
        caps.append({'text': ' '.join(x['w'] for x in g), 'start': g[0]['start'], 'end': g[-1]['end'], 'line': g[0]['line'],
                     'gold': [x['w'].upper().strip('.,:?') for x in g if x['w'].upper().strip('.,:?') in GOLD]})
    for k in range(len(caps)):
        nxt = caps[k + 1]['start'] if k + 1 < len(caps) else DURATION
        # a word stays up until the next one, or a short beat after it ends at a pause
        caps[k]['until'] = round(min(nxt, caps[k]['end'] + 0.45, cuts['end'] - 0.02), 3)
    json.dump({'captions': caps}, open(os.path.join(ROOT, 'build', 'vo_timing.json'), 'w'), indent=1)

    def srt(t):
        ms = int(round(t * 1000))
        return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'
    with open(os.path.join(ROOT, 'subtitles.srt'), 'w') as fh:
        for n, l in enumerate(lines, 1):
            fh.write(f"{n}\n{srt(l['start'])} --> {srt(l['end'])}\n{l['text']}\n\n")
    for s in scenes:
        print(f"{s['start']:6.2f}-{s['end']:6.2f}  {s['key']}")
    print(len(caps), 'caption groups;', ' | '.join(c['text'] for c in caps[:14]), '...')


if __name__ == '__main__':
    main()
