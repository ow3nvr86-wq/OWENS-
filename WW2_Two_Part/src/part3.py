"""The Battle of Midway (4-7 June 1942): one continuous shot over a real map of the Pacific. The camera flies from Pearl
Harbor to Midway, to the codebreakers in Hawaii, to the two fleets, the torpedo planes, the dive bombers, the burning
carriers and the pull-back that shows Japan's tide turning. Every time comes from part3/scene_timing.json (the measured
words of the narration)."""
import math

import cairo
import numpy as np

from core import W, H, EV as E, Camera, clamp, smooth, smoother, ease_out, ease_in, ramp, hash01, vnoise, fnoise, set_c, \
    path_smooth, path_poly, soft_glow
import mapdata as M
import text as TX
from common import hexc, sm, visible, scr, draw_grid, spline, along, arrow, plane, burst, dot, \
    SEA, SEA2, LAND, WHITE, YELLOW, INK, RED, RED_L, RED_D, BLUE, BLUE_L, ARROW

BLUE_A = hexc('3f8cff')
SEA = hexc('0f2a4a')
SEA2 = hexc('163a63')
LANDC = hexc('2b3d58')
END = 99.0
MIDWAY = (182.63, 28.2)
HAWAII = (202.05, 21.4)
NAGUMO = [('AKAGI', 180.35, 32.55), ('KAGA', 180.95, 32.25), ('SORYU', 180.45, 31.85), ('HIRYU', 181.75, 33.3)]
US_TF = [('ENTERPRISE', 187.25, 32.0), ('HORNET', 187.85, 31.7), ('YORKTOWN', 186.55, 31.5)]
CAM = [
    (0.0, 168.0, 32.0, 12), (E['pearl'] - 0.4, 190.0, 26.0, 15), (E['pearl'] + 0.5, 197.0, 24.0, 22), (E['then'] + 0.1, 190.0, 29.0, 22),
    (E['carriers'], 180.8, 32.2, 78), (E['planned'] - 0.1, 175.0, 32.0, 20, 'out'), (E['midway'] + 0.2, 182.6, 28.6, 80),
    (E['island'], 182.63, 28.2, 150), (E['american'] + 0.6, 201.0, 24.0, 34, 'out'), (E['messages'], 196.0, 25.5, 30),
    (E['june'] + 0.2, 184.0, 30.4, 66, 'out'), (E['torpedo'], 184.0, 31.0, 92), (E['wiped'], 183.4, 31.7, 110),
    (E['pulled'] + 0.1, 181.7, 32.2, 150), (E['dive'] - 0.1, 181.7, 32.2, 150), (E['hit'], 181.0, 32.3, 190), (E['fourth'] + 0.3, 181.6, 32.8, 190),
    (E['never'] + 0.1, 170.0, 33.0, 15, 'out'), (E['tide'], 168.0, 33.0, 14), (END, 166.0, 33.0, 14.5),
]
CAM[-1] = (max(E['voice_end'] + 2.0, CAM[-2][0] + 2.0), 166.0, 33.0, 14.5)
SHAKES = [(E['pearl'], 16), (E['three'], 16), (E['trap'], 14), (E['june'], 14), (E['wiped'], 12), (E['dive'], 12), (E['hit'], 22), (E['sunk'], 18), (E['tide'], 14)]


def cam_state(t):
    if t <= CAM[0][0]:
        return CAM[0][1:4]
    for k0, k1 in zip(CAM, CAM[1:]):
        (t0, *a), (t1, *b) = k0[:4], k1[:4]
        if t <= t1:
            x = (t - t0) / (t1 - t0)
            u = smoother(x)
            uz = smoother(clamp(x * 1.7)) if len(k1) > 4 else u
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * uz)
    return CAM[-1][1:4]


