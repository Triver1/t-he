#!/bin/bash
# Generates the board: gen_config.py writes config.yaml from the case geometry and mux_map.json, Ergogen builds both
# halves from it and footprints/, finish.py renumbers the right half and adds the board text, set_edge.py adds the
# outlines from the case, art.py draws the top silkscreen field lines, then the design rules, the routing from
# routes.py, the checks and the PCB mock's part list.
# Usage: ./build.sh [out.kicad_pcb]  (default totem_he.kicad_pcb, which this replaces)
set -eo pipefail
cd "$(dirname "$0")"
OUT=${1:-totem_he.kicad_pcb}
D() { docker run --rm "$@" 2>&1 | { grep -vE "requested image|Debug: Adding|memory leak" || true; }; }
python3 gen_config.py
rm -rf out
D -v "$PWD":/w -w /w node:20 sh -c "npm i -g ergogen@4.2.1 >/dev/null 2>&1 && ergogen . -o out | tail -1"
D -v "$PWD":/w -w /w kicad/kicad:8.0 python3 finish.py out/pcbs/totem_he.kicad_pcb out/finished.kicad_pcb
D -v "$PWD/..":/w -w /w/case openscad/openscad:latest openscad -D 'part="pcb"' -o /w/pcb/out/pcb2d.svg totem_he_case.scad
python3 set_edge.py out/pcb2d.svg out/finished.kicad_pcb "$OUT"
D -v "$PWD":/w -w /w kicad/kicad:8.0 python3 art.py "$OUT"
python3 mkpro.py "$OUT"
BOARD="$OUT" ./r dump >/dev/null && python3 routes.py >/dev/null && BOARD="$OUT" ./r batch out/routes.txt | tail -1
BOARD="$OUT" ./r drc | head -1
python3 netcheck.py "$OUT" | tail -1
python3 gen_mock.py
