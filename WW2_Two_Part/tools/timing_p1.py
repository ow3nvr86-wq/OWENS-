"""Part 1: build part1/scene_timing.json and the word-by-word captions from the measured word times of the voiceover
(part1/build/words.json), so every camera move, flood, arrow, title and sound lands on the word it belongs to."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'part1')
HL = {'1939', 'HITLER', '1ST', 'POLAND', 'WAR', '1940', 'SIX', 'WEEKS', 'SURRENDER', 'EAST', 'THREE', 'MILLION', 'TWENTY', 'MILES',
      'MOSCOW', '7TH', 'PEARL', 'HARBOR', 'TWO', 'APART'}
GLUE = {'in', 'to', 'the', 'a', 'on', 'it', 'so', 'of', 'and', 'by', 'with', 'this', 'was', 'they\'re', 'than', 'from', 'just', 'into',
        'then', 'how', 'all', 'one', 'part', 'less', 'over'}


def main():
    J = json.load(open(os.path.join(D, 'build', 'words.json')))
    W = J['words']
    dur = math_ceil(J['duration'] + 0.75)

    def clean(w):
        return re.sub(r"[^a-z0-9']", '', w.lower())

    def at(word, n=1):
        k = 0
        for x in W:
            if clean(x['w']) == word:
                k += 1
                if k == n:
                    return round(x['start'], 3)
        raise KeyError(word)

    E = {k: at(*v) for k, v in dict(
        y1939=('1939',), europe=('europe',), two=('two',), later=('later',), hitler=('hitler',), most=('most',),
        sept=('september',), first=('1st',), y1939b=('1939', 2), germany=('germany',), invades=('invades',), poland=('poland',),
        britain=('britain',), france=('france',), declare=('declare',), war=('war',), in1940=('in', 2), y1940=('1940',),
        tanks=('tanks',), west=('west',), france2=('france', 2), biggest=('biggest',), earth=('earth',), falls=('falls',),
        six=('six',), weeks=('weeks',), britain2=('britain', 2), refuses=('refuses',), surrender=('surrender',), so=('so',),
        hitler2=('hitler', 2), turns=('turns',), east=('east',), over=('over',), three=('three',), million=('million',),
        troops=('troops',), pour=('pour',), soviet=('soviet',), by=('by',), december=('december',), less=('less',),
        twenty=('twenty',), miles=('miles',), moscow=('moscow',), then=('then',), december7=('december', 2), seventh=('7th',),
        japan=('japan',), attacks=('attacks',), pearl=('pearl',), harbor=('harbor',), part=('part',), two2=('two', 2),
        how=('how',), fell=('fell',), apart=('apart',)).items()}
    E['voice_end'] = round(W[-1]['end'], 3)
    Y = 0.185
    titles = [
        dict(start=E['y1939'], end=E['two'] + 0.02, style='year', text='1939', y=Y),
        dict(start=E['two'] + 0.02, end=E['later'] + 0.1, style='year', text='1940', y=Y),
        dict(start=E['later'] + 0.1, end=E['sept'] - 0.12, style='year', text='1941', y=Y),
        dict(start=E['sept'], end=E['britain'] - 0.08, style='date', text='SEPT 1, 1939', y=Y),
        dict(start=E['britain'], end=E['in1940'] - 0.06, style='date', text='SEPT 3, 1939', y=Y),
        dict(start=E['war'], end=E['in1940'] - 0.06, style='plateb', text='BRITAIN AND FRANCE DECLARE WAR', y=Y + 0.062),
        dict(start=E['y1940'], end=E['france2'] - 0.08, style='year', text='1940', y=Y),
        dict(start=E['france2'], end=E['falls'] - 0.05, style='date', text='MAY 1940', y=Y),
        dict(start=E['falls'], end=E['six'] - 0.03, style='plate', text='FRANCE FALLS', y=Y),
        dict(start=E['six'], end=E['britain2'] - 0.08, style='big', text='6 WEEKS|MAY 10 - JUNE 22, 1940', y=Y + 0.012),
        dict(start=E['britain2'], end=E['so'] - 0.06, style='date', text='SUMMER 1940', y=Y),
        dict(start=E['refuses'], end=E['so'] - 0.06, style='plateb', text='THE BATTLE OF BRITAIN', y=Y + 0.062),
        dict(start=E['so'], end=E['over'] - 0.06, style='year', text='1941', y=Y),
        dict(start=E['over'], end=E['by'] - 0.06, style='plate', text='JUNE 22, 1941', y=0.152),
        dict(start=E['december'], end=E['then'] - 0.05, style='date', text='DECEMBER 1941', y=Y),
        dict(start=E['december7'], end=E['part'] - 0.06, style='date', text='DEC 7, 1941', y=Y),
        dict(start=E['part'], end=dur, style='part', text='PART 2', y=Y + 0.01),
        dict(start=E['how'], end=dur, style='plate', text='HOW IT ALL FELL APART', y=Y + 0.105),
    ]
    T = {'title': 'World War II, Part 1: How Hitler Took Europe', 'duration': dur, 'events': E, 'titles': titles,
         'scenes': [{'id': 1, 'key': 'main', 'name': 'One continuous map shot', 'start': 0.0, 'end': dur}]}
    json.dump(T, open(os.path.join(D, 'scene_timing.json'), 'w'), indent=1)

    caps, i = [], 0
    while i < len(W):
        g = [W[i]]
        while clean(g[-1]['w']) in GLUE and i + 1 < len(W) and W[i + 1]['line'] == W[i]['line'] and len(g) < 3 \
                and len(' '.join(x['w'] for x in g)) < 9:
            i += 1
            g.append(W[i])
        i += 1
        caps.append({'text': ' '.join(x['w'] for x in g), 'start': g[0]['start'], 'end': g[-1]['end'],
                     'hl': [x['w'].upper().strip('.,:?') for x in g if x['w'].upper().strip('.,:?') in HL]})
    for k, c in enumerate(caps):
        nxt = caps[k + 1]['start'] if k + 1 < len(caps) else dur
        c['until'] = round(min(nxt, c['end'] + 0.5), 3)
    json.dump({'captions': caps}, open(os.path.join(D, 'build', 'vo_timing.json'), 'w'), indent=1)

    def srt(t):
        ms = int(round(t * 1000))
        return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'
    lines = {}
    for x in W:
        lines.setdefault(x['line'], []).append(x)
    with open(os.path.join(D, 'subtitles.srt'), 'w') as fh:
        for n, (k, ws) in enumerate(sorted(lines.items()), 1):
            fh.write(f"{n}\n{srt(ws[0]['start'])} --> {srt(ws[-1]['end'])}\n{' '.join(w['w'] for w in ws)}\n\n")
    print('duration', dur, '|', ' | '.join(c['text'] for c in caps))


def math_ceil(x):
    import math
    return math.ceil(x * 2) / 2


if __name__ == '__main__':
    main()
