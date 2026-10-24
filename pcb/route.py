"""Hand-routing helper for totem_he.kicad_pcb: draws the board, lists what is still open, and adds tracks and vias
one at a time, so every route is placed on purpose instead of by an autorouter. Runs inside the KiCad container
(see ./r). Coordinates are board millimetres, y pointing down, as KiCad shows them.

  view [x0 y0 x1 y1] [--scale PX_PER_MM] [--out FILE]   picture of the board or a region: top copper red, underside
                                                         blue, vias black, open connections as dashed yellow lines
  open [NET_SUBSTRING]                                   connections still open, with both ends
  track NET LAYER WIDTH x,y x,y ...                      a trace through the points on F or B
  via NET x,y                                            a 0.6/0.3 mm through via
  delete x,y [RADIUS]                                    removes tracks and vias within RADIUS mm (default 0.3)
  undo                                                   restores the board as it was before the last change
  drc                                                    violation and open-connection counts
  dump                                                   writes out/pads.json: every part, pad, net and position
  batch FILE                                             runs track/via/delete lines from FILE as one change
"""
import math
import os
import re
import shutil
import subprocess
import sys

import pcbnew
from pcbnew import FromMM, ToMM

BOARD = os.environ.get('BOARD', 'totem_he.kicad_pcb')
UNDO = '.route_undo'
V = lambda x, y: pcbnew.VECTOR2I(FromMM(x), FromMM(y))


def drc_report():
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--severity-all', '-o', '/tmp/drc.txt', BOARD], capture_output=True)
    return open('/tmp/drc.txt').read()


