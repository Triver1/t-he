"""Replaces a board's Edge.Cuts with the case's PCB outline, exported by OpenSCAD as SVG.

Outline changes in ../case/totem_he_case.scad reach the board through this. The SVG's y already runs down like
KiCad's; it is the left half's outline, and the right's is the same mirrored about halves.AXIS_X. Points closer than
0.02 mm to a straight run are dropped. Prints how far the new edge moved from the old one, so an unintended change
shows.

Export:  openscad -D 'part="pcb"' -o pcb2d.svg ../case/totem_he_case.scad
Usage:   set_edge.py <pcb2d.svg> <in.kicad_pcb> <out.kicad_pcb>
"""
import math
import re
import sys
import uuid

from halves import AXIS_X

svg, src, dst = sys.argv[1:4]
NUM = r'(-?[\d.]+(?:e-?\d+)?)'


def segd(p, a, b):
    vx, vy, wx, wy = b[0] - a[0], b[1] - a[1], p[0] - a[0], p[1] - a[1]
    L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, (wx * vx + wy * vy) / L))
    return math.hypot(wx - t * vx, wy - t * vy)


def simplify(pts, tol):
    """Douglas-Peucker on an open polyline."""
    if len(pts) < 3:
        return pts
    i, d = max(((i, segd(pts[i], pts[0], pts[-1])) for i in range(1, len(pts) - 1)), key=lambda t: t[1])
    if d <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:i + 1], tol)[:-1] + simplify(pts[i:], tol)


rings = []
for path in re.findall(r' d="([^"]+)"', open(svg).read()):
    for ring in re.split(r'(?=M)', path):
        pts = [(float(x), float(y)) for x, y in re.findall(NUM + ',' + NUM, ring)]
        if len(pts) > 2:
            rings.append(pts)
area = lambda p: abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2
outline = max(rings, key=area)                 # the holes are separate rings; the board edge is the big one
# close the loop, simplify, and start at the first vertex again
start = max(range(len(outline)), key=lambda i: (outline[i][0], -outline[i][1]))
loop = outline[start:] + outline[:start] + [outline[start]]
loop = simplify(loop, 0.02)[:-1]
right = [(2 * AXIS_X - x, y) for x, y in loop][::-1]

s = open(src).read()
pat = re.compile(r'\n\t?\s*\(gr_line\s*\(start ' + NUM + ' ' + NUM + r'\)\s*\(end ' + NUM + ' ' + NUM + r'\)(?:(?!\(gr_).)*?\(layer "Edge\.Cuts"\)(?:(?!\(gr_).)*?\)\s*\)', re.S)
old = [((float(m[1]), float(m[2])), (float(m[3]), float(m[4]))) for m in pat.finditer(s)]
new = [(ring[i - 1], ring[i]) for ring in (loop, right) for i in range(len(ring))]
if old:
    template = pat.search(s)[0]
    moved_out = max(min(segd(p, a, b) for a, b in new) for e in old for p in e)
    moved_in = max(min(segd(p, a, b) for a, b in old) for e in new for p in e)
    print(f'{len(old)} edge lines replaced by {len(new)}; largest move: old vertex to new edge {moved_out:.3f} mm, '
          f'new vertex to old edge {moved_in:.3f} mm')
else:   # a freshly generated board has no outline yet
    template = '\n\t(gr_line\n\t\t(start 0 0)\n\t\t(end 0 0)\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "0")\n\t)'
    print(f'{len(new)} edge lines added')

lines = ''
for a, b in new:
    g = re.sub(r'\(start ' + NUM + ' ' + NUM + r'\)', f'(start {a[0]:.4f} {a[1]:.4f})', template, count=1)
    g = re.sub(r'\(end ' + NUM + ' ' + NUM + r'\)', f'(end {b[0]:.4f} {b[1]:.4f})', g, count=1)
    g = re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{uuid.uuid4()}")', g)
    lines += g
first = pat.search(s).start() if old else s.rstrip().rindex(')')
s = pat.sub('', s)
s = s[:first] + lines + s[first:]
open(dst, 'w').write(s)
