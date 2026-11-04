"""Pose library: walk cycles, five distinct dance cycles, idles, head turns, reactions, gestures and
musicians. Each function returns a pose dict for time t (seconds). Times are quantised 'on twos' by the
caller, so every pose is a separate drawing held for two frames, as in hand-drawn animation."""
import math

from core import fnoise, hash01, clamp, smooth
from figures import base_pose

TAU = 2 * math.pi


def idle(t, seed=0, look=0.0, turn=0.25):
    p = base_pose()
    ph = t * 0.9 + hash01(seed, 1) * 10
    p['turn'] = turn
    p['bob'] = 0.8 * math.sin(ph * 2.1)
    p['sway'] = 1.2 * fnoise(ph * 0.4, seed)
    p['ua_b'] = -0.1 + 0.04 * math.sin(ph * 1.3)
    p['fa_b'] = -0.02
    p['ua_f'] = 0.1 - 0.04 * math.sin(ph * 1.1)
    p['fa_f'] = 0.04
    p['tilt'] = 0.05 * fnoise(ph * 0.5, seed + 3)
    p['look'] = look
    blink = (t * 1.0 + hash01(seed, 2) * 5) % 4.1
    p['eyes'] = 0.1 if blink < 0.12 else 1.0
    return p


def walk(t, seed=0, period=1.05, stride=1.0, tired=0.0):
    """Profile walk cycle (facing +x): contact, passing, contact, passing."""
    p = base_pose()
    ph = (t / period + hash01(seed, 5)) * TAU
    s = math.sin(ph)
    cph = math.cos(ph)
    p['turn'] = 0.88
    p['hturn'] = 0.8
    sw = 0.4 * stride
    p['th_f'] = sw * s
    p['th_b'] = -sw * s
    # the swinging leg bends at the knee while it passes
    p['sh_f'] = p['th_f'] - 0.75 * max(0.0, -cph) * stride
    p['sh_b'] = p['th_b'] - 0.75 * max(0.0, cph) * stride
    p['ft_f'] = 0.25 * max(0.0, -cph)
    p['ft_b'] = 0.25 * max(0.0, cph)
    p['bob'] = -2.2 * abs(cph) + 1.0 + tired * 2
    p['ua_f'] = -0.32 * s * stride
    p['fa_f'] = p['ua_f'] + 0.3
    p['ua_b'] = 0.32 * s * stride
    p['fa_b'] = p['ua_b'] + 0.3
    p['lean'] = 0.05 + tired * 0.22
    p['tilt'] = 0.04 * math.sin(ph * 2) + tired * 0.2
    p['skirt'] = -0.25 * s
    p['eyes'] = 1.0 - tired * 0.5
    p['brow'] = tired * 0.6
    return p


