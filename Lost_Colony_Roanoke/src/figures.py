"""2D character rig and ink renderer for the English colonists of Roanoke, 1587-1590.

A character is a set of design parameters (age, build, clothing, headwear, colours, face). A pose is a
dictionary of joint angles in screen space (0 = pointing down, positive = towards the side the figure faces),
plus head turn, expression and props. `draw_figure` builds every body part from the pose by forward
kinematics and draws it as an inked, cel-shaded, hatched shape, with a fresh 'boil' of the lines on every
new drawing. All units are character units: an adult is about 170 units tall, feet at y = 0, y downwards.
"""
import math

import cairo
import numpy as np

from core import (PAL, ink_shape, ink_line, taper_stroke, set_c, ellipse_pts, mix, shade_c, hash01, wob,
                  path_smooth, soft_glow, hatch_lines)


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])


def dirv(a):
    """Unit vector for a limb angle: 0 points down, +pi/2 points towards +x."""
    return np.array([math.sin(a), math.cos(a)])


def capsule(a, b, wa, wb, n=6):
    """Tapered limb outline from point a (width wa) to point b (width wb), rounded ends."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d) + 1e-6
    u = d / L
    nv = np.array([-u[1], u[0]])
    pts = []
    for k in range(n + 1):  # side 1
        t = k / n
        w = wa + (wb - wa) * t
        bulge = 1.0 + 0.10 * math.sin(math.pi * t)
        pts.append(a + d * t + nv * w * 0.5 * bulge)
    for k in range(1, 6):  # end cap at b
        ang = math.pi * k / 6
        pts.append(b + (nv * math.cos(ang) + u * math.sin(ang)) * wb * 0.5)
    for k in range(n, -1, -1):
        t = k / n
        w = wa + (wb - wa) * t
        bulge = 1.0 + 0.10 * math.sin(math.pi * t)
        pts.append(a + d * t - nv * w * 0.5 * bulge)
    for k in range(1, 6):
        ang = math.pi * k / 6
        pts.append(a + (-nv * math.cos(ang) - u * math.sin(ang)) * wa * 0.5)
    return np.array(pts)


# ----------------------------------------------------------------------------------------------
# Character designs
# ----------------------------------------------------------------------------------------------
def make_char(seed, sex=None, age=None, role='colonist', **over):
    """A plausible English colonist of 1587 (men, women and children, mostly from London), varied by seed.
    Roles: colonist, gent (ruff and capotain), soldier (morion), sailor (knitted cap)."""
    r = lambda k: hash01(seed, k)
    if sex is None:
        sex = 'f' if r(1) < 0.3 else 'm'
    if age is None:
        age = ['young', 'adult', 'adult', 'adult', 'child'][int(r(2) * 5)] if role == 'colonist' else 'adult'
    skins = [PAL['skin'], PAL['skin2'], PAL['skin3'], mix(PAL['skin'], PAL['skin2'], 0.5)]
    hairs = [PAL['hair_dk'], PAL['hair_br'], PAL['hair_bl'], PAL['hair_dk']]
    c = dict(seed=seed, sex=sex, age=age, role=role)
    c['height'] = {'child': 112, 'young': 166, 'adult': 170, 'old': 162}[age] * (0.96 + 0.08 * r(3)) * (0.95 if sex == 'f' else 1.0)
    c['build'] = 0.92 + 0.2 * r(4)
    c['skin'] = skins[int(r(5) * 4)]
    c['hair'] = PAL['hair_gr'] if age == 'old' else hairs[int(r(6) * 4)]
    c['nose'] = 0.85 + 0.4 * r(7)
    c['jaw'] = 0.9 + 0.25 * r(8)
    c['eye'] = 0.9 + 0.25 * r(9)
    c['brow_w'] = 0.8 + 0.5 * r(10)
    c['hunch'] = 0.16 if age == 'old' else 0.0
    c['beard'] = None
    cloth = [PAL['brown'], PAL['umber'], PAL['green3'], PAL['grey2'], PAL['brown2'], PAL['charcoal2'],
             mix(PAL['burg3'], PAL['brown'], 0.5), PAL['green'], PAL['parch3']]
    if sex == 'f':
        c['dress'] = 'gown'
        c['gown'] = cloth[int(r(11) * len(cloth))]
        c['apron'] = PAL['linen2'] if r(12) < 0.65 else None
        c['sleeve'] = c['gown'] if r(13) < 0.6 else shade_c(c['gown'], -0.25)
        c['head'] = 'coif' if r(14) < 0.8 else 'kerchief'
        if age == 'child':
            c['head'] = 'coif' if r(14) < 0.6 else 'none'
        c['partlet'] = PAL['linen']
    else:
        c['dress'] = 'jerkin'
        c['coat'] = cloth[int(r(11) * len(cloth))]
        c['hose'] = [PAL['charcoal2'], PAL['brown'], PAL['grey2'], PAL['green3'], PAL['umber']][int(r(15) * 5)]
        c['hose2'] = c['hose']
        c['sleeve'] = c['coat'] if r(18) < 0.5 else shade_c(c['coat'], -0.3)
        c['slashed'] = False
        c['head'] = ['capotain', 'none', 'monmouth', 'capotain', 'none'][int(r(20) * 5)]
        if age == 'child':
            c['head'] = 'none' if r(20) < 0.6 else 'monmouth'
        c['cap'] = [PAL['charcoal'], PAL['brown'], PAL['umber'], PAL['ink'], PAL['green3']][int(r(21) * 5)]
        if age in ('adult', 'old') and r(22) < 0.6:
            c['beard'] = 'full' if r(23) < 0.4 else 'short'
        c['partlet'] = PAL['linen']
    c['shoe'] = PAL['ink'] if r(24) < 0.5 else PAL['wood2']
    if role == 'gent':
        c.update(head='capotain', cap=PAL['ink'], ruff=True, coat=[PAL['charcoal'], PAL['burg3'], PAL['umber']][int(r(30) * 3)])
        c['sleeve'] = c['coat']
        if sex == 'f':
            c.update(gown=[PAL['burg3'], PAL['charcoal2'], PAL['green3']][int(r(31) * 3)], head='coif')
            c['sleeve'] = c['gown']
    if role == 'soldier':
        c.update(head='morion', coat=[PAL['brown2'], PAL['umber'], PAL['burg3']][int(r(30) * 3)], hose=PAL['charcoal2'], hose2=PAL['charcoal2'])
        c['sleeve'] = shade_c(c['coat'], -0.2)
    if role == 'sailor':
        c.update(head='monmouth', cap=[PAL['burg3'], PAL['charcoal2'], PAL['grey2']][int(r(30) * 3)],
                 coat=[PAL['parch3'], PAL['grey2'], PAL['brown2']][int(r(31) * 3)])
        c['sleeve'] = c['coat']
    c.update(over)
    if 'coat' in over and 'sleeve' not in over:
        c['sleeve'] = over['coat']
    if 'gown' in over and 'sleeve' not in over:
        c['sleeve'] = over['gown']
    return c


# ----------------------------------------------------------------------------------------------
# Poses
# ----------------------------------------------------------------------------------------------
def base_pose():
    return dict(bob=0.0, sway=0.0, lean=0.0, turn=0.25, tilt=0.0, hturn=None, nod=0.0,
                ua_b=-0.12, fa_b=-0.05, ua_f=0.12, fa_f=0.05, ual_b=1.0, fal_b=1.0, ual_f=1.0, fal_f=1.0,
                th_b=-0.06, sh_b=-0.04, th_f=0.06, sh_f=0.04, thl_b=1.0, thl_f=1.0, shl_b=1.0, shl_f=1.0,
                ft_b=0.0, ft_f=0.0, skirt=0.0, flare=0.0, swirl=0.0,
                brow=0.0, eyes=1.0, look=0.0, lookv=0.0, mouth=0.0, smile=0.0,
                prop=None, prop_t=0.0, arms_front=False, hands='open')


# ----------------------------------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------------------------------
class Pen:
    """Holds the per-figure drawing state: scale-dependent line widths and boil."""

    def __init__(self, pix, seed, boil_k):
        self.pix = max(pix, 0.05)
        self.seed = seed
        self.k = boil_k
        self.lw = float(np.clip(1.15, 1.6 / self.pix, 6.5 / self.pix))
        self.lw_fine = self.lw * 0.55
        self.boil = min(0.55, 1.4 / self.pix) if boil_k is not None else 0.0
        self.hsp = max(5.5 / self.pix, 1.3)
        self.hw = max(1.0 / self.pix, 0.25)
        self.detail = self.pix > 1.1
        self.hi = self.pix > 3.0
        self.n = 0

    def sd(self):
        self.n += 1
        return self.seed * 131 + self.n * 7 + (self.k or 0) * 977

    def shape(self, ctx, pts, fill, shadow=0.0, hatch=True, sdark=-0.32, lw=None, smooth_path=True, hangle=45):
        sh = None
        if shadow > 0:
            sh = (shade_c(fill, sdark), shadow * 1.55)
        hat = (self.hsp, hangle, self.hw, 0.5) if (hatch and self.detail and shadow > 0) else None
        pts = np.asarray(pts, float)
        ink_shape(ctx, pts, fill, lw=self.lw if lw is None else lw, shadow=sh, hatch=hat,
                  seed=self.sd(), boil=self.boil, smooth_path=smooth_path)
        if hat is not None and shadow > 1.0 and self.pix > 1.6:
            # core shadow: a second, crossing set of strokes deeper inside the shadow side
            ink_shape(ctx, pts, None, lw=0, shadow=((0, 0, 0, 0), shadow * 0.75),
                      hatch=(self.hsp * 1.1, hangle - 90, self.hw * 0.9, 0.32), seed=self.sd(), smooth_path=smooth_path)

    def line(self, ctx, pts, lw=None, col=None, alpha=1.0):
        ink_line(ctx, pts, self.lw_fine if lw is None else lw, col, self.sd(), self.boil, alpha=alpha)


def skeleton(c, p):
    """Forward kinematics: joint positions in character units (feet at y = 0)."""
    hk = c['height'] / 170.0
    bw = c['build']
    turn = p['turn']
    J = {'hk': hk}
    P = np.array([p['sway'], -92.0 * hk + p['bob']])
    lean = p['lean'] + c['hunch']
    J['P'] = P
    J['lean'] = lean
    J['N'] = P + rot(np.array([0.0, -48.0 * hk]), lean)
    sw = 19.0 * hk * bw * (1 - 0.5 * turn)
    J['Sb'] = J['N'] + rot(np.array([-sw, 6.5 * hk]), lean)
    J['Sf'] = J['N'] + rot(np.array([sw * (1 - 0.35 * turn), 6.5 * hk]), lean)
    J['Wb'] = P + rot(np.array([-12.0 * hk * bw * (1 - 0.45 * turn), -14.0 * hk]), lean * 0.6)
    J['Wf'] = P + rot(np.array([12.0 * hk * bw * (1 - 0.6 * turn), -14.0 * hk]), lean * 0.6)
    hw = 8.0 * hk * bw * (1 - 0.7 * turn)
    J['Hb'] = P + np.array([-hw, 0.0])
    J['Hf'] = P + np.array([hw, 0.0])
    head_r = 11.6 * hk * (1.28 if c['age'] == 'child' else 1.0)
    J['r'] = head_r
    J['Hd'] = J['N'] + rot(np.array([0.0, -head_r * 1.15]), lean + p['tilt'] * 0.5)
    for s in ('b', 'f'):
        S = J['S' + s]
        E = S + dirv(p['ua_' + s]) * 29.0 * hk * p['ual_' + s]
        Wr = E + dirv(p['fa_' + s]) * 25.0 * hk * p['fal_' + s]
        J['E' + s], J['R' + s] = E, Wr
        Hp = J['H' + s]
        K = Hp + dirv(p['th_' + s]) * 45.0 * hk * p['thl_' + s]
        A = K + dirv(p['sh_' + s]) * 43.0 * hk * p['shl_' + s]
        J['K' + s], J['A' + s] = K, A
    return J


def draw_figure(ctx, c, p, x, y, s, face=1, pix=None, boil_k=0, alpha=1.0, light=None, tint=None):
    """Draw character c in pose p with feet at (x, y), s world units per character unit, facing +x
    (face=1) or -x (face=-1). pix: screen pixels per character unit (sets line weight and detail)."""
    if pix is None:
        pix = s
    pen = Pen(pix, c['seed'], boil_k)
    J = skeleton(c, p)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * face, s)
    if alpha < 1.0:
        ctx.push_group()
    order_arms_back = not p['arms_front']
    if order_arms_back:
        draw_arm(ctx, c, p, J, 'b', pen)
    draw_leg(ctx, c, p, J, 'b', pen)
    draw_leg(ctx, c, p, J, 'f', pen)
    draw_body(ctx, c, p, J, pen)
    draw_head(ctx, c, p, J, pen)
    if not order_arms_back:
        draw_arm(ctx, c, p, J, 'b', pen)
    draw_prop_back(ctx, c, p, J, pen)
    draw_arm(ctx, c, p, J, 'f', pen)
    draw_prop(ctx, c, p, J, pen)
    if alpha < 1.0:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()
    return J


def draw_leg(ctx, c, p, J, s, pen):
    hk = J['hk']
    Hp, K, A = J['H' + s], J['K' + s], J['A' + s]
    long_skirt = c['dress'] in ('gown', 'robe') or c['sex'] == 'f'
    hose = c.get('hose' if s == 'b' else 'hose2', PAL['charcoal2'])
    if c['sex'] == 'f':
        hose = shade_c(PAL['linen2'], -0.35)
    if s == 'b':
        hose = shade_c(hose, -0.12)
    if not long_skirt:
        pen.shape(ctx, capsule(Hp, K, 11.5 * hk, 8.6 * hk), hose, shadow=2.2 * hk)
    pen.shape(ctx, capsule(K, A, 8.4 * hk, 5.6 * hk), hose, shadow=2.0 * hk)
    if not long_skirt and pen.detail:
        # knee and garter
        pen.line(ctx, [K + np.array([-4.0, 0.5]) * hk, K + np.array([4.0, 0.8]) * hk])
    draw_shoe(ctx, c, p, J, s, pen)


def draw_shoe(ctx, c, p, J, s, pen):
    """Broad-toed leather shoe of about 1518 (the 'cow-mouth' fashion), with a sole, an instep strap
    and the ankle opening; foreshortened when the figure faces us."""
    hk = J['hk']
    A = J['A' + s]
    turn = p['turn']
    fwd = 0.55 + 0.45 * turn
    ang = p['ft_' + s]
    L = 22.0 * hk * fwd
    wdt = 10.0 * hk * (1 - 0.3 * turn)
    hh = 6.0 * hk
    col = c.get('shoe_col', c['shoe'])
    if s == 'b':
        col = shade_c(col, -0.15)
    heel = -5.5 * hk * fwd
    upper = [[heel - 1.0 * hk, -hh * 0.2], [heel, -hh * 0.95], [L * 0.2, -hh * 1.05], [L * 0.62, -hh * 0.85],
             [L * 0.92, -hh * 0.62], [L + wdt * 0.18, -hh * 0.1], [L + wdt * 0.12, hh * 0.28], [L * 0.6, hh * 0.38],
             [L * 0.1, hh * 0.36], [heel - 0.5 * hk, hh * 0.3]]
    sole = [[heel - 0.8 * hk, hh * 0.18], [L + wdt * 0.15, hh * 0.18], [L + wdt * 0.1, hh * 0.5], [heel - 0.6 * hk, hh * 0.5]]
    cs, sn = math.cos(ang), math.sin(ang)
    off = A + np.array([0.0, 3.4 * hk])
    def T(q):
        return np.array([[v[0] * cs - v[1] * sn, v[0] * sn + v[1] * cs] for v in q]) + off
    pen.shape(ctx, T(sole), shade_c(col, -0.4), lw=pen.lw_fine, hatch=False)
    pen.shape(ctx, T(upper), col, shadow=1.8 * hk, hatch=False, sdark=-0.4)
    if pen.detail:
        # ankle opening, instep strap and the broad toe seam
        pen.line(ctx, T([[heel + 0.5 * hk, -hh * 0.85], [L * 0.15, -hh * 0.6], [L * 0.38, -hh * 0.75]]), lw=pen.lw_fine)
        pen.line(ctx, T([[L * 0.32, -hh * 1.0], [L * 0.42, hh * 0.25]]), lw=pen.lw_fine * 1.4)
        if pen.hi:
            pen.line(ctx, T([[L * 0.75, -hh * 0.7], [L * 0.8, hh * 0.25]]), lw=pen.lw_fine * 0.7, alpha=0.6)
            ctx.new_path()
            q = T([[L * 0.37, -hh * 0.35]])[0]
            ctx.arc(q[0], q[1], 0.9 * hk, 0, 2 * math.pi)
            set_c(ctx, PAL['grey3'])
            ctx.fill()


def draw_arm(ctx, c, p, J, s, pen):
    hk = J['hk']
    S, E, R = J['S' + s], J['E' + s], J['R' + s]
    col = c.get('sleeve') or c.get('gown') or c.get('coat')
    if s == 'b':
        col = shade_c(col, -0.12)
    if c.get('slashed'):
        # puffed, slashed upper sleeve (fashionable about 1515-1520)
        pen.shape(ctx, capsule(S, E, 13.5 * hk, 10.5 * hk), col, shadow=2.4 * hk)
        if pen.detail:
            for k in range(3):
                t = 0.25 + 0.25 * k
                q = S + (E - S) * t
                u = (E - S) / (np.linalg.norm(E - S) + 1e-6)
                nv = np.array([-u[1], u[0]])
                pen.shape(ctx, capsule(q - nv * 3.4 * hk, q + nv * 3.4 * hk, 2.0 * hk, 2.0 * hk), PAL['linen2'], lw=pen.lw_fine)
    else:
        pen.shape(ctx, capsule(S, E, 11.0 * hk, 9.2 * hk), col, shadow=2.4 * hk)
    pen.shape(ctx, capsule(E, R, 9.0 * hk, 7.0 * hk), col, shadow=2.0 * hk)
    if c.get('fur') and c['dress'] in ('gown',):
        pen.shape(ctx, capsule(R - (R - E) * 0.12, R + (R - E) * 0.05, 9.0 * hk, 8.6 * hk), c['fur'], lw=pen.lw_fine)
    else:
        pen.shape(ctx, capsule(R - (R - E) * 0.08, R + (R - E) * 0.04, 7.2 * hk, 7.0 * hk), PAL['linen'], lw=pen.lw_fine)
    draw_hand(ctx, c, p, J, s, pen)


def draw_hand(ctx, c, p, J, s, pen):
    hk = J['hk']
    E, R = J['E' + s], J['R' + s]
    u = (R - E) / (np.linalg.norm(R - E) + 1e-6)
    nv = np.array([-u[1], u[0]])
    L = 8.5 * hk
    wdt = 5.4 * hk
    style = p['hands'] if isinstance(p['hands'], str) else p['hands'].get(s, 'open')
    if style == 'fist':
        L *= 0.7
    C0 = R + u * 0.5 * hk
    pts = [C0 + nv * wdt * 0.5, C0 + u * L * 0.55 + nv * wdt * 0.62, C0 + u * L + nv * wdt * 0.25,
           C0 + u * L * 1.05 - nv * wdt * 0.15, C0 + u * L * 0.7 - nv * wdt * 0.55, C0 - nv * wdt * 0.5]
    pen.shape(ctx, pts, c['skin'], shadow=1.2 * hk, hatch=False)
    # thumb
    th = [C0 + u * 2.0 * hk - nv * wdt * 0.45, C0 + u * 4.0 * hk - nv * wdt * 1.05, C0 + u * 6.2 * hk - nv * wdt * 0.9,
          C0 + u * 5.0 * hk - nv * wdt * 0.35]
    pen.shape(ctx, th, c['skin'], lw=pen.lw_fine)
    if pen.hi and style != 'fist':
        for k in range(3):
            a = C0 + u * L * 0.6 + nv * wdt * (0.32 - 0.3 * k)
            pen.line(ctx, [a, a + u * L * 0.38], lw=pen.lw_fine * 0.8)


def draw_body(ctx, c, p, J, pen):
    hk = J['hk']
    P, N, Sb, Sf, Wb, Wf = J['P'], J['N'], J['Sb'], J['Sf'], J['Wb'], J['Wf']
    lean = J['lean']
    turn = p['turn']
    if c['sex'] == 'f' or c['dress'] in ('gown', 'robe'):
        draw_long_skirt(ctx, c, p, J, pen)
    else:
        draw_jerkin_skirt(ctx, c, p, J, pen)
    # torso
    col = c.get('gown') or c.get('coat')
    chest = [Sb + rot(np.array([-1.5, -2.0]) * hk, lean), N + rot(np.array([-6.0, -1.5]) * hk, lean),
             N + rot(np.array([6.0, -1.5]) * hk, lean), Sf + rot(np.array([1.5, -2.0]) * hk, lean),
             Sf + rot(np.array([0.5, 14.0]) * hk, lean), Wf + np.array([0.0, 2.0 * hk]),
             (Wb + Wf) / 2 + np.array([0.0, 3.5 * hk]), Wb + np.array([0.0, 2.0 * hk]),
             Sb + rot(np.array([-0.5, 14.0]) * hk, lean)]
    pen.shape(ctx, chest, col, shadow=3.0 * hk)
    cx = (N + (Wb + Wf) / 2) / 2
    ax = turn * 5.5 * hk
    if c['sex'] == 'f':
        # square neckline with a linen partlet, laced bodice
        nk = [N + rot(np.array([-7.5 + ax, 0.0]) * hk, lean), N + rot(np.array([7.0 + ax, 0.0]) * hk, lean),
              N + rot(np.array([6.0 + ax, 10.0]) * hk, lean), N + rot(np.array([-6.5 + ax, 10.0]) * hk, lean)]
        pen.shape(ctx, nk, c['partlet'], smooth_path=False, lw=pen.lw_fine)
        if pen.detail:
            pen.line(ctx, [N + rot(np.array([-6.5 + ax, 3.0]) * hk, lean), N + rot(np.array([6.0 + ax, 3.0]) * hk, lean)])
            if c.get('apron'):
                pass
            for k in range(4):
                yy = 13 + k * 5.5
                a1 = N + rot(np.array([-2.4 + ax, yy]) * hk, lean)
                a2 = N + rot(np.array([2.4 + ax, yy + 2.6]) * hk, lean)
                pen.line(ctx, [a1, a2], lw=pen.lw_fine * 0.8)
    else:
        if c['dress'] in ('gown', 'robe') and c.get('fur'):
            # fur collar falling over the shoulders, open front
            fc = [Sb + rot(np.array([-3.0, -1.0]) * hk, lean), N + rot(np.array([-5.0 + ax, -2.5]) * hk, lean),
                  N + rot(np.array([5.0 + ax, -2.5]) * hk, lean), Sf + rot(np.array([3.0, -1.0]) * hk, lean),
                  Sf + rot(np.array([-2.0, 9.0]) * hk, lean), N + rot(np.array([3.5 + ax, 22.0]) * hk, lean),
                  N + rot(np.array([-3.5 + ax, 22.0]) * hk, lean), Sb + rot(np.array([2.0, 9.0]) * hk, lean)]
            pen.shape(ctx, fc, c['fur'], shadow=2.0 * hk, hangle=-40)
            sh_ = [N + rot(np.array([-3.0 + ax, 2.0]) * hk, lean), N + rot(np.array([3.0 + ax, 2.0]) * hk, lean),
                   N + rot(np.array([2.0 + ax, 20.0]) * hk, lean), N + rot(np.array([-2.0 + ax, 20.0]) * hk, lean)]
            pen.shape(ctx, sh_, PAL['charcoal'] if c['role'] != 'priest' else PAL['linen'], lw=pen.lw_fine)
            if pen.detail and c['role'] == 'physician':
                pen.line(ctx, [N + rot(np.array([ax, 4.0]) * hk, lean), N + rot(np.array([ax, 20.0]) * hk, lean)], col=PAL['parch3'])
        else:
            # doublet with a linen shirt collar and buttons
            nk = [N + rot(np.array([-5.0 + ax, -1.0]) * hk, lean), N + rot(np.array([5.0 + ax, -1.0]) * hk, lean),
                  N + rot(np.array([3.0 + ax, 6.0]) * hk, lean), N + rot(np.array([-3.0 + ax, 6.0]) * hk, lean)]
            pen.shape(ctx, nk, c['partlet'], lw=pen.lw_fine)
            if pen.detail:
                for k in range(5):
                    q = N + rot(np.array([ax * 1.1, 9.0 + k * 6.5]) * hk, lean)
                    ctx.new_path()
                    ctx.arc(q[0], q[1], 0.9 * hk, 0, 2 * math.pi)
                    set_c(ctx, PAL['ink'])
                    ctx.fill()
                pen.line(ctx, [Wb + np.array([0.5, 1.0]) * hk, (Wb + Wf) / 2 + np.array([0, 2.4]) * hk, Wf + np.array([-0.5, 1.0]) * hk],
                         lw=pen.lw * 0.9)
    if c.get('ruff'):
        # a small pleated linen ruff, worn by gentlemen and gentlewomen in the 1580s
        q = N + rot(np.array([ax * 0.6, -1.0 * hk]), lean)
        rr = ellipse_pts(q[0], q[1], 10.5 * hk, 4.2 * hk, 26)
        pen.shape(ctx, rr, PAL['linen'], shadow=1.2 * hk, sdark=-0.15, hatch=False)
        if pen.detail:
            for k in range(9):
                a_ = math.pi * (0.08 + 0.84 * k / 8)
                pen.line(ctx, [q + np.array([math.cos(a_) * 4 * hk, math.sin(a_) * 1.5 * hk]),
                               q + np.array([math.cos(a_) * 10 * hk, math.sin(a_) * 4 * hk])], lw=pen.lw_fine * 0.7, alpha=0.6)
    if c.get('surplice'):
        sp = [Sb + rot(np.array([-2.0, 2.0]) * hk, lean), Sf + rot(np.array([2.0, 2.0]) * hk, lean),
              Wf + np.array([6.0, 26.0]) * hk, Wb + np.array([-6.0, 26.0]) * hk]
        pen.shape(ctx, sp, PAL['linen'], shadow=2.0 * hk)
    _ = cx


def draw_long_skirt(ctx, c, p, J, pen):
    hk = J['hk']
    P, Wb, Wf = J['P'], J['Wb'], J['Wf']
    Ab, Af, Kb, Kf = J['Ab'], J['Af'], J['Kb'], J['Kf']
    col = c.get('gown') or c.get('coat')
    robe = c['dress'] in ('robe', 'gown') and c['sex'] == 'm'
    hem_y = (-7.0 if not robe else -5.0) * hk - c.get('hem', 0.0) * hk
    base_half = (27.0 if not robe else 22.0) * hk * c['build'] * (1 - 0.25 * p['turn'])
    sw, fl, swirl = p['skirt'], p['flare'], p['swirl']
    n = 9
    hem = []
    for i in range(n):
        u = i / (n - 1) * 2 - 1  # -1..1 across the hem
        xx = P[0] * 0.5 + u * base_half * (1 + 0.45 * fl) + sw * 11.0 * hk * (1 - 0.3 * u * u)
        yy = hem_y + 3.5 * hk * math.sin(u * 3.0 + swirl) * (0.3 + fl) - fl * 6.0 * hk * (u * u)
        yy += 1.2 * hk * (hash01(c['seed'], i) - 0.5)
        hem.append([xx, yy])
    hem = np.array(hem)
    # the skirt rides up over a lifted knee
    for K, A in ((Kb, Ab), (Kf, Af)):
        lift = (-6.0 * hk) - A[1]
        if lift > 2.0:
            d = np.abs(hem[:, 0] - A[0]) / (base_half * 0.9)
            k = np.clip(1 - d, 0, 1) ** 1.5
            hem[:, 1] -= k * min(lift * 0.85, 30 * hk)
            hem[:, 0] += k * (A[0] - hem[:, 0]) * 0.15
    top_b = Wb + np.array([-1.0 * hk, -2.0 * hk])
    top_f = Wf + np.array([1.0 * hk, -2.0 * hk])
    mid_b = (top_b + hem[0]) / 2 + np.array([-3.0 * hk * (1 + fl), 0])
    mid_f = (top_f + hem[-1]) / 2 + np.array([3.0 * hk * (1 + fl), 0])
    pts = np.vstack([[top_b], [mid_b], hem, [mid_f], [top_f]])
    pen.shape(ctx, pts, col, shadow=5.0 * hk, hangle=60)
    if pen.detail:
        # folds from the waist to the hem
        for i in (2, 4, 6):
            top = top_b + (top_f - top_b) * (i / (n - 1))
            b = hem[i] + np.array([0.0, -1.0 * hk])
            mid = (top + b) / 2 + np.array([sw * 3.0 * hk, 0])
            pen.line(ctx, [top + np.array([0.0, 6.0 * hk]), mid, b], lw=pen.lw_fine, alpha=0.8)
    if c.get('apron') and c['sex'] == 'f':
        ax = p['turn'] * 6.0 * hk
        a_top_b = (top_b * 0.62 + top_f * 0.38) + np.array([ax, 0.0])
        a_top_f = (top_b * 0.22 + top_f * 0.78) + np.array([ax, 0.0])
        ab = hem[2] * 0.6 + hem[3] * 0.4 + np.array([ax * 0.8, -6.0 * hk])
        af = hem[6] * 0.6 + hem[5] * 0.4 + np.array([ax * 0.8, -6.0 * hk])
        ap = [a_top_b, a_top_f, af + np.array([1.5 * hk, 0]), (ab + af) / 2 + np.array([0, 1.5 * hk]), ab - np.array([1.5 * hk, 0])]
        pen.shape(ctx, ap, c['apron'], shadow=2.4 * hk, lw=pen.lw * 0.85)
        if pen.detail:
            pen.line(ctx, [a_top_b * 0.5 + a_top_f * 0.5 + np.array([0, 3 * hk]), (ab + af) / 2 - np.array([0, 4 * hk])], alpha=0.6)
    if c.get('fur') and robe:
        ax = p['turn'] * 5.0 * hk
        fr = [(top_b + top_f) / 2 + np.array([ax - 2.0 * hk, 0]), (top_b + top_f) / 2 + np.array([ax + 2.0 * hk, 0]),
              (hem[4] + hem[5]) / 2 + np.array([ax * 0.6 + 2.5 * hk, -1.0 * hk]), (hem[4] + hem[5]) / 2 + np.array([ax * 0.6 - 2.5 * hk, -1.0 * hk])]
        pen.shape(ctx, fr, c['fur'], lw=pen.lw_fine)
    # belt
    if c['sex'] == 'f' or robe:
        pen.shape(ctx, capsule(top_b + np.array([0, 1.5 * hk]), top_f + np.array([0, 1.5 * hk]), 3.0 * hk, 3.0 * hk),
                  shade_c(col, -0.45), lw=pen.lw_fine)


def draw_jerkin_skirt(ctx, c, p, J, pen):
    """Men's knee-high pleated jerkin skirt over hose."""
    hk = J['hk']
    P, Wb, Wf = J['P'], J['Wb'], J['Wf']
    col = c['coat']
    hem_y = P[1] + 34.0 * hk
    half = 17.0 * hk * c['build'] * (1 - 0.2 * p['turn'])
    sw = p['skirt']
    n = 7
    hem = []
    for i in range(n):
        u = i / (n - 1) * 2 - 1
        hem.append([P[0] + u * half * (1 + 0.5 * p['flare']) + sw * 6.0 * hk, hem_y + 1.6 * hk * math.cos(u * 6.0) - p['flare'] * 5.0 * hk * u * u])
    hem = np.array(hem)
    top_b = Wb + np.array([-0.8 * hk, -2.0 * hk])
    top_f = Wf + np.array([0.8 * hk, -2.0 * hk])
    pts = np.vstack([[top_b], hem, [top_f]])
    pen.shape(ctx, pts, col, shadow=3.5 * hk, hangle=60)
    if pen.detail:
        for i in range(1, n - 1):
            top = top_b + (top_f - top_b) * (i / (n - 1))
            pen.line(ctx, [top + np.array([0, 4 * hk]), hem[i] - np.array([0, 1.0 * hk])], lw=pen.lw_fine, alpha=0.75)
    pen.shape(ctx, capsule(top_b + np.array([0, 1.5 * hk]), top_f + np.array([0, 1.5 * hk]), 3.0 * hk, 3.0 * hk),
              PAL['ink'] if col != PAL['ink'] else PAL['brown'], lw=pen.lw_fine)
    if pen.detail:
        # a purse hanging at the belt
        q = top_f * 0.65 + top_b * 0.35 + np.array([0, 4.0 * hk])
        pen.shape(ctx, ellipse_pts(q[0], q[1] + 3.0 * hk, 3.2 * hk, 3.8 * hk, 10), PAL['wood2'], lw=pen.lw_fine)


