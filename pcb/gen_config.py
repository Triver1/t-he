"""Writes config.yaml for Ergogen: both halves of Tot-HE-m in one PCB, from ../case/totem_geometry.scad and mux_map.json.

The left half uses the geometry as it is; the right half is mirrored about halves.AXIS_X with each part turned to
minus its angle, so footprints keep their land patterns. Every net carries its half's prefix (L/VCC, R/VCC).

mux_map.json gives each mux's position ("at": board x, y, angle) per half; this script works out the channels.
Each mux takes one finger group, and its channels follow the order in which those sensors sit around it, so the
sensor lines fan in without crossing and the common pin (Z) faces the XIAO. The result is written back to
mux_map.json ("chan"), which netcheck.py and ../firmware/gen_firmware.py check the board against.
Usage: gen_config.py  (writes config.yaml and mux_map.json beside it)
"""
import itertools
import json
import math
import os
import re

from halves import AXIS_X, PREFIX

HERE = os.path.dirname(os.path.abspath(__file__))
geo = open(os.path.join(HERE, '..', 'case', 'totem_geometry.scad')).read()
NAMES = ['pinky_top', 'ring_top', 'middle_top', 'index_top', 'inner_top',
         'pinky_home', 'ring_home', 'middle_home', 'index_home', 'inner_home',
         'pinky_bottom', 'ring_bottom', 'middle_bottom', 'index_bottom', 'inner_bottom',
         'outer', 'thumb1', 'thumb2', 'thumb3']
rows = re.findall(r'\[([-\d.]+), ([-\d.]+), ([-\d.]+), [01]\]', re.search(r'totem_keys = \[(.*?)\];', geo, re.S)[1])
KEYS = {n: (float(x), float(y), float(r)) for n, (x, y, r) in zip(NAMES, rows)}   # geometry frame: y up
HOLES = [tuple(map(float, m)) for m in re.findall(r'\[([-\d.]+), ([-\d.]+)\]', re.search(r'totem_holes = \[(.*?)\];', geo)[1])]
XIAO = tuple(map(float, re.search(r'totem_xiao = \[([-\d.]+), ([-\d.]+)\]', geo).groups()))
TRRS = tuple(map(float, re.search(r'totem_trrs = \[([-\d.]+), ([-\d.]+)\]', geo).groups()))

GROUPS = {'IC1': ('ADC_A', ['outer', 'pinky_top', 'pinky_home', 'pinky_bottom', 'ring_top', 'ring_home', 'ring_bottom']),
          'IC2': ('ADC_B', ['middle_top', 'middle_home', 'middle_bottom', 'index_top', 'index_home', 'index_bottom']),
          'IC3': ('ADC_C', ['inner_top', 'inner_home', 'inner_bottom', 'thumb1', 'thumb2', 'thumb3'])}
# 74HC4051 on the underside, pin -> (x, y) in the footprint's own frame (footprints/mux_4051.js), and its channel
MUX_PAD = {str(n): (-2.7, 4.445 - 1.27 * (n - 1)) for n in range(1, 9)}
MUX_PAD.update({str(n): (2.7, -4.445 + 1.27 * (n - 9)) for n in range(9, 17)})
CHANNEL = {'13': 0, '14': 1, '15': 2, '12': 3, '1': 4, '5': 5, '2': 6, '4': 7}


def side_xy(side, x, y_geo, r):
    """geometry point -> (board x, board y down, angle) on the given half"""
    return (x, -y_geo, r) if side == 'left' else (2 * AXIS_X - x, -y_geo, -r)


def place(at, local):
    x, y, r = at
    a = math.radians(r)
    lx, ly = local
    return x + lx * math.cos(a) + ly * math.sin(a), y - lx * math.sin(a) + ly * math.cos(a)


def crosses(a, b, c, d):
    o = lambda p, q, s: (q[0] - p[0]) * (s[1] - p[1]) - (q[1] - p[1]) * (s[0] - p[0])
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0


def channels(at, sensors, xiao):
    """key -> channel: sensors in the same turning order as the channel pins around the mux, Z toward the XIAO"""
    centre = at[:2]
    ang = lambda q: math.atan2(q[1] - centre[1], q[0] - centre[0])
    wrap = lambda d: abs((d + math.pi) % (2 * math.pi) - math.pi)
    pins = {n: place(at, MUX_PAD[n]) for n in list(CHANNEL) + ['3']}
    slots = sorted(pins, key=lambda n: ang(pins[n]))
    items = sorted([(ang(sensors[k]), k) for k in sensors] + [(ang(xiao), 'Z')])
    best = None
    for used in itertools.combinations(range(len(slots)), len(items)):
        for turn in range(len(items)):
            pairs = list(zip(items[turn:] + items[:turn], [slots[i] for i in used]))
            if any((k == 'Z') != (n == '3') for (_, k), n in pairs):
                continue
            cost = sum(wrap(a - ang(pins[n])) for (a, _), n in pairs)
            if best is None or cost < best[0]:
                best = (cost, {k: n for (_, k), n in pairs if k != 'Z'})
    pick = best[1]
    for _ in range(100):   # straight lines can still cross next to the chip: swap the pair until none do
        pair = next(((a, b) for a, b in itertools.combinations(pick, 2)
                     if crosses(sensors[a], pins[pick[a]], sensors[b], pins[pick[b]])), None)
        if not pair:
            break
        pick[pair[0]], pick[pair[1]] = pick[pair[1]], pick[pair[0]]
    return {k: CHANNEL[n] for k, n in pick.items()}


