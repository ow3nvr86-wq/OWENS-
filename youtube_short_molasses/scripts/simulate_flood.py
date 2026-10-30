"""2D shallow-water simulation of the 1919 tank failure (a 'dam break' of molasses).

Solves the shallow-water equations with a second-order MUSCL / HLL finite-volume scheme
(Heun RK2 time stepping) on a 1 m grid. Buildings are reflective walls. Molasses is given
turbulent bed friction plus a laminar viscous drag whose viscosity rises as the evening
air cools it (the 2016 Sharp/Rubinstein/Kennedy estimate: a factor of four or more).

Outputs build/flood_sim.npz, which the Blender script reads each frame:
  times[k], h[k, ny, nx] (float16 depth), speed[k, ny, nx] (float16),
  debris positions / yaw / roll, the pushed house offset, the elevated-railway bend.

Run: python scripts/simulate_flood.py
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as L  # noqa: E402

G = 9.81
DX = 1.0
CFL = 0.4
T_END = 42.0
CF_TURB = 0.0015          # turbulent bed-friction coefficient
NU0 = 0.004               # kinematic viscosity, m^2/s (≈8 Pa·s at 1400 kg/m^3)
HARBOUR_SINK = 10.0       # e-folding time (s) for molasses sinking once it reaches the water
DRY = 1e-3
H_VEL = 0.02           # below this depth velocities are zeroed (wet/dry front)
U_MAX = 30.0


def out_times():
    return np.concatenate([np.arange(0.0, 14.0, 1.0 / 30.0), np.arange(14.0, T_END + 1e-6, 0.25)])


def nu_at(t):
    """Viscosity ramps up ×4 as the molasses cools from late afternoon into the freezing night."""
    s = min(1.0, max(0.0, (t - 12.0) / 22.0))
    return NU0 * (1.0 + 3.0 * s * s * (3 - 2 * s))


def minmod(a, b):
    return np.where(a * b > 0, np.sign(a) * np.minimum(np.abs(a), np.abs(b)), 0.0)


def hll_x(hL, uL, vL, hR, uR, vR):
    cL, cR = np.sqrt(G * hL), np.sqrt(G * hR)
    sL = np.minimum(uL - cL, uR - cR)
    sR = np.maximum(uL + cL, uR + cR)
    sL = np.where(hL <= DRY, uR - 2 * cR, sL)
    sR = np.where(hR <= DRY, uL + 2 * cL, sR)
    FL = (hL * uL, hL * uL * uL + 0.5 * G * hL * hL, hL * uL * vL)
    FR = (hR * uR, hR * uR * uR + 0.5 * G * hR * hR, hR * uR * vR)
    UL = (hL, hL * uL, hL * vL)
    UR = (hR, hR * uR, hR * vR)
    denom = np.where(np.abs(sR - sL) < 1e-9, 1e-9, sR - sL)
    out = []
    for fl, fr, ul, ur in zip(FL, FR, UL, UR):
        mid = (sR * fl - sL * fr + sL * sR * (ur - ul)) / denom
        out.append(np.where(sL >= 0, fl, np.where(sR <= 0, fr, mid)))
    return out


def flux_div_x(h, u, v, solid):
    """d/dx of the x-fluxes, shape (ny, nx). Walls are handled by mirrored ghost states."""
    pad = ((0, 0), (2, 2))
    hp, up, vp = (np.pad(a, pad, mode='edge') for a in (h, u, v))
    sp = np.pad(solid, pad, mode='constant', constant_values=False)
    near_wall = sp[:, 1:-1] | sp[:, :-2] | sp[:, 2:]
    sl = {}
    for name, q in (('h', hp), ('u', up), ('v', vp)):
        d = minmod(q[:, 2:] - q[:, 1:-1], q[:, 1:-1] - q[:, :-2])
        sl[name] = np.where(near_wall, 0.0, d)
    # faces between padded cells k and k+1, k = 1 .. nx+1
    k = slice(1, -2)
    k1 = slice(2, -1)
    hL = hp[:, k] + 0.5 * sl['h'][:, :-1]
    uL = up[:, k] + 0.5 * sl['u'][:, :-1]
    vL = vp[:, k] + 0.5 * sl['v'][:, :-1]
    hR = hp[:, k1] - 0.5 * sl['h'][:, 1:]
    uR = up[:, k1] - 0.5 * sl['u'][:, 1:]
    vR = vp[:, k1] - 0.5 * sl['v'][:, 1:]
    sL_, sR_ = sp[:, k], sp[:, k1]
    hL, hR = np.maximum(hL, 0), np.maximum(hR, 0)
    # wall on the right: mirror the left state; wall on the left: mirror the right state
    hR = np.where(sR_, hL, hR); uR = np.where(sR_, -uL, uR); vR = np.where(sR_, vL, vR)
    hL = np.where(sL_, hR, hL); uL = np.where(sL_, -uR, uL); vL = np.where(sL_, vR, vL)
    F = hll_x(hL, uL, vL, hR, uR, vR)
    both = sL_ & sR_
    F = [np.where(both, 0.0, f) for f in F]
    return [(f[:, 1:] - f[:, :-1]) / DX for f in F]


def velocities(h, hu, hv):
    wet = h > H_VEL
    u = np.clip(np.where(wet, hu / np.maximum(h, H_VEL), 0.0), -U_MAX, U_MAX)
    v = np.clip(np.where(wet, hv / np.maximum(h, H_VEL), 0.0), -U_MAX, U_MAX)
    return u, v


def rhs(h, hu, hv, solid):
    u, v = velocities(h, hu, hv)
    fx = flux_div_x(h, u, v, solid)
    gy = flux_div_x(h.T, v.T, u.T, solid.T)       # y-sweep: swap roles of u and v
    dh = -(fx[0] + gy[0].T)
    dhu = -(fx[1] + gy[2].T)
    dhv = -(fx[2] + gy[1].T)
    return dh, dhu, dhv


def main():
    x0, x1, y0, y1 = L.DOMAIN
    nx, ny = int((x1 - x0) / DX), int((y1 - y0) / DX)
    xc = x0 + DX * (np.arange(nx) + 0.5)
    yc = y0 + DX * (np.arange(ny) + 0.5)
    X, Y = np.meshgrid(xc, yc)
    solid = np.zeros((ny, nx), bool)
    for b in L.buildings():
        solid |= (X >= b['x0']) & (X <= b['x1']) & (Y >= b['y0']) & (Y <= b['y1'])
    harbour = Y < L.SEAWALL_Y
    r2 = (X - L.TANK_X) ** 2 + (Y - L.TANK_Y) ** 2
    h = np.where(r2 < L.TANK_R ** 2, L.FILL_H, 0.0)
    hu = np.zeros_like(h); hv = np.zeros_like(h)
    vol0 = h.sum() * DX * DX

    def sample(field, px, py):
        i = int(np.clip((py - y0) / DX - 0.5, 0, ny - 1)); j = int(np.clip((px - x0) / DX - 0.5, 0, nx - 1))
        return field[i, j], i, j

    # debris state
    deb = [dict(name=n, kind=k, x=x, y=y, yaw=yaw, vx=0.0, vy=0.0, z=0.0, roll=0.0, spin=0.0) for n, k, x, y, yaw in L.DEBRIS]
    # house pushed off its foundation
    H = L.PUSHED_HOUSE
    house = dict(dx=0.0, dy=0.0, vx=0.0, vy=0.0, tilt=0.0)
    hm = (X >= H['x0']) & (X <= H['x1']) & (Y >= H['y0']) & (Y <= H['y1'])
    # elevated railway: momentum flux hitting the columns near the tank
    el_band = (np.abs(Y - (L.EL_Y - L.EL_COL_DY)) < 1.5) & (np.abs(X - L.TANK_X) < 26)
    el_imp = 0.0

    times = out_times()
    rec = {k: [] for k in ('h', 'speed')}
    rec_deb, rec_house, rec_el, front = [], [], [], []
    t, k_out, steps = 0.0, 0, 0
    t0 = time.time()
    while k_out < len(times):
        if t >= times[k_out] - 1e-9:
            # record an output frame
            u, v = velocities(h, hu, hv)
            rec['h'].append(h.astype(np.float16))
            sp = np.sqrt(u ** 2 + v ** 2)
            rec['speed'].append(sp.astype(np.float16))
            rec_deb.append([(d['x'], d['y'], d['z'], d['yaw'], d['roll']) for d in deb])
            rec_house.append((house['dx'], house['dy'], house['tilt']))
            rec_el.append(el_imp)
            row = h[np.argmin(np.abs(yc - L.EL_Y))]
            wetx = xc[row > 0.3]
            front.append((t, float(wetx.min()) if len(wetx) else 0.0, float(wetx.max()) if len(wetx) else 0.0,
                          float(np.max(h[(Y > L.STREET_Y0) & (Y < L.STREET_Y1)]))))
            k_out += 1
            if k_out % 30 == 0:
                vol = h.sum() * DX * DX
                print(f't={t:5.2f}s steps={steps} max_h={h.max():.2f} vol={vol / vol0:.3f} '
                      f'max_speed={sp.max():.1f} m/s  ({time.time() - t0:.0f}s wall)', flush=True)
            continue
        u, v = velocities(h, hu, hv)
        hu, hv = h * u, h * v
        c = np.sqrt(G * h)
        smax = max(float(np.max(np.abs(u) + c)), float(np.max(np.abs(v) + c)), 1e-3)
        dt = min(CFL * DX / smax, 0.05)
        dt = min(dt, times[k_out] - t)
        # Heun RK2
        d1 = rhs(h, hu, hv, solid)
        h1 = np.maximum(h + dt * d1[0], 0); hu1 = hu + dt * d1[1]; hv1 = hv + dt * d1[2]
        d2 = rhs(h1, hu1, hv1, solid)
        h = np.maximum(0.5 * (h + h1 + dt * d2[0]), 0)
        hu = 0.5 * (hu + hu1 + dt * d2[1]); hv = 0.5 * (hv + hv1 + dt * d2[2])
        # implicit friction: turbulent + laminar viscous drag (viscosity rises as it cools)
        hs = np.maximum(h, 0.02)
        spd = np.sqrt(hu ** 2 + hv ** 2) / hs
        damp = 1.0 + dt * (CF_TURB * spd / hs + 3.0 * nu_at(t) / hs ** 2)
        hu /= damp; hv /= damp
        # molasses reaching the harbour sinks below the surface
        sink = np.exp(-dt / HARBOUR_SINK)
        h = np.where(harbour, h * sink, h); hu = np.where(harbour, hu * sink, hu); hv = np.where(harbour, hv * sink, hv)
        dry = (h < DRY) | solid
        h[dry] = 0; hu[dry] = 0; hv[dry] = 0

        # ---- coupled rigid bodies (one-way: the flow pushes them) ----
        u, v = velocities(h, hu, hv)
        for d in deb:
            hl, i, j = sample(h, d['x'], d['y'])
            heavy = d['kind'] in ('truck', 'wagon')
            if hl > (0.6 if heavy else 0.25):
                tau = 1.2 if heavy else 0.35
                a = 1 - math.exp(-dt / tau)
                d['vx'] += (u[i, j] - d['vx']) * a
                d['vy'] += (v[i, j] - d['vy']) * a
            else:
                f = math.exp(-dt / 0.25)
                d['vx'] *= f; d['vy'] *= f
            nxp, nyp = d['x'] + d['vx'] * dt, d['y'] + d['vy'] * dt
            _, i2, j2 = sample(h, nxp, d['y'])
            if solid[i2, j2]: d['vx'] *= -0.2; nxp = d['x']
            _, i2, j2 = sample(h, d['x'], nyp)
            if solid[i2, j2]: d['vy'] *= -0.2; nyp = d['y']
            d['x'], d['y'] = nxp, nyp
            sp_ = math.hypot(d['vx'], d['vy'])
            target_z = hl * (0.35 if heavy else 0.55)
            if d['y'] < L.SEAWALL_Y:      # off the seawall and into the water
                target_z = -1.4 - (3.0 if heavy else 0.3)
            d['z'] += (target_z - d['z']) * (1 - math.exp(-dt / 0.2))
            d['spin'] += (sp_ * 0.12 * (1 if sum(map(ord, d['name'])) % 2 else -1) - d['spin']) * (1 - math.exp(-dt / 0.5))
            d['yaw'] += d['spin'] * dt
            d['roll'] += sp_ * dt / (0.35 if d['kind'] == 'barrel' else 2.0)
        # house: drag force from the flow over its footprint
        fx = float(np.sum((h * u * np.abs(u))[hm])); fy = float(np.sum((h * v * np.abs(v))[hm]))
        k_force, c_drag = 4.5e-5, 1.1
        house['vx'] += dt * (k_force * fx - c_drag * house['vx'])
        house['vy'] += dt * (k_force * fy - c_drag * house['vy'])
        house['dx'] += house['vx'] * dt; house['dy'] += house['vy'] * dt
        dist = math.hypot(house['dx'], house['dy'])
        house["tilt"] = min(0.14, dist * 0.04)
        # railway: accumulate northward momentum flux on the columns
        el_imp += dt * float(np.sum((h * np.maximum(v, 0) ** 2)[el_band]))
        t += dt; steps += 1

    el = np.array(rec_el)
    el_bend = np.clip(el / max(el.max(), 1e-6), 0, 1)
    fr = np.array(front)
    # front speed along Commercial Street, westward, between 20 m and 80 m from the tank
    w = fr[:, 1]
    i_a = np.argmax(w < L.TANK_X - 20); i_b = np.argmax(w < L.TANK_X - 80)
    v_front = 60.0 / max(fr[i_b, 0] - fr[i_a, 0], 1e-6) if i_b > i_a else float('nan')
    print(f'front speed along street ≈ {v_front:.1f} m/s = {v_front * 2.237:.1f} mph; '
          f'peak depth in street ≈ {fr[:, 3].max():.1f} m = {fr[:, 3].max() * 3.281:.0f} ft')
    out = os.path.join(os.path.dirname(HERE), 'build', 'flood_sim.npz')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, times=times, h=np.array(rec['h']), speed=np.array(rec['speed']),
                        x0=x0, y0=y0, dx=DX, nx=nx, ny=ny, debris=np.array(rec_deb),
                        debris_names=np.array([d['name'] for d in deb]), house=np.array(rec_house),
                        el_bend=el_bend, front=fr, solid=solid)
    print('wrote', out, f'({os.path.getsize(out) / 1e6:.0f} MB)')


if __name__ == '__main__':
    main()
