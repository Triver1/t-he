"""Writes config.yaml for Ergogen from ../totem_geometry.scad and the case's PCB outline DXF.
Usage: python gen_config.py left|right  (mirrors x for the right half)"""
import sys, re, math
sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2 else '.')
side = sys.argv[1]
M = -1 if side == 'right' else 1
g = open('../totem_geometry.scad').read()
K = [[float(v) for v in m] for m in re.findall(r'\[([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+)\]', re.search(r'totem_keys = \[(.*?)\];', g, re.S)[1])]
H = [tuple(map(float, m)) for m in re.findall(r'\[([-\d.]+), ([-\d.]+)\]', re.search(r'totem_holes = \[(.*?)\];', g)[1])]
xiao = tuple(map(float, re.search(r'totem_xiao = \[([-\d.]+), ([-\d.]+)\]', g).groups()))
trrs = tuple(map(float, re.search(r'totem_trrs = \[([-\d.]+), ([-\d.]+)\]', g).groups()))

NAMES = ['pinky_top', 'ring_top', 'middle_top', 'index_top', 'inner_top',
         'pinky_home', 'ring_home', 'middle_home', 'index_home', 'inner_home',
         'pinky_bottom', 'ring_bottom', 'middle_bottom', 'index_bottom', 'inner_bottom',
         'outer', 'thumb1', 'thumb2', 'thumb3']
keys = {n: (M * k[0], k[1], M * k[2]) for n, k in zip(NAMES, K)}
# sensor output nets: one per key, and which mux input reads it
MUX = {'A': ['pinky_bottom', 'pinky_home', 'pinky_top', 'outer', 'ring_bottom', 'ring_home', 'ring_top'],
       'B': ['middle_bottom', 'middle_home', 'middle_top', 'index_bottom', 'index_home', 'index_top', 'thumb1', 'thumb2'],
       'C': ['inner_bottom', 'inner_home', 'inner_top', 'thumb3']}
MUX_AT = {'A': (58, -80, 90), 'B': (61, -71.2, 90), 'C': (121, -45, 0)}   # long axis along x for A and B
net = {k: f'K_{k.upper()}' for k in NAMES}

def f(x): return f'{x:.3f}'
out = ['meta:', '  engine: 4.1.0', f'  name: totem_he_{side}', 'units:', '  u: 19.05', 'points:', '  zones:',
       '    origin:', '      anchor: {shift: [0, 0]}', '      columns: {o: }', '      rows: {r: {tags: [helper]}}']
cols = [('pinky', ['pinky_bottom', 'pinky_home', 'pinky_top']), ('ring', ['ring_bottom', 'ring_home', 'ring_top']),
        ('middle', ['middle_bottom', 'middle_home', 'middle_top']), ('index', ['index_bottom', 'index_home', 'index_top']),
        ('inner', ['inner_bottom', 'inner_home', 'inner_top']), ('outer', ['outer']), ('thumb1', ['thumb1']), ('thumb2', ['thumb2']), ('thumb3', ['thumb3'])]
for zone, rows in cols:
    x0, y0, r = keys[rows[0]]
    tag = 'thumb' if zone.startswith('thumb') else 'alpha'
    out += [f'    {zone}:', f'      anchor: {{shift: [{f(x0)}, {f(y0)}], rotate: {f(r)}}}',
            f'      key: {{padding: u, tags: [{tag}]}}', '      columns: {c: }', '      rows:']
    for i, name in enumerate(rows):
        x, y, _ = keys[name]
        ex = x0 - i * 19.05 * math.sin(math.radians(r)); ey = y0 + i * 19.05 * math.cos(math.radians(r))
        dx, dy = x - ex, y - ey   # residual from the anisotropic Choc-to-MX scaling, in the key's frame
        lx = dx * math.cos(math.radians(-r)) - dy * math.sin(math.radians(-r)); ly = dx * math.sin(math.radians(-r)) + dy * math.cos(math.radians(-r))
        adj = f', adjust: {{shift: [{f(lx)}, {f(ly)}]}}' if abs(lx) + abs(ly) > 0.0005 else ''
        out.append(f'        {name.split("_")[-1] if "_" in name else "k"}: {{name: {name}, out_net: {net[name]}{adj}}}')

# board outline: the case's PCB shape (TOTEM's edge grown under the MX housings), exterior ring only
exec(open(f'{sys.argv[2]}/fit2.py').read().split('pcb=dxf(')[0])
from shapely import affinity
pcb = affinity.scale(dxf('/tmp/fitt/pcb.dxf'), 1, -1, origin=(0, 0)).simplify(0.02)
ring = list(pcb.exterior.coords)[:-1]
if M < 0: ring = [(-x, y) for x, y in ring][::-1]
out += ['outlines:', '  board:', '    - what: polygon', '      operation: add', '      points:']
for x, y in ring: out.append(f'        - {{ref: origin_o_r, shift: [{f(x)}, {f(y)}]}}')
out += ['  plate:', '    - what: outline', '      name: board', '    - what: rectangle', '      operation: subtract', '      where: [alpha, thumb]', '      size: 14']
out += ['pcbs:', f'  totem_he_{side}:', '    template: kicad8', '    outlines:', '      main: {outline: board}', '    footprints:',
        '      - what: switch_he', '        where: [alpha, thumb]', '        params: {VCC: VCC, GND: GND, OUT: "{{out_net}}"}']
for m, ks in MUX.items():
    x, y, r = MUX_AT[m]
    ys = ', '.join(f'Y{i}: {net[k]}' for i, k in enumerate(ks))
    out += ['      - what: mux_4051', f'        where: {{ref: origin_o_r, shift: [{f(M * x)}, {f(y)}], rotate: {f(M * r)}}}',
            f'        params: {{VCC: VCC, GND: GND, Z: ADC_{m}, S0: SEL0, S1: SEL1, S2: SEL2, {ys}}}']
out += ['      - what: xiao_rp2040', f'        where: {{ref: origin_o_r, shift: [{f(M * xiao[0])}, {f(xiao[1])}], rotate: {f(M * 90)}}}',
        '        params: {D0: ADC_A, D1: ADC_B, D2: ADC_C, D4: SEL0, D5: SEL1, D8: SEL2, D6: TX, D7: RX, V3: VCC, GND: GND}',
        '      - what: ceoloide/trrs_pj320a', f'        where: {{ref: origin_o_r, shift: [{f(M * trrs[0])}, {f(trrs[1])}]}}',
        '        params: {TP: VCC, R1: TX, R2: RX, SL: GND}']
for i, (x, y) in enumerate(H):
    out += ['      - what: ceoloide/mounting_hole_plated', f'        where: {{ref: origin_o_r, shift: [{f(M * x)}, {f(y)}]}}', '        params: {drill: 2.2}']
open('config.yaml', 'w').write('\n'.join(out) + '\n')
print(side, len(ring), 'outline points')