def draw_head(ctx, c, p, J, pen):
    """The head and face: skull, ears, eyes, brows, nose, mouth, age lines, hair, beard and headwear."""
    hk = J['hk']
    r = J['r']
    Hd = J['Hd']
    N = J['N']
    lean = J['lean']
    f = p['hturn'] if p['hturn'] is not None else p['turn']
    f = float(np.clip(f, -0.2, 1.0))
    ctx.save()
    # neck
    neck = capsule(N + rot(np.array([0, 2.0 * hk]), lean), Hd + rot(np.array([f * 1.5 * hk, r * 0.6]), lean), 8.0 * hk, 7.4 * hk)
    if c['head'] != 'wimple':
        pen.shape(ctx, neck, c['skin'], shadow=1.8 * hk, hatch=False)
    ctx.translate(Hd[0], Hd[1])
    ctx.rotate(lean + p['tilt'])
    ctx.translate(0, p['nod'] * r * 0.2)
    skin = c['skin']
    child = c['age'] == 'child'
    old = c['age'] == 'old'
    # back hair or hood behind the head
    if c['head'] == 'hood':
        hood = [[-r * 1.25, r * 0.5], [-r * 1.3, -r * 0.5], [-r * 0.6, -r * 1.35], [r * 0.5, -r * 1.35], [r * 1.25, -r * 0.4],
                [r * 1.25, r * 0.7], [r * 1.6, r * 1.6], [-r * 1.6, r * 1.6]]
        pen.shape(ctx, hood, c['cap'], shadow=2.2 * hk)
    elif c['head'] in ('coif', 'kerchief', 'wimple'):
        back = [[-r * 1.1 + f * r * 0.1, -r * 0.2], [-r * 0.75, -r * 1.2], [r * 0.6, -r * 1.25], [r * 1.05, -r * 0.3],
                [r * 1.0, r * 0.7], [-r * 1.2, r * 0.95 + (0.4 * r if c['head'] == 'coif' else 0)]]
        pen.shape(ctx, back, PAL['linen'] if c['head'] != 'kerchief' else PAL['parch2'], shadow=2.0 * hk)
    # skull and face outline
    jaw = c['jaw']
    pts = []
    for i in range(28):
        th = 2 * math.pi * i / 28
        xx = math.sin(th) * r * 0.88
        yy = -math.cos(th) * r * 1.06
        if yy > 0:  # lower face narrows to the jaw and chin
            k = yy / (r * 1.06)
            xx *= 1 - (0.28 / jaw) * k * k
            yy *= 1.0 + 0.12 * k
        if child:
            yy *= 0.94
        xx += f * r * 0.16 * max(0.0, yy / r) if xx > 0 else f * r * 0.05 * max(0.0, yy / r)
        pts.append([xx, yy])
    face_pts = np.array(pts)
    # profile: the nose and brow push out of the outline when turned
    if f > 0.55:
        nose_t = np.array([r * (0.88 + 0.22 * c['nose'] * (f - 0.5) * 2), r * 0.25])
        idx = int(np.argmin(np.abs(face_pts[:, 1] - r * 0.25) + (face_pts[:, 0] < 0) * 99))
        face_pts = np.insert(face_pts, idx, [[r * 0.86, r * 0.02], nose_t, [r * 0.8, r * 0.42]], axis=0)
    pen.shape(ctx, face_pts, skin, shadow=2.2 * hk, hatch=pen.hi, sdark=-0.22)
    xc = f * r * 0.52
    # ears
    if c['head'] in ('none', 'flat', 'bonnet', 'capotain', 'morion', 'monmouth'):
        ex = -r * 0.86 + f * r * 0.42
        ear = ellipse_pts(ex, r * 0.08, r * 0.17, r * 0.27, 10)
        pen.shape(ctx, ear, shade_c(skin, -0.08), lw=pen.lw_fine)
        if f < 0.35:
            ear2 = ellipse_pts(r * 0.86 - f * 0.2 * r, r * 0.08, r * 0.15 * (1 - f), r * 0.26, 10)
            pen.shape(ctx, ear2, shade_c(skin, -0.08), lw=pen.lw_fine)
    if pen.pix * r > 3.0:
        draw_face(ctx, c, p, pen, r, f, xc, old, child, hk)
    # hair
    if c['head'] in ('none', 'flat', 'bonnet', 'capotain', 'morion', 'monmouth'):
        hair_col = c['hair']
        if c['sex'] == 'm' or child:
            top = [[-r * 0.95, r * 0.05], [-r * 0.98, -r * 0.55], [-r * 0.55, -r * 1.12], [r * 0.25, -r * 1.18],
                   [r * 0.9, -r * 0.7], [r * 0.92, -r * 0.2], [r * 0.6, -r * 0.62], [r * 0.0, -r * 0.7], [-r * 0.6, -r * 0.45]]
            if c['sex'] == 'm':  # short-cropped hair
                top = [[-r * 1.02, r * 0.55], [-r * 1.08, -r * 0.5], [-r * 0.55, -r * 1.14], [r * 0.3, -r * 1.18],
                       [r * 0.98, -r * 0.6], [r * 1.0, r * 0.35], [r * 0.8, r * 0.38], [r * 0.7, -r * 0.4],
                       [r * 0.0, -r * 0.66], [-r * 0.6, -r * 0.42], [-r * 0.72, r * 0.5]]
            top = np.array(top) + np.array([f * r * 0.08, 0])
            pen.shape(ctx, top, hair_col, shadow=1.6 * hk, sdark=-0.4)
            if pen.detail:
                for k in range(5):
                    a0 = np.array([-r * 0.7 + k * r * 0.35, -r * 0.95 + abs(k - 2) * r * 0.08])
                    pen.line(ctx, [a0, a0 + np.array([r * 0.08, r * 0.5])], lw=pen.lw_fine * 0.7, alpha=0.7)
    if c.get('beard'):
        bl = 0.75 if c['beard'] == 'short' else 1.25
        bd = [[-r * 0.8, r * 0.15], [-r * 0.62, r * (0.9 + 0.2 * bl)], [xc * 0.6, r * (1.15 + 0.35 * bl)],
              [r * 0.72 + f * r * 0.1, r * (0.85 + 0.2 * bl)], [r * 0.82, r * 0.18], [r * 0.5, r * 0.52], [xc + r * 0.3, r * 0.74],
              [xc - r * 0.3, r * 0.74], [-r * 0.45, r * 0.5]]
        pen.shape(ctx, bd, c['hair'], shadow=1.5 * hk, sdark=-0.4)
        if pen.detail:
            for k in range(6):
                a0 = np.array([-r * 0.55 + k * r * 0.24 + xc * 0.3, r * 0.75])
                pen.line(ctx, [a0, a0 + np.array([r * 0.03, r * 0.35 * bl])], lw=pen.lw_fine * 0.7, alpha=0.7)
        if pen.pix * r > 3.0:
            mouth_y = r * 0.62
            pen.line(ctx, [[xc - r * 0.22, mouth_y], [xc + r * 0.2, mouth_y + r * 0.02]], lw=pen.lw_fine)
    draw_headwear(ctx, c, p, pen, r, f, hk)
    ctx.restore()


