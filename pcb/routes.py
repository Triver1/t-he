"""The routing plan: every trace on the board, written out as waypoints, applied with route.py (./r batch).

Each section is one deliberate pattern; points are board millimetres unless a helper takes them in a part's own
frame (local), so the same pattern repeats at every switch and survives regenerating the board. Corners are cut at
45 degrees. Layers: the underside (B) carries the signals, the top (F) carries 3.3 V and ground.
Usage: python3 routes.py [SECTION ...]   (writes out/routes.txt; then ./r batch out/routes.txt)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = {p['ref']: p for p in json.load(open(os.path.join(HERE, 'out', 'pads.json')))}
SIGNAL, POWER, RAIL = 0.25, 0.4, 0.5
cmds = []


def local(ref, lx, ly):
    p = PARTS[ref]
    a = math.radians(p['rot'])
    return (p['x'] + lx * math.cos(a) + ly * math.sin(a), p['y'] - lx * math.sin(a) + ly * math.cos(a))


def pad(ref, num, layer='B'):
    hits = [q for q in PARTS[ref]['pads'] if q['num'] == num and q[layer]]
    smd = [q for q in hits if not q['drill']]
    q = (smd or hits)[0]
    return (q['x'], q['y'])


def net(ref, num):
    return next(q['net'] for q in PARTS[ref]['pads'] if q['num'] == num and q['net'])


def chamfer(pts, c=1.0):
    """cuts each corner between two straight runs back by up to c mm, for 45 degree bends"""
    out = [pts[0]]
    for a, b, d in zip(pts, pts[1:], pts[2:]):
        la, lb = math.dist(a, b), math.dist(b, d)
        if la < 1e-6 or lb < 1e-6:
            continue
        u = ((b[0] - a[0]) / la, (b[1] - a[1]) / la)
        v = ((d[0] - b[0]) / lb, (d[1] - b[1]) / lb)
        if abs(u[0] * v[0] + u[1] * v[1]) > 0.3:     # only right angles are cut; 45 degree bends stay as they are
            out.append(b)
            continue
        k = min(c, la / 2, lb / 2)
        out += [(b[0] - u[0] * k, b[1] - u[1] * k), (b[0] + v[0] * k, b[1] + v[1] * k)]
    return out + [pts[-1]]


def track(net_name, layer, width, pts, c=1.0):
    pts = chamfer(pts, c) if c else pts
    cmds.append(f'track {net_name} {layer} {width} ' + ' '.join(f'{x:.4f},{y:.4f}' for x, y in pts))


def switches():
    return sorted((r for r, p in PARTS.items() if p['kind'] == 'switch_he'), key=lambda r: int(r[1:]))


def sensor_stubs():
    """the same short stubs at every sensor, on the underside: power to its two vias, the output out between the
    capacitor pads (it leaves at local (-0.75, 4.8))"""
    for s in switches():
        L = lambda *pts: [local(s, x, y) for x, y in pts]
        vcc, gnd, out = net(s, '1'), net(s, '3'), net(s, '2')
        track(vcc, 'B', POWER, L((1.05, -0.95), (2.0, -0.95), (2.5, -0.45), (2.5, 2.0)), 0)
        track(vcc, 'B', POWER, L((0.2875, 3.6), (1.2, 3.6), (2.5, 2.3), (2.5, 2.0)), 0)
        track(gnd, 'B', POWER, L((-1.05, 0), (-1.7, 0), (-2.2, 0.5), (-2.2, 1.9)), 0)
        track(gnd, 'B', POWER, L((-1.7875, 3.6), (-2.2, 3.19), (-2.2, 1.9)), 0)
        track(out, 'B', SIGNAL, L((1.05, 0.95), (-0.05, 0.95), (-0.75, 1.65), (-0.75, 4.8)), 0)


def via(ref, num):
    q = next(q for q in PARTS[ref]['pads'] if q['num'] == num and q['drill'] and q['drill'] < 0.5)
    return (q['x'], q['y'])


def add_via(net_name, pt):
    cmds.append(f'via {net_name} {pt[0]:.4f},{pt[1]:.4f}')


# each mux's power vias, placed by hand next to the nearest 3.3 V and ground teeth on top: (VCC, GND by the
# capacitor, GND by the pin 6-8 strip)
MUX_VIAS = {'IC1': ((29.0, 50.04), (29.0, 47.96), (41.17, 43.9)),
            'IC2': ((70.8, 43.0), (66.1, 36.96), None),
            'IC3': ((109.0, 69.46), (109.0, 71.54), (96.83, 75.6)),
            'IC101': ((218.74, 51.4), (217.0, 47.96), None),
            'IC102': ((183.0, 40.04), (186.08, 36.4), None),
            'IC103': ((165.77, 79.0), (163.7, 79.9), (162.03, 64.2))}
# where a mux's 3.3 V via takes its feed: the capacitor, or pin 16 directly
VIA_FROM_16 = {'IC2'}


def mux_local():
    """underside, each mux: pin 16 into its capacitor, the capacitor and the pin 6-8 strip to their vias"""
    for ic, (v, g, gs) in MUX_VIAS.items():
        vcc, gnd = net(ic, '16'), net(ic, 'C2')
        L = lambda *pts: [local(ic, x, y) for x, y in pts]
        track(vcc, 'B', POWER, L((2.7, 4.445), (2.7, 5.9), (1.6, 7.0), (1.0375, 7.35)), 0)
        track(vcc, 'B', POWER, [pad(ic, '16') if ic in VIA_FROM_16 else pad(ic, 'C1'), v])
        if g:
            track(gnd, 'B', POWER, [pad(ic, 'C2'), g])
        if gs:
            track(gnd, 'B', POWER, [local(ic, -2.7, -3.175), gs])
        for pt, n in ((v, vcc), (g, gnd), (gs, gnd)):
            if pt:
                add_via(n, pt)
    # IC2 joins its pin 6-8 strip to its capacitor's ground under the chip, between the pin rows; so do IC101 and
    # IC102 on the right
    track('L/GND', 'B', POWER, [local('IC2', -1.5, -3.175), (77.0, 37.8), (68.9, 37.8), pad('IC2', 'C2')])
    for ic in ('IC101', 'IC102'):
        track('R/GND', 'B', POWER, [pad(ic, 'C2'), local(ic, -1.0375, 6.2), local(ic, 0, 5.16), local(ic, 0, -2.2),
                                    local(ic, -0.975, -3.175), local(ic, -2.7, -3.175)], 0)
    # IC1 joins its two ground points under the chip, between the pin rows: the pinky column's ground (from the
    # XIAO) meets the rest of the ground there
    track('L/GND', 'B', POWER, [pad('IC1', 'C2'), local('IC1', -1.0375, 6.2), local('IC1', 0, 5.16), local('IC1', 0, -2.2),
                                local('IC1', -0.975, -3.175), local('IC1', -2.7, -3.175)], 0)


def power_left():
    """top layer, left half: a 3.3 V rail along the top edge with a tooth down each column, ground teeth up each
    column joined by a rail along the bottom edge, so the two combs interleave without crossing"""
    V, G = 'L/VCC', 'L/GND'
    xiao_3v3, xiao_gnd = pad('MCU1', '12', 'F'), pad('MCU1', '13', 'F')
    tip_l, tip_r = (122.17, 15.46), (126.77, 15.46)
    # 3.3 V rail: XIAO 3V3 along the top edge to the TRRS tip, joining both tip pads
    track(V, 'F', RAIL, [xiao_3v3, (xiao_3v3[0], 5.6), (120.0, 5.6), (120.0, tip_l[1]), tip_l, tip_r])
    # pinky: down the corridor right of the XIAO, then the column; past the mux's ground via on its right
    s1, s6, s11 = via('S1', '1'), via('S6', '1'), via('S11', '1')
    track(V, 'F', RAIL, [(34.0, 5.6), (34.0, 26.0), (s1[0], 26.0 + 34.0 - s1[0]), s1])
    track(V, 'F', RAIL, [s1, (s1[0], 42.0), (30.0, 44.05), (30.0, 55.5), (s6[0], 55.5 + s6[0] - 30.0), s6, s11], 0.8)
    track(V, 'F', RAIL, [MUX_VIAS['IC1'][0], (30.0, MUX_VIAS['IC1'][0][1])], 0)
    # outer key: from the bottom of the pinky column, under the pinky bottom key
    outer = via('S16', '1')
    track(V, 'F', RAIL, [s11, (s11[0], 81.5), (outer[0], 81.5), outer])
    # ring, middle, index, inner: straight teeth from the rail through each column
    for col in (('S2', 'S7', 'S12'), ('S3', 'S8', 'S13'), ('S4', 'S9', 'S14'), ('S5', 'S10', 'S15')):
        pts = [via(s, '1') for s in col]
        track(V, 'F', RAIL, [(pts[0][0], 5.6)] + pts, 0)
    # thumb 1 from the middle column, over thumb 1's ground via
    m3, t1 = via('S13', '1'), via('S17', '1')
    track(V, 'F', RAIL, [m3, (m3[0], 72.0), (74.8, 76.0), (t1[0], 76.0), t1])
    # thumb 2 from the index column, under thumb 2's ground via
    i3, t2 = via('S14', '1'), via('S18', '1')
    track(V, 'F', RAIL, [i3, (i3[0], 86.0), (t2[0], 86.0), t2])
    # inner column on to IC3's 3.3 V via and thumb 3, passing right of IC3's ground via
    n3, ic3v, t3 = via('S15', '1'), MUX_VIAS['IC3'][0], via('S19', '1')
    track(V, 'F', RAIL, [n3, ic3v, (110.5, ic3v[1] + 1.5), (110.5, 80.0), (t3[0], 80.0 + t3[0] - 110.5), t3])

    # ground: the pinky column hangs off the XIAO's GND pin, down the left edge
    g1, g6, g11 = via('S1', '3'), via('S6', '3'), via('S11', '3')
    track(G, 'F', RAIL, [xiao_gnd, (xiao_gnd[0], 6.3), (12.0, 6.3), (12.0, 29.0), (g1[0], 29.0), g1, g6, g11])
    ic1g = MUX_VIAS['IC1'][1]
    track(G, 'F', RAIL, [ic1g, (g1[0] + (g6[0] - g1[0]) * (ic1g[1] - g1[1]) / (g6[1] - g1[1]), ic1g[1])], 0)
    # bottom rail, following the board edge, and the outer key onto it
    # 1.25 mm inside the bottom edge: flat to x 87.5, then along the thumbs' 15 and 30 degree edges
    rail_y = lambda x: 87.4 if x <= 87.8 else 87.4 + (x - 87.8) * 0.2685 if x <= 106.06 else 92.3 + (x - 106.06) * 0.5775
    rail = [(11.5, 87.4), (87.8, 87.4), (106.06, rail_y(106.06)), (116.02, rail_y(116.02))]
    track(G, 'F', RAIL, rail, 0)
    og = via('S16', '3')
    track(G, 'F', RAIL, [og, (11.5, og[1] + 11.5 - og[0]), (11.5, 87.4)], 0)
    # ring: tooth down to the rail, with IC1's pin-7 ground via joining it
    r = [via(s, '3') for s in ('S2', 'S7', 'S12')]
    track(G, 'F', RAIL, r + [(r[2][0], 87.4)], 0)
    ic1g7 = MUX_VIAS['IC1'][2]
    track(G, 'F', RAIL, [ic1g7, (r[1][0] + (r[2][0] - r[1][0]) * (ic1g7[1] - r[1][1]) / (r[2][1] - r[1][1]), ic1g7[1])], 0)
    # middle and index teeth down to the rail; IC2's ground vias join the index tooth
    m = [via(s, '3') for s in ('S3', 'S8', 'S13')]
    track(G, 'F', RAIL, m + [(m[2][0], 87.4)], 0)
    i = [via(s, '3') for s in ('S4', 'S9', 'S14')]
    track(G, 'F', RAIL, i + [(i[2][0], 87.4)], 0)
    # thumb 1 straight down to the rail; thumb 2 up to IC3's pin-7 ground via, then over to the inner tooth
    tg1 = via('S17', '3')
    track(G, 'F', RAIL, [tg1, (tg1[0], 87.4)], 0)
    n = [via(s, '3') for s in ('S5', 'S10', 'S15')]
    ic3g7, tg2 = MUX_VIAS['IC3'][2], via('S18', '3')
    track(G, 'F', RAIL, [tg2, ic3g7, (n[0][0], ic3g7[1])], 0)
    # past thumb 2's right peg hole on the right
    track(G, 'F', RAIL, n + [(n[0][0], 79.5), (106.5, 81.8), (106.5, rail_y(106.5))], 0)
    ic3g = MUX_VIAS['IC3'][1]
    track(G, 'F', RAIL, [ic3g, (n[0][0], ic3g[1])], 0)
    # thumb 3 down to the end of the rail
    tg3 = via('S19', '3')
    track(G, 'F', RAIL, [tg3, (tg3[0], rail_y(tg3[0]))], 0)


def exit_(ref):
    """where a sensor's output stub ends, between its capacitor pads"""
    return local(ref, -0.75, 4.8)


