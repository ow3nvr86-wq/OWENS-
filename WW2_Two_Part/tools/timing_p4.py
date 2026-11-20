"""Part 4 (Cuban Missile Crisis): scene_timing.json and captions from the measured word times of George's narration."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'part4')
DUR = 40.5
HL = {'OCTOBER', '1962', 'MISSILES', 'CUBA', '90', 'FLORIDA', 'QUARANTINE', 'SHIPS', 'SUBMARINE', 'NUCLEAR', 'TORPEDO', 'ARKHIPOV', 'CREDITED',
      'KHRUSHCHEV', 'REMOVE', 'SECRET', 'TURKEY', 'CLOSEST', 'WAR', '22ND', '28TH'}
GLUE = {'in', 'to', 'the', 'a', 'on', 'it', 'of', 'and', 'by', 'with', 'an', 'is', 'from', 'then', 'its', 'if', 'not', 'went', 'was', 'were', 'call',
        'has', 'also', 'her', 'his', 'out', 'over'}


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
        oct1=('october',), y1962=('1962',), spy=('spy',), plane=('plane',), found=('found',), soviet=('soviet',), missiles=('missiles',),
        cuba=('cuba',), ninety=('90',), miles=('miles',), florida=('florida',), oct2=('october', 2), d22=('22nd',), kennedy=('kennedy',),
        television=('television',), announced=('announced',), quarantine=('quarantine',), cuba2=('cuba', 2), ships=('ships',),
        sailing=('sailing',), line=('line',), beneath=('beneath',), submarine=('submarine',), carried=('carried',), nuclear=('nuclear',),
        torpedo=('torpedo',), hunting=('hunting',), officer=('officer',), vasili=('vasili',), arkhipov=('arkhipov',), credited=('credited',),
        refusing=('refusing',), fire=('fire',), oct3=('october', 3), d28=('28th',), khrushchev=('khrushchev',), agreed=('agreed',),
        remove=('remove',), missiles2=('missiles', 2), invade=('invade',), cuba3=('cuba', 3), secret=('secret',), deal=('deal',),
        turkey=('turkey',), historians=('historians',), closest=('closest',), nuclear2=('nuclear', 2), war=('war',)).items()}
    E['voice_end'] = round(W[-1]['end'], 3)
    Y = 0.185
    titles = [
        dict(start=E['oct1'], end=E['ninety'] - 0.05, style='date', text='OCTOBER 1962', y=Y),
        dict(start=E['spy'], end=E['ninety'] - 0.05, style='plateb', text='U-2 SPY PLANE', y=Y + 0.062),
        dict(start=E['ninety'], end=E['florida'] + 0.35, style='big', text='90 MILES|FROM FLORIDA', y=Y + 0.025),
        dict(start=E['oct2'], end=E['ships'] - 0.05, style='date', text='OCT 22, 1962', y=Y),
        dict(start=E['announced'], end=E['ships'] - 0.05, style='plateb', text='US NAVAL QUARANTINE', y=Y + 0.062),
        dict(start=E['ships'], end=E['beneath'] - 0.06, style='plate', text='SOVIET SHIPS HEAD FOR CUBA', y=Y),
        dict(start=E['beneath'], end=E['officer'] - 0.06, style='date', text='SOVIET SUBMARINE B-59', y=Y),
        dict(start=E['torpedo'], end=E['officer'] - 0.06, style='plate', text='NUCLEAR TORPEDO ON BOARD', y=Y + 0.062),
        dict(start=E['officer'], end=E['oct3'] - 0.06, style='date', text='VASILI ARKHIPOV', y=Y),
        dict(start=E['credited'], end=E['oct3'] - 0.06, style='plate', text='CREDITED WITH STOPPING A LAUNCH', y=Y + 0.062),
        dict(start=E['oct3'], end=E['secret'] - 0.06, style='date', text='OCT 28, 1962', y=Y),
        dict(start=E['khrushchev'], end=E['secret'] - 0.06, style='plateb', text='MISSILES TO BE REMOVED', y=Y + 0.062),
        dict(start=E['secret'], end=E['historians'] - 0.06, style='date', text='A SECRET DEAL', y=Y),
        dict(start=E['turkey'], end=E['historians'] - 0.06, style='plate', text='US MISSILES LEAVE TURKEY, 1963', y=Y + 0.062),
        dict(start=E['closest'], end=DUR, style='big', text='13 DAYS|ON THE BRINK', y=Y + 0.03),
    ]
    T = {'title': 'The Cuban Missile Crisis', 'duration': DUR, 'events': E, 'titles': titles,
         'scenes': [{'id': 1, 'key': 'main', 'name': 'One continuous map shot', 'start': 0.0, 'end': DUR}]}
    json.dump(T, open(os.path.join(D, 'scene_timing.json'), 'w'), indent=1)
    caps, i = [], 0
    key = lambda x: re.sub(r"[^A-Z0-9']", '', x['w'].upper())
    while i < len(W):
        g = [W[i]]
        while clean(g[-1]['w']) in GLUE and i + 1 < len(W) and W[i + 1]['line'] == W[i]['line'] and len(g) < 3 \
                and len(' '.join(x['w'] for x in g)) < 9:
            i += 1
            g.append(W[i])
        i += 1
        caps.append({'text': ' '.join(x['w'] for x in g), 'start': g[0]['start'], 'end': g[-1]['end'], 'hl': [key(x) for x in g if key(x) in HL]})
    for k, c in enumerate(caps):
        nxt = caps[k + 1]['start'] if k + 1 < len(caps) else DUR
        c['until'] = round(min(nxt, c['end'] + 0.5), 3)
    json.dump({'captions': caps}, open(os.path.join(D, 'build', 'vo_timing.json'), 'w'), indent=1)
    print(len(caps), 'captions;', E['voice_end'])


if __name__ == '__main__':
    main()