def draw_face(ctx, c, p, pen, r, f, xc, old, child, hk):
    eye_y = -r * 0.05
    es = r * 0.17 * c['eye'] * (1.12 if child else 1.0)
    look = p['look']
    eopen = p['eyes']
    brow = p['brow']
    for side in (-1, 1):
        if side == 1:
            ex = xc + r * 0.36 * (1 - 0.75 * f)
            wk = 1 - 0.55 * f
        else:
            ex = xc - r * 0.36 * (1 - 0.25 * f)
            wk = 1 - 0.1 * f
        if side == 1 and f > 0.85:
            continue
        w = es * 1.25 * wk
        hgt = es * 0.62 * max(eopen, 0.05)
        # eye white
        if eopen > 0.15:
            alm = [[ex - w, eye_y], [ex - w * 0.3, eye_y - hgt], [ex + w * 0.5, eye_y - hgt * 0.95], [ex + w, eye_y],
                   [ex + w * 0.3, eye_y + hgt * 0.6], [ex - w * 0.4, eye_y + hgt * 0.55]]
            ink_shape(ctx, np.array(alm), PAL['linen'], lw=0, seed=pen.sd(), boil=pen.boil * 0.5)
            # iris
            ix = ex + look * w * 0.45 + f * w * 0.2
            iy = eye_y + p['lookv'] * hgt * 0.4
            ctx.save()
            ctx.new_path()
            path_smooth(ctx, alm, True)
            ctx.clip()
            ctx.new_path()
            ctx.arc(ix, iy, es * 0.42, 0, 2 * math.pi)
            set_c(ctx, PAL['umber'])
            ctx.fill()
            ctx.arc(ix, iy, es * 0.2, 0, 2 * math.pi)
            set_c(ctx, PAL['ink'])
            ctx.fill()
            if pen.hi:
                ctx.arc(ix - es * 0.12, iy - es * 0.14, es * 0.08, 0, 2 * math.pi)
                set_c(ctx, PAL['linen'])
                ctx.fill()
            ctx.restore()
        # upper lid: the strongest line of the face
        lid = [[ex - w * 1.05, eye_y + es * 0.05], [ex - w * 0.3, eye_y - hgt * 1.05 - es * 0.05],
               [ex + w * 0.5, eye_y - hgt * 1.0 - es * 0.05], [ex + w * 1.05, eye_y - es * 0.05]]
        taper_stroke(ctx, lid, pen.lw * 1.5, pen.lw * 0.6, PAL['ink'], pen.sd(), pen.boil * 0.5)
        if eopen > 0.15 and pen.hi:
            pen.line(ctx, [[ex - w * 0.7, eye_y + hgt * 0.62], [ex + w * 0.6, eye_y + hgt * 0.5]], lw=pen.lw_fine * 0.7, alpha=0.6)
        if old or pen.hi:
            # crease above the lid, and age lines
            pen.line(ctx, [[ex - w * 0.8, eye_y - hgt - es * 0.45], [ex + w * 0.7, eye_y - hgt - es * 0.4]],
                     lw=pen.lw_fine * 0.7, alpha=0.55)
        if old:
            pen.line(ctx, [[ex - w * 0.6, eye_y + es * 0.75], [ex + w * 0.5, eye_y + es * 0.85]], lw=pen.lw_fine * 0.7, alpha=0.6)
            pen.line(ctx, [[ex + side * w * 1.1, eye_y - es * 0.1], [ex + side * w * 1.5, eye_y + es * 0.25]], lw=pen.lw_fine * 0.6, alpha=0.6)
        # brow: inner end rises with worry
        by = eye_y - es * 1.55
        inner = ex - side * w * 0.9
        outer = ex + side * w * 1.1
        b_in = by - brow * es * 0.75
        b_out = by + brow * es * 0.25
        taper_stroke(ctx, [[inner, b_in], [(inner + outer) / 2, (b_in + b_out) / 2 - es * 0.25], [outer, b_out]],
                     pen.lw * 1.6 * c['brow_w'], pen.lw * 0.5, c['hair'] if c['hair'] != PAL['hair_gr'] else PAL['grey2'],
                     pen.sd(), pen.boil * 0.5)
    # nose
    ns = c['nose']
    nx = xc + f * r * 0.22
    nt = r * 0.34
    if f <= 0.55:
        pen.line(ctx, [[xc - r * 0.06 + f * r * 0.05, eye_y - es * 0.3], [nx + r * 0.08 * ns, nt - r * 0.02]], lw=pen.lw_fine, alpha=0.75)
        pen.line(ctx, [[nx - r * 0.14 * ns, nt + r * 0.04], [nx, nt + r * 0.1], [nx + r * 0.14 * ns, nt + r * 0.03]], lw=pen.lw_fine)
    else:
        pen.line(ctx, [[nx + r * 0.05, nt + r * 0.06], [nx + r * 0.2, nt + r * 0.1]], lw=pen.lw_fine)
    # mouth
    my = r * 0.6
    mw = r * 0.25 * (1 - 0.4 * f)
    mo = p['mouth']
    sm = p['smile']
    if not c.get('beard') or c['beard'] == 'short':
        if mo > 0.15:
            mpts = [[xc - mw, my], [xc, my - mo * r * 0.08], [xc + mw, my], [xc + mw * 0.4, my + mo * r * 0.3], [xc - mw * 0.4, my + mo * r * 0.3]]
            ink_shape(ctx, np.array(mpts), PAL['burg3'], lw=pen.lw_fine, seed=pen.sd(), boil=pen.boil * 0.5)
        else:
            taper_stroke(ctx, [[xc - mw, my - sm * r * 0.08], [xc, my + r * 0.02], [xc + mw, my - sm * r * 0.08]],
                         pen.lw * 1.0, pen.lw * 0.6, PAL['ink'], pen.sd(), pen.boil * 0.5)
        if pen.detail:
            pen.line(ctx, [[xc - mw * 0.5, my + r * 0.2 + mo * r * 0.2], [xc + mw * 0.5, my + r * 0.2 + mo * r * 0.2]], lw=pen.lw_fine * 0.7, alpha=0.5)
    if old:
        pen.line(ctx, [[xc - mw * 1.3, nt + r * 0.05], [xc - mw * 1.5, my + r * 0.12]], lw=pen.lw_fine * 0.7, alpha=0.6)
        pen.line(ctx, [[xc + mw * 1.3, nt + r * 0.05], [xc + mw * 1.5, my + r * 0.12]], lw=pen.lw_fine * 0.7, alpha=0.6)
        pen.line(ctx, [[xc - r * 0.35, -r * 0.55], [xc + r * 0.3, -r * 0.55]], lw=pen.lw_fine * 0.6, alpha=0.45)
    if pen.hi:
        # cheekbone and jaw shading strokes
        for k in range(3):
            x0 = -r * 0.62 + k * r * 0.07
            pen.line(ctx, [[x0, r * 0.15 + k * r * 0.05], [x0 + r * 0.1, r * 0.4 + k * r * 0.05]], lw=pen.lw_fine * 0.6, alpha=0.4)


