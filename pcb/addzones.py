"""Appends two GND fill zones (F.Cu and B.Cu) to a .kicad_pcb as text, covering the board's bounding box.
Usage: addzones.py <in.kicad_pcb> <out.kicad_pcb>"""
import re, sys, uuid
s = open(sys.argv[1]).read()
net = re.search(r'\(net (\d+) "GND"\)', s)[1]
xs, ys = [], []
for m in re.finditer(r'\(gr_line\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(?:(?!gr_line).)*?Edge\.Cuts', s, re.S):
    xs += [float(m[1]), float(m[3])]; ys += [float(m[2]), float(m[4])]
x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
zones = ''
for layer in ('F.Cu', 'B.Cu'):
    zones += f'''
  (zone (net {net}) (net_name "GND") (layer "{layer}") (uuid "{uuid.uuid4()}") (hatch edge 0.5)
    (connect_pads (clearance 0.25))
    (min_thickness 0.25) (filled_areas_thickness no)
    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
    (polygon (pts (xy {x0} {y0}) (xy {x1} {y0}) (xy {x1} {y1}) (xy {x0} {y1})))
  )'''
i = s.rstrip().rfind(')')
open(sys.argv[2], 'w').write(s[:i] + zones + '\n)\n')
print('zones added, net', net, 'bbox', x0, y0, x1, y1)
