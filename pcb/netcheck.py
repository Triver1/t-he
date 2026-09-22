"""Checks the netlist of the generated boards: every pad's net against what the design says it should be.
Usage: netcheck.py  (reads out/<side>/pcbs/totem_he_<side>.kicad_pcb)"""
import re, sys
MUX = {'IC1': ['K_PINKY_BOTTOM', 'K_PINKY_HOME', 'K_PINKY_TOP', 'K_OUTER', 'K_RING_BOTTOM', 'K_RING_HOME', 'K_RING_TOP'],
       'IC2': ['K_MIDDLE_BOTTOM', 'K_MIDDLE_HOME', 'K_MIDDLE_TOP', 'K_INDEX_BOTTOM', 'K_INDEX_HOME', 'K_INDEX_TOP', 'K_THUMB1', 'K_THUMB2'],
       'IC3': ['K_INNER_BOTTOM', 'K_INNER_HOME', 'K_INNER_TOP', 'K_THUMB3']}
ADC = {'IC1': 'ADC_A', 'IC2': 'ADC_B', 'IC3': 'ADC_C'}
# 74HC4051 pins: 1 Y4, 2 Y6, 3 Z, 4 Y7, 5 Y5, 6 E, 7 VEE, 8 GND, 9 S2, 10 S1, 11 S0, 12 Y3, 13 Y0, 14 Y1, 15 Y2, 16 VCC
MUXPIN = {'13': 0, '14': 1, '15': 2, '12': 3, '1': 4, '5': 5, '2': 6, '4': 7}
XIAO = {'1': 'ADC_A', '2': 'ADC_B', '3': 'ADC_C', '5': 'SEL0', '6': 'SEL1', '9': 'SEL2', '7': 'TX', '8': 'RX', '12': 'VCC', '13': 'GND'}
TRRS = {'4': 'VCC', '5': 'TX', '3': 'RX', '2': 'GND'}   # PJ-320A: tip, ring 1, ring 2, sleeve
fails = 0
def check(cond, msg):
    global fails
    if not cond: fails += 1; print('FAIL', msg)
for side in ('left', 'right'):
    s = open(f'out/{side}/pcbs/totem_he_{side}.kicad_pcb').read()
    fps = {}
    blocks = re.split(r'\n\s*\(footprint "', s)[1:]
    for b in blocks:
        name = b.split('"', 1)[0]; ref = re.search(r'\(property "Reference" "([^"]*)"', b)
        pads = {}
        for pm in re.finditer(r'\(pad "([^"]*)"([^\n]*)', b):   # Ergogen writes each pad on one line
            n = re.search(r'\(net \d+ "([^"]*)"\)', pm[2])
            if n: pads[pm[1]] = n[1]
        fps[ref[1] if ref else name] = (name, pads)
    keys = {r: p for r, (n, p) in fps.items() if n.endswith('switch_he')}
    check(len(keys) == 19, f'{side}: 19 switches ({len(keys)})')
    outs = set()
    for r, p in keys.items():
        check(p.get('1') == 'VCC' and p.get('2') == 'GND' and p.get('3', '').startswith('K_'), f'{side} {r}: sensor pads VCC/GND/OUT, got {p.get("1")}/{p.get("2")}/{p.get("3")}')
        check(p.get('C1') == 'VCC' and p.get('C2') == 'GND', f'{side} {r}: cap across VCC/GND')
        outs.add(p.get('3'))
    check(len(outs) == 19, f'{side}: 19 distinct sensor nets')
    seen = set()
    for ic, chans in MUX.items():
        n, p = fps[ic]
        check(p.get('16') == 'VCC' and p.get('8') == 'GND' and p.get('6') == 'GND' and p.get('7') == 'GND', f'{side} {ic}: VCC/GND/E/VEE')
        check(p.get('3') == ADC[ic], f'{side} {ic}: Z -> {ADC[ic]} (got {p.get("3")})')
        check(p.get('11') == 'SEL0' and p.get('10') == 'SEL1' and p.get('9') == 'SEL2', f'{side} {ic}: S0..S2')
        check(p.get('C1') == 'VCC' and p.get('C2') == 'GND', f'{side} {ic}: cap')
        for pin, idx in MUXPIN.items():
            want = chans[idx] if idx < len(chans) else None
            got = p.get(pin)
            if want: check(got == want, f'{side} {ic} Y{idx} (pin {pin}) -> {want}, got {got}'); seen.add(got)
            else: check(got is None or not got.startswith(('K_', 'ADC', 'SEL', 'VCC')), f'{side} {ic} Y{idx} unused, got {got}')
    check(seen == outs, f'{side}: every sensor output reaches exactly one mux input (missing {outs - seen}, extra {seen - outs})')
    n, p = fps['MCU1']
    for pin, want in XIAO.items(): check(p.get(pin) == want, f'{side} XIAO pin {pin} -> {want}, got {p.get(pin)}')
    for pin in ('4', '10', '11', '14'): check(p.get(pin) is None, f'{side} XIAO pin {pin} unconnected, got {p.get(pin)}')
    n, p = fps['TRRS1']
    for pin, want in TRRS.items(): check(p.get(pin) == want, f'{side} TRRS pin {pin} -> {want}, got {p.get(pin)}')
    print(f'{side}: {len(fps)} footprints checked')
print('netlist OK' if fails == 0 else f'{fails} problems')
