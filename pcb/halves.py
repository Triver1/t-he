"""Where the right half sits in totem_he.kicad_pcb, which holds both halves side by side for one order.

The right half is the left mirrored about x = AXIS_X (mm, board coordinates), with each footprint turned to minus
its angle but not mirrored, so every part keeps its land pattern. Its references are the left's plus RIGHT_REF
(S101 is S1's twin), and every net carries its half's prefix (L/VCC, R/VCC) so the halves stay separate.
"""
BOARD_W = 129.867                         # the left outline spans x 0 to this
GAP = 5.0                                 # between the two inner edges, for JLCPCB's routing cutter
AXIS_X = BOARD_W + GAP / 2
RIGHT_REF = 100
PREFIX = {'left': 'L/', 'right': 'R/'}
