"""Part 2: build part2/scene_timing.json and the word-by-word captions from the measured word times of the narration."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'part2')
DUR = 38.5
HL = {'TWO', 'UNSTOPPABLE', 'FROZEN', 'BREAK', 'STALINGRAD', '1943', 'SURRENDERS', 'PACIFIC', '6TH', '1944', 'D-DAY', '156,000',
      'NORMANDY', 'CRUSHED', '1945', 'BERLIN', 'ATOMIC', 'BOMBS', 'JAPAN', 'OVER', '70', '85', 'MILLION'}
GLUE = {'in', 'to', 'the', 'a', 'on', 'it', 'of', 'and', 'by', 'with', 'an', 'is', 'from', 'then', 'part', 'one', 'both', 'about', 'two'}


def main():
    W = json.load(open(os.path.join(D, 'build', 'words.json')))['words']

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
        part=('part',), two=('two',), hitlers=("hitler's",), empire=('empire',), unstoppable=('unstoppable',), then=('then',),
        frozen=('frozen',), city=('city',), began=('began',), brk=('break',), stalingrad=('stalingrad',), y1943=('1943',),
        an=('an',), entire=('entire',), german=('german',), army=('army',), surrenders=('surrenders',), america=('america',),
        fights=('fights',), across=('across',), pacific=('pacific',), june=('june',), sixth=('6th',), y1944=('1944',),
        dday=('dday',), about=('about',), n156=('156000',), allied=('allied',), troops=('troops',), land=('land',),
        normandy=('normandy',), single=('single',), day=('day',), germany=('germany',), crushed=('crushed',), both=('both',),
        sides=('sides',), inmay=('in', 4), may=('may',), y1945=('1945',), soviet=('soviet',), berlin=('berlin',),
        surrenders2=('surrenders', 2), august=('august',), two2=('two', 2), atomic=('atomic',), bombs=('bombs',), fall=('fall',),
        japan=('japan',), by=('by',), september=('september',), war=('war',), over=('over',), estimated=('estimated',),
        seventy=('70',), eightyfive=('85',), million=('million',), people=('people',), died=('died',)).items()}
    E['n156'] = round(min(E['n156'], E['about'] + 0.32), 3)
    E['voice_end'] = round(W[-1]['end'], 3)
    Y = 0.185
    titles = [
        dict(start=E['part'], end=E['hitlers'] - 0.06, style='part', text='PART 2', y=Y + 0.01),
        dict(start=E['hitlers'], end=E['then'] - 0.06, style='year', text='1942', y=Y),
        dict(start=E['empire'], end=E['then'] - 0.06, style='plate', text="HITLER'S EMPIRE AT ITS PEAK", y=Y + 0.075),
        dict(start=E['frozen'], end=E['stalingrad'] - 0.05, style='date', text='WINTER 1942', y=Y),
        dict(start=E['stalingrad'], end=E['america'] - 0.08, style='date', text='STALINGRAD', y=Y),
        dict(start=E['surrenders'], end=E['america'] - 0.08, style='plateb', text='FEB 2, 1943: THE GERMAN 6TH ARMY SURRENDERS', y=Y + 0.062),
        dict(start=E['america'] + 0.35, end=E['june'] - 0.08, style='date', text='1942 - 1945', y=Y),
        dict(start=E['fights'] + 0.3, end=E['june'] - 0.08, style='plateb', text='ISLAND BY ISLAND TOWARDS JAPAN', y=Y + 0.062),
        dict(start=E['june'], end=E['about'] - 0.06, style='date', text='JUNE 6, 1944', y=0.163),
        dict(start=E['dday'], end=E['about'] - 0.06, style='big', text='D-DAY', y=0.262),
        dict(start=E['germany'], end=E['may'] - 0.05, style='date', text='1944 - 1945', y=Y),
        dict(start=E['y1945'], end=E['august'] - 0.08, style='date', text='MAY 8, 1945', y=Y),
        dict(start=E['surrenders2'], end=E['august'] - 0.08, style='plateb', text='GERMANY SURRENDERS', y=Y + 0.062),
        dict(start=E['august'], end=E['by'] - 0.06, style='date', text='AUGUST 1945', y=Y),
        dict(start=E['september'], end=E['estimated'] - 0.06, style='date', text='SEPT 2, 1945', y=Y),
        dict(start=E['war'], end=E['estimated'] - 0.06, style='plateb', text='JAPAN SURRENDERS. THE WAR IS OVER.', y=Y + 0.062),
    ]
    T = {'title': 'World War II, Part 2: How It All Fell Apart', 'duration': DUR, 'events': E, 'titles': titles,
         'scenes': [{'id': 1, 'key': 'main', 'name': 'One continuous map shot', 'start': 0.0, 'end': DUR}]}
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
                     'hl': [x['w'].upper().strip('.:?') .rstrip(',') for x in g if x['w'].upper().strip('.:?').rstrip(',') in HL]})
    for k, c in enumerate(caps):
        nxt = caps[k + 1]['start'] if k + 1 < len(caps) else DUR
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
    print(' | '.join(c['text'] for c in caps))


if __name__ == '__main__':
    main()
