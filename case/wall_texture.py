"""Generates wall_texture.scad: a texture carved into the carry case frame's outer face. The face is unrolled to a
strip (s along it, z up it) and cut to a depth that varies over it, in one of two styles:
  scales   a jittered field of pointed scales, stretched along a tilt that sways across the wall; each is a ramp with a
           raised spine, deepest at its lower end and flush at its top
  stripes  45 degree stripes, each stepping in at its lower edge and ramping back out to flush at its upper edge
Either way, the step at each edge goes inwards as it rises, so nothing overhangs, and edges blend over EDGE mm so they
print as creases. Every repeat around the loop is a whole number, so the pattern closes on itself, and it fades out
towards both rims so the lids sit on a plain edge. One closed polyhedron does the cut.
Usage: wall_texture.py <outline.svg> <wall_texture.scad> [scales|stripes] [grid scale, 1 = print]
"""
import bisect
import json
import math
import random
import re
import sys

DEPTH, ABOVE = 0.6, 0.2
Z0, Z1, FADE = 1.5, 56.8, 2.0
CELL_W, CELL_H, JITTER = 5.0, 3.4, 0.35
LEAN, LEAN_WAVE, STRETCH, EDGE = 0.75, 18.0, 1.7, 0.5
STRIPE = 6.0                                       # stripe pitch, measured square to the stripes
S_STEP, Z_STEP = 0.25, 0.2

style = sys.argv[3] if len(sys.argv) > 3 else 'scales'
grid = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
pts = [(float(a), -float(b)) for a, b in re.findall(r'(-?[\d.]+),(-?[\d.]+)', open(sys.argv[1]).read())]
if pts[0] == pts[-1]:
    pts.pop()
if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) < 0:
    pts.reverse()
closed = pts + pts[:1]
cum = [0.0]
for a, b in zip(closed, closed[1:]):
    cum.append(cum[-1] + math.dist(a, b))
total = cum[-1]


def at(s):
    s %= total
    i = min(bisect.bisect_right(cum, s) - 1, len(pts) - 1)
    t = (s - cum[i]) / (cum[i + 1] - cum[i])
    return closed[i][0] + t * (closed[i + 1][0] - closed[i][0]), closed[i][1] + t * (closed[i + 1][1] - closed[i][1])


def normal(s):
    a, b = at(s - 0.6), at(s + 0.6)
    d = math.dist(a, b) or 1.0
    return (b[1] - a[1]) / d, -(b[0] - a[0]) / d   # outward on a counter-clockwise loop


rng = random.Random(7)
cols = round(total / CELL_W)
pitch = total / cols
rows = round((Z1 - Z0) / CELL_H)
row_h = (Z1 - Z0) / rows
lean_turns = round(total / 120)


def lean(s, z):                                    # the scales' tilt from vertical, swaying across the wall like swell
    return LEAN * math.sin(2 * math.pi * (z / LEAN_WAVE + lean_turns * s / total))


seeds = []                                          # rows x cols of (s, z, tilt, depth share)
for r in range(rows):
    row = []
    for c in range(cols):
        ss = (c + 0.5 * (r % 2) + rng.uniform(-JITTER, JITTER)) * pitch
        zz = Z0 + (r + 0.5 + rng.uniform(-JITTER, JITTER)) * row_h
        row.append((ss, zz, lean(ss, zz) + rng.uniform(-0.15, 0.15), rng.uniform(0.6, 1.0)))
    seeds.append(row)


def local(s, z, seed):
    """along the scale's axis (up the scale) and across it, the along axis divided by STRETCH"""
    ss, zz, tilt, _ = seed
    ds, dz = (s - ss + total / 2) % total - total / 2, z - zz
    along = dz * math.cos(tilt) + ds * math.sin(tilt)
    across = ds * math.cos(tilt) - dz * math.sin(tilt)
    return along, across


def scale_depth(s, z, seed):
    along, across = local(s, z, seed)
    ramp = min(1.0, max(0.0, 0.55 - along / (STRETCH * row_h)))   # deepest at the scale's lower end
    spine = 0.6 + 0.4 * min(1.0, abs(across) / (0.5 * pitch))       # a raised spine down its middle
    return DEPTH * seed[3] * ramp * spine