def signals_left():
    """underside, left half: the sensor fans into their muxes, and the bus from the XIAO along the top edge"""
    S = SIGNAL
    x = lambda ref, num: pad(ref, num)[0]
    # bus: leaves the XIAO between its pin rows (top-row pins drop in, bottom-row pins rise), east under the mounting
    # hole, up through the notch above the middle-top key and down on the far side. From the top: DATA, SEL0, SEL1,
    # SEL2, ADC_C, ADC_B
    west = {'L/DATA': 11.0, 'L/SEL0': 11.8, 'L/SEL1': 12.6, 'L/SEL2': 13.4, 'L/ADC_C': 14.2, 'L/ADC_B': 15.0}
    notch = {n: y - 7.9 for n, y in west.items()}
    east = {'L/DATA': 5.2, 'L/SEL0': 6.5, 'L/SEL1': 7.3, 'L/SEL2': 8.1, 'L/ADC_C': 8.9}
    pin = {'L/DATA': '8', 'L/SEL0': '9', 'L/SEL1': '10', 'L/SEL2': '11', 'L/ADC_C': '2', 'L/ADC_B': '3'}
    order = list(west)
    for i, n in enumerate(order):
        p = pad('MCU1', pin[n])
        climb = 53.0 + 0.331 * i                 # 45 degree climbs, 0.8 mm apart square to the lines
        pts = [p, (p[0], west[n]), (climb, west[n]), (climb + 7.9, notch[n])]
        if n == 'L/ADC_B':
            z = pad('IC2', '3')                  # the lowest line drops first, east of the middle column's pegs
            pts += [(74.75, notch[n]), (74.75, 32.0), (z[0], 33.35), z]
        else:
            c = 69.25 + 1.131 * (4 - i)          # descents along x - y = c, 0.8 mm apart, the lower line first
            pts += [(c + notch[n], notch[n]), (c + east[n], east[n])]
            if n == 'L/DATA':
                tip = pad('TRRS1', '3')
                pts += [(119.6, east[n]), (119.6, tip[1]), tip]
            else:                                # down the corridor between the index and inner columns into IC3
                col = {'L/ADC_C': 94.3, 'L/SEL2': x('IC3', '9'), 'L/SEL1': x('IC3', '10'), 'L/SEL0': x('IC3', '11')}[n]
                pts += [(col, east[n])]
                if n == 'L/ADC_C':               # past the west end, then under the chip between its pin rows
                    z = pad('IC3', '3')
                    pts += [(col, 70.5), (z[0], 70.5), z]
                else:
                    pts += [pad('IC3', {'L/SEL2': '9', 'L/SEL1': '10', 'L/SEL0': '11'}[n])]
        track(n, 'B', S, pts, 0.6)
    track('L/DATA', 'F', S, [pad('TRRS1', '3', 'F'), (126.77, pad('TRRS1', '3', 'F')[1])], 0)

    # select lines to IC1 and IC2: a via on each bus line, the top layer to a via beside the pin, the pin on the underside
    for n, (bx, ic1_y) in {'L/SEL0': (37.1, 54.2), 'L/SEL1': (36.3, 55.0), 'L/SEL2': (35.5, 55.8)}.items():
        num = {'L/SEL0': '11', 'L/SEL1': '10', 'L/SEL2': '9'}[n]
        a, t = (bx, west[n]), (x('IC1', num), ic1_y)
        add_via(n, a); add_via(n, t)
        track(n, 'F', S, [a, (bx, ic1_y), t], 0)
        track(n, 'B', S, [t, pad('IC1', num)], 0)
    # to IC2: down beside the index column's pegs, then in under them (S0 west of the pegs, S1 and S2 east)
    for n, top in {'L/SEL0': [(80.6, 6.5), (80.6, 39.6), (77.2, 43.0)],
                   'L/SEL1': [(83.6, 7.3), (83.6, 40.4), (81.07, 40.4), (78.47, 43.0)],
                   'L/SEL2': [(84.4, 8.1), (84.4, 41.2), (81.55, 41.2), (79.75, 43.0)]}.items():
        num = {'L/SEL0': '11', 'L/SEL1': '10', 'L/SEL2': '9'}[n]
        add_via(n, top[0]); add_via(n, top[-1])
        track(n, 'F', S, top, 0)
        track(n, 'B', S, [top[-1], pad('IC2', num)], 0)
    z = pad('IC1', '3')                          # IC1's common: down from D0 and over the pinky top key
    track('L/ADC_A', 'B', S, [pad('MCU1', '1'), (14.19, 26.5), (21.0, 33.3), (z[0] - 0.8, 33.3), (z[0], 34.1), z], 0.6)

    # IC1's fan: pinky top and the ring keys from above, the rest from below, hooking round a sensor where needed
    p = lambda n: pad('IC1', n)
    e = {k: exit_(r) for k, r in (('pt', 'S1'), ('ph', 'S6'), ('pb', 'S11'), ('o', 'S16'), ('rt', 'S2'), ('rh', 'S7'), ('rb', 'S12'))}
    track('L/K_PINKY_TOP', 'B', S, [e['pt'], (e['pt'][0], 44.3), (p('2')[0] - 0.8, 44.3), p('2')], 0.6)
    track('L/K_RING_TOP', 'B', S, [e['rt'], (e['rt'][0], 26.8), (p('4')[0], 26.8 + e['rt'][0] - p('4')[0]), p('4')], 0.6)
    track('L/K_RING_HOME', 'B', S, [e['rh'], (e['rh'][0], 45.9), (44.8, 45.9), (44.8, 43.0), (p('5')[0], 43.0), p('5')], 0.6)
    track('L/K_PINKY_HOME', 'B', S, [p('14'), (p('14')[0], 54.5), (25.07, 54.5), (25.07, 63.5), (e['ph'][0], 63.5), e['ph']], 0.6)
    track('L/K_OUTER', 'B', S, [p('15'), (p('15')[0], 53.5), (20.0, 53.5), (20.0, e['o'][1]), e['o']], 0.6)
    track('L/K_PINKY_BOTTOM', 'B', S, [p('13'), (p('13')[0], 57.0), (37.9, 57.5), (37.9, 80.0), (36.3, 81.6), (e['pb'][0], 81.6), e['pb']], 0.6)
    track('L/K_RING_BOTTOM', 'B', S, [p('12'), (p('12')[0], 56.6), (45.6, 56.6), (45.6, 65.0), (e['rb'][0], 65.0), e['rb']], 0.6)

    # IC2's fan: middle keys from the west, index keys from the east
    p = lambda n: pad('IC2', n)
    e = {k: exit_(r) for k, r in (('mt', 'S3'), ('mh', 'S8'), ('mb', 'S13'), ('it', 'S4'), ('ih', 'S9'), ('ib', 'S14'))}
    track('L/K_MIDDLE_TOP', 'B', S, [e['mt'], (e['mt'][0], 15.3), (71.8, 15.3 + 71.8 - e['mt'][0]), (71.8, 33.0), (p('2')[0], 33.33), p('2')], 0.6)
    track('L/K_MIDDLE_HOME', 'B', S, [e['mh'], (p('1')[0] - 0.5, e['mh'][1]), p('1')], 0.6)
    track('L/K_MIDDLE_BOTTOM', 'B', S, [p('14'), (p('14')[0], 44.0), (71.8, 44.0), (71.8, 53.5), (e['mb'][0], 53.5), e['mb']], 0.6)
    track('L/K_INDEX_TOP', 'B', S, [e['it'], (e['it'][0], 32.6), (p('5')[0] + 0.5, 32.6), p('5')], 0.6)
    track('L/K_INDEX_HOME', 'B', S, [p('12'), (p('12')[0], 44.4), (e['ih'][0], 44.4), e['ih']], 0.6)
    track('L/K_INDEX_BOTTOM', 'B', S, [p('13'), (p('13')[0], 45.2), (83.7, 45.2), (83.7, 63.0), (e['ib'][0], 63.0), e['ib']], 0.6)

    # IC3's fan: inner keys down the corridor beside the bus, thumbs from below
    p = lambda n: pad('IC3', n)
    e = {k: exit_(r) for k, r in (('nt', 'S5'), ('nh', 'S10'), ('nb', 'S15'), ('t1', 'S17'), ('t2', 'S18'), ('t3', 'S19'))}
    track('L/K_INNER_TOP', 'B', S, [e['nt'], (e['nt'][0], 27.8), (99.2, 27.8), (99.2, 64.5), (p('12')[0], 65.0), p('12')], 0.6)
    track('L/K_INNER_HOME', 'B', S, [e['nh'], (e['nh'][0], 46.8), (100.0, 46.8), (100.0, 64.5), (p('13')[0], 65.1), p('13')], 0.6)
    track('L/K_INNER_BOTTOM', 'B', S, [e['nb'], (e['nb'][0], 65.9), (p('15')[0] + 0.5, 65.9), p('15')], 0.6)
    track('L/K_THUMB1', 'B', S, [e['t1'], (e['t1'][0], 84.3), (81.5, 84.3), (81.5, 77.4), (p('4')[0], 77.4), p('4')], 0.6)
    track('L/K_THUMB2', 'B', S, [e['t2'], (e['t2'][0], 86.6), (102.6, 86.6), (102.6, 75.8), (p('2')[0], 75.23), p('2')], 0.6)
    t3 = local('S19', -0.75, 5.8)               # this key is turned 30 degrees: carry on along the stub first
    track('L/K_THUMB3', 'B', S, [e['t3'], t3, (t3[0] - (t3[1] - 92.0), 92.0), (105.4, 92.0), (105.4, 75.4), (p('1')[0], 74.44), p('1')], 0.6)

    # the link's ground: down the right edge underneath, then on top to thumb 3's ground
    g = (128.0, 84.0)
    track('L/GND', 'F', S, [pad('TRRS1', '2', 'F'), (126.77, pad('TRRS1', '2', 'F')[1])], 0)
    track('L/GND', 'B', POWER, [(126.77, pad('TRRS1', '2')[1]), (128.3, 9.44), (128.3, 83.7), g], 0)
    add_via('L/GND', g)
    track('L/GND', 'F', RAIL, [g, (127.6, 84.0), (127.6, 87.6), (126.0, 89.2), (126.0, 93.6), (121.0, 96.5), (via('S19', '3')[0], 96.5)], 0)


