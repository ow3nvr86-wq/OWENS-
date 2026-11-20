"""The Cuban Missile Crisis (October 1962): one continuous shot over a real map of the Caribbean. The camera follows the
U-2 over Cuba, the missile sites and their reach, the naval quarantine, the Soviet ships and submarine B-59, the
agreement of 28 October and the secret deal, and ends on a pulse around Cuba. Times come from part4/scene_timing.json."""
import math

import cairo
import numpy as np

from core import W, H, EV as E, Camera, clamp, smooth, smoother, ease_out, ease_in, ramp, hash01, vnoise, fnoise, set_c, \
    path_smooth, path_poly, soft_glow
import mapdata as M
import text as TX
from common import hexc, sm, visible, scr, draw_grid, spline, along, arrow, plane, burst, dot, \
    WHITE, YELLOW, INK, RED, RED_L, RED_D, BLUE, BLUE_L, ARROW

BLUE_A = hexc('3f8cff')
SEA = hexc('0f2a4a')
SEA2 = hexc('163a63')
LANDC = hexc('2b3d58')
END = 99.0
HAVANA = (-82.36, 23.13)
KEYWEST = (-81.78, 24.56)
DC = (-77.04, 38.9)
MIAMI = (-80.19, 25.76)
SITES = [(-83.0, 22.7), (-82.4, 22.85), (-80.1, 22.8), (-79.5, 22.45), (-83.35, 22.55)]
CENTRE = (-79.0, 21.5)
ARC_R = 9.0
SUB = (-70.0, 23.6)

CAM = [
    (0.0, -80.0, 27.0, 42), (E['spy'] - 0.2, -82.0, 24.2, 62), (E['found'] + 0.1, -82.0, 23.1, 120), (E['ninety'] - 0.3, -81.4, 24.0, 135),
    (E['florida'] + 0.1, -80.0, 29.5, 46, 'out'), (E['oct2'] + 0.2, -76.0, 25.0, 42), (E['quarantine'] + 0.6, -72.5, 23.5, 52),
    (E['ships'] - 0.1, -68.0, 24.4, 44), (E['beneath'] - 0.1, -69.6, 23.8, 70), (E['submarine'] + 0.3, -70.0, 23.7, 150),
    (E['hunting'], -70.0, 23.6, 190), (E['arkhipov'] + 0.6, -70.0, 23.6, 215), (E['fire'] + 0.2, -70.0, 23.6, 225),
    (E['oct3'] + 0.4, -80.0, 23.3, 66, 'out'), (E['agreed'] + 0.5, -80.5, 23.2, 80), (E['secret'] - 0.1, -78.0, 27.0, 36, 'out'),
    (E['closest'] - 0.1, -76.0, 26.0, 28), (END, -75.0, 26.0, 24),
]
CAM[-1] = (max(E['voice_end'] + 2.0, CAM[-2][0] + 2.0), -75.0, 26.0, 24)
SHAKES = [(E['found'], 16), (E['ninety'], 14), (E['quarantine'], 14), (E['torpedo'], 16), (E['remove'], 12), (E['closest'], 16)]


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


def draw_map(ctx, cam, z, t):
    set_c(ctx, SEA)
    ctx.paint()
    draw_grid(ctx, cam, z, 0.05)
    hh = (H / 2 + 40) / z
    sp = max(10.0 / z, 9.0)
    ctx.new_path()
    yy = math.floor((cam.cy - hh) / sp) * sp
    while yy < cam.cy + hh:
        ctx.move_to(cam.cx - (W / 2 + 40) / z, yy)
        ctx.line_to(cam.cx + (W / 2 + 40) / z, yy)
        yy += sp
    set_c(ctx, hexc('2a5b8f'), 0.2)
    ctx.set_line_width(1.2 / z)
    ctx.stroke()
    M.stroke(ctx, 'LAND', SEA2, 22 / z, 0.9)
    M.fill(ctx, 'LAND', LANDC)
    M.fill(ctx, 'USA', hexc('34527a'))
    found = sm(t, E['found'] + 0.05, E['found'] + 0.6)
    gone = sm(t, E['remove'], E['cuba3'] + 0.5)
    M.fill(ctx, 'CUBA', hexc('7a3a3f'), 0.4 + 0.5 * found * (1 - 0.7 * gone))
    for n in ('USA', 'CUBA', 'MEX', 'BHS', 'HTI', 'JAM'):
        if visible(cam, z, n):
            M.stroke(ctx, n, WHITE, 1.2 / z, 0.35)
    M.stroke(ctx, 'LAND', WHITE, 1.2 / z, 0.3)