def dance(style, t, seed=0, energy=1.0, tired=0.0):
    """Five dance cycles, each with its own rhythm, so that no two dancers move alike."""
    p = base_pose()
    off = hash01(seed, 9) * 7.0
    tt = t + off
    if style == 'whirl':
        # the first dancer: arms raised over the head, swaying and turning, head thrown back
        ph = tt * TAU / 1.35
        s, s2 = math.sin(ph), math.sin(ph * 2)
        p['turn'] = 0.2 + 0.18 * math.sin(ph * 0.5)
        p['sway'] = 7.0 * s * energy
        p['lean'] = -0.13 * s * energy
        p['bob'] = -3.5 * abs(s2) * energy
        p['ua_b'] = -(2.35 + 0.25 * math.sin(ph + 0.6)) * energy - 0.12 * (1 - energy)
        p['fa_b'] = -(3.3 + 0.3 * math.sin(ph + 1.3)) * energy
        p['ua_f'] = (2.1 + 0.3 * math.sin(ph + 2.0)) * energy + 0.12 * (1 - energy)
        p['fa_f'] = (3.2 + 0.35 * math.sin(ph + 2.4)) * energy
        lift = max(0.0, math.sin(ph))
        lift2 = max(0.0, -math.sin(ph))
        p['th_f'] = 0.12 + 0.25 * lift
        p['thl_f'] = 1 - 0.38 * lift * energy
        p['sh_f'] = 0.05 - 0.15 * lift
        p['th_b'] = -0.12 - 0.25 * lift2
        p['thl_b'] = 1 - 0.38 * lift2 * energy
        p['sh_b'] = -0.05 + 0.15 * lift2
        p['ft_f'] = 0.4 * lift
        p['ft_b'] = -0.4 * lift2
        p['skirt'] = -0.9 * math.cos(ph) * energy
        p['flare'] = (0.35 + 0.35 * abs(math.cos(ph))) * energy
        p['swirl'] = ph * 1.5
        p['tilt'] = (-0.3 + 0.18 * math.sin(ph * 0.5 + 1)) * energy
        p['eyes'] = 0.32 + 0.1 * math.sin(ph * 0.3)
        p['brow'] = 0.55
        p['mouth'] = 0.3 + 0.15 * abs(s)
        p['look'] = 0.0
        p['lookv'] = -0.8
    elif style == 'jig':
        ph = tt * TAU / 0.82
        s = math.sin(ph)
        p['turn'] = 0.3 + 0.1 * math.sin(ph * 0.25)
        p['bob'] = -6.0 * abs(math.sin(ph)) * energy
        lf, lb = max(0.0, s), max(0.0, -s)
        p['th_f'] = 0.15 + 0.5 * lf
        p['thl_f'] = 1 - 0.5 * lf
        p['sh_f'] = 0.15 - 0.4 * lf
        p['th_b'] = -0.15 - 0.5 * lb
        p['thl_b'] = 1 - 0.5 * lb
        p['sh_b'] = -0.15 + 0.4 * lb
        p['ft_f'] = 0.5 * lf
        p['ft_b'] = -0.5 * lb
        p['ua_b'] = -(0.7 + 0.45 * s) * energy
        p['fa_b'] = p['ua_b'] - 1.6
        p['ua_f'] = (0.7 - 0.45 * s) * energy
        p['fa_f'] = p['ua_f'] + 1.6
        p['lean'] = 0.06 * s
        p['skirt'] = -0.6 * math.cos(ph)
        p['flare'] = 0.3
        p['swirl'] = ph
        p['tilt'] = 0.1 * math.sin(ph * 0.5)
        p['eyes'] = 0.55
        p['brow'] = 0.4
        p['mouth'] = 0.2
        p['hands'] = 'fist'
    elif style == 'convulse':
        # irregular jerks: a new pose snaps in every 0.2-0.35 s and is held
        k = math.floor(tt / 0.27)
        u = (tt / 0.27) - k
        def jitter(i, a):
            v0 = (hash01(seed, k, i) - 0.5) * 2
            v1 = (hash01(seed, k + 1, i) - 0.5) * 2
            return a * (v0 + (v1 - v0) * smooth(clamp(u * 3)))
        p['turn'] = 0.25 + 0.15 * jitter(1, 1)
        p['lean'] = jitter(2, 0.22)
        p['tilt'] = jitter(3, 0.45)
        p['sway'] = jitter(4, 6)
        p['bob'] = -abs(jitter(5, 5))
        p['ua_b'] = -1.1 + jitter(6, 1.0)
        p['fa_b'] = p['ua_b'] - 0.6 + jitter(7, 1.0)
        p['ua_f'] = 1.1 + jitter(8, 1.0)
        p['fa_f'] = p['ua_f'] + 0.6 + jitter(9, 1.0)
        p['th_f'] = 0.15 + jitter(10, 0.3)
        p['sh_f'] = p['th_f'] - 0.2 + jitter(11, 0.3)
        p['th_b'] = -0.15 + jitter(12, 0.3)
        p['sh_b'] = p['th_b'] + 0.2 + jitter(13, 0.3)
        p['thl_f'] = 1 - 0.3 * abs(jitter(14, 1))
        p['skirt'] = jitter(15, 0.8)
        p['flare'] = 0.25
        p['swirl'] = tt * 4
        p['eyes'] = 0.25 + 0.4 * abs(jitter(16, 1))
        p['brow'] = 0.8
        p['mouth'] = 0.45 + 0.3 * jitter(17, 1)
        p['lookv'] = -0.6
        p['hands'] = 'fist' if jitter(18, 1) > 0 else 'open'
    elif style == 'stomp':
        ph = tt * TAU / 1.1
        s = math.sin(ph)
        p['turn'] = 0.35
        p['lean'] = 0.32 + 0.08 * s
        p['bob'] = -4.0 * max(0.0, s) * energy + 2.0
        lf = max(0.0, s)
        lb = max(0.0, -s)
        p['th_f'] = 0.3 + 0.35 * lf
        p['thl_f'] = 1 - 0.45 * lf
        p['sh_f'] = 0.1
        p['th_b'] = -0.25 - 0.35 * lb
        p['thl_b'] = 1 - 0.45 * lb
        p['sh_b'] = -0.1
        p['ua_b'] = -0.4 - 0.5 * lb
        p['fa_b'] = p['ua_b'] - 0.3
        p['ua_f'] = 0.4 + 0.5 * lf
        p['fa_f'] = p['ua_f'] + 0.3
        p['tilt'] = 0.3 + 0.15 * s
        p['skirt'] = -0.5 * math.cos(ph)
        p['flare'] = 0.2
        p['swirl'] = ph
        p['eyes'] = 0.45
        p['brow'] = 0.7
        p['mouth'] = 0.35
        p['hands'] = 'fist'
    elif style == 'sway':
        # exhausted, but still moving: heavy, lolling sway
        ph = tt * TAU / 2.2
        s = math.sin(ph)
        p['turn'] = 0.2
        p['sway'] = 6.0 * s
        p['lean'] = 0.18 * s + 0.12
        p['bob'] = 2.0 + 2.0 * abs(math.sin(ph * 2))
        p['ua_b'] = -0.15 - 0.35 * max(0.0, -s)
        p['fa_b'] = p['ua_b'] + 0.2
        p['ua_f'] = 0.15 + 0.35 * max(0.0, s)
        p['fa_f'] = p['ua_f'] - 0.2
        p['th_f'] = 0.1 + 0.12 * s
        p['th_b'] = -0.1 + 0.12 * s
        p['sh_f'] = p['th_f'] * 0.4
        p['sh_b'] = p['th_b'] * 0.4
        p['tilt'] = 0.45 * math.sin(ph + 0.8)
        p['skirt'] = -0.6 * math.cos(ph)
        p['flare'] = 0.1
        p['swirl'] = ph * 0.5
        p['eyes'] = 0.22
        p['brow'] = 0.9
        p['mouth'] = 0.35
    elif style == 'twirl':
        ph = tt * TAU / 1.6
        s = math.sin(ph)
        p['turn'] = abs(math.sin(ph * 0.5))
        p['ua_b'] = -1.5 - 0.2 * s
        p['fa_b'] = p['ua_b'] - 0.2
        p['ua_f'] = 1.5 + 0.2 * s
        p['fa_f'] = p['ua_f'] + 0.2
        p['bob'] = -3.0 * abs(math.sin(ph * 2))
        p['th_f'] = 0.2 + 0.2 * s
        p['th_b'] = -0.2 + 0.2 * s
        p['sh_f'] = p['th_f']
        p['sh_b'] = p['th_b']
        p['skirt'] = math.cos(ph) * 0.9
        p['flare'] = 0.6
        p['swirl'] = ph * 2
        p['tilt'] = -0.2
        p['eyes'] = 0.3
        p['brow'] = 0.5
        p['mouth'] = 0.25
    # exhaustion slows the energy and droops the head
    if tired > 0:
        p['lean'] += 0.1 * tired
        p['tilt'] += 0.25 * tired
        p['eyes'] = min(p['eyes'], 1 - 0.75 * tired)
        p['brow'] = max(p['brow'], tired)
    return p