def power_right():
    """top layer, right half: the same interleaved combs as the left. The XIAO's 3V3 reaches the top rail through a
    thin trace between its pin rows; its GND reaches the pinky column through a short underside jumper; the outer
    key's 3.3 V comes down the right edge, thumb 3's down the left edge from the TRRS tip"""
    V, G = 'R/VCC', 'R/GND'
    x3v3 = pad('MCU101', '12', 'F')
    tip_l, tip_r = pad('TRRS101', '4', 'F'), (142.56, 15.46)
    tip_l = (137.96, 15.46)
    # top rail: from the TRRS tip along the top edge, up into the notch above the middle-top key (the bus vias sit
    # under the rail's usual line there), to the XIAO
    track(V, 'F', RAIL, [tip_l, tip_r, (144.73, 15.46), (144.73, 5.6), (185.6, 5.6), (190.2, 1.0), (202.5, 1.0),
                         (207.1, 5.6), (244.19, 5.6)], 0)
    track(V, 'F', 0.3, [(244.19, 5.6), (244.19, 20.8), x3v3], 0)
    # teeth: inner, index, middle, ring
    for col in (('S105', 'S110', 'S115'), ('S104', 'S109', 'S114'), ('S103', 'S108', 'S113'), ('S102', 'S107', 'S112')):
        pts = [via(s, '1') for s in col]
        top = 1.0 if 190.2 <= pts[0][0] <= 202.5 else 5.6
        track(V, 'F', RAIL, [(pts[0][0], top)] + pts, 0)
    # pinky: straight down from the XIAO's 3V3
    p1, p6, p11 = via('S101', '1'), via('S106', '1'), via('S111', '1')
    track(V, 'F', RAIL, [x3v3, (x3v3[0], 26.0), (p1[0], 26.0 + x3v3[0] - p1[0]), p1, p6, p11], 0)
    # outer key: down the right edge from the XIAO
    o = via('S116', '1')
    track(V, 'F', RAIL, [(x3v3[0], 26.0), (253.3, 26.0), (253.3, 62.5), (o[0], 62.5), o], 0)
    # thumb 1 from the index column, over thumb 1's ground via
    i3, t1 = via('S114', '1'), via('S117', '1')
    track(V, 'F', RAIL, [i3, (i3[0], 76.0), (t1[0], 76.0), t1])
    # thumb 2 from the inner column, over thumb 2's ground via; IC3's 3.3 V via sits on it
    n3, t2 = via('S115', '1'), via('S118', '1')
    track(V, 'F', RAIL, [n3, (n3[0], 79.0), (t2[0], 79.0), t2])
    # thumb 3 from the TRRS tip, down the left edge
    t3 = via('S119', '1')
    track(V, 'F', POWER, [tip_l, (136.5, tip_l[1] + 1.46), (136.5, 86.0), (143.86, 86.0), (t3[0] - 1.01, t3[1]), t3], 0)
    # mux 3.3 V vias onto their teeth
    track(V, 'F', RAIL, [MUX_VIAS['IC102'][0], (via('S109', '1')[0], MUX_VIAS['IC102'][0][1])], 0)

    # ground: teeth down to a rail 1.25 mm inside the bottom edge
    rail_y = lambda x: 87.4 if x >= 177.0 else 87.4 + (177.0 - x) * 0.2685 if x >= 158.67 else 92.3 + (158.67 - x) * 0.5775
    track(G, 'F', RAIL, [(253.23, 87.4), (177.0, 87.4), (158.67, rail_y(158.67)), (144.9, rail_y(144.9))], 0)
    for col in (('S105', 'S110', 'S115'), ('S104', 'S109', 'S114'), ('S103', 'S108', 'S113'), ('S102', 'S107', 'S112'),
                ('S101', 'S106', 'S111')):
        pts = [via(s, '3') for s in col]
        track(G, 'F', RAIL, pts + [(pts[2][0], rail_y(pts[2][0]))], 0)
    og = via('S116', '3')
    track(G, 'F', RAIL, [og, (253.23, og[1] + 253.23 - og[0]), (253.23, 87.4)], 0)
    for t in ('S117', 'S118', 'S119'):
        g = via(t, '3')
        track(G, 'F', RAIL, [g, (g[0], rail_y(g[0]))], 0)
    # the XIAO's GND: a short jumper underneath, then down to the top of the pinky column
    xg = pad('MCU101', '13')
    j = (239.0, 28.6)
    track(G, 'B', POWER, [xg, (xg[0], j[1]), j], 0)
    add_via(G, j)
    track(G, 'F', RAIL, [j, (j[0], 30.6), (via('S101', '3')[0], 32.5), via('S101', '3')], 0)
    # mux ground vias onto their teeth
    ic1g = MUX_VIAS['IC101'][1]
    track(G, 'F', RAIL, [ic1g, (214.25, ic1g[1])], 0)
    ic2g = MUX_VIAS['IC102'][1]
    track(G, 'F', RAIL, [ic2g, (via('S103', '3')[0], ic2g[1])], 0)
    ic3g = MUX_VIAS['IC103'][2]
    track(G, 'F', RAIL, [ic3g, (via('S104', '3')[0], ic3g[1])], 0)
    ic3c = MUX_VIAS['IC103'][1]
    track(G, 'F', RAIL, [ic3c, (ic3c[0], 81.9), via('S118', '3')], 0)
    # the link: GND and DATA pads of the jack joined on top; the jack's ground reaches thumb 3's via the left edge
    track(G, 'F', POWER, [(137.96, 7.91), (142.56, 7.91)], 0)
    track('R/DATA', 'F', SIGNAL, [(137.96, 10.91), (142.56, 10.91)], 0)
    gv = (138.5, 89.5)
    track(G, 'B', POWER, [(137.96, 7.91), (136.4, 9.47), (136.4, 88.0), gv], 0)
    add_via(G, gv)
    track(G, 'F', RAIL, [gv, (143.5, 89.5), (144.9, 90.9), via('S119', '3')], 0)


