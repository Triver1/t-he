"""Top silkscreen artwork: the field lines of a bar magnet lying under the Tot-HE-m title on each half (r = L·sin²θ
around a dipole), cut wherever they would cross a switch square, the XIAO, the jack, a mounting hole, board text or
come within EDGE mm of the board edge, plus the cat from art/cat_pcb.geojson (a potrace trace of the drawing, strokes
thickened so the whiskers print) beside the inner column on each half, the same way round on both.
Runs inside the KiCad container, after set_edge.py.
Usage: art.py <board.kicad_pcb>  (edits it in place)
"""
import json
import math
import os
import sys

import pcbnew
from pcbnew import FromMM, ToMM

from halves import AXIS_X

MAGNET = (55.0, 71.6)                     # left half, centre of the title; the right half mirrors it
LOOPS = [6 * 1.2 ** i for i in range(24)]
STEP, MIN_RUN, EDGE, WIDTH = 0.15, 3.0, 0.8, 0.15
KEEP = {'switch_he': (-7.4, 7.4, -7.4, 7.4), 'xiao_rp2040': (-9.6, 9.6, -10.9, 12.5),
        'trrs_pj320a': (-3.8, 3.8, -1.0, 15.4), 'mounting_hole_plated': None}
CAT = (114.0, 53.4, 14.0)                # left half: top-left corner and width in mm, centred between the field lines and hole H1

b = pcbnew.LoadBoard(sys.argv[1])
cat = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'art', 'cat_pcb.geojson')))['features']
px = [p for f in cat for ring in f['geometry']['coordinates'] for p in ring]
cx0, cy1 = min(p[0] for p in px), max(p[1] for p in px)
scale = CAT[2] / (max(p[0] for p in px) - cx0)
cat_h = (cy1 - min(p[1] for p in px)) * scale
for left in (CAT[0], 2 * AXIS_X - CAT[0] - CAT[2]):
    shapes = pcbnew.SHAPE_POLY_SET()
    for f in cat:
        for i, ring in enumerate(f['geometry']['coordinates']):
            chain = pcbnew.SHAPE_LINE_CHAIN()
            for x, y in ring:                  # potrace's y points up
                chain.Append(FromMM(left + (x - cx0) * scale), FromMM(CAT[1] + (cy1 - y) * scale))
            chain.SetClosed(True)
            if i == 0:
                shapes.AddOutline(chain)
            else:
                shapes.AddHole(chain, shapes.OutlineCount() - 1)
    shapes.Simplify(pcbnew.SHAPE_POLY_SET.PM_FAST)
    shapes.Fracture(pcbnew.SHAPE_POLY_SET.PM_FAST)
    for i in range(shapes.OutlineCount()):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_POLY); s.SetLayer(pcbnew.F_SilkS)
        s.SetPolyShape(pcbnew.SHAPE_POLY_SET(shapes.Outline(i))); s.SetFilled(True); s.SetWidth(0)
        b.Add(s)
boxes, holes = [], []
for f in b.GetFootprints():
    kind = f.GetFPIDAsString().split(':')[-1]
    if kind not in KEEP:
        continue
    x, y = ToMM(f.GetPosition().x), ToMM(f.GetPosition().y)
    if KEEP[kind] is None:
        holes.append((x, y, 2.8))
    else:
        boxes.append((x, y, math.radians(f.GetOrientationDegrees()), KEEP[kind]))
texts = [(x0 - 0.6, CAT[1] - 0.6, x0 + CAT[2] + 0.6, CAT[1] + cat_h + 0.6)
         for x0 in (CAT[0], 2 * AXIS_X - CAT[0] - CAT[2])]   # the cats
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.F_SilkS and isinstance(d, pcbnew.PCB_TEXT):
        bb = d.GetBoundingBox()
        texts.append((ToMM(bb.GetLeft()) - 0.6, ToMM(bb.GetTop()) - 0.6, ToMM(bb.GetRight()) + 0.6, ToMM(bb.GetBottom()) + 0.6))
outline = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(outline)
inside = outline.CloneDropTriangulation()
inside.Deflate(FromMM(EDGE), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FromMM(0.05))


def clear(x, y, left):
    if (x < AXIS_X) != left or not inside.Contains(pcbnew.VECTOR2I(FromMM(x), FromMM(y))):
        return False
    for cx, cy, a, (x0, x1, y0, y1) in boxes:     # into the part's own frame (gen_config.place, inverted)
        dx, dy = x - cx, y - cy
        lx, ly = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        if x0 <= lx <= x1 and y0 <= ly <= y1:
            return False
    if any(math.hypot(x - hx, y - hy) < r for hx, hy, r in holes):
        return False
    return not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in texts)


def field_line(cx, cy, L, up):
    """one closed field line, as points spaced about STEP apart"""
    pts, t = [], 0.002
    while t < math.pi - 0.002:
        r = L * math.sin(t) ** 2
        pts.append((cx + r * math.cos(t), cy + (-1 if up else 1) * r * math.sin(t)))
        speed = L * math.sin(t) * math.sqrt(4 * math.cos(t) ** 2 + math.sin(t) ** 2) + 1e-6
        t += STEP / speed
    return pts


def add(run):
    keep = [run[0]]                        # drop points that sit on a straight run, so curves stay smooth but short
    for p in run[1:-1]:
        if math.dist(p, keep[-1]) >= 0.6:
            keep.append(p)
    keep.append(run[-1])
    for (xa, ya), (xb, yb) in zip(keep, keep[1:]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.F_SilkS); s.SetWidth(FromMM(WIDTH))
        s.SetStart(pcbnew.VECTOR2I(FromMM(xa), FromMM(ya))); s.SetEnd(pcbnew.VECTOR2I(FromMM(xb), FromMM(yb)))
        b.Add(s)


count = 0
for cx in (MAGNET[0], 2 * AXIS_X - MAGNET[0]):
    for L in LOOPS:
        for up in (True, False):
            run = []
            for p in field_line(cx, MAGNET[1], L, up) + [None]:
                if p is not None and clear(*p, cx < AXIS_X):
                    run.append(p)
                    continue
                if len(run) > 1 and sum(math.dist(a, c) for a, c in zip(run, run[1:])) >= MIN_RUN:
                    add(run); count += 1
                run = []
b.Save(sys.argv[1])
print(f'{count} field-line runs and two cats on F.SilkS')