def twirl_face(t, seed=0):
    """For 'twirl' the figure turns all the way round: flip the drawing every half turn."""
    ph = ((t + hash01(seed, 9) * 7.0) / 1.6) % 1.0
    return 1 if ph < 0.5 else -1


def react(t, t0, seed=0, kind='stare', turn=0.25, look_dir=1.0):
    """Onlookers: turn towards the dancer, then stare, recoil or cover the mouth."""
    p = idle(t, seed, turn=turn)
    u = smooth(clamp((t - t0) / 0.5))
    p['hturn'] = turn + (0.55 - turn) * u if look_dir > 0 else turn * (1 - u)
    p['look'] = 0.8 * u * look_dir
    p['brow'] = 0.7 * u
    p['eyes'] = 1.0 + 0.1 * u
    if kind == 'recoil':
        p['lean'] = -0.12 * u
        p['ua_f'] = 0.12 + 0.6 * u
        p['fa_f'] = p['ua_f'] + 1.9 * u
        p['mouth'] = 0.45 * u
    elif kind == 'mouth':
        p['ua_f'] = 0.12 + 0.35 * u
        p['fa_f'] = 0.04 + 2.75 * u
        p['arms_front'] = u > 0.5
        p['mouth'] = 0.2
    elif kind == 'point':
        p['ua_f'] = 0.12 + 1.35 * u
        p['fa_f'] = p['ua_f'] + 0.15
        p['mouth'] = 0.3 * u
    elif kind == 'cross':
        # crossing oneself / clasped hands
        p['ua_f'] = 0.1 + 0.3 * u
        p['fa_f'] = 0.1 + 2.5 * u
        p['ua_b'] = -0.1 - 0.3 * u
        p['fa_b'] = -0.1 - 2.5 * u
        p['arms_front'] = u > 0.5
        p['tilt'] = 0.15 * u
    elif kind == 'whisper':
        p['lean'] = 0.08 * u
        p['ua_f'] = 0.15 + 0.4 * u
        p['fa_f'] = 0.1 + 2.6 * u
        p['mouth'] = 0.15 * math.sin(t * 9) ** 2
    else:
        p['mouth'] = 0.25 * u
    return p


