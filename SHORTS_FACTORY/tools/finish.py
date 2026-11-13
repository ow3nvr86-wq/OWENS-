"""Master the mix to about -14 LUFS (true peak <= -1.5 dBTP), encode final.mp4 (H.264 1080x1920 30 fps + AAC) from the
rendered frames, and save thumbnail.png (the frame at script.json "thumbnail_cue", or the middle of the video).
Run: $SHORTS_PY tools/finish.py episodes/<name>"""
import json, os, re, subprocess, sys
EP = sys.argv[1]; W = os.path.join(EP, 'work'); A = os.path.join(EP, 'audio')
S = json.load(open(os.path.join(EP, 'script.json'))); WJ = json.load(open(os.path.join(W, 'words.json')))
run = lambda *a: subprocess.run(list(a), capture_output=True, text=True, check=True)
# two-pass loudnorm
m = run('ffmpeg', '-hide_banner', '-i', os.path.join(A, 'mix.wav'), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-').stderr
j = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
af = ('loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:'
      'measured_thresh={input_thresh}:offset={target_offset},aresample=48000').format(**j)
run('ffmpeg', '-y', '-hide_banner', '-i', os.path.join(A, 'mix.wav'), '-af', af, '-ar', '48000', '-ac', '2', os.path.join(A, 'master.wav'))
out = os.path.join(EP, 'final.mp4')
run('ffmpeg', '-y', '-hide_banner', '-framerate', '30', '-i', os.path.join(W, 'frames', 'f%05d.jpg'), '-i', os.path.join(A, 'master.wav'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-maxrate', '9M', '-bufsize', '18M', '-pix_fmt', 'yuv420p', '-r', '30',
    '-vf', 'scale=1080:1920:flags=lanczos', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out)
# thumbnail
cue = S.get('thumbnail_cue'); t = WJ['duration'] / 2
if cue:
    for w in WJ['words']:
        if re.sub(r'[^a-z0-9]', '', w['word'].lower()) == re.sub(r'[^a-z0-9]', '', cue.lower()): t = w['start'] + 0.4; break
f = min(WJ['frames'] - 1, round(t * 30))
run('ffmpeg', '-y', '-hide_banner', '-i', os.path.join(W, 'frames', 'f%05d.jpg' % f), os.path.join(EP, 'thumbnail.png'))
r = run('ffmpeg', '-hide_banner', '-i', out, '-af', 'ebur128=peak=true', '-f', 'null', '-').stderr
print('final.mp4 %.1f MB' % (os.path.getsize(out) / 1e6), '| thumbnail frame', f)
print('\n'.join(l.strip() for l in r[r.rindex('Summary:'):].splitlines() if re.search(r'I:|Peak:', l)))