def draw_headwear(ctx, c, p, pen, r, f, hk):
    hw = c['head']
    if hw == 'flat':
        # broad flat cap (barett), worn tilted
        ctx.save()
        ctx.translate(f * r * 0.05, -r * 0.72)
        ctx.rotate(-0.15)
        brim = ellipse_pts(0, 0, r * 1.38, r * 0.42, 22)
        pen.shape(ctx, brim, c['cap'], shadow=1.5 * hk, sdark=-0.5)
        crown = [[-r * 0.85, -r * 0.05], [-r * 0.72, -r * 0.55], [r * 0.1, -r * 0.72], [r * 0.85, -r * 0.4], [r * 0.9, -r * 0.02]]
        pen.shape(ctx, crown, shade_c(c['cap'], 0.08), shadow=1.2 * hk, sdark=-0.4)
        if pen.detail:
            pen.line(ctx, [[-r * 1.1, r * 0.05], [0, r * 0.25], [r * 1.1, r * 0.05]], lw=pen.lw_fine, alpha=0.6)
        ctx.restore()
    elif hw == 'capotain':
        # the tall-crowned, brimmed English hat of the 1580s
        ctx.save()
        ctx.translate(f * r * 0.06, -r * 0.78)
        ctx.rotate(-0.06)
        brim = ellipse_pts(0, 0, r * 1.5, r * 0.34, 24)
        pen.shape(ctx, brim, c['cap'], shadow=1.4 * hk, sdark=-0.5)
        crown = [[-r * 0.8, -r * 0.02], [-r * 0.74, -r * 0.9], [-r * 0.62, -r * 1.42], [r * 0.05, -r * 1.55], [r * 0.66, -r * 1.4],
                 [r * 0.78, -r * 0.88], [r * 0.82, -r * 0.02]]
        pen.shape(ctx, crown, shade_c(c['cap'], 0.06), shadow=1.6 * hk, sdark=-0.45, hangle=60)
        band = [[-r * 0.79, -r * 0.08], [r * 0.81, -r * 0.08], [r * 0.79, -r * 0.34], [-r * 0.77, -r * 0.34]]
        pen.shape(ctx, band, c.get('band', PAL['burg3']), lw=pen.lw_fine, smooth_path=False)
        ctx.restore()
    elif hw == 'morion':
        # a soldier's morion helmet: a crested steel cap with an up-turned brim
        steel = c.get('steel', PAL['grey'])
        ctx.save()
        ctx.translate(f * r * 0.06, -r * 0.55)
        brim = [[-r * 1.55, -r * 0.55], [-r * 1.0, -r * 0.05], [0, r * 0.12], [r * 1.0, -r * 0.05], [r * 1.55, -r * 0.55],
                [r * 1.25, -r * 0.2], [0, -r * 0.12], [-r * 1.25, -r * 0.2]]
        pen.shape(ctx, brim, steel, shadow=1.0 * hk, sdark=-0.4)
        dome = [[-r * 0.95, -r * 0.1], [-r * 0.9, -r * 0.75], [-r * 0.4, -r * 1.12], [r * 0.4, -r * 1.12], [r * 0.9, -r * 0.75], [r * 0.95, -r * 0.1]]
        pen.shape(ctx, dome, shade_c(steel, 0.12), shadow=2.0 * hk, sdark=-0.45)
        comb = [[-r * 0.55, -r * 1.0], [-r * 0.3, -r * 1.55], [r * 0.3, -r * 1.58], [r * 0.6, -r * 1.0]]
        pen.shape(ctx, comb, steel, lw=pen.lw_fine, sdark=-0.4, shadow=0.8 * hk)
        if pen.detail:
            soft_glow(ctx, -r * 0.35, -r * 0.7, r * 0.5, PAL['parch'], 0.35)
        ctx.restore()
    elif hw == 'monmouth':
        # a sailor's knitted cap
        cap = [[-r * 1.02, -r * 0.15], [-r * 0.95, -r * 0.85], [-r * 0.35, -r * 1.3], [r * 0.45, -r * 1.28], [r * 1.0, -r * 0.8],
               [r * 1.02, -r * 0.15]]
        pen.shape(ctx, np.array(cap) + np.array([f * r * 0.08, 0]), c['cap'], shadow=1.8 * hk, sdark=-0.4)
        pen.shape(ctx, capsule([-r * 1.04 + f * r * 0.08, -r * 0.2], [r * 1.04 + f * r * 0.08, -r * 0.2], r * 0.3, r * 0.3),
                  shade_c(c['cap'], -0.15), lw=pen.lw_fine)
    elif hw == 'bonnet':
        cap = [[-r * 0.98, -r * 0.2], [-r * 0.9, -r * 0.92], [-r * 0.2, -r * 1.3], [r * 0.6, -r * 1.2], [r * 1.0, -r * 0.6],
               [r * 0.98, -r * 0.15], [0.0, -r * 0.45]]
        pen.shape(ctx, cap, c['cap'], shadow=1.6 * hk, sdark=-0.5)
        pen.shape(ctx, capsule([-r * 0.98, -r * 0.2], [r * 0.98, -r * 0.15], r * 0.22, r * 0.22), shade_c(c['cap'], 0.1), lw=pen.lw_fine)
    elif hw == 'hood':
        rim = [[-r * 1.05, r * 0.65], [-r * 1.12, -r * 0.4], [-r * 0.55, -r * 1.22], [r * 0.45, -r * 1.24], [r * 1.12, -r * 0.4],
               [r * 1.08, r * 0.7], [r * 0.85, r * 0.62], [r * 0.82, -r * 0.35], [r * 0.3, -r * 0.92], [-r * 0.35, -r * 0.92],
               [-r * 0.85, -r * 0.35], [-r * 0.86, r * 0.6]]
        rim = np.array(rim) + np.array([f * r * 0.18, 0])
        pen.shape(ctx, rim, c['cap'], shadow=2.0 * hk)
    elif hw in ('coif', 'kerchief', 'wimple'):
        col = PAL['linen'] if hw != 'kerchief' else PAL['parch2']
        band = [[-r * 1.02, r * 0.45], [-r * 1.04, -r * 0.45], [-r * 0.55, -r * 1.16], [r * 0.45, -r * 1.2], [r * 1.04, -r * 0.5],
                [r * 1.02, r * 0.45], [r * 0.82, r * 0.42], [r * 0.82, -r * 0.4], [r * 0.3, -r * 0.82], [-r * 0.35, -r * 0.82],
                [-r * 0.84, -r * 0.38], [-r * 0.84, r * 0.42]]
        band = np.array(band) + np.array([f * r * 0.15, 0])
        pen.shape(ctx, band, col, shadow=2.0 * hk, sdark=-0.18)
        if pen.detail:
            pen.line(ctx, [[-r * 0.9 + f * r * 0.15, -r * 0.55], [f * r * 0.15, -r * 1.02], [r * 0.9 + f * r * 0.15, -r * 0.6]],
                     lw=pen.lw_fine * 0.7, alpha=0.5)
        if hw == 'wimple':
            ch = [[-r * 0.85, r * 0.1], [-r * 0.7, r * 1.0], [r * 0.0, r * 1.35], [r * 0.75, r * 1.0], [r * 0.85, r * 0.1],
                  [r * 0.62, r * 0.85], [0.0, r * 1.08], [-r * 0.62, r * 0.85]]
            ch = np.array(ch) + np.array([f * r * 0.15, 0])
            pen.shape(ctx, ch, col, shadow=1.5 * hk, sdark=-0.18)
            neck = [[-r * 0.75, r * 0.95], [r * 0.75, r * 0.95], [r * 1.3, r * 2.1], [-r * 1.3, r * 2.1]]
            pen.shape(ctx, np.array(neck) + np.array([f * r * 0.1, 0]), col, shadow=1.5 * hk, sdark=-0.18)