def make_cam(t):
    lon, lat, pxd = cam_state(t)
    z = pxd / M.K
    x, y = M.P(lon, lat)
    sx = sy = 0.0
    for t0, amp in SHAKES:
        u = (t - t0) / 0.38
        if 0 <= u <= 1:
            k = (1 - u) ** 2 * amp
            sx += k * vnoise(t * 42, int(t0 * 10))
            sy += k * vnoise(t * 42, int(t0 * 10) + 5)
    return Camera(x + sx / z, y + sy / z, z, anchor=(0.0, 0.0)), z


def blob(ctx, cx, cy, R, seed, t):
    pts = []
    for k in range(64):
        a = k / 64 * 2 * math.pi
        r = R * (1 + 0.14 * fnoise(math.cos(a) * 1.8 + seed, seed, 3) + 0.05 * fnoise(math.sin(a) * 3.0 + t * 0.8, seed + 9, 2))
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    ctx.new_path()
    path_smooth(ctx, np.array(pts), True, 0.5)


def draw_map(ctx, cam, z, t):
    set_c(ctx, SEA)
    ctx.paint()
    draw_grid(ctx, cam, z, 0.05)
    M.stroke(ctx, 'LAND', SEA2, 22 / z, 0.9)
    M.fill(ctx, 'LAND', LANDC)
    # engraved wave lines
    hh = (H / 2 + 40) / z
    sp = max(10.0 / z, 9.0)
    ctx.new_path()
    y0 = math.floor((cam.cy - hh) / sp) * sp
    yy = y0
    while yy < cam.cy + hh:
        ctx.move_to(cam.cx - (W / 2 + 40) / z, yy)
        ctx.line_to(cam.cx + (W / 2 + 40) / z, yy)
        yy += sp
    set_c(ctx, hexc('2a5b8f'), 0.2)
    ctx.set_line_width(1.2 / z)
    ctx.stroke()
    # Japan's empire at its height: red, fading as the tide turns
    tide = sm(t, E['never'] - 0.2, E['tide'] + 2.2)
    if visible(cam, z, 'JAP_EMPIRE', 600):
        M.fill(ctx, 'JAP_EMPIRE', RED, 0.9 * (1 - 0.65 * tide))
        M.fill(ctx, 'JPN', RED, 1.0 - 0.5 * tide)
        if tide > 0:
            ctx.save()
            M.clip(ctx, ['JAP_EMPIRE', 'JPN'])
            mx, my = M.P(*MIDWAY)
            blob(ctx, mx, my, 1500 * tide ** 0.9 + 1, 5, t)
            set_c(ctx, BLUE, 0.9)
            ctx.fill_preserve()
            set_c(ctx, BLUE_L, 0.9)
            ctx.set_line_width(7 / z)
            ctx.stroke()
            ctx.restore()
    if visible(cam, z, 'HAWAII', 400):
        M.fill(ctx, 'HAWAII', hexc('46567a'))
        M.stroke(ctx, 'HAWAII', WHITE, 2 / z, 0.8)
    M.stroke(ctx, 'LAND', WHITE, 1.3 / z, 0.34)
    # Midway: two tiny islands, drawn large enough to read (the real atoll is a few km across)
    mx, my = M.P(*MIDWAY)
    s = 1.0 / z
    k = sm(t, E['trap'] - 0.3, E['trap'] + 0.3)
    for r, a in ((46, 0.12), (22, 0.3)):
        soft_glow(ctx, mx, my, r * 2.5 * s * 3, hexc('f4e3a0'), a * k)
    for dx, dy, rx, ry in ((0, 0, 17, 11), (-14, 12, 9, 6)):
        ctx.save()
        ctx.translate(mx + dx * s, my + dy * s)
        ctx.scale(rx * s, ry * s)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        set_c(ctx, hexc('e9d9a0'), 0.4 + 0.6 * k)
        ctx.fill_preserve()
        set_c(ctx, INK, 0.9 * k)
        ctx.set_line_width(2.5 * s)
        ctx.stroke()


