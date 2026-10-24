"""Derives the QMK tables from the board and checks every connection the firmware relies on.

Reads the .kicad_pcb file (not the design data behind it), follows each sensor output to a mux channel and each mux
to a XIAO pin, and writes qmk/the_he/he_map.h and qmk/the_he/keyboard.json. Any connection the firmware cannot work
with is reported as an error and nothing is written. The result is also compared with ../pcb/mux_map.json. The file
holds both halves (see ../pcb/halves.py); each is read and checked on its own.

Usage: gen_firmware.py [board.kicad_pcb]  (default: ../pcb/totem_he.kicad_pcb)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, '..', 'pcb')
sys.path.insert(0, PCB)
from halves import RIGHT_REF, PREFIX  # noqa: E402
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PCB, 'totem_he.kicad_pcb')

# 74HC4051, Nexperia datasheet rev 12 table 2
MUX_Y = {'13': 0, '14': 1, '15': 2, '12': 3, '1': 4, '5': 5, '2': 6, '4': 7}
MUX_Z, MUX_S, MUX_E, MUX_VEE, MUX_GND, MUX_VCC = '3', ('11', '10', '9'), '6', '7', '8', '16'
# XIAO RP2040, Seeed wiki: pad number -> label -> RP2040 GPIO
XIAO_PAD = {str(i + 1): f'D{i}' for i in range(7)}
XIAO_PAD.update({'8': 'D7', '9': 'D8', '10': 'D9', '11': 'D10', '12': '3V3', '13': 'GND', '14': '5V'})
XIAO_GP = {'D0': 26, 'D1': 27, 'D2': 28, 'D3': 29, 'D4': 6, 'D5': 7, 'D6': 0, 'D7': 1, 'D8': 2, 'D9': 4, 'D10': 3}
ADC_GP = {26, 27, 28, 29}
# PJ-320A: ring 1 lands on the tip pad, so ring 2 is the only signal
TRRS_PIN = {'4': 'tip', '3': 'ring2', '2': 'sleeve'}

KEYS = ['pinky_top', 'ring_top', 'middle_top', 'index_top', 'inner_top',
        'pinky_home', 'ring_home', 'middle_home', 'index_home', 'inner_home',
        'outer', 'pinky_bottom', 'ring_bottom', 'middle_bottom', 'index_bottom', 'inner_bottom',
        'thumb1', 'thumb2', 'thumb3']
ROWS, COLS = 3, 8

errors, notes = [], []


def parse(path, side):
    """one half's footprints: reference -> (library name, (x, y), {pad number: net name without the half's prefix})"""
    s = open(path).read()
    fps = {}
    for block in re.split(r'\n\s*\(footprint "', s)[1:]:
        name = block.split('"', 1)[0]
        ref = re.search(r'\(property "Reference" "([^"]*)"', block)[1]
        if (int(re.search(r'\d+$', ref)[0]) >= RIGHT_REF) != (side == 'right'):
            continue
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', block)
        pads = {}
        # pcbnew writes a pad over several lines, so split on the keyword rather than on lines
        for chunk in block.split('(pad "')[1:]:
            num = chunk.split('"', 1)[0]
            net = re.search(r'\(net \d+ "([^"]*)"\)', chunk.split('(pad "')[0])
            if net and num and check(net[1].startswith(PREFIX[side]), f'{side} {ref}: net {net[1]} is not on this half'):
                pads[num] = net[1][len(PREFIX[side]):]
        fps[ref] = (name, (float(at[1]), float(at[2])), pads)
    return fps


def check(cond, msg):
    if not cond:
        errors.append(msg)
    return cond


def half(path, side):
    fps = parse(path, side)
    mcu = next(p for n, _, p in fps.values() if n.endswith('xiao_rp2040'))
    net_to_xiao = {}
    for pad, net in mcu.items():
        net_to_xiao.setdefault(net, []).append(XIAO_PAD[pad])
    check(mcu.get('12') == 'VCC', f'{side}: XIAO 3V3 is on {mcu.get("12")}, not VCC')
    check(mcu.get('13') == 'GND', f'{side}: XIAO GND is on {mcu.get("13")}, not GND')
    check('14' not in mcu, f'{side}: XIAO 5V is connected to {mcu.get("14")}; the sensors are 3.3 V parts')

    def xiao_pin(net, what):
        pins = [p for p in net_to_xiao.get(net, []) if p in XIAO_GP]
        if check(len(pins) == 1, f'{side}: {what} ({net}) reaches XIAO pins {pins or "none"}, expected exactly one'):
            return pins[0]

    muxes = {r: p for r, (n, _, p) in fps.items() if n.endswith('mux_4051')}
    check(len(muxes) == ROWS, f'{side}: {len(muxes)} muxes, expected {ROWS}')
    rows, sel = {}, None
    for ref, p in sorted(muxes.items()):
        check(p.get(MUX_VCC) == 'VCC', f'{side} {ref}: VCC pin on {p.get(MUX_VCC)}')
        for pin, what in ((MUX_GND, 'GND'), (MUX_VEE, 'VEE'), (MUX_E, 'E, active low')):
            check(p.get(pin) == 'GND', f'{side} {ref}: {what} (pin {pin}) on {p.get(pin)}, must be GND')
        d = xiao_pin(p.get(MUX_Z), f'{ref} common Z')
        if d and check(XIAO_GP[d] in ADC_GP, f'{side} {ref}: common goes to {d} = GP{XIAO_GP[d]}, which has no ADC'):
            rows[ref] = d
        s = tuple(xiao_pin(p.get(pin), f'{ref} S{i}') for i, pin in enumerate(MUX_S))
        if sel is None:
            sel = s
        check(s == sel, f'{side} {ref}: select lines S0..S2 on {s}, other muxes on {sel}')
    # the firmware's row index is the ADC pin order D0, D1, D2
    order = sorted(rows, key=lambda r: XIAO_GP[rows[r]])
    row_of = {ref: i for i, ref in enumerate(order)}

    keymap = {}
    switches = {r: (at, p) for r, (n, at, p) in fps.items() if n.endswith('switch_he')}
    check(len(switches) == 19, f'{side}: {len(switches)} switches, expected 19')
    pos = {}
    for ref, (at, p) in switches.items():
        outs = [n for n in p.values() if n.startswith('K_')]
        if not check(len(set(outs)) == 1, f'{side} {ref}: sensor output nets {outs}'):
            continue
        key = outs[0][2:].lower()
        pos[key] = at
        hits = [(m, MUX_Y[pin]) for m, mp in muxes.items() for pin, n in mp.items() if n == outs[0] and pin in MUX_Y]
        other = [(m, pin) for m, mp in muxes.items() for pin, n in mp.items() if n == outs[0] and pin not in MUX_Y]
        check(not other, f'{side} {key}: sensor output also on mux pins {other}')
        if check(len(hits) == 1, f'{side} {key}: sensor output reaches mux inputs {hits}, expected exactly one'):
            m, ch = hits[0]
            if m in row_of:
                keymap[key] = (row_of[m], ch)
    check(len(set(keymap.values())) == len(keymap), f'{side}: two keys share a mux channel')
    check(set(keymap) == set(KEYS), f'{side}: keys {sorted(set(KEYS) ^ set(keymap))} missing or unexpected')

    trrs = next(p for n, _, p in fps.values() if 'trrs' in n)
    link = {TRRS_PIN[k]: v for k, v in trrs.items() if k in TRRS_PIN}
    check(link.get('tip') == 'VCC' and link.get('sleeve') == 'GND',
          f'{side}: TRRS tip {link.get("tip")}, sleeve {link.get("sleeve")}; expected VCC on the tip and GND on the sleeve')
    data = xiao_pin(link.get('ring2'), 'TRRS ring 2')
    return {'rows': [rows[r] for r in order], 'sel': sel, 'keys': keymap, 'pos': pos, 'data': data, 'mux_of_row': order}


L, R = half(BOARD, 'left'), half(BOARD, 'right')
for what in ('rows', 'sel', 'data'):
    check(L[what] == R[what], f'{what}: left {L[what]}, right {R[what]}; the firmware uses one set of pins for both halves')

mm = json.load(open(os.path.join(PCB, 'mux_map.json')))
for side, h in (('left', L), ('right', R)):
    design = {key: (ic, int(ch)) for ic, m in mm[side].items() for ch, key in m['chan'].items()}
    mux_of = lambda row: 'IC%d' % (int(h['mux_of_row'][row][2:]) % RIGHT_REF)
    board = {k: (mux_of(r), c) for k, (r, c) in h['keys'].items()}
    diff = {k: (board.get(k), design.get(k)) for k in KEYS if board.get(k) != design.get(k)}
    check(not diff, f'{side}: board and mux_map.json disagree (board, design): {diff}')

if errors:
    print('WIRING ERRORS, nothing written:')
    for e in errors:
        print('  ' + e)
    sys.exit(1)

# ---- he_map.h ---------------------------------------------------------------------------------------------------
gp = lambda d: f'GP{XIAO_GP[d]}'


def table(h):
    grid = [['NULL'] * COLS for _ in range(ROWS)]
    for k, (r, c) in h['keys'].items():
        grid[r][c] = f'"{k}"'
    return ',\n'.join('    {' + ', '.join(row) + '}' for row in grid)


def present(h):
    bits = [0] * ROWS
    for r, c in h['keys'].values():
        bits[r] |= 1 << c
    return ', '.join(f'0x{b:02X}' for b in bits)


hdr = f'''// Generated by firmware/gen_firmware.py from the board. Do not edit.
#pragma once

// mux commons, one per matrix row: {', '.join(f'{d} (mux {m})' for d, m in zip(L['rows'], L['mux_of_row']))}
#define HE_ROW_PINS {{ {', '.join(gp(d) for d in L['rows'])} }}
// shared select lines S0 (LSB), S1, S2: {', '.join(L['sel'])}
#define HE_SEL_PINS {{ {', '.join(gp(d) for d in L['sel'])} }}

// channels with a sensor on them, one bit per mux channel
#define HE_PRESENT_LEFT  {{ {present(L)} }}
#define HE_PRESENT_RIGHT {{ {present(R)} }}

// key names, printed by the self test
#define HE_NAMES_LEFT {{ \\
{table(L).replace(chr(10), ' ' + chr(92) + chr(10))} \\
}}
#define HE_NAMES_RIGHT {{ \\
{table(R).replace(chr(10), ' ' + chr(92) + chr(10))} \\
}}


// split link: one half-duplex wire on TRRS ring 2, {L['data']}
#define SERIAL_USART_TX_PIN {gp(L['data'])}
'''
out = os.path.join(HERE, 'qmk', 'the_he')
open(os.path.join(out, 'he_map.h'), 'w').write(hdr)

# ---- keyboard.json layout: positions from the left board, mirrored for the right -----------------------------
U = 19.05
xs = [p[0] for p in L['pos'].values()]
ys = [p[1] for p in L['pos'].values()]
x0, x1, y0 = min(xs), max(xs), min(ys)
gap = 1.5
left_order = ['pinky_top', 'ring_top', 'middle_top', 'index_top', 'inner_top',
              'pinky_home', 'ring_home', 'middle_home', 'index_home', 'inner_home',
              'outer', 'pinky_bottom', 'ring_bottom', 'middle_bottom', 'index_bottom', 'inner_bottom']
thumbs = sorted(['thumb1', 'thumb2', 'thumb3'], key=lambda k: L['pos'][k][0])
layout = []


def entry(k, h, row_off, mirror):
    x, y = L['pos'][k]
    ux = (x - x0) / U
    if mirror:
        ux = (x1 - x0) / U * 2 + gap - ux
    r, c = h['keys'][k]
    return {'matrix': [r + row_off, c], 'x': round(ux, 2), 'y': round((y - y0) / U, 2), 'label': k}


rows_l = [left_order[0:5], left_order[5:10], left_order[10:16]]
for rl in rows_l:
    layout += [entry(k, L, 0, False) for k in rl]
    layout += [entry(k, R, ROWS, True) for k in reversed(rl)]
layout += [entry(k, L, 0, False) for k in thumbs]
layout += [entry(k, R, ROWS, True) for k in reversed(thumbs)]
for e in layout:
    del e['label']

kb = {
    'keyboard_name': 'Tot-HE-m',
    'manufacturer': 'Tot-HE-m',
    'maintainer': 'tristan',
    'processor': 'RP2040',
    'bootloader': 'rp2040',
    'board': 'GENERIC_RP_RP2040',
    'usb': {'vid': '0xFEED', 'pid': '0x7E57', 'device_version': '0.1.0'},
    'features': {'bootmagic': False, 'extrakey': True, 'mousekey': False, 'nkro': True, 'console': True},
    'matrix_size': {'rows': ROWS * 2, 'cols': COLS},
    'split': {'enabled': True, 'serial': {'driver': 'vendor'},
              'transport': {'sync': {'matrix_state': True}}},
    'layouts': {'LAYOUT': {'layout': layout}},
}
json.dump(kb, open(os.path.join(out, 'keyboard.json'), 'w'), indent=4)

print(f'rows {L["rows"]}, select {L["sel"]}, split link {L["data"]}')
for side, h in (('left', L), ('right', R)):
    print(f'{side} matrix (row = mux on D0/D1/D2, column = channel):')
    for r in range(ROWS):
        print('   ', ' '.join(f'{next((k for k, v in h["keys"].items() if v == (r, c)), "-"):>13}' for c in range(COLS)))
for n in notes:
    print('note:', n)
print('wrote he_map.h and keyboard.json; board matches mux_map.json')
