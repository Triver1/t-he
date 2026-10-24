"""Joins the two halves with snap-off tabs for fabrication: each tab bridges the gap between the facing straight
edges, with a row of 0.5 mm unplated holes (mouse bites) along both edges so the tab snaps off there.
Runs inside the KiCad container (see gerbers.sh).
Usage: panel.py <in.kicad_pcb> <out.kicad_pcb>
"""
import sys

import pcbnew
from pcbnew import FromMM, ToMM

TABS = (25.0, 45.0, 65.0)     # tab centre y; clear of the jacks (y 6-17) and the mounting holes (y 74.5)
TAB_W = 5.0
HOLE, PITCH = 0.5, 0.8
INSET = HOLE / 2              # hole centres sit this far off the board edge, in the tab, so the hole edge meets it

src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
V = lambda x, y: pcbnew.VECTOR2I(FromMM(x), FromMM(y))
r3 = lambda v: round(ToMM(v), 3)

edges = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT
         and r3(d.GetStart().x) == r3(d.GetEnd().x)]
mid = ToMM(b.GetBoardEdgesBoundingBox().Centre().x)
left = max((d for d in edges if r3(d.GetStart().x) < mid), key=lambda d: r3(d.GetStart().x))
right = min((d for d in edges if r3(d.GetStart().x) > mid), key=lambda d: r3(d.GetStart().x))
xl, xr = r3(left.GetStart().x), r3(right.GetStart().x)
y_top = max(min(r3(d.GetStart().y), r3(d.GetEnd().y)) for d in (left, right))
y_bot = min(max(r3(d.GetStart().y), r3(d.GetEnd().y)) for d in (left, right))
width = left.GetWidth()


def line(x0, y0, x1, y1):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1)); s.SetWidth(width); b.Add(s)


kept = [left, right]          # removed items stay referenced, or their SWIG wrappers break
for d in kept:
    b.Remove(d)
cuts = [y_top] + [y for c in sorted(TABS) for y in (c - TAB_W / 2, c + TAB_W / 2)] + [y_bot]
for y0, y1 in zip(cuts[::2], cuts[1::2]):
    line(xl, y0, xl, y1); line(xr, y0, xr, y1)
for c in TABS:
    for y in (c - TAB_W / 2, c + TAB_W / 2):
        line(xl, y, xr, y)

fp = pcbnew.FOOTPRINT(b); fp.SetReference('PANEL'); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
b.Add(fp)
n = int((TAB_W - HOLE) // PITCH) + 1
for c in TABS:
    y0 = c - (n - 1) * PITCH / 2
    for i in range(n):
        for x in (xl + INSET, xr - INSET):
            p = pcbnew.PAD(fp); p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetSize(V(HOLE, HOLE)); p.SetDrillSize(V(HOLE, HOLE)); p.SetLayerSet(p.UnplatedHoleMask())
            p.SetPosition(V(x, y0 + i * PITCH)); fp.Add(p)
b.Save(dst)
print(f'{len(TABS)} tabs between x {xl} and {xr}, {n} holes per edge per tab')