mux_path = os.path.join(HERE, 'mux_map.json')
mux_map = json.load(open(mux_path))
f = lambda v: f'{v:.4f}'.rstrip('0').rstrip('.')
out = ['meta:', '  engine: 4.1.0', '  name: totem_he', 'units:', '  u: 19.05', 'points:', '  zones:',
       '    origin:', '      anchor: {shift: [0, 0]}', '      columns: {o: }', '      rows: {r: {tags: [helper]}}']
parts = []
for side in ('left', 'right'):
    P = PREFIX[side]
    s = side[0]
    for n in NAMES:
        x, y, r = side_xy(side, *KEYS[n])
        out += [f'    {s}_{n}:', f'      anchor: {{shift: [{f(x)}, {f(-y)}], rotate: {f(r)}}}',
                f'      key: {{tags: [key_{s}], out_net: "{P}K_{n.upper()}"}}', '      columns: {c: }', '      rows: {r: }']
    sensors = {n: side_xy(side, *KEYS[n])[:2] for n in NAMES}
    xiao = side_xy(side, XIAO[0], XIAO[1], 90)
    for ic, (adc, keys) in GROUPS.items():
        at = tuple(mux_map[side][ic]['at'])
        # Z points at where its line arrives: the XIAO, or the "z_to" point in mux_map.json if the line comes another way
        if mux_map[side][ic].get('fixed'):        # channel order set by hand in mux_map.json, for routing
            chan = {k: int(c) for c, k in mux_map[side][ic]['chan'].items()}
        else:
            chan = channels(at, {k: sensors[k] for k in keys}, tuple(mux_map[side][ic].get('z_to', xiao[:2])))
        mux_map[side][ic].update(adc=adc, chan={str(c): k for k, c in sorted(chan.items(), key=lambda t: t[1])})
        ys = ', '.join(f'Y{c}: "{P}K_{k.upper()}"' for k, c in sorted(chan.items(), key=lambda t: t[1]))
        parts += ['  - what: mux_4051', f'    where: {{ref: origin_o_r, shift: [{f(at[0])}, {f(-at[1])}], rotate: {f(at[2])}}}',
                  f'    params: {{VCC: "{P}VCC", GND: "{P}GND", Z: "{P}{adc}", S0: "{P}SEL0", S1: "{P}SEL1", S2: "{P}SEL2", {ys}}}']
    parts += ['  - what: switch_he', f'    where: [key_{s}]', '    params: {VCC: "%sVCC", GND: "%sGND", OUT: "{{out_net}}"}' % (P, P)]
    parts += ['  - what: xiao_rp2040', f'    where: {{ref: origin_o_r, shift: [{f(xiao[0])}, {f(-xiao[1])}], rotate: {f(xiao[2])}}}',
              # the select lines and the link leave from the top row and the mux outputs from the bottom row, in the
              # order the top-edge bus needs them (see routes.py)
              f'    params: {{D0: "{P}ADC_A", D1: "{P}ADC_C", D2: "{P}ADC_B", D8: "{P}SEL0", D9: "{P}SEL1", D10: "{P}SEL2", '
              f'D7: "{P}DATA", V3: "{P}VCC", GND: "{P}GND"}}']
    tx, ty, tr = side_xy(side, TRRS[0], TRRS[1], 0)
    parts += ['  - what: trrs_pj320a', f'    where: {{ref: origin_o_r, shift: [{f(tx)}, {f(-ty)}], rotate: {f(tr)}}}',
              f'    params: {{TP: "{P}VCC", R2: "{P}DATA", SL: "{P}GND"}}']
    for hx, hy in HOLES:
        x, y, _ = side_xy(side, hx, hy, 0)
        parts += ['  - what: mounting_hole_plated', f'    where: {{ref: origin_o_r, shift: [{f(x)}, {f(-y)}]}}']
out += ['pcbs:', '  totem_he:', '    template: kicad8', '    references: true', '    footprints:'] + ['    ' + p for p in parts]
open(os.path.join(HERE, 'config.yaml'), 'w').write('\n'.join(out) + '\n')
json.dump(mux_map, open(mux_path, 'w'), indent=1)
print('wrote config.yaml and mux_map.json:', ', '.join(f'{s} {ic} {len(m["chan"])} keys' for s in mux_map for ic, m in mux_map[s].items()))