def gesture(kind, t, seed=0, turn=0.45):
    """Council chamber gestures: speaking with an open hand, pointing at a paper, raising the flask,
    writing, arms folded, head in hand."""
    p = idle(t, seed, turn=turn)
    ph = t + hash01(seed, 4) * 5
    if kind == 'talk':
        a = 0.5 + 0.5 * math.sin(ph * 2.3)
        p['ua_f'] = 0.55 + 0.35 * a
        p['fa_f'] = p['ua_f'] + 1.6 - 0.4 * a
        p['mouth'] = 0.35 * abs(math.sin(ph * 7.0)) * (0.5 + 0.5 * math.sin(ph * 1.3))
        p['brow'] = 0.5
        p['tilt'] = 0.08 * math.sin(ph * 1.7)
        p['hturn'] = turn + 0.15 * math.sin(ph * 0.8)
    elif kind == 'flask':
        a = smooth(clamp((ph % 6.0) / 1.0))
        p['ua_f'] = 1.2 + 0.7 * a
        p['fa_f'] = p['ua_f'] + 1.3
        p['prop'] = 'flask'
        p['tilt'] = -0.18 * a
        p['look'] = 0.5
        p['lookv'] = -0.7 * a
        p['brow'] = 0.65
    elif kind == 'write':
        p['lean'] = 0.25
        p['tilt'] = 0.25
        p['ua_f'] = 0.6
        p['fa_f'] = 1.95 + 0.08 * math.sin(ph * 11)
        p['prop'] = 'quill'
        p['lookv'] = 0.7
        p['eyes'] = 0.7
    elif kind == 'fold':
        p['ua_f'] = 0.35
        p['fa_f'] = 2.2
        p['ua_b'] = -0.35
        p['fa_b'] = -2.2
        p['arms_front'] = True
        p['brow'] = 0.75
        p['mouth'] = 0.0
    elif kind == 'chin':
        p['ua_f'] = 0.3
        p['fa_f'] = 3.0
        p['tilt'] = 0.12
        p['brow'] = 0.85
        p['arms_front'] = True
    elif kind == 'book':
        p['ua_f'] = 0.45
        p['fa_f'] = 2.1
        p['ua_b'] = -0.45
        p['fa_b'] = -2.1
        p['arms_front'] = True
        p['prop'] = 'book'
        p['lookv'] = 0.6
        p['tilt'] = 0.15
        p['mouth'] = 0.25 * abs(math.sin(ph * 6.0))
    elif kind == 'point':
        a = 0.5 + 0.5 * math.sin(ph * 1.1)
        p['ua_f'] = 1.0 + 0.2 * a
        p['fa_f'] = p['ua_f'] + 0.3
        p['lean'] = 0.12
        p['mouth'] = 0.3 * abs(math.sin(ph * 6.5))
        p['brow'] = 0.6
    elif kind == 'watch':
        p['brow'] = 0.4
        p['mouth'] = 0.0
        p['ua_f'] = 0.2
        p['fa_f'] = 2.4
        p['ua_b'] = -0.2
        p['fa_b'] = -2.4
        p['arms_front'] = True
    return p


def musician(kind, t, seed=0):
    """Hired musicians: tabor drum, shawm, bagpipe and fiddle, each playing in time."""
    p = idle(t, seed, turn=0.35)
    beat = 0.5
    ph = t / beat
    hit = (ph % 1.0)
    if kind == 'drum':
        p['prop'] = 'drum'
        up = math.exp(-hit * 6) if hit < 0.5 else 0.0
        p['ua_f'] = 0.55 + 0.6 * (1 - up)
        p['fa_f'] = p['ua_f'] + 1.0 - 0.9 * (1 - up)
        p['ua_b'] = -0.25
        p['fa_b'] = 0.9
        p['bob'] = 1.5 * math.exp(-hit * 5)
        p['tilt'] = 0.15
        p['lookv'] = 0.4
    elif kind == 'shawm':
        p['prop'] = 'shawm'
        p['ua_f'] = 0.7
        p['fa_f'] = 2.4 + 0.05 * math.sin(t * 13)
        p['ua_b'] = 0.55
        p['fa_b'] = 2.15 + 0.05 * math.sin(t * 11)
        p['arms_front'] = True
        p['tilt'] = -0.12 + 0.05 * math.sin(t * 2)
        p['lean'] = -0.05 + 0.04 * math.sin(t * 2)
        p['eyes'] = 0.6
        p['hturn'] = 0.6
    elif kind == 'bagpipe':
        p['prop'] = 'bagpipe'
        p['ua_f'] = 0.6
        p['fa_f'] = 2.6
        p['ua_b'] = 0.35
        p['fa_b'] = 2.5
        p['arms_front'] = True
        p['hturn'] = 0.6
        p['bob'] = 1.2 * math.sin(t * math.pi / beat)
    elif kind == 'fiddle':
        p['prop'] = 'fiddle'
        bow = math.sin(t * math.pi / beat)
        p['ua_f'] = 0.9 + 0.35 * bow
        p['fa_f'] = 2.0 - 0.5 * bow
        p['ua_b'] = -1.2
        p['fa_b'] = -2.6
        p['tilt'] = 0.3
        p['hturn'] = 0.5
        p['eyes'] = 0.5
    p['brow'] = max(p['brow'], 0.3)
    return p