def ship(ctx, x, y, ang, z, s=1.0, col=WHITE, alpha=1.0, wake=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    sc = s / z
    ctx.scale(sc, sc)
    ctx.new_path()
    path_poly(ctx, np.array([(-17, -5), (12, -5), (19, 0), (12, 5), (-17, 5)], float), True)
    set_c(ctx, INK, 0.5 * alpha)
    ctx.save()
    ctx.translate(1.5, 4)
    ctx.fill_preserve()
    ctx.restore()
    set_c(ctx, col, alpha)
    ctx.fill_preserve()
    set_c(ctx, INK, alpha)
    ctx.set_line_width(1.6)
    ctx.stroke()
    ctx.rectangle(-4, -3, 8, 6)
    set_c(ctx, INK, 0.7 * alpha)
    ctx.fill()
    if wake:
        ctx.move_to(-18, 0)
        ctx.line_to(-58, 0)
        set_c(ctx, WHITE, 0.3 * alpha)
        ctx.set_line_width(4)
        ctx.stroke()
    ctx.restore()


def sub_icon(ctx, x, y, ang, z, s=1.0, alpha=1.0, glow=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    sc = s / z
    ctx.scale(sc, sc)
    if glow > 0:
        soft_glow(ctx, 0, 0, 90, hexc('ff5a4a'), 0.55 * glow * alpha)
    ctx.new_path()
    ctx.save()
    ctx.scale(34, 8)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    set_c(ctx, hexc('3a4250'), alpha)
    ctx.fill_preserve()
    set_c(ctx, hexc('ff7a6a'), alpha)
    ctx.set_line_width(2.2)
    ctx.stroke()
    ctx.rectangle(-6, -14, 12, 8)
    set_c(ctx, hexc('3a4250'), alpha)
    ctx.fill_preserve()
    set_c(ctx, hexc('ff7a6a'), alpha)
    ctx.stroke()
    ctx.restore()


def missile_site(ctx, x, y, z, k, gone=0.0):
    if k <= 0:
        return
    px = 1.0 / z
    a = k * (1 - gone)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(px, px)
    soft_glow(ctx, 0, 0, 50, hexc('ff3b30'), 0.5 * a)
    ctx.new_path()
    path_poly(ctx, np.array([(0, -17 * (0.5 + 0.5 * k)), (14 * k, 10), (-14 * k, 10)], float), True)
    set_c(ctx, hexc('ff4a3d'), a)
    ctx.fill_preserve()
    set_c(ctx, INK, a)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def draw_action(ctx, cam, z, t):
    px = 1.0 / z
    hx, hy = M.P(*HAVANA)
    # the U-2 crosses Cuba and photographs it
    if E['spy'] - 0.4 <= t <= E['found'] + 1.2:
        path = spline(M.PP([(-80.5, 25.6), (-82.0, 23.9), (-83.2, 22.7), (-81.0, 22.9), (-79.5, 22.6), (-77.6, 22.0)]), 80)
        u = smooth(ramp(t, E['spy'] - 0.3, E['found'] + 0.7))
        al = 1 - sm(t, E['found'] + 0.7, E['found'] + 1.2)
        seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(seg)])
        n = int(np.searchsorted(cum, u * cum[-1]))
        if n > 1:
            ctx.new_path()
            path_poly(ctx, path[:n], False)
            set_c(ctx, WHITE, 0.55 * al)
            ctx.set_line_width(3 * px)
            ctx.set_dash([10 * px, 8 * px])
            ctx.stroke()
            ctx.set_dash([])
        p, a = along(path, u)
        plane(ctx, p[0], p[1], a, z, 2.6, WHITE, al)
        # camera flashes
        for j, (lo, la) in enumerate(SITES[:3]):
            kk = (t - (E['found'] - 0.4 + 0.18 * j)) / 0.4
            if 0 <= kk < 1:
                sx, sy = M.P(lo, la)
                soft_glow(ctx, sx, sy, 150 * px * (0.6 + kk), hexc('fff4dc'), 0.8 * (1 - kk))
    # the missile sites appear; their reach towards Washington
    if t >= E['found']:
        for j, (lo, la) in enumerate(SITES):
            sx, sy = M.P(lo, la)
            k = sm(t, E['found'] + 0.1 * j, E['found'] + 0.1 * j + 0.4)
            missile_site(ctx, sx, sy, z, k, sm(t, E['remove'] + 0.1 * j, E['remove'] + 0.1 * j + 0.5))
    # "90 miles": the line from Key West to Cuba
    if E['ninety'] - 0.15 <= t <= E['oct2'] + 0.2:
        al = sm(t, E['ninety'] - 0.15, E['ninety'] + 0.2) * (1 - sm(t, E['florida'] + 0.1, E['oct2'] + 0.2))
        kx, ky = M.P(*KEYWEST)
        cx_, cy_ = M.P(-81.85, 23.05)
        ctx.new_path()
        ctx.move_to(kx, ky)
        ctx.line_to(kx + (cx_ - kx) * smooth(ramp(t, E['ninety'] - 0.1, E['miles'] + 0.2)), ky + (cy_ - ky) * smooth(ramp(t, E['ninety'] - 0.1, E['miles'] + 0.2)))
        set_c(ctx, YELLOW, al)
        ctx.set_line_width(5 * px)
        ctx.set_dash([14 * px, 9 * px])
        ctx.stroke()
        ctx.set_dash([])
    # range ring: missiles on Cuba reach Washington
    if E['ninety'] + 0.2 <= t <= E['oct2'] + 0.4:
        al = sm(t, E['florida'] - 0.3, E['florida'] + 0.3) * (1 - sm(t, E['oct2'] - 0.1, E['oct2'] + 0.4))
        dxx, dyy = M.P(*DC)
        rad = math.hypot(dxx - hx, dyy - hy) * smooth(ramp(t, E['florida'] - 0.2, E['florida'] + 0.8))
        for lw, a in ((16, 0.14), (5, 0.8)):
            ctx.new_path()
            ctx.arc(hx, hy, rad, 0, 2 * math.pi)
            set_c(ctx, RED_L, a * al)
            ctx.set_line_width(lw * px)
            ctx.stroke()
    # the quarantine: an arc of American ships round the east of Cuba
    if E['oct2'] <= t <= E['beneath'] + 3.5:
        k = smooth(ramp(t, E['announced'], E['quarantine'] + 0.7))
        a0, a1 = math.radians(-70), math.radians(70)
        cxm, cym = M.P(*CENTRE)
        R = ARC_R * M.K
        ctx.new_path()
        ctx.arc(cxm, cym, R, a0, a0 + (a1 - a0) * k)
        for lw, a in ((14, 0.15), (4, 0.9)):
            set_c(ctx, BLUE_L, a)
            ctx.set_line_width(lw * px)
            ctx.set_dash([18 * px, 10 * px])
            ctx.stroke_preserve()
        ctx.new_path()
        ctx.set_dash([])
        for i in range(9):
            f = i / 8
            a = a0 + (a1 - a0) * f
            if f <= k + 0.02:
                ship(ctx, cxm + R * math.cos(a), cym + R * math.sin(a), a + math.pi / 2, z, 1.9, hexc('cfe4ff'), 1.0)
    # Soviet ships sail west towards the line, and then the sub
    if E['ships'] - 0.2 <= t <= E['arkhipov'] + 1.0:
        al = sm(t, E['ships'] - 0.2, E['ships'] + 0.2) * (1 - sm(t, E['hunting'] - 0.2, E['hunting'] + 0.4))
        u = smooth(ramp(t, E['ships'] - 0.1, E['line'] + 0.3))
        for i, (lo, la) in enumerate(((-52.0, 26.0), (-52.5, 22.5), (-51.5, 19.5))):
            p0 = np.array(M.P(lo, la))
            p1 = np.array(M.P(-69.8 - 1.5 * i, 24.0 - 1.6 * i + 1.0))
            p = p0 + (p1 - p0) * u
            ship(ctx, p[0], p[1], math.atan2(p1[1] - p0[1], p1[0] - p0[0]), z, 2.0, hexc('ffb3a8'), al)
    if E['beneath'] <= t <= E['fire'] + 1.2:
        al = sm(t, E['beneath'], E['beneath'] + 0.4) * (1 - sm(t, E['fire'] + 0.6, E['fire'] + 1.2))
        sx, sy = M.P(*SUB)
        glow = 0.5 + 0.5 * math.sin(t * 5) if E['torpedo'] < t < E['credited'] else 0.0
        if t > E['credited'] + 0.2:
            glow *= 1 - sm(t, E['refusing'], E['fire'] + 0.2)
        sub_icon(ctx, sx, sy, math.radians(185), z, 2.6, al, max(glow, 0.0))
        # sonar pings from the hunters
        for r in range(3):
            v = ((t - E['beneath']) * 0.8 + r / 3) % 1.0
            set_c(ctx, BLUE_L, 0.55 * (1 - v) * al)
            ctx.set_line_width(3 * px)
            ctx.arc(sx, sy, (30 + 250 * v) * px, 0, 2 * math.pi)
            ctx.stroke()
        # American destroyers close in
        hk = smooth(ramp(t, E['hunting'] - 0.3, E['arkhipov']))
        for i in range(4):
            a = math.radians(40 + 90 * i + 8 * math.sin(t * 0.8 + i))
            rr = (330 - 160 * hk) * px
            ship(ctx, sx + rr * math.cos(a), sy + rr * math.sin(a), a + math.pi / 2 + math.pi, z, 2.4, hexc('cfe4ff'), al * sm(t, E['hunting'] - 0.4, E['hunting']))
        if E['torpedo'] <= t <= E['fire'] + 1.2:
            k = sm(t, E['torpedo'], E['torpedo'] + 0.3)
            nx, ny = sx - 62 * px, sy
            soft_glow(ctx, nx, ny, 40 * px, hexc('ffe36a'), 0.7 * k * al)
            set_c(ctx, hexc('ffe36a'), k * al)
            ctx.arc(nx, ny, 7 * px, 0, 2 * math.pi)
            ctx.fill()
    # the agreement: the missiles go home
    if E['oct3'] <= t <= E['secret'] + 0.5:
        for j, (lo, la) in enumerate(SITES):
            sx, sy = M.P(lo, la)
            u = sm(t, E['remove'] + 0.1 * j, E['remove'] + 0.1 * j + 1.4)
            if 0 < u < 1:
                ctx.save()
                ctx.translate(sx + 90 * px * u, sy - 20 * px * u)
                ctx.restore()
        arrow(ctx, [(-79.2, 22.6), (-74.0, 22.8), (-68.0, 23.2)], smooth(ramp(t, E['remove'], E['invade'])), z, 34, hexc('7fe3b0'),
              1 - sm(t, E['secret'] - 0.2, E['secret'] + 0.3))
    # the pulse at the end
    if t >= E['closest']:
        hx2, hy2 = M.P(-79.0, 21.8)
        for r in range(3):
            v = ((t - E['closest']) * 0.6 + r / 3) % 1.0
            set_c(ctx, RED_L, 0.7 * (1 - v))
            ctx.set_line_width(4 * px)
            ctx.arc(hx2, hy2, (30 + 520 * v) * px, 0, 2 * math.pi)
            ctx.stroke()


