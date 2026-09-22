"""Writes the KiCad project file that holds the design rules DRC uses. Usage: mkpro.py <board.kicad_pcb>"""
import json, sys, os
pcb = sys.argv[1]; name = os.path.basename(pcb)[:-len('.kicad_pcb')]
pro = {
  "board": {"design_settings": {
    "rules": {"min_clearance": 0.2, "min_copper_edge_clearance": 0.25, "min_track_width": 0.2, "min_via_diameter": 0.6,
              "min_through_hole_diameter": 0.3, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25, "min_via_annular_width": 0.13,
              "min_text_height": 0.5, "min_text_thickness": 0.08, "min_silk_clearance": 0.0, "solder_mask_min_width": 0.0},
    "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore"}}},
  "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
                                 "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                                 "bus_width": 12, "line_style": 0, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
                   "meta": {"version": 3}},
  "meta": {"filename": name + ".kicad_pro", "version": 1}}
json.dump(pro, open(pcb[:-len('.kicad_pcb')] + '.kicad_pro', 'w'), indent=2)
print('wrote', name + '.kicad_pro')