# ----------------------------------------------------------------------------------------------
# Props: urine flask, book, quill, drum, shawm, bagpipe, fiddle, torch, cross, staff
# ----------------------------------------------------------------------------------------------
def draw_prop_back(ctx, c, p, J, pen):
    hk = J['hk']
    pr = p['prop']
    if pr == 'chest':
        # a sea chest carried in front with both arms
        Wf, Wb = J['Wf'], J['Wb']
        cx, cy = (Wf[0] + Wb[0]) / 2 + 25 * hk, Wf[1] - 9 * hk
        box = [[cx - 18 * hk, cy - 11 * hk], [cx + 18 * hk, cy - 11 * hk], [cx + 18 * hk, cy + 11 * hk], [cx - 18 * hk, cy + 11 * hk]]
        pen.shape(ctx, box, PAL['wood'], shadow=3 * hk, smooth_path=False)
        pen.shape(ctx, [[cx - 19 * hk, cy - 11 * hk], [cx - 17 * hk, cy - 17 * hk], [cx + 17 * hk, cy - 17 * hk], [cx + 19 * hk, cy - 11 * hk]],
                  PAL['wood3'], lw=pen.lw_fine, smooth_path=False)
        if pen.detail:
            for dx in (-12, 12):
                pen.line(ctx, [[cx + dx * hk, cy - 16 * hk], [cx + dx * hk, cy + 11 * hk]], lw=pen.lw * 0.9, col=PAL['charcoal'])
    if False:
        pass
    elif pr == 'sack':
        Sb = J['Sb']
        cx, cy = Sb[0] - 9 * hk, Sb[1] - 11 * hk
        pen.shape(ctx, ellipse_pts(cx, cy, 17 * hk, 12 * hk, 18, rot=0.4), PAL['parch3'], shadow=3 * hk)
    if pr == 'drum':
        Wf = J['Wf']
        cx, cy = Wf[0] + 6 * hk, Wf[1] + 4 * hk
        body = [[cx - 16 * hk, cy - 12 * hk], [cx + 16 * hk, cy - 12 * hk], [cx + 16 * hk, cy + 12 * hk], [cx - 16 * hk, cy + 12 * hk]]
        pen.shape(ctx, body, PAL['wood3'], shadow=3 * hk, smooth_path=False)
        pen.shape(ctx, ellipse_pts(cx, cy - 12 * hk, 16 * hk, 4.5 * hk, 18), PAL['parch'], lw=pen.lw_fine)
        if pen.detail:
            for k in range(5):
                x0 = cx - 15 * hk + k * 7.5 * hk
                pen.line(ctx, [[x0, cy - 10 * hk], [x0 + 7.5 * hk, cy + 11 * hk]], lw=pen.lw_fine * 0.8, col=PAL['burg3'])
    if pr == 'bagpipe':
        Sb, Sf = J['Sb'], J['Sf']
        cx, cy = (Sb[0] + Sf[0]) / 2 - 10 * hk, Sf[1] + 14 * hk
        bag = ellipse_pts(cx, cy, 15 * hk, 10 * hk, 18, rot=0.3)
        pen.shape(ctx, bag, PAL['brown'], shadow=3 * hk)
        for k, (dx, ln) in enumerate(((-8, 34), (-2, 40))):
            a = np.array([cx + dx * hk, cy - 8 * hk])
            pen.shape(ctx, capsule(a, a + np.array([-6 * hk, -ln * hk]), 2.6 * hk, 2.0 * hk), PAL['wood2'], lw=pen.lw_fine)


