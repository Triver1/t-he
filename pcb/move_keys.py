"""Moves every switch footprint to its position in ../case/totem_geometry.scad and prints what moved.

Each switch is matched to the nearest key in the geometry file; rotation is left as it is. Board coordinates are
the geometry's with y flipped for the left half, and mirrored about halves.AXIS_X for the right. Moving a switch
moves its sensor and capacitor with it; reroute what it touches afterwards.
Runs inside the KiCad container. Usage: move_keys.py <in.kicad_pcb> <out.kicad_pcb>
"""
import math
import re
import sys

import pcbnew
from pcbnew import FromMM, ToMM
from halves import AXIS_X

src, dst = sys.argv[1:3]
geo = open('../case/totem_geometry.scad').read()
keys = [(float(x), float(y)) for x, y in re.findall(r'\[([-\d.]+), ([-\d.]+), [-\d.]+, [01]\]',
                                                     re.search(r'totem_keys = \[(.*?)\];', geo, re.S)[1])]
targets = [(x, -y) for x, y in keys] + [(2 * AXIS_X - x, -y) for x, y in keys]

board = pcbnew.LoadBoard(src)
used = set()
for f in board.GetFootprints():
    if not f.GetFPIDAsString().endswith('switch_he'):
        continue
    p = (ToMM(f.GetPosition().x), ToMM(f.GetPosition().y))
    i = min(range(len(targets)), key=lambda i: math.dist(p, targets[i]))
    assert i not in used and math.dist(p, targets[i]) < 5, f'{f.GetReference()} has no key of its own near {p}'
    used.add(i)
    d = math.dist(p, targets[i])
    if d > 0.001:
        f.SetPosition(pcbnew.VECTOR2I(FromMM(targets[i][0]), FromMM(targets[i][1])))
        print(f'{f.GetReference()}: ({p[0]:.3f}, {p[1]:.3f}) -> ({targets[i][0]:.3f}, {targets[i][1]:.3f}), {d:.2f} mm')
assert len(used) == len(targets), f'{len(used)} switches for {len(targets)} keys'
board.Save(dst)
