"""Turns Ergogen's output into totem_he.kicad_pcb: renumbers the right half's parts (Ergogen counts on from the left,
S20 to S38; they become S101 to S119, so each right part is its left twin plus RIGHT_REF) and saves the board in
KiCad 8's own format. Runs inside the KiCad container. Usage: finish.py <ergogen.kicad_pcb> <out.kicad_pcb>
"""
import re
import sys
from collections import defaultdict

import pcbnew

from halves import AXIS_X, RIGHT_REF

src, dst = sys.argv[1:3]
board = pcbnew.LoadBoard(src)
right = defaultdict(list)
for fp in board.GetFootprints():
    if pcbnew.ToMM(fp.GetPosition().x) > AXIS_X:
        head, num = re.match(r'(\D+)(\d+)$', fp.GetReference()).groups()
        right[head].append((int(num), fp))
for head, fps in right.items():
    for i, (_, fp) in enumerate(sorted(fps, key=lambda t: t[0])):
        fp.SetReference(f'{head}{RIGHT_REF + 1 + i}')

# board text in the free area between the bottom row and the thumb keys (left half x 40-70, y 67-88), mirrored for the right
TOP = [('Tot-HE-m', 3.2, 0.5, -5.6), ('hall effect split', 1.2, 0.18, -2.0), ('{side}  ·  rev 1  ·  2026-10', 1.0, 0.15, 0.2)]
BOTTOM = [('Tot-HE-m  {side}  rev 1', 1.4, 0.2, 4.6),
          ('TRRS: tip 3V3  ·  ring 2 DATA  ·  sleeve GND', 1.0, 0.15, 6.4),
          ('USB on one half only  ·  plug TRRS with USB out', 1.0, 0.15, 7.8)]
for side, x in (('LEFT', 55.0), ('RIGHT', 2 * AXIS_X - 55.0)):
    for layer, lines in ((pcbnew.F_SilkS, TOP), (pcbnew.B_SilkS, BOTTOM)):
        for text, size, width, dy in lines:
            t = pcbnew.PCB_TEXT(board)
            t.SetText(text.format(side=side)); t.SetLayer(layer); t.SetMirrored(layer == pcbnew.B_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size))); t.SetTextThickness(pcbnew.FromMM(width))
            t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(76.0 + dy)))
            board.Add(t)
board.Save(dst)
print(', '.join(f'{head}: {len(fps)} right-half parts renumbered from {head}{RIGHT_REF + 1}' for head, fps in right.items()))