def carrier(ctx, x, y, ang, z, s=1.0, col=WHITE, alpha=1.0, burn=0.0, sink=0.0, t=0.0, seed=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang + 0.5 * sink * (1 if seed % 2 else -1))
    sc = s / z * (1 - 0.5 * sink)
    ctx.scale(sc, sc)
    al = alpha * (1 - sink ** 2)
    ctx.new_path()
    path_poly(ctx, np.array([(-40, -8), (34, -8), (44, -2), (44, 2), (34, 8), (-40, 8)], float), True)
    set_c(ctx, INK, 0.5 * al)
    ctx.save()
    ctx.translate(2, 6)
    ctx.fill_preserve()
    ctx.restore()
    set_c(ctx, col, al)
    ctx.fill_preserve()
    set_c(ctx, INK, al)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.rectangle(-8, -11, 14, 6)
    set_c(ctx, INK, al)
    ctx.fill()
    ctx.move_to(-36, 0)
    ctx.line_to(30, 0)
    set_c(ctx, INK, 0.45 * al)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.move_to(-40, 0)
    ctx.line_to(-110, 0)
    set_c(ctx, WHITE, 0.3 * al)
    ctx.set_line_width(5)
    ctx.stroke()
    if burn > 0:
        for i in range(8):
            fx = -34 + 66 * hash01(i, seed)
            fl = 0.6 + 0.4 * math.sin(t * 17 + i * 2.1 + seed)
            soft_glow(ctx, fx, -6 - 6 * fl, (22 + 26 * hash01(i, seed + 1)) * burn * fl, hexc('ff7a1a'), 0.85 * burn * al)
            soft_glow(ctx, fx, -8 - 8 * fl, 12 * burn * fl, hexc('ffe9a0'), 0.8 * burn * al)
        for i in range(10):
            u = ((t * 0.9 + hash01(i, seed + 5)) % 1.0)
            soft_glow(ctx, -20 + 50 * hash01(i, seed + 6) + 40 * u, -20 - 120 * u, (16 + 40 * u) * burn, (0.1, 0.1, 0.12, 1), 0.5 * (1 - u) * burn * al)
    ctx.restore()