def signals_right():
    """underside, right half: the same scheme as the left, mirrored, with the XIAO's pin rows the other way round"""
    S = SIGNAL
    x = lambda ref, num: pad(ref, num)[0]
    # bus: from the top: ADC_B, ADC_C, SEL2, SEL1, SEL0, DATA. West past the XIAO, up through the notch above the
    # middle-top key and down on its west side
    west = {'R/ADC_B': 11.0, 'R/ADC_C': 11.8, 'R/SEL2': 12.6, 'R/SEL1': 13.4, 'R/SEL0': 14.2, 'R/DATA': 15.0}
    notch = {n: y - 7.9 for n, y in west.items()}
    after = {'R/ADC_C': 5.2, 'R/SEL2': 6.0, 'R/SEL1': 6.8, 'R/SEL0': 7.6, 'R/DATA': 8.4}
    k = {'R/ADC_C': 190.96, 'R/SEL2': 192.09, 'R/SEL1': 193.22, 'R/SEL0': 194.35, 'R/DATA': 195.48}   # descents along x + y = k
    pin = {'R/ADC_B': '3', 'R/ADC_C': '2', 'R/SEL2': '11', 'R/SEL1': '10', 'R/SEL0': '9', 'R/DATA': '8'}
    drop = {'R/SEL0': 171.0, 'R/SEL1': 170.2, 'R/SEL2': 169.4, 'R/ADC_C': 168.6}     # down the corridor into IC3
    for i, n in enumerate(west):
        p = pad('MCU101', pin[n])
        climb = 211.73 - 0.331 * i
        pts = [p, (p[0], west[n]), (climb, west[n]), (climb - 7.9, notch[n])]
        if n == 'R/ADC_B':                       # ends on a via; the top layer takes it to IC2
            pts += [(189.9, notch[n])]
        else:
            pts += [(k[n] - notch[n], notch[n]), (k[n] - after[n], after[n])]
            if n == 'R/DATA':                    # hops over IC3's drop on the top layer
                pts += [(176.5, after[n])]
            else:
                pts += [(drop[n], after[n])]
                if n == 'R/ADC_C':               # over IC3's north end, then under the chip between its pin columns
                    z = pad('IC103', '3')
                    pts += [(drop[n], 64.3), (164.73, 64.3), (164.73, z[1]), z]
                else:
                    t = pad('IC103', {'R/SEL2': '9', 'R/SEL1': '10', 'R/SEL0': '11'}[n])
                    pts += [(drop[n], t[1]), t]
        track(n, 'B', S, pts, 0.6)
    # ADC_B: a via at the end of its bus line, down on the top layer past the middle column's pegs to IC2
    a, b = (189.9, notch['R/ADC_B']), (x('IC102', '3'), 33.8)
    add_via('R/ADC_B', a); add_via('R/ADC_B', b)
    track('R/ADC_B', 'F', S, [a, (189.9, 29.9), (b[0], 31.53), b], 0)
    track('R/ADC_B', 'B', S, [b, pad('IC102', '3')], 0)
    # DATA: over the corridor on top, then along y 10.91 under the mounting hole to the jack
    a, b = (176.5, after['R/DATA']), (162.0, 10.91)
    add_via('R/DATA', a); add_via('R/DATA', b)
    track('R/DATA', 'F', S, [a, (174.0, 10.91), b], 0)
    track('R/DATA', 'B', S, [b, (142.56, 10.91)], 0)
    # select lines to IC2 (straight down between the middle column's teeth) and IC1 (straight down from beside
    # the XIAO): a via on the bus line, the top layer, a via under the pin
    for n, num in (('R/SEL0', '11'), ('R/SEL1', '10'), ('R/SEL2', '9')):
        for ic, a, ty in (('IC102', None, 44.0), ('IC101', None, 54.0)):
            px = x(ic, num)
            ay = notch[n] if ic == 'IC102' else west[n]
            a, t = (px, ay), (px, ty)
            add_via(n, a); add_via(n, t)
            track(n, 'F', S, [a, t], 0)
            track(n, 'B', S, [t, pad(ic, num)], 0)
    # IC1's common: down the right edge of the XIAO, then west
    z = pad('IC101', '3')
    track('R/ADC_A', 'B', S, [pad('MCU101', '1'), (252.6, 10.24), (252.6, 31.5), (z[0] + 0.5, 31.5), (z[0], 32.0), z], 0.6)

    # IC1's fan
    p = lambda n: pad('IC101', n)
    e = {k_: exit_(r) for k_, r in (('pt', 'S101'), ('ph', 'S106'), ('pb', 'S111'), ('o', 'S116'), ('rt', 'S102'), ('rh', 'S107'), ('rb', 'S112'))}
    track('R/K_RING_TOP', 'B', S, [e['rt'], (e['rt'][0], 26.7), (p('2')[0], 26.7 + p('2')[0] - e['rt'][0]), p('2')], 0.6)
    track('R/K_RING_HOME', 'B', S, [e['rh'], (p('1')[0] - 0.5, e['rh'][1]), p('1')], 0.6)
    track('R/K_PINKY_TOP', 'B', S, [e['pt'], (e['pt'][0], 44.0), (p('5')[0] + 0.5, 44.0), p('5')], 0.6)
    track('R/K_RING_BOTTOM', 'B', S, [p('15'), (p('15')[0], 54.4), (219.1, 58.86), (219.1, 65.0), (e['rb'][0], 65.0), e['rb']], 0.6)
    track('R/K_PINKY_HOME', 'B', S, [p('12'), (p('12')[0], 55.2), (232.5, 55.2), (233.0, 55.7), (233.0, 62.8), (e['ph'][0], 62.8), e['ph']], 0.6)
    track('R/K_OUTER', 'B', S, [p('13'), (p('13')[0], 56.0), (229.8, 56.0), (229.8, 66.0), (247.0, 66.0), (247.0, 76.6), (e['o'][0], 76.6), e['o']], 0.6)
    track('R/K_PINKY_BOTTOM', 'B', S, [p('14'), (p('14')[0], 56.8), (227.0, 56.8), (227.0, 81.6), (e['pb'][0], 81.6), e['pb']], 0.6)

    # IC2's fan
    p = lambda n: pad('IC102', n)
    e = {k_: exit_(r) for k_, r in (('mt', 'S103'), ('mh', 'S108'), ('mb', 'S113'), ('it', 'S104'), ('ih', 'S109'), ('ib', 'S114'))}
    track('R/K_INDEX_TOP', 'B', S, [e['it'], (e['it'][0], 24.7), (e['it'][0] + 33.57 - 24.7, 33.57), (p('1')[0] - 0.5, 33.57), (p('1')[0], 34.07), p('1')], 0.6)
    track('R/K_MIDDLE_TOP', 'B', S, [e['mt'], (e['mt'][0], 15.3), (193.2, 15.3 + e['mt'][0] - 193.2), (193.2, 34.3), (p('4')[0], 34.7), p('4')], 0.6)
    track('R/K_MIDDLE_HOME', 'B', S, [e['mh'], (p('5')[0], e['mh'][1] + e['mh'][0] - p('5')[0]), p('5')], 0.6)
    track('R/K_INDEX_HOME', 'B', S, [e['ih'], (e['ih'][0], 43.6), (p('15')[0] - 0.5, 43.6), (p('15')[0], 43.1), p('15')], 0.6)
    track('R/K_INDEX_BOTTOM', 'B', S, [e['ib'], (e['ib'][0], 62.8), (184.0, 62.8), (184.0, 44.4), (p('14')[0] - 0.5, 44.4), (p('14')[0], 43.9), p('14')], 0.6)
    track('R/K_MIDDLE_BOTTOM', 'B', S, [e['mb'], (e['mb'][0], 53.4), (193.2, 53.4), (193.2, 45.0), (p('12')[0], 44.13), p('12')], 0.6)

    # IC3's fan: inner keys down the west side of their column into the west pins, thumbs into the east pins
    p = lambda n: pad('IC103', n)
    e = {k_: exit_(r) for k_, r in (('nt', 'S105'), ('nh', 'S110'), ('nb', 'S115'), ('t1', 'S117'), ('t2', 'S118'), ('t3', 'S119'))}
    track('R/K_INNER_BOTTOM', 'B', S, [e['nb'], (e['nb'][0], p('5')[1] - 0.5), (e['nb'][0] + 0.5, p('5')[1]), p('5')], 0.6)
    track('R/K_INNER_HOME', 'B', S, [e['nh'], (e['nh'][0], 46.8), (155.22, 46.8), (155.22, p('4')[1]), p('4')], 0.6)
    track('R/K_INNER_TOP', 'B', S, [e['nt'], (e['nt'][0], 27.8), (154.52, 27.8), (154.52, p('2')[1]), p('2')], 0.6)
    t3 = local('S119', -0.75, 5.8)
    track('R/K_THUMB3', 'B', S, [e['t3'], t3, (152.0, t3[1] - (152.0 - t3[0])), (152.0, p('1')[1]), p('1')], 0.6)
    t2 = local('S118', -0.75, 5.8)
    track('R/K_THUMB2', 'B', S, [e['t2'], t2, (171.8, t2[1]), (171.8, p('15')[1]), p('15')], 0.6)
    track('R/K_THUMB1', 'B', S, [e['t1'], (e['t1'][0], 84.3), (183.4, 84.3), (183.4, p('14')[1]), p('14')], 0.6)


SECTIONS = {'sensor_stubs': sensor_stubs, 'mux_local': mux_local, 'power_left': power_left, 'signals_left': signals_left,
            'power_right': power_right, 'signals_right': signals_right}

if __name__ == '__main__':
    for name in sys.argv[1:] or SECTIONS:
        SECTIONS[name]()
    open(os.path.join(HERE, 'out', 'routes.txt'), 'w').write('\n'.join(cmds) + '\n')
    print(len(cmds), 'tracks written to out/routes.txt')