def draw_prop(ctx, c, p, J, pen):
    hk = J['hk']
    pr = p['prop']
    if pr == 'baby':
        # an infant swaddled in linen, held in the crook of the arms
        Sf, Sb = J['Sf'], J['Sb']
        cx, cy = (Sf[0] + Sb[0]) / 2 + 8 * hk, Sf[1] + 22 * hk
        pen.shape(ctx, ellipse_pts(cx, cy, 17 * hk, 8.5 * hk, 20, rot=-0.3), PAL['linen'], shadow=2.2 * hk, sdark=-0.18)
        hx, hy = cx + 13 * hk, cy - 9 * hk
        pen.shape(ctx, ellipse_pts(hx, hy, 7.4 * hk, 7.4 * hk, 16), PAL['linen2'], lw=pen.lw_fine)
        pen.shape(ctx, ellipse_pts(hx + 1.2 * hk, hy + 0.8 * hk, 5.0 * hk, 5.2 * hk, 14), PAL['skin'], lw=pen.lw_fine)
        if pen.hi:
            pen.line(ctx, [[hx - 0.8 * hk, hy], [hx + 0.6 * hk, hy + 0.3 * hk]], lw=pen.lw_fine * 0.6)
            pen.line(ctx, [[hx + 2.0 * hk, hy], [hx + 3.2 * hk, hy + 0.3 * hk]], lw=pen.lw_fine * 0.6)
        return
    if pr is None:
        return
    Rf, Rb, Ef = J['Rf'], J['Rb'], J['Ef']
    u = (Rf - Ef) / (np.linalg.norm(Rf - Ef) + 1e-6)
    if pr == 'flask':
        # the physician's urine flask (matula), held up to the light
        q = Rf + u * 9 * hk + np.array([0, -8 * hk])
        ctx.save()
        body = ellipse_pts(q[0], q[1], 7.5 * hk, 8.5 * hk, 18)
        ink_shape(ctx, body, (0.78, 0.66, 0.36, 0.75), lw=pen.lw, seed=pen.sd(), boil=pen.boil)
        liquid = ellipse_pts(q[0], q[1] + 2.5 * hk, 6.5 * hk, 5.5 * hk, 16)
        ink_shape(ctx, liquid, (0.85, 0.62, 0.22, 0.8), lw=0, seed=pen.sd())
        neck = capsule(q + np.array([0, -7 * hk]), q + np.array([0, -16 * hk]), 3.2 * hk, 3.8 * hk)
        ink_shape(ctx, neck, (0.82, 0.74, 0.5, 0.6), lw=pen.lw_fine, seed=pen.sd(), boil=pen.boil)
        soft_glow(ctx, q[0] - 2 * hk, q[1] - 2 * hk, 6 * hk, PAL['candle2'], 0.5)
        ctx.restore()
    elif pr == 'book':
        q = (Rf + Rb) / 2 + np.array([0, -2 * hk])
        bk = [[q[0] - 14 * hk, q[1] - 2 * hk], [q[0], q[1] + 1 * hk], [q[0] + 14 * hk, q[1] - 2 * hk], [q[0] + 13 * hk, q[1] - 11 * hk],
              [q[0], q[1] - 9 * hk], [q[0] - 13 * hk, q[1] - 11 * hk]]
        pen.shape(ctx, bk, PAL['parch'], shadow=1.5 * hk, smooth_path=False)
        if pen.detail:
            for k in range(4):
                yy = q[1] - 8 * hk + k * 2 * hk
                pen.line(ctx, [[q[0] - 11 * hk, yy], [q[0] - 2 * hk, yy + 0.8 * hk]], lw=pen.lw_fine * 0.6, alpha=0.5)
                pen.line(ctx, [[q[0] + 2 * hk, yy + 0.8 * hk], [q[0] + 11 * hk, yy]], lw=pen.lw_fine * 0.6, alpha=0.5)
    elif pr == 'quill':
        q = Rf + u * 6 * hk
        taper_stroke(ctx, [q + np.array([2 * hk, 4 * hk]), q + np.array([-4 * hk, -10 * hk]), q + np.array([-9 * hk, -22 * hk])],
                     0.6 * hk, 3.2 * hk, PAL['linen2'], pen.sd(), pen.boil)
    elif pr == 'drumstick':
        q = Rf + u * 6 * hk
        pen.shape(ctx, capsule(q, q + u * 16 * hk + np.array([0, -4 * hk]), 1.8 * hk, 1.6 * hk), PAL['wood3'], lw=pen.lw_fine)
        pen.shape(ctx, ellipse_pts(*(q + u * 17 * hk + np.array([0, -4 * hk])), 2.6 * hk, 2.6 * hk, 8), PAL['parch2'], lw=pen.lw_fine)
    elif pr == 'drum':
        q = Rf + u * 6 * hk
        pen.shape(ctx, capsule(q, q + u * 15 * hk, 1.8 * hk, 1.5 * hk), PAL['wood3'], lw=pen.lw_fine)
    elif pr == 'shawm':
        # double-reed shawm held to the mouth by both hands
        Hd = J['Hd']
        mouth = Hd + rot(np.array([J['r'] * 0.55, J['r'] * 0.62]), J['lean'] + p['tilt'])
        end = (Rf + Rb) / 2 + np.array([10 * hk, 14 * hk])
        d = end - mouth
        ln = np.linalg.norm(d)
        end = mouth + d / ln * 46 * hk
        pen.shape(ctx, capsule(mouth, end, 2.2 * hk, 3.6 * hk), PAL['wood'], shadow=1 * hk, lw=pen.lw)
        bell = end + d / ln * 3 * hk
        pen.shape(ctx, ellipse_pts(bell[0], bell[1], 4.8 * hk, 3.4 * hk, 12, rot=math.atan2(d[1], d[0]) + math.pi / 2), PAL['wood3'], lw=pen.lw_fine)
        if pen.detail:
            for k in range(5):
                q = mouth + d / ln * (16 + k * 5) * hk
                ctx.new_path()
                ctx.arc(q[0], q[1], 0.7 * hk, 0, 2 * math.pi)
                set_c(ctx, PAL['ink'])
                ctx.fill()
    elif pr == 'bagpipe':
        Hd = J['Hd']
        mouth = Hd + rot(np.array([J['r'] * 0.55, J['r'] * 0.62]), J['lean'] + p['tilt'])
        chanter_end = (Rf + Rb) / 2 + np.array([4 * hk, 22 * hk])
        pen.shape(ctx, capsule(mouth + np.array([0, 4 * hk]), mouth + np.array([-8 * hk, 14 * hk]), 1.8 * hk, 1.8 * hk), PAL['wood2'], lw=pen.lw_fine)
        pen.shape(ctx, capsule((Rf + Rb) / 2 + np.array([0, -10 * hk]), chanter_end, 2.4 * hk, 3.2 * hk), PAL['wood'], lw=pen.lw_fine)
    elif pr == 'fiddle':
        Sb = J['Sb']
        body_c = Sb + np.array([2 * hk, 8 * hk])
        fid = [[-8, -4], [-4, -6], [6, -5], [12, -3], [12, 4], [6, 6], [-4, 5], [-8, 3]]
        a = -0.5
        pts = np.array([rot(np.array(v, float) * hk, a) for v in fid]) + body_c
        pen.shape(ctx, pts, PAL['wood3'], shadow=1.6 * hk)
        neck_end = body_c + rot(np.array([-26 * hk, 0]), a)
        pen.shape(ctx, capsule(body_c + rot(np.array([-7 * hk, 0]), a), neck_end, 2.4 * hk, 2.0 * hk), PAL['wood2'], lw=pen.lw_fine)
        bow_a = Rf + u * 4 * hk
        pen.line(ctx, [bow_a + np.array([-22 * hk, 6 * hk]), bow_a + np.array([14 * hk, -4 * hk])], lw=pen.lw * 0.9)
    elif pr == 'torch':
        q = Rf + u * 4 * hk
        top = q + np.array([2 * hk, -30 * hk])
        pen.shape(ctx, capsule(q + np.array([0, 8 * hk]), top, 2.6 * hk, 3.4 * hk), PAL['wood2'], lw=pen.lw_fine)
        fl = 1 + 0.25 * math.sin(p['prop_t'] * 23) + 0.15 * math.sin(p['prop_t'] * 37)
        soft_glow(ctx, top[0], top[1] - 6 * hk, 40 * hk, PAL['candle'], 0.35)
        flame = [[top[0] - 4 * hk, top[1]], [top[0] - 3 * hk, top[1] - 9 * hk * fl], [top[0] + 1 * hk, top[1] - 16 * hk * fl],
                 [top[0] + 3 * hk, top[1] - 8 * hk * fl], [top[0] + 4 * hk, top[1]]]
        ink_shape(ctx, np.array(flame), PAL['candle2'], lw=pen.lw_fine, ink=PAL['burg2'], seed=pen.sd(), boil=pen.boil * 2)
    elif pr == 'cross':
        q = Rf + u * 5 * hk
        pen.shape(ctx, capsule(q + np.array([0, 4 * hk]), q + np.array([0, -16 * hk]), 2 * hk, 2 * hk), PAL['wood3'], lw=pen.lw_fine)
        pen.shape(ctx, capsule(q + np.array([-6 * hk, -9 * hk]), q + np.array([6 * hk, -9 * hk]), 2 * hk, 2 * hk), PAL['wood3'], lw=pen.lw_fine)
    elif pr == 'palm':
        # a martyr's palm frond
        q = Rf + u * 5 * hk
        tip = q + np.array([10 * hk, -62 * hk])
        ink_line(ctx, np.array([q + np.array([0, 6 * hk]), q + np.array([6 * hk, -30 * hk]), tip]), pen.lw * 1.2, PAL['green3'])
        for k in range(10):
            t_ = 0.2 + k * 0.08
            b = q + (tip - q) * t_
            for sgn in (-1, 1):
                pen.line(ctx, [b, b + np.array([sgn * 10 * hk * (1.1 - t_), -6 * hk])], lw=pen.lw * 0.8, col=PAL['green3'])
    elif pr == 'staff':
        q = Rf + u * 5 * hk
        pen.shape(ctx, capsule(q + np.array([2 * hk, -24 * hk]), np.array([q[0] + 8 * hk, 0.0]), 2.4 * hk, 2.0 * hk), PAL['wood'], lw=pen.lw_fine)
    elif pr in ('hammer', 'axe'):
        q = Rf + u * 4 * hk
        hv = np.array([u[1], -u[0]])        # the handle is gripped across the fist
        nv = u
        end = q + hv * 26 * hk
        pen.shape(ctx, capsule(q - hv * 4 * hk, end, 2.2 * hk, 2.0 * hk), PAL['wood3'], lw=pen.lw_fine)
        u = hv
        if pr == 'hammer':
            pen.shape(ctx, capsule(end - nv * 6 * hk, end + nv * 6 * hk, 7 * hk, 7 * hk), PAL['wood'], shadow=1.2 * hk, lw=pen.lw_fine)
        else:
            blade = [end - u * 5 * hk, end + nv * 9 * hk - u * 7 * hk, end + nv * 11 * hk + u * 4 * hk, end + u * 3 * hk]
            pen.shape(ctx, blade, PAL['grey'], lw=pen.lw_fine, smooth_path=False, shadow=1 * hk)
    elif pr == 'log':
        # a timber carried on the shoulder
        Sf = J['Sf']
        a = np.array([Sf[0] - 55 * hk, Sf[1] - 4 * hk])
        b = np.array([Sf[0] + 45 * hk, Sf[1] - 9 * hk])
        pen.shape(ctx, capsule(a, b, 11 * hk, 10 * hk), PAL['wood'], shadow=3 * hk, hangle=10)
        pen.shape(ctx, ellipse_pts(b[0], b[1], 3.4 * hk, 5.2 * hk, 12), PAL['wood3'], lw=pen.lw_fine)
    elif pr == 'lantern':
        q = Rf + u * 5 * hk
        top = q + np.array([0, 4 * hk])
        pen.line(ctx, [q, top], lw=pen.lw_fine)
        box = [[top[0] - 5 * hk, top[1]], [top[0] + 5 * hk, top[1]], [top[0] + 5.5 * hk, top[1] + 13 * hk], [top[0] - 5.5 * hk, top[1] + 13 * hk]]
        fl = 1 + 0.08 * math.sin(p['prop_t'] * 21) + 0.05 * math.sin(p['prop_t'] * 33)
        soft_glow(ctx, top[0], top[1] + 7 * hk, 70 * hk * fl, PAL['candle'], 0.32)
        pen.shape(ctx, box, PAL['candle2'], lw=pen.lw_fine, smooth_path=False)
        pen.shape(ctx, [[top[0] - 6.5 * hk, top[1]], [top[0], top[1] - 4.5 * hk], [top[0] + 6.5 * hk, top[1]]], PAL['charcoal'], lw=pen.lw_fine, smooth_path=False)
        soft_glow(ctx, top[0], top[1] + 7 * hk, 12 * hk * fl, PAL['candle2'], 0.9)
    elif pr == 'trumpet':
        # a long natural trumpet raised to the lips
        Hd = J['Hd']
        mouth = Hd + rot(np.array([J['r'] * 0.6, J['r'] * 0.6]), J['lean'] + p['tilt'])
        d = np.array([math.cos(-0.22), math.sin(-0.22)])
        end = mouth + d * 62 * hk
        pen.shape(ctx, capsule(mouth, end, 1.6 * hk, 2.0 * hk), PAL['candle'], lw=pen.lw_fine)
        bell = [end - np.array([0, 1.5 * hk]), end + rot(np.array([8 * hk, -6 * hk]), -0.22), end + rot(np.array([8 * hk, 6 * hk]), -0.22),
                end + np.array([0, 1.5 * hk])]
        pen.shape(ctx, bell, PAL['candle'], lw=pen.lw_fine, smooth_path=False, shadow=1 * hk)
    elif pr == 'oar':
        q = (Rf + Rb) / 2
        d = np.array([math.sin(p.get('oar_a', 0.9)), math.cos(p.get('oar_a', 0.9))])
        pen.shape(ctx, capsule(q - d * 12 * hk, q + d * 95 * hk, 2.4 * hk, 2.6 * hk), PAL['wood3'], lw=pen.lw_fine)
        bl = q + d * 95 * hk
        pen.shape(ctx, capsule(bl - d * 16 * hk, bl + d * 4 * hk, 6 * hk, 6 * hk), PAL['wood3'], lw=pen.lw_fine)
    elif pr == 'musket':
        # a matchlock held upright, its butt on the ground
        q = Rf + u * 3 * hk
        base = np.array([q[0] + 4 * hk, -2.0])
        top = np.array([q[0] + 2 * hk, q[1] - 62 * hk])
        pen.shape(ctx, capsule(base, base + (top - base) * 0.3, 5.5 * hk, 3.4 * hk), PAL['wood'], lw=pen.lw_fine)
        pen.shape(ctx, capsule(base + (top - base) * 0.28, top, 2.2 * hk, 1.8 * hk), PAL['charcoal2'], lw=pen.lw_fine)
    elif pr == 'roll':
        # a rolled map or drawing
        q = Rf + u * 4 * hk
        nv = np.array([-u[1], u[0]])
        pen.shape(ctx, capsule(q - nv * 15 * hk, q + nv * 15 * hk, 4.6 * hk, 4.6 * hk), PAL['parch'], shadow=1.2 * hk, lw=pen.lw_fine)
    elif pr == 'basket':
        q = Rf + u * 2 * hk
        bk = [[q[0] - 13 * hk, q[1] + 1 * hk], [q[0] + 13 * hk, q[1] + 1 * hk], [q[0] + 10 * hk, q[1] + 16 * hk], [q[0] - 10 * hk, q[1] + 16 * hk]]
        pen.shape(ctx, bk, PAL['brown3'], shadow=2 * hk, hangle=-30)
        pen.line(ctx, [[q[0] - 12 * hk, q[1] + 1 * hk], [q[0], q[1] - 9 * hk], [q[0] + 12 * hk, q[1] + 1 * hk]], lw=pen.lw * 0.9)
    elif pr == 'paper':
        q = Rf + u * 7 * hk
        pp = [[q[0] - 8 * hk, q[1] - 10 * hk], [q[0] + 9 * hk, q[1] - 12 * hk], [q[0] + 10 * hk, q[1] + 8 * hk], [q[0] - 7 * hk, q[1] + 10 * hk]]
        pen.shape(ctx, pp, PAL['parch'], shadow=1.2 * hk, smooth_path=False, lw=pen.lw_fine)