def draw_action(ctx, cam, z, t):
    px = 1.0 / z
    # Pearl Harbor
    k = (t - E['harbor']) / 1.4
    if 0 <= k < 1:
        x, y = M.P(*HAWAII)
        for j in range(3):
            burst(ctx, x + (j - 1) * 24 * px, y + (j % 2) * 14 * px, (t - E['harbor'] - 0.1 * j) / 1.2, z, 1.2, j)
    # the hook's outcome, previewed: three Japanese carriers burning
    if E['three'] - 0.15 <= t <= E['planned'] - 0.05:
        al = sm(t, E['three'] - 0.15, E['three'] + 0.25) * (1 - sm(t, E['planned'] - 0.35, E['planned'] - 0.05))
        for i, (nm, lo, la) in enumerate(NAGUMO[:3]):
            x, y = M.P(lo, la)
            ky = sm(t, E['three'] + 0.2 * i, E['three'] + 0.2 * i + 0.5)
            carrier(ctx, x, y, math.radians(190), z, 2.4, hexc('ffd7d2'), al, ky, 0.0, t, i)
    # Japan's plan: the invasion force and the carriers converge on Midway
    if E['planned'] - 0.1 <= t <= E['american'] + 0.5:
        al = 1 - sm(t, E['american'] - 0.1, E['american'] + 0.3)
        u = smooth(ramp(t, E['planned'], E['tiny'] + 0.4))
        arrow(ctx, [(139, 35.5), (150, 38.5), (164, 37.0), (176, 32.0), (181.0, 29.2)], u, z, 36, ARROW, al)
        arrow(ctx, [(146, 15.5), (160, 20.5), (172, 25.0), (180.0, 27.4)], u, z, 30, ARROW, al)
        arrow(ctx, [(165, 44.0), (172, 38.0), (178, 33.0)], u, z, 26, ARROW, al)
    # codebreakers: intercepted radio traffic from Japan's fleet to Hawaii, and the answer to Midway
    if E['american'] + 0.1 <= t <= E['june'] + 0.4:
        al = sm(t, E['american'] + 0.1, E['american'] + 0.5) * (1 - sm(t, E['june'] - 0.2, E['june'] + 0.3))
        hx, hy = M.P(*HAWAII)
        fx, fy = M.P(181.5, 32.5)
        mx, my = M.P(*MIDWAY)
        u = smooth(ramp(t, E['codebreakers'], E['secret'] + 0.5))
        ctx.set_dash([14 * px, 10 * px])
        for (x0, y0, x1, y1, col) in ((fx, fy, hx, hy, YELLOW),):
            ctx.new_path()
            ctx.move_to(x0, y0)
            ctx.curve_to((x0 + x1) / 2, y0 - 120 * px, (x0 + x1) / 2, y1 - 160 * px, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
            set_c(ctx, col, 0.95 * al)
            ctx.set_line_width(4 * px)
            ctx.stroke()
        ctx.set_dash([])
        for r in range(3):
            v = ((t - E['american']) * 0.9 + r / 3) % 1.0
            set_c(ctx, YELLOW, 0.5 * (1 - v) * al * smooth(ramp(t, E['codebreakers'], E['codebreakers'] + 0.3)))
            ctx.set_line_width(3 * px)
            ctx.arc(hx, hy, (30 + 150 * v) * px, 0, 2 * math.pi)
            ctx.stroke()
        arrow(ctx, [(202.0, 22.4), (194.0, 26.0), (186.5, 27.9)], smooth(ramp(t, E['messages'] - 0.05, E['messages'] + 0.8)), z, 34, BLUE_A, al)
    # the two fleets
    if E['june'] - 0.2 <= t <= E['never'] + 0.4:
        ka = sm(t, E['june'] - 0.2, E['june'] + 0.4)
        sunk_h = sm(t, E['sunk'], E['sunk'] + 1.4)
        mrg = sm(t, E['never'] - 0.2, E['never'] + 0.4)
        for i, (nm, lo, la) in enumerate(NAGUMO):
            x, y = M.P(lo, la)
            hit = sm(t, E['hit'] + 0.12 * i, E['hit'] + 0.12 * i + 0.4) if i < 3 else sm(t, E['fought'] - 0.2, E['fought'] + 0.5) * (1 if t < E['sunk'] else 0.0 if False else 1)
            burn = hit if i < 3 else hit
            sk = sunk_h if i == 3 else sm(t, E['fourth'] + 1.0, E['never'] + 0.6) * 0.0
            carrier(ctx, x + 3 * math.sin(t * 1.2 + i) * px, y, math.radians(190), z, 2.7 if z > 40 else 2.0, hexc('ffd7d2'), ka * (1 - mrg), burn, sk, t, i)
        for i, (nm, lo, la) in enumerate(US_TF):
            x, y = M.P(lo, la)
            carrier(ctx, x, y + 2 * math.sin(t * 1.1 + i) * px, math.radians(10), z, 2.7 if z > 40 else 2.0, hexc('cfe4ff'), ka * (1 - mrg), 0, 0, t, i + 4)
        # torpedo planes from the US carriers to Japan's carriers; most do not return
        if E['torpedo'] - 0.1 <= t <= E['pulled'] + 0.6:
            u0 = ramp(t, E['torpedo'] - 0.1, E['wiped'] + 0.2)
            alp = 1 - sm(t, E['pulled'], E['pulled'] + 0.5)
            ax, ay = M.P(187.4, 31.8)
            bx, by = M.P(181.2, 32.3)
            for i in range(10):
                f = smooth(clamp(u0 * 1.15 - 0.03 * i))
                off = np.array([0, (i - 4.5) * 34 * px])
                p = np.array([ax + (bx - ax) * f, ay + (by - ay) * f]) + off + np.array([8 * px * math.sin(t * 7 + i), 0])
                dead = i < 9 and t > E['wiped'] + 0.05 + 0.07 * i
                if dead:
                    kk = (t - E['wiped'] - 0.05 - 0.07 * i) / 0.5
                    burst(ctx, p[0], p[1], kk, z, 0.5, i)
                    if kk > 0.45:
                        continue
                plane(ctx, p[0], p[1], math.atan2(by - ay, bx - ax), z, 3.6, hexc('9fd0ff'), alp)
    # the fighters come down to the waves; the dive bombers fall from the clouds
    if E['pulled'] - 0.2 <= t <= E['hit'] + 1.0:
        al = sm(t, E['fighters'] - 0.4, E['fighters']) * (1 - sm(t, E['hit'] + 0.2, E['hit'] + 0.6))
        for i in range(12):
            ang = i / 12 * 2 * math.pi
            cx, cy = M.P(181.4, 32.4)
            conv = smooth(ramp(t, E['pulled'], E['waves']))
            rr = (150 - 90 * conv) * px
            p = np.array([cx + math.cos(ang + t * 1.4) * rr * 1.3, cy + math.sin(ang + t * 1.4) * rr])
            plane(ctx, p[0], p[1], ang + t * 1.4 + math.pi / 2, z, 2.1, hexc('ff8a80'), al)
    if E['dive'] - 0.1 <= t <= E['hit'] + 0.7:
        for i in range(15):
            tgt = [M.P(lo, la) for _, lo, la in NAGUMO[:3]][i % 3]
            u = smooth(ramp(t, E['dive'] + 0.2 + 0.05 * i, E['hit'] + 0.05 * (i % 5)))
            ox = (hash01(i, 3) - 0.5) * 500 * px
            oy = -(260 + 200 * hash01(i, 4)) * px
            p = np.array([tgt[0] + ox * (1 - u), tgt[1] + oy * (1 - u)]) + np.array([(hash01(i, 6) - 0.5) * 30 * px, (hash01(i, 7) - 0.5) * 30 * px])
            ang = math.atan2(-oy, -ox)
            gone = sm(t, E['hit'] + 0.05 * (i % 5), E['hit'] + 0.25 + 0.05 * (i % 5))
            if u > 0 and gone < 1:
                plane(ctx, p[0], p[1], ang, z, 3.8 - 1.8 * u, hexc('9fd0ff'), 1 - gone)
            if u >= 0.98:
                burst(ctx, tgt[0] + (hash01(i, 8) - 0.5) * 36 * px, tgt[1] + (hash01(i, 9) - 0.5) * 18 * px, (t - E['hit'] - 0.05 * (i % 5)) / 0.7, z, 0.55, i)


LABELS = []


def draw_overlay(ctx, cam, z, t, os_):
    ctx.save()
    ctx.identity_matrix()
    # Japan and Hawaii, then Midway
    for txt, lo, la, t0, t1, size in (('JAPAN', 138.0, 38.5, 0.1, E['then'], 56), ('HAWAII', 202.5, 24.6, E['pearl'] - 0.3, E['then'], 50),
                                      ('JAPAN\'S EMPIRE', 158.0, 30.0, 0.2, E['pearl'] - 0.4, 52), ('MIDWAY', 182.63, 26.8, E['midway'], E['american'], 62),
                                      ('PEARL HARBOR', 202.3, 20.4, E['pearl'], E['then'], 40), ('HAWAII', 200.5, 20.6, E['american'] + 0.5, E['june'], 50),
                                      ('MIDWAY', 182.63, 27.0, E['met'], E['wiped'] + 0.5, 46)):
        if t0 <= t <= t1 + 0.25:
            x, y = scr(cam, lo, la)
            if -200 < x < 1280 and 290 < y < 1150:
                al, s = TX.pop(t, t0)
                TX.paint_label(ctx, txt, x, y, size, os_, TX.WHITE, al * (1 - sm(t, t1, t1 + 0.2)), s)
    # fleets: names appear as they are hit
    if E['met'] <= t <= E['fourth'] + 0.8 and z > 40:
        for i, (nm, lo, la) in enumerate(NAGUMO):
            if i == 3 and t < E['fought'] - 0.3:
                continue
            x, y = scr(cam, lo, la)
            al, s = TX.pop(t, E['met'] + 0.1 * i if i < 3 else E['fought'] - 0.3)
            al *= 1 - sm(t, E['sunk'] + 1.0, E['sunk'] + 1.5) if i == 3 else 1.0
            if 300 < y < 1150 and -100 < x < 1180:
                TX.paint_label(ctx, nm, x, y + 70, 34, os_, TX.RED_L, al, s, ow=5)
        for i, (nm, lo, la) in enumerate(US_TF):
            x, y = scr(cam, lo, la)
            al, s = TX.pop(t, E['met'] + 0.15 * i)
            if 300 < y < 1150 and -100 < x < 1180:
                TX.paint_label(ctx, nm, x, y + 70, 30, os_, TX.BLUE, al * (1 - sm(t, E['never'] - 0.2, E['never'] + 0.2)), s, ow=5)
    # the intercepted message
    if E['secret'] - 0.1 <= t <= E['june'] + 0.1:
        al = sm(t, E['secret'] - 0.1, E['secret'] + 0.25) * (1 - sm(t, E['june'] - 0.15, E['june'] + 0.1))
        x0, y0, wd, ht = 120, 560, 840, 190
        ctx.save()
        ctx.scale(os_, os_)
        ctx.rectangle(x0, y0, wd, ht)
        set_c(ctx, INK, 0.82 * al)
        ctx.fill_preserve()
        set_c(ctx, YELLOW, al)
        ctx.set_line_width(5)
        ctx.stroke()
        res = sm(t, E['messages'] - 0.1, E['messages'] + 0.35)
        for k in range(26):
            r = hash01(k, int(t * 14))
            shown = hash01(k, 3) > res
            if shown:
                bx, by = x0 + 40 + k * 30, y0 + 40
                set_c(ctx, YELLOW, (0.25 + 0.7 * r) * al)
                ctx.rectangle(bx, by, 20, 8 + 30 * r)
                ctx.fill()
        ctx.restore()
        TX.paint_label(ctx, 'INTERCEPTED JAPANESE MESSAGE', 540, y0 + 28, 28, os_, TX.YELLOW, al, 1.0, ow=0, fn='semi' if False else 'black')
        pa, ps = TX.pop(t, E['messages'])
        TX.paint_label(ctx, '"AF"  =  MIDWAY', 540, y0 + 132, 84, os_, TX.WHITE, pa * al, ps, ow=0, fn='anton')
    # altitude gauge: fighters pulled down to sea level, then the dive bombers high above them
    if E['pulled'] - 0.3 <= t <= E['hit'] + 0.2:
        al = sm(t, E['pulled'] - 0.3, E['pulled'] + 0.1) * (1 - sm(t, E['hit'] - 0.1, E['hit'] + 0.2))
        gx, gy0, gy1 = 960, 440, 1020
        ctx.save()
        ctx.scale(os_, os_)
        ctx.rectangle(gx - 5, gy0, 10, gy1 - gy0)
        set_c(ctx, WHITE, 0.35 * al)
        ctx.fill()
        for yy, nm in ((gy0, 'HIGH'), (gy1, 'SEA')):
            set_c(ctx, WHITE, 0.8 * al)
            ctx.rectangle(gx - 26, yy - 2, 52, 4)
            ctx.fill()
        fy = gy0 + (gy1 - gy0) * smooth(ramp(t, E['pulled'] + 0.1, E['waves'] + 0.3))
        set_c(ctx, hexc('ff8a80'), al)
        ctx.arc(gx, fy, 17, 0, 2 * math.pi)
        ctx.fill_preserve()
        set_c(ctx, INK, al)
        ctx.set_line_width(4)
        ctx.stroke()
        if t > E['dive'] - 0.1:
            bb = sm(t, E['dive'] - 0.1, E['dive'] + 0.4)
            by_ = gy0 + 10 + (gy1 - gy0 - 70) * smooth(ramp(t, E['dive'] + 0.5, E['hit'])) * 0.9
            set_c(ctx, hexc('9fd0ff'), bb * al)
            ctx.arc(gx, by_, 17, 0, 2 * math.pi)
            ctx.fill_preserve()
            set_c(ctx, INK, bb * al)
            ctx.stroke()
        ctx.restore()
        TX.paint_label(ctx, 'HIGH', gx - 4, gy0 - 36, 30, os_, TX.WHITE, al, 1.0, ow=4)
        TX.paint_label(ctx, 'SEA LEVEL', gx - 4, gy1 + 34, 30, os_, TX.WHITE, al, 1.0, ow=4)
        TX.paint_label(ctx, 'JAPANESE FIGHTERS', gx - 30, (gy0 + gy1) / 2 - 18, 30, os_, TX.RED_L, al * sm(t, E['fighters'], E['fighters'] + 0.3), 1.0, ow=4, clampx=False)
    # clouds the dive bombers fall out of
    kc = sm(t, E['clouds'] - 1.4, E['clouds'] - 0.3) * (1 - sm(t, E['hit'] - 0.3, E['hit'] + 0.4))
    if kc > 0:
        for i in range(16):
            x = ((hash01(i, 1) * 1500 - 220) + 70 * t * (0.3 + hash01(i, 5))) % 1500 - 220
            y = 180 + hash01(i, 2) * 1500
            soft_glow(ctx, x * os_, y * os_, (150 + 230 * hash01(i, 3)) * os_, (0.92, 0.95, 1.0, 1), 0.5 * kc)
    # white flash on the first hit
    f = (t - E['hit']) / 0.3
    if 0 <= f < 1:
        set_c(ctx, hexc('fff4dc'), 0.55 * (1 - f) ** 2)
        ctx.paint()
    ctx.restore()


def scene_main(ctx, t, os_):
    cam, z = make_cam(t)
    ctx.save()
    cam.apply(ctx, 1.0, os_)
    draw_map(ctx, cam, z, t)
    draw_action(ctx, cam, z, t)
    ctx.restore()
    draw_overlay(ctx, cam, z, t, os_)
    c0, _ = make_cam(t - 1 / 60)
    c1, _ = make_cam(t + 1 / 60)
    bx, by = (c1.cx - c0.cx) * z * 0.55, (c1.cy - c0.cy) * z * 0.55
    look = dict(dark=0.0, desat=0.03, bloom=0.3, vig=0.5, grain=0.03, tint=(1.0, 1.0, 1.03))
    if abs(bx) > 22 or abs(by) > 22:
        look['blur'] = (min(abs(bx), 420), min(abs(by), 240))
        k = min(1.0, math.hypot(bx, by) / 260)
        ctx.save()
        ctx.identity_matrix()
        ctx.translate(540 * os_, 960 * os_)
        ctx.rotate(math.atan2(by, bx))
        for i in range(22):
            fr = int(t * 30)
            y = (hash01(i, fr) - 0.5) * 2200
            x = (hash01(i, fr + 7) - 0.5) * 1400
            ln = 260 + 900 * hash01(i, fr + 3)
            set_c(ctx, WHITE, (0.06 + 0.2 * hash01(i, fr + 5)) * k)
            ctx.set_line_width((1.5 + 4 * hash01(i, fr + 9)) * os_)
            ctx.move_to((x - ln / 2) * os_, y * os_)
            ctx.line_to((x + ln / 2) * os_, y * os_)
            ctx.stroke()
        ctx.restore()
    return look
