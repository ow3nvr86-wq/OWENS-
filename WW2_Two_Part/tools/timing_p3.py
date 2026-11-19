"""Part 3 (Midway): scene_timing.json and captions from the measured word times of George's narration."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'part3')
DUR = 38.5
HL = {'SIX', 'MONTHS', 'PEARL', 'HARBOR', 'UNSTOPPABLE', 'THREE', 'CARRIERS', 'TRAP', 'MIDWAY', 'CODEBREAKERS', 'JUNE', '4TH', '1942',
      'TORPEDO', 'WIPED', 'DIVE', 'BOMBERS', 'BURNING', 'FOURTH', 'SUNK', 'NEVER', 'TURNED'}
GLUE = {'in', 'to', 'the', 'a', 'on', 'it', 'of', 'and', 'by', 'with', 'an', 'is', 'from', 'then', 'but', 'two', 'its', 'had', 'out', 'down', 'was',
        'were', 'few', 'at', 'after'}


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
        six=('six',), pearl=('pearl',), harbor=('harbor',), unstoppable=('unstoppable',), then=('then',), minutes=('minutes',),
        three=('three',), carriers=('carriers',), planned=('planned',), trap=('trap',), midway=('midway',), tiny=('tiny',),
        island=('island',), pacific=('pacific',), american=('american',), codebreakers=('codebreakers',), secret=('secret',),
        messages=('messages',), june=('june',), y1942=('1942',), fleets=('fleets',), met=('met',), torpedo=('torpedo',),
        planes=('planes',), attacked=('attacked',), wiped=('wiped',), out=('out',), pulled=('pulled',), fighters=('fighters',),
        waves=('waves',), dive=('dive',), bombers=('bombers',), clouds=('clouds',), three2=('three', 2), hit=('hit',),
        burning=('burning',), minutes2=('minutes', 2), fourth=('fourth',), fought=('fought',), sunk=('sunk',), never=('never',),
        recovered=('recovered',), edge=('edge',), tide=('tide',), war=('war',), turned=('turned',)).items()}
    E['voice_end'] = round(W[-1]['end'], 3)
    Y = 0.185
    titles = [
        dict(start=E['pearl'] - 0.05, end=E['then'] - 0.06, style='date', text='DEC 7, 1941', y=Y),
        dict(start=E['pearl'] + 0.55, end=E['then'] - 0.06, style='plate', text='6 MONTHS LATER', y=Y + 0.062),
        dict(start=E['three'], end=E['planned'] - 0.06, style='big', text='3 CARRIERS|LOST IN MINUTES', y=Y + 0.025),
        dict(start=E['planned'], end=E['american'] - 0.06, style='date', text='JAPAN\'S PLAN', y=Y),
        dict(start=E['trap'], end=E['american'] - 0.06, style='plate', text='AN AMBUSH AT MIDWAY ATOLL', y=Y + 0.062),
        dict(start=E['codebreakers'], end=E['june'] - 0.06, style='date', text='US NAVY CODEBREAKERS', y=Y),
        dict(start=E['secret'], end=E['june'] - 0.06, style='plateb', text='STATION HYPO, HAWAII', y=Y + 0.062),
        dict(start=E['june'], end=E['torpedo'] - 0.06, style='date', text='JUNE 4, 1942', y=Y),
        dict(start=E['torpedo'], end=E['dive'] - 0.06, style='plateb', text='US TORPEDO PLANES', y=Y),
        dict(start=E['dive'], end=E['hit'] - 0.05, style='plateb', text='US DIVE BOMBERS', y=Y),
        dict(start=E['hit'], end=E['fourth'] - 0.05, style='plate', text='AKAGI  -  KAGA  -  SORYU', y=Y),
        dict(start=E['sunk'] - 0.1, end=E['never'] - 0.05, style='plate', text='HIRYU SUNK', y=Y),
        dict(start=E['tide'], end=DUR, style='big', text='TURNING POINT|BATTLE OF MIDWAY, JUNE 1942', y=Y + 0.03),
    ]
    T = {'title': 'The Battle of Midway', 'duration': DUR, 'events': E, 'titles': titles,
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
        key = lambda x: re.sub(r"[^A-Z0-9']", '', x['w'].upper())
        caps.append({'text': ' '.join(x['w'] for x in g), 'start': g[0]['start'], 'end': g[-1]['end'], 'hl': [key(x) for x in g if key(x) in HL]})
    for k, c in enumerate(caps):
        nxt = caps[k + 1]['start'] if k + 1 < len(caps) else DUR
        c['until'] = round(min(nxt, c['end'] + 0.5), 3)
    json.dump({'captions': caps}, open(os.path.join(D, 'build', 'vo_timing.json'), 'w'), indent=1)
    print(' | '.join(c['text'] for c in caps))


if __name__ == '__main__':
    main()