def open_pairs(report):
    """unconnected items as ((x, y), label, (x, y), label)"""
    pairs = []
    for block in report.split('\n[')[1:]:
        if not block.startswith('unconnected_items'):
            continue
        ends = re.findall(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (.*)', block)
        if len(ends) == 2:
            (x1, y1, l1), (x2, y2, l2) = ends
            pairs.append(((float(x1), float(y1)), l1, (float(x2), float(y2)), l2))
    return pairs


def violations(report):
    out = []
    for block in report.split('\n[')[1:]:
        kind = block.split(']')[0]
        if kind != 'unconnected_items':
            out.append((kind, ' | '.join(l.strip() for l in block.splitlines()[1:4])))
    return out


def snapshot():
    os.makedirs(UNDO, exist_ok=True)
    n = len(os.listdir(UNDO))
    shutil.copy(BOARD, f'{UNDO}/{n:04d}.kicad_pcb')


def net_of(board, name):
    net = board.FindNet(name)
    if not net or net.GetNetCode() == 0:
        sys.exit(f'no net {name}')
    return net


def report_new(before):
    after = violations(drc_report())
    new = [v for v in after if v not in before and v[0] != 'track_dangling']   # unfinished traces are expected
    print(f'{len(new)} new violation(s)' + ''.join(f'\n  {k}: {t}' for k, t in new))


def view(args):
    from PIL import Image, ImageDraw, ImageFont
    scale, out, box, pins = 12.0, 'out/view.png', None, False
    rest = []
    it = iter(args)
    for a in it:
        if a == '--pins':
            pins = True
        elif a == '--scale':
            scale = float(next(it))
        elif a == '--out':
            out = next(it)
        else:
            rest.append(float(a))
    b = pcbnew.LoadBoard(BOARD)
    if len(rest) == 4:
        box = rest
    else:
        bb = b.GetBoardEdgesBoundingBox()
        box = [ToMM(bb.GetLeft()) - 2, ToMM(bb.GetTop()) - 2, ToMM(bb.GetRight()) + 2, ToMM(bb.GetBottom()) + 2]
    x0, y0, x1, y1 = box
    W, H = int((x1 - x0) * scale), int((y1 - y0) * scale)
    im = Image.new('RGB', (W, H), '#fbfaf6')
    d = ImageDraw.Draw(im, 'RGBA')
    T = lambda x, y: ((x - x0) * scale, (y - y0) * scale)
    Tv = lambda v: T(ToMM(v.x), ToMM(v.y))
    font = ImageFont.truetype('DejaVuSans.ttf', max(9, int(scale * 0.55)))
    small = ImageFont.truetype('DejaVuSans.ttf', max(8, int(scale * 0.42)))
    step = 1 if x1 - x0 < 30 else 5 if x1 - x0 < 120 else 10
    for g in range(int(x0 // step) * step, int(x1) + 1, step):
        d.line([T(g, y0), T(g, y1)], fill=(0, 0, 0, 22)); d.text((T(g, y0)[0] + 2, 2), f'{g}', fill='#999', font=small)
    for g in range(int(y0 // step) * step, int(y1) + 1, step):
        d.line([T(x0, g), T(x1, g)], fill=(0, 0, 0, 22)); d.text((2, T(x0, g)[1] + 1), f'{g}', fill='#999', font=small)
    ol = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(ol)
    for i in range(ol.OutlineCount()):
        o = ol.Outline(i)
        d.line([Tv(o.CPoint(j)) for j in range(o.PointCount())] + [Tv(o.CPoint(0))], fill='#888', width=2)
    colours = {pcbnew.F_Cu: (214, 60, 48, 150), pcbnew.B_Cu: (47, 111, 214, 150)}
    for f in b.GetFootprints():
        for p in f.Pads():
            for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
                if p.IsOnLayer(layer):
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, layer, 0, FromMM(0.01))
                    for i in range(ps.OutlineCount()):
                        o = ps.Outline(i)
                        d.polygon([Tv(o.CPoint(j)) for j in range(o.PointCount())], fill=colours[layer])
            if p.GetDrillSizeX():
                c = Tv(p.GetPosition()); r = ToMM(p.GetDrillSizeX()) / 2 * scale
                d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill='#fbfaf6')
        c = Tv(f.GetPosition())
        d.text((c[0] + 2, c[1] - scale * 6.5), f.GetReference(), fill='#777', font=small)
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            c = Tv(t.GetPosition()); r = ToMM(t.GetWidth()) / 2 * scale
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill='#222')
        else:
            d.line([Tv(t.GetStart()), Tv(t.GetEnd())], fill=(214, 60, 48, 230) if t.GetLayer() == pcbnew.F_Cu else (30, 90, 200, 230),
                   width=max(1, int(ToMM(t.GetWidth()) * scale)))
    for (a, la, c, lc) in open_pairs(drc_report()):
        (ax, ay), (cx, cy) = T(*a), T(*c)
        n = max(1, int(((cx - ax) ** 2 + (cy - ay) ** 2) ** 0.5 / 6))
        for i in range(0, n, 2):
            d.line([(ax + (cx - ax) * i / n, ay + (cy - ay) * i / n), (ax + (cx - ax) * (i + 1) / n, ay + (cy - ay) * (i + 1) / n)], fill=(230, 170, 0, 255), width=2)
    if pins:
        label_pins(b, im, d, T, Tv, scale)
    elif scale >= 18:   # close up: label pads with their net
        for f in b.GetFootprints():
            for p in f.Pads():
                n = str(p.GetNetname()).split('/')[-1]
                if n and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    c = Tv(p.GetPosition())
                    if 0 <= c[0] < W and 0 <= c[1] < H:
                        d.text((c[0] - 3, c[1] - 5), n.replace('K_', '').lower()[:10], fill='#111', font=small)
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    im.save(out)
    print(out, im.size)


MUX_PIN = {'1': 'Y4', '2': 'Y6', '3': 'Z', '4': 'Y7', '5': 'Y5', '6': 'E', '7': 'VEE', '8': 'GND', '9': 'S2',
           '10': 'S1', '11': 'S0', '12': 'Y3', '13': 'Y0', '14': 'Y1', '15': 'Y2', '16': 'VCC'}
XIAO_PIN = {str(i + 1): f'D{i}' for i in range(11)} | {'12': '3V3', '13': 'GND', '14': '5V'}
TRRS_PIN = {'2': 'sleeve', '3': 'ring2', '4': 'tip'}
SENSOR_PIN = {'1': 'VCC', '2': 'OUT', '3': 'GND', 'C1': 'C+', 'C2': 'C-'}


def label_pins(b, im, d, T, Tv, scale):
    """every copper pad: pin name and net; IC and XIAO labels point away from the chip along the pin"""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype('DejaVuSans-Bold.ttf', max(8, int(scale * 0.36)))
    short = lambda p: str(p.GetNetname()).split('/')[-1].replace('K_', '').lower() if str(p.GetNetname()).split('/')[-1].startswith('K_') \
        else str(p.GetNetname()).split('/')[-1]

    def text_at(x, y, s, colour, angle=0.0, anchor='mm'):
        w = int(font.getlength(s)) + 8; h = font.size + 8
        t = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(t).text((4, h / 2), s, font=font, fill=colour, anchor='lm', stroke_width=2, stroke_fill='#ffffff')
        if 90 < angle % 360 < 270:   # keep text readable: flip it and grow it the other way
            angle += 180; anchor = 'rm' if anchor == 'lm' else anchor
        t = t.rotate(angle, expand=True, resample=Image.BICUBIC)
        a = math.radians(angle)
        if anchor == 'lm':
            x += (w / 2 - 4) * math.cos(a); y -= (w / 2 - 4) * math.sin(a)
        elif anchor == 'rm':
            x -= (w / 2 - 4) * math.cos(a); y += (w / 2 - 4) * math.sin(a)
        im.paste(t, (int(x - t.width / 2), int(y - t.height / 2)), t)

    for f in b.GetFootprints():
        kind = f.GetFPIDAsString().split(':')[-1]
        pads = [p for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
        if kind in ('mux_4051', 'xiao_rp2040'):
            names = MUX_PIN if kind == 'mux_4051' else XIAO_PIN
            num = {p.GetNumber(): p for p in pads if p.GetNumber().isdigit()}
            pos = {n: (ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for n, p in num.items()}
            half = len(names) // 2
            (ax, ay), (bx, by) = pos['1'], pos[str(half)]
            nx, ny = -(by - ay), bx - ax; L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
            cx = sum(x for x, _ in pos.values()) / len(pos); cy = sum(y for _, y in pos.values()) / len(pos)
            for n, p in num.items():
                x, y = pos[n]
                s = 1 if (x - cx) * nx + (y - cy) * ny > 0 else -1
                net = short(p)
                s_txt = names[n] if net == names[n] else f'{names[n]} {net or "nc"}'
                gap = (ToMM(p.GetSize().x) if kind == 'xiao_rp2040' else 1.0) / 2 + 0.25
                px, py = T(x + s * nx * gap, y + s * ny * gap)
                text_at(px, py, s_txt, '#7a1f00' if kind == 'mux_4051' else '#0b4f1c',
                        math.degrees(math.atan2(-s * ny, s * nx)), 'lm')
        else:
            done = set()
            for p in pads:
                n = p.GetNumber()
                x, y = Tv(p.GetPosition())
                net = short(p)
                if kind == 'trrs_pj320a':
                    text_at(x, y - scale * 1.0, f'{TRRS_PIN.get(n, n)} {net or "nc"}', '#4b0a63')
                elif kind == 'switch_he':
                    via = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                    s = ('via ' + net) if via else SENSOR_PIN.get(n, n)
                    text_at(x, y + (scale * 0.75 if via else 0), s, '#333333' if via else '#0a3a8c')
                elif net and n not in done:
                    text_at(x, y, net, '#333333')
                done.add(n)
            if kind == 'switch_he':
                key = next((short(p) for p in pads if p.GetNumber() == '2'), '')
                c = Tv(f.GetPosition())
                text_at(c[0], c[1] + scale * 7.3, f'{f.GetReference()} {key}', '#000000')


def apply(b, op, args):
    if op == 'track':
        net = net_of(b, args[0]); layer = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}[args[1]]; width = float(args[2])
        pts = [tuple(map(float, a.split(','))) for a in args[3:]]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if abs(xa - xb) + abs(ya - yb) < 1e-4:
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(xa, ya)); t.SetEnd(V(xb, yb)); t.SetWidth(FromMM(width))
            t.SetLayer(layer); t.SetNet(net); b.Add(t)
    elif op == 'via':
        net = net_of(b, args[0]); x, y = map(float, args[1].split(','))
        v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(FromMM(0.6)); v.SetDrill(FromMM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); b.Add(v)
    elif op == 'delete':
        x, y = map(float, args[0].split(',')); r = float(args[1]) if len(args) > 1 else 0.3
        for t in [t for t in b.GetTracks() if t.HitTest(V(x, y), FromMM(r))]:
            b.Remove(t)
    else:
        sys.exit(__doc__)


def main():
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'view':
        return view(args)
    if cmd == 'open':
        pairs = open_pairs(drc_report())
        pairs = [p for p in pairs if not args or args[0] in p[1] + p[3]]
        for (a, la, c, lc) in pairs:
            print(f'({a[0]:.2f}, {a[1]:.2f}) {la}\n   -> ({c[0]:.2f}, {c[1]:.2f}) {lc}')
        return print(len(pairs), 'open')
    if cmd == 'drc':
        rep = drc_report()
        real = [v for v in violations(rep) if v[0] != 'track_dangling']
        print(len(real), 'violations,', len(open_pairs(rep)), 'open connections')
        for k, t in real[:15]:
            print(' ', k, t)
        return
    if cmd == 'dump':
        import json
        b = pcbnew.LoadBoard(BOARD)
        parts = []
        for f in b.GetFootprints():
            parts.append({'ref': f.GetReference(), 'kind': f.GetFPIDAsString().split(':')[-1], 'x': ToMM(f.GetPosition().x),
                          'y': ToMM(f.GetPosition().y), 'rot': f.GetOrientationDegrees(),
                          'pads': [{'num': p.GetNumber(), 'x': ToMM(p.GetPosition().x), 'y': ToMM(p.GetPosition().y),
                                    'net': str(p.GetNetname()), 'F': p.IsOnLayer(pcbnew.F_Cu), 'B': p.IsOnLayer(pcbnew.B_Cu),
                                    'drill': ToMM(p.GetDrillSizeX())} for p in f.Pads()]})
        json.dump(parts, open('out/pads.json', 'w'), indent=0)
        return print(len(parts), 'parts written to out/pads.json')
    if cmd == 'undo':
        snaps = sorted(os.listdir(UNDO)) if os.path.isdir(UNDO) else []
        if not snaps:
            sys.exit('nothing to undo')
        shutil.move(f'{UNDO}/{snaps[-1]}', BOARD)
        return print('restored', snaps[-1])
    before = violations(drc_report())
    snapshot()
    b = pcbnew.LoadBoard(BOARD)
    lines = [l.split() for l in open(args[0]) if l.strip() and not l.startswith('#')] if cmd == 'batch' else [[cmd] + args]
    counts = {}
    for op, *a in lines:
        apply(b, op, a)
        counts[op] = counts.get(op, 0) + 1
    print(', '.join(f'{n} {op}' for op, n in counts.items()))
    b.Save(BOARD)
    report_new(before)


main()
