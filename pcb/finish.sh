#!/bin/sh
# usage: finish.sh <side>   after Freerouting wrote routed/<side>.ses
set -e; cd "$(dirname "$0")"; s=$1
K() { docker run --rm -v "$PWD":/w -w /w kicad/kicad:8.0 "$@" 2>&1 | grep -v "requested image" || true; }
K python3 route.py finish routed/${s}_prep.kicad_pcb routed/$s.ses routed/${s}_imported.kicad_pcb
python3 addzones.py routed/${s}_imported.kicad_pcb routed/${s}_zoned.kicad_pcb
K python3 route.py fill routed/${s}_zoned.kicad_pcb - routed/totem_he_$s.kicad_pcb
python3 mkpro.py routed/totem_he_$s.kicad_pcb
K sh -c "kicad-cli pcb drc --severity-all -o routed/drc_$s.txt routed/totem_he_$s.kicad_pcb >/dev/null 2>&1; kicad-cli pcb export svg --layers 'F.Cu,B.Cu,F.SilkS,Edge.Cuts' --page-size-mode 2 --exclude-drawing-sheet -o routed/routed_$s.svg routed/totem_he_$s.kicad_pcb >/dev/null 2>&1"
echo "$s DRC: $(grep -o '^\[[a-z_]*\]' routed/drc_$s.txt | sort | uniq -c | tr '\n' ' ')"
