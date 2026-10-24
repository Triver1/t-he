"""Checks the board's netlist against the design, for each half: the left's footprints (S1, IC1, MCU1...) on L/ nets
and the right's (S101, IC101, MCU101...) on R/ nets, with no net shared between the halves.
Usage: netcheck.py [board.kicad_pcb]  (default: totem_he.kicad_pcb beside this script)"""
import json, os, re, sys
from halves import RIGHT_REF, PREFIX
_MAP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mux_map.json')))
MUX = {h: {ic: {int(c): k for c, k in m['chan'].items()} for ic, m in muxes.items()} for h, muxes in _MAP.items()}
ADC = {h: {ic: m['adc'] for ic, m in muxes.items()} for h, muxes in _MAP.items()}
# 74HC4051 pins: 1 Y4, 2 Y6, 3 Z, 4 Y7, 5 Y5, 6 E, 7 VEE, 8 GND, 9 S2, 10 S1, 11 S0, 12 Y3, 13 Y0, 14 Y1, 15 Y2, 16 VCC
MUXPIN = {'13': 0, '14': 1, '15': 2, '12': 3, '1': 4, '5': 5, '2': 6, '4': 7}
XIAO = {'1': 'ADC_A', '2': 'ADC_C', '3': 'ADC_B', '9': 'SEL0', '10': 'SEL1', '11': 'SEL2', '8': 'DATA', '12': 'VCC', '13': 'GND'}
TRRS = {'4': 'VCC', '3': 'DATA', '2': 'GND'}   # PJ-320A: tip (ring 1 shares its pad), ring 2, sleeve
SENSOR_PINS = ['VCC', 'OUT', 'GND']            # SOT-23 49E-class and DRV5055: 1 VCC, 2 OUT, 3 GND
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'totem_he.kicad_pcb')
fails = 0
def check(cond, msg):
    global fails
    if not cond: fails += 1; print('FAIL', msg)
s = open(BOARD).read()
for side in ('left', 'right'):
    fps = {}
    for b in re.split(r'\n\s*\(footprint "', s)[1:]:
        name = b.split('"', 1)[0]; ref = re.search(r'\(property "Reference" "([^"]*)"', b)[1]
        head, num = re.match(r'(.*?)(\d+)$', ref).groups()
        if (int(num) >= RIGHT_REF) != (side == 'right'):
            continue
        pads = {}
        # a pad can be written on one line or over several, so split on the pad keyword
        for chunk in b.split('(pad "')[1:]:
            n = re.search(r'\(net \d+ "([^"]*)"\)', chunk.split('(pad "')[0])
            if n:
                check(n[1].startswith(PREFIX[side]), f'{side} {ref}: net {n[1]} belongs to the other half')
                pads[chunk.split('"', 1)[0]] = n[1][len(PREFIX[side]):]
        fps[head + str(int(num) % RIGHT_REF)] = (name, pads)
    keys = {r: p for r, (n, p) in fps.items() if n.endswith('switch_he')}
    check(len(keys) == 19, f'{side}: 19 switches ({len(keys)})')
    outs = set()
    for r, p in keys.items():
        got = [p.get('1'), p.get('2'), p.get('3')]
        want = [n if n != 'OUT' else 'K_' for n in SENSOR_PINS]
        check(all(g == w if w != 'K_' else (g or '').startswith('K_') for g, w in zip(got, want)),
              f'{side} {r}: sensor pads {"/".join(SENSOR_PINS)}, got {"/".join(str(x) for x in got)}')
        check(p.get('C1') == 'VCC' and p.get('C2') == 'GND', f'{side} {r}: cap across VCC/GND')
        outs.add(p.get(str(SENSOR_PINS.index('OUT') + 1)))
    check(len(outs) == 19, f'{side}: 19 distinct sensor nets')
    seen = set()
    for ic, chans in MUX[side].items():
        n, p = fps[ic]
        check(p.get('16') == 'VCC' and p.get('8') == 'GND' and p.get('6') == 'GND' and p.get('7') == 'GND', f'{side} {ic}: VCC/GND/E/VEE')
        check(p.get('3') == ADC[side][ic], f'{side} {ic}: Z -> {ADC[side][ic]} (got {p.get("3")})')
        check(p.get('11') == 'SEL0' and p.get('10') == 'SEL1' and p.get('9') == 'SEL2', f'{side} {ic}: S0..S2')
        check(p.get('C1') == 'VCC' and p.get('C2') == 'GND', f'{side} {ic}: cap')
        for pin, idx in MUXPIN.items():
            want = 'K_' + chans[idx].upper() if idx in chans else None
            got = p.get(pin)
            if want: check(got == want, f'{side} {ic} Y{idx} (pin {pin}) -> {want}, got {got}'); seen.add(got)
            else: check(got is None or not got.startswith(('K_', 'ADC', 'SEL', 'VCC')), f'{side} {ic} Y{idx} unused, got {got}')
    check(seen == outs, f'{side}: every sensor output reaches exactly one mux input (missing {outs - seen}, extra {seen - outs})')
    n, p = fps['MCU1']
    for pin, want in XIAO.items(): check(p.get(pin) == want, f'{side} XIAO pin {pin} -> {want}, got {p.get(pin)}')
    for pin in ('4', '5', '6', '7', '14'): check(p.get(pin) is None, f'{side} XIAO pin {pin} unconnected, got {p.get(pin)}')
    n, p = fps['TRRS1']
    for pin, want in TRRS.items(): check(p.get(pin) == want, f'{side} TRRS pin {pin} -> {want}, got {p.get(pin)}')
    print(f'{side}: {len(fps)} footprints checked')
print('netlist OK' if fails == 0 else f'{fails} problems')