def stripe_depth(s, z):
    pitch = total / round(total / (STRIPE * math.sqrt(2)))   # along the loop, so a whole number of stripes fits
    w = ((s + z) / pitch) % 1.0                      # 0 to 1 across one stripe, rising with z
    edge = EDGE / STRIPE                             # the blend, as a share of the stripe
    return DEPTH * (w / edge * (1 - edge) if w < edge else 1 - w)   # steps in at the stripe's lower edge, then rises out


def cut(s, z):
    if not Z0 <= z <= Z1:
        return 0.0
    if style == 'stripes':
        return stripe_depth(s, z) * max(0.0, min(1.0, (z - Z0) / FADE, (Z1 - z) / FADE))
    r0, c0 = int((z - Z0) / row_h), int(s // pitch)
    near = []
    for r in range(max(0, r0 - 2), min(rows, r0 + 3)):
        for c in range(c0 - 3, c0 + 4):
            seed = seeds[r][c % cols]
            along, across = local(s, z, seed)
            near.append(((along / STRETCH) ** 2 + across ** 2, seed))
    near.sort(key=lambda e: e[0])
    (d1, a), (d2, b) = near[0], near[1]
    gap = (math.sqrt(d2) - math.sqrt(d1)) / 2        # roughly the distance to the edge between the two nearest scales
    blend = min(1.0, gap / EDGE) * 0.5 + 0.5
    depth = scale_depth(s, z, a) * blend + scale_depth(s, z, b) * (1 - blend)
    fade = min(1.0, (z - Z0) / FADE, (Z1 - z) / FADE)
    return depth * max(0.0, fade)


step_s, step_z = S_STEP * grid, Z_STEP * grid
stations = sorted(set(round(s, 3) for s in cum[:-1]) | {round(i * step_s, 3) for i in range(int(total / step_s))})
stations = [s for s, nxt in zip(stations, stations[1:] + [stations[0] + total]) if nxt - s > 0.05]
rows_z = [Z0 + (Z1 - Z0) * j / round((Z1 - Z0) / step_z) for j in range(round((Z1 - Z0) / step_z) + 1)]
n, m = len(stations), len(rows_z)
geo = [(at(s), normal(s)) for s in stations]
v = []
for z in rows_z:                                   # outer sheet, then inner sheet, each row by row
    for (x, y), (nx, ny) in geo:
        v.append([round(x + nx * ABOVE, 3), round(y + ny * ABOVE, 3), round(z, 3)])
for z in rows_z:
    for s, ((x, y), (nx, ny)) in zip(stations, geo):
        d = cut(s, z)
        v.append([round(x - nx * d, 3), round(y - ny * d, 3), round(z, 3)])
O, I = 0, n * m
idx = lambda sheet, j, i: sheet + j * n + i % n
f = []
for j in range(m - 1):
    for i in range(n):
        f.append([idx(O, j, i), idx(O, j, i + 1), idx(O, j + 1, i + 1), idx(O, j + 1, i)])
        f.append([idx(I, j, i), idx(I, j + 1, i), idx(I, j + 1, i + 1), idx(I, j, i + 1)])
for i in range(n):
    f.append([idx(O, 0, i), idx(I, 0, i), idx(I, 0, i + 1), idx(O, 0, i + 1)])
    f.append([idx(O, m - 1, i), idx(O, m - 1, i + 1), idx(I, m - 1, i + 1), idx(I, m - 1, i)])
vol = 0.0
for q in f:
    p0 = v[q[0]]
    for i1, i2 in zip(q[1:], q[2:]):
        p1, p2 = v[i1], v[i2]
        vol += (p0[0] * (p1[1] * p2[2] - p1[2] * p2[1]) - p0[1] * (p1[0] * p2[2] - p1[2] * p2[0]) + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0])) / 6
if vol > 0:                                        # OpenSCAD lists a face's corners clockwise from outside
    f = [q[::-1] for q in f]
open(sys.argv[2], 'w').write('// generated by wall_texture.py\nmodule wall_texture() polyhedron('
                             + json.dumps(v, separators=(',', ':')) + ',' + json.dumps(f, separators=(',', ':')) + ');\n')
print(f'{total:.1f} mm loop, {n} x {m} grid, {style}')