# ----------------------------------------------------------------------------------------------
# Colonists at work (Roanoke, 1587)
# ----------------------------------------------------------------------------------------------
def carry(p, kind):
    """Overlay arm positions for carrying: 'chest' (both forearms under a box), 'baby' (cradled),
    'log' (steadied on the shoulder), 'sack' (over the back shoulder)."""
    if kind == 'chest':
        p.update(ua_f=0.2, fa_f=1.45, ua_b=0.3, fa_b=1.5, fal_f=0.85, fal_b=0.85, arms_front=True, prop='chest')
    elif kind == 'baby':
        p.update(ua_f=0.1, fa_f=2.45, fal_f=0.72, ua_b=0.45, fa_b=1.65, fal_b=0.8, arms_front=True, prop='baby', lookv=0.5)
    elif kind == 'log':
        p.update(ua_f=1.7, fa_f=4.5, fal_f=0.8, prop='log')
    elif kind == 'sack':
        p.update(ua_b=2.6, fa_b=4.2, ual_b=0.7, prop='sack')
    return p


def hammer(t, seed=0, rate=1.25):
    """Driving a peg or post with a mallet: lift, hold, strike."""
    p = idle(t, seed, turn=0.6)
    ph = ((t * rate) + hash01(seed, 7)) % 1.0
    up = smooth(clamp(ph / 0.55)) if ph < 0.55 else 1 - smooth(clamp((ph - 0.55) / 0.12))
    p['ua_f'] = 0.9 + 1.5 * up
    p['fa_f'] = p['ua_f'] + 0.6 + 1.0 * up
    p['ua_b'] = 0.5
    p['fa_b'] = 1.3
    p['lean'] = 0.12 + 0.08 * (1 - up)
    p['tilt'] = 0.2
    p['lookv'] = 0.6
    p['prop'] = 'hammer'
    p['brow'] = 0.4
    return p


def saw(t, seed=0, rate=1.6):
    """One end of a two-man saw: push and pull."""
    p = idle(t, seed, turn=0.7)
    s = math.sin((t * rate + hash01(seed, 8)) * TAU)
    p['ua_f'] = 0.9 + 0.35 * s
    p['fa_f'] = 1.5 + 0.2 * s
    p['ua_b'] = 0.7 + 0.35 * s
    p['fa_b'] = 1.4 + 0.2 * s
    p['lean'] = 0.25 + 0.06 * s
    p['th_f'] = 0.25
    p['sh_f'] = 0.0
    p['th_b'] = -0.2
    p['sh_b'] = -0.2
    p['lookv'] = 0.6
    p['arms_front'] = True
    return p


def row(t, seed=0, rate=0.55):
    """Rowing seated in a boat (legs hidden by the gunwale)."""
    p = idle(t, seed, turn=0.85)
    ph = (t * rate + hash01(seed, 9)) % 1.0
    s = math.sin(ph * TAU)
    p['lean'] = 0.15 * s
    p['ua_f'] = 1.0 - 0.45 * s
    p['fa_f'] = 1.6 - 0.2 * s
    p['ua_b'] = 0.9 - 0.45 * s
    p['fa_b'] = 1.5 - 0.2 * s
    p['oar_a'] = 0.8 + 0.5 * s
    p['prop'] = 'oar'
    p['arms_front'] = True
    return p


def wave_hand(t, seed=0, turn=0.3):
    p = idle(t, seed, turn=turn)
    p['ua_f'] = 2.6 + 0.1 * math.sin(t * 3)
    p['fa_f'] = 3.0 + 0.45 * math.sin(t * 7 + seed)
    p['lookv'] = -0.2
    return p
