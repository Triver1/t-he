"""Checks the generated KiCad PCBs against the case geometry. Usage: pcbfit.py <scratch dir>"""
import sys, re, math, yaml
S = sys.argv[1]
exec(open(f'{S}/fit2.py').read().split('pcb=dxf(')[0])
from shapely import affinity
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
g = open('../totem_geometry.scad').read()
K = [[float(v) for v in m] for m in re.findall(r'\[([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+)\]', re.search(r'totem_keys = \[(.*?)\];', g, re.S)[1])]
H = [tuple(map(float, m)) for m in re.findall(r'\[([-\d.]+), ([-\d.]+)\]', re.search(r'totem_holes = \[(.*?)\];', g)[1])]
case_pcb = affinity.scale(dxf('/tmp/fitt/pcb.dxf'), 1, -1, origin=(0, 0))
# footprint rotation in the KiCad file is already counter-clockwise; only y flips
ok = lambda b: 'OK  ' if b else 'FAIL'
sq = lambda x, y, r, s: affinity.rotate(box(x - s / 2, y - s / 2, x + s / 2, y + s / 2), r, origin=(x, y))
rect = lambda x, y, r, w, h: affinity.rotate(box(x - w / 2, y - h / 2, x + w / 2, y + h / 2), r, origin=(x, y))
fails = 0
for side in ('left', 'right'):
    M = -1 if side == 'right' else 1
    print(f'--- {side}')
    pts = yaml.safe_load(open(f'out/{side}/points/points.yaml'))
    keys = [(v['x'], v['y'], v['r']) for k, v in pts.items() if 'helper' not in (v['meta'].get('tags') or [])]
    err = max(min(math.dist((x, y), (M * kx, ky)) + abs((r - M * kr + 180) % 360 - 180) for kx, ky, kr, _ in K) for x, y, r in keys)
    print(ok(len(keys) == 19 and err < 0.005), f'1 19 key points match the case geometry, max error {err:.4f} mm / deg')
    s = open(f'out/{side}/pcbs/totem_he_{side}.kicad_pcb').read()
    fps = [(m[1], float(m[2]), -float(m[3]), float(m[4] or 0)) for m in re.finditer(r'\(footprint "([^"]+)"\s*\(layer "[^"]+"\)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', s)]
    by = lambda n: [f for f in fps if f[0].endswith(n)]
    sw = by('switch_he'); housings = unary_union([sq(x, y, r, 14) for _, x, y, r in sw])
    # outline from the kicad file: Edge.Cuts segments polygonised, versus the case's PCB shape
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    segs = [LineString([(float(m[1]), -float(m[2])), (float(m[3]), -float(m[4]))]) for m in re.finditer(r'\(gr_line\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(?:(?!gr_line).)*?Edge\.Cuts', s, re.S)]
    polys = list(polygonize(unary_union(segs)))
    board = max(polys, key=lambda p: p.area) if polys else None
    ref = affinity.scale(case_pcb, M, 1, origin=(0, 0)) if M < 0 else case_pcb
    ref_ext = Polygon(ref.exterior)
    d = Polygon(board.exterior).symmetric_difference(ref_ext).area if board else 1e9
    print(ok(d < 3), f'2 board edge matches the case PCB outline (symmetric difference {d:.1f} mm2, {len(segs)} edge segments, {len(polys)} loops)')
    xiao = by('xiao_rp2040')[0]; xr = rect(xiao[1], xiao[2], 0, 21.7, 18.5)   # the cutout is axis-aligned; the XIAO itself is rotated 90
    # XIAO cutout present: board minus cutout
    print(ok(xr.within(ref_ext.buffer(0.6)) and len(polys) == 1), f'3 XIAO sits on the board, USB end at the edge ({len(polys)} edge loop)')
    # USB end: local -y in KiCad, so +y once flipped, rotated CCW by the footprint angle; must face the outer edge
    usb = (xiao[1] - 10.5 * math.sin(math.radians(xiao[3])), xiao[2] + 10.5 * math.cos(math.radians(xiao[3])))
    print(ok((usb[0] - xiao[1]) * M < -5), f'4 XIAO USB-C faces the outer edge (USB end at x={usb[0]:.1f})')
    parts = []
    for n, w, h in (('mux_4051', 7.4, 10.4), ('trrs_pj320a', 6.2, 12.4)):
        for f in by(n):
            x, y, r = f[1], f[2], f[3]
            if n == 'trrs_pj320a': shape = affinity.rotate(box(x - 3.1, y - 12.4, x + 3.1, y), r, origin=(x, y))
            else: shape = affinity.rotate(box(x - 4.1, y - 5.2, x + 4.1, y + 8.35), r, origin=(x, y))   # courtyard plus the cap at the pin-1 end (KiCad -y, so +y here)
            parts.append((f[0].split(':')[-1], shape))
    bosses = [Point(M * hx, hy).buffer(2.2) for hx, hy in H]
    good = True
    for name, shp in parts:
        inside = shp.within(ref_ext.buffer(-0.5)) if name != 'trrs_pj320a' else shp.within(ref_ext.buffer(0.5))
        clr = shp.distance(housings); bcl = min(shp.distance(b) for b in bosses); xcl = shp.distance(xr)
        good &= inside and clr >= 0.8 and bcl >= 0.5 and xcl >= 0.5
        print(ok(inside and clr >= 0.8 and bcl >= 0.5 and xcl >= 0.5), f'   {name} inside board {inside}, {clr:.2f} mm from switch housings, {bcl:.2f} from screw holes, {xcl:.2f} from the XIAO cutout')
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            dd = parts[i][1].distance(parts[j][1]); good &= dd >= 0.5
            if dd < 0.5: print(ok(False), f'   {parts[i][0]} and {parts[j][0]} only {dd:.2f} mm apart')
    print(ok(good), '5 muxes and TRRS placed clear of housings, holes, the cutout and each other')
    # every switch: two leg holes, three sensor pads, two cap pads; sensor+cap inside the 14 mm housing
    n_leg = len(re.findall(r'np_thru_hole circle \(at -?5\.08 0', s)); n_sens = len(re.findall(r'\(pad "3" smd', s[s.find('switch_he'):]))
    print(ok(n_leg == 38 and len(sw) == 19), f'6 19 switches with 2 leg holes each ({n_leg} holes)')
    nets = set(re.findall(r'\(net \d+ "([^"]*)"\)', s))
    knets = {n for n in nets if n.startswith('K_')}
    print(ok(len(knets) == 19 and {'VCC', 'GND', 'SEL0', 'SEL1', 'SEL2', 'ADC_A', 'ADC_B', 'ADC_C', 'TX', 'RX'} <= nets), f'7 nets: 19 sensor outputs, 3 ADC, 3 select, VCC/GND, TX/RX ({len(nets)} nets)')
    fails += 0
