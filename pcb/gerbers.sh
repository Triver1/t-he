#!/bin/sh
# Fabrication files for JLCPCB: both halves joined by snap-off tabs (panel.py), Gerbers and drill files, zipped.
# Usage: ./gerbers.sh  (writes Tot-HE-m_jlcpcb_gerbers.zip)
set -e
cd "$(dirname "$0")"
rm -rf gerbers Tot-HE-m_jlcpcb_gerbers.zip && mkdir -p gerbers out
PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin" docker run --rm -v "$PWD":/w -w /w kicad/kicad:8.0 sh -c '
python3 panel.py totem_he.kicad_pcb out/panel.kicad_pcb &&
kicad-cli pcb export gerbers -o gerbers/ --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask out/panel.kicad_pcb >/dev/null &&
kicad-cli pcb export drill -o gerbers/ --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 out/panel.kicad_pcb >/dev/null' 2>&1 | grep -vE "requested image|Debug|memory leak" || true
(cd gerbers && zip -q ../Tot-HE-m_jlcpcb_gerbers.zip ./*)
ls -la Tot-HE-m_jlcpcb_gerbers.zip