def draw_overlay(ctx, cam, z, t, os_):
    ctx.save()
    ctx.identity_matrix()
    for txt, lo, la, t0, t1, size, dy in (('CUBA', -78.4, 21.6, 0.2, E['oct2'], 54, 0), ('FLORIDA', -81.6, 27.2, 0.1, E['spy'] - 0.1, 44, 0),
                                          ('HAVANA', HAVANA[0], HAVANA[1], E['found'] + 0.3, E['ninety'] - 0.1, 40, 60),
                                          ('KEY WEST', KEYWEST[0], KEYWEST[1], E['ninety'], E['florida'] - 0.3, 38, -52),
                                          ('WASHINGTON, D.C.', DC[0], DC[1], E['florida'] + 0.4, E['oct2'], 40, 56),
                                          ('MIAMI', MIAMI[0], MIAMI[1], E['florida'] + 0.1, E['oct2'] - 0.3, 34, 50),
                                          ('CUBA', -79.0, 21.8, E['oct2'] + 0.3, E['ships'], 56, 0),
                                          ('ATLANTIC OCEAN', -58.0, 20.2, E['ships'] - 0.3, E['beneath'] - 0.1, 44, 0),
                                          ('CUBA', -80.0, 21.8, E['oct3'], E['secret'], 56, 0)):
        if t0 <= t <= t1 + 0.25:
            x, y = scr(cam, lo, la)
            if -200 < x < 1280 and 300 < y < 1150:
                al, s = TX.pop(t, t0)
                if txt in ('WASHINGTON, D.C.', 'KEY WEST', 'MIAMI', 'HAVANA'):
                    dot(ctx, x, y, os_, al * (1 - sm(t, t1, t1 + 0.2)), YELLOW, 9)
                TX.paint_label(ctx, txt, x, y + dy, size, os_, TX.WHITE, al * (1 - sm(t, t1, t1 + 0.2)), s)
    if E['oct2'] + 0.5 <= t <= E['beneath'] + 3.0:
        x, y = scr(cam, -69.5, 30.4)
        al, s = TX.pop(t, E['quarantine'])
        TX.paint_label(ctx, 'QUARANTINE LINE', x, y, 40, os_, TX.BLUE, al * (1 - sm(t, E['beneath'] + 2.6, E['beneath'] + 3.0)), s, ow=5)
    if E['beneath'] <= t <= E['fire'] + 1.2:
        x, y = scr(cam, *SUB)
        al, s = TX.pop(t, E['submarine'])
        al *= 1 - sm(t, E['fire'] + 0.6, E['fire'] + 1.1)
        TX.paint_label(ctx, 'B-59', x, y - 96, 56, os_, TX.RED_L, al, s)
        if t >= E['hunting']:
            ha, hs = TX.pop(t, E['hunting'])
            TX.paint_label(ctx, 'US NAVY', x + 190, y + 150, 34, os_, TX.BLUE, ha * al, hs, ow=5)
        if E['arkhipov'] <= t:
            k = sm(t, E['refusing'], E['fire'] + 0.1)
            # a red "no" ring closes over the torpedo
            set_c(ctx, TX.RED_L if False else (1, 0.33, 0.31, 1), 0.9 * k * al)
            ctx.set_line_width(8 * os_)
            cx_, cy_ = x - 70 * 1.0, y
            ctx.arc(cx_, cy_, 52 * os_, 0, 2 * math.pi)
            ctx.stroke()
            ctx.move_to(cx_ - 37 * os_, cy_ - 37 * os_)
            ctx.line_to(cx_ + 37 * os_, cy_ + 37 * os_)
            ctx.stroke()
    # the secret deal: a padlocked folder, then the missiles leaving Turkey
    if E['secret'] <= t <= E['historians'] + 0.1:
        al = sm(t, E['secret'], E['secret'] + 0.3) * (1 - sm(t, E['historians'] - 0.2, E['historians'] + 0.1))
        cx_, cy_ = 540, 700
        ctx.save()
        ctx.scale(os_, os_)
        ctx.rectangle(cx_ - 200, cy_ - 60, 400, 270)
        set_c(ctx, hexc('d8c28c'), al)
        ctx.fill_preserve()
        set_c(ctx, INK, al)
        ctx.set_line_width(8)
        ctx.stroke()
        ctx.rectangle(cx_ - 200, cy_ - 100, 150, 46)
        set_c(ctx, hexc('d8c28c'), al)
        ctx.fill_preserve()
        set_c(ctx, INK, al)
        ctx.stroke()
        ctx.arc(cx_, cy_ + 60, 50, math.pi, 2 * math.pi)
        set_c(ctx, INK, al)
        ctx.set_line_width(16)
        ctx.stroke()
        ctx.rectangle(cx_ - 64, cy_ + 60, 128, 96)
        set_c(ctx, hexc('ffd23f'), al)
        ctx.fill_preserve()
        set_c(ctx, INK, al)
        ctx.set_line_width(7)
        ctx.stroke()
        ctx.arc(cx_, cy_ + 100, 13, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
        TX.paint_label(ctx, 'TOP SECRET', cx_, cy_ - 150, 54, os_, TX.RED_L, al, 1.0, ow=6)
        if t >= E['turkey']:
            ta, ts = TX.pop(t, E['turkey'])
            TX.paint_label(ctx, 'JUPITER MISSILES, TURKEY', cx_, cy_ + 270, 42, os_, TX.WHITE, ta * al, ts, ow=6)
            TX.paint_label(ctx, 'REMOVED APRIL 1963', cx_, cy_ + 330, 38, os_, TX.YELLOW, ta * al, ts, ow=6)
    f = (t - E['found']) / 0.3
    if 0 <= f < 1:
        set_c(ctx, hexc('fff4dc'), 0.5 * (1 - f) ** 2)
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
