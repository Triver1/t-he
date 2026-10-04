#!/bin/sh
# Writes the JLCPCB order files for the board into production/: THE_gerbers.zip (Gerbers and drill) and the
# unzipped files. Run it once both halves are routed and DRC reports no unconnected items. The file holds both
# halves side by side, so one order of 5 gives 5 left and 5 right boards.
# Settings follow JLCPCB's KiCad guide: Protel extensions, solder mask subtracted from silkscreen, one Excellon file
# for plated and unplated holes, alternate drill mode for the oval TRRS holes.
set -e; cd "$(dirname "$0")"
K() { docker run --rm -v "$PWD":/w -w /w kicad/kicad:8.0 "$@" 2>&1 | grep -vE "requested image|Debug: Adding" || true; }
rm -rf production && mkdir -p production/files
K kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask -o production/files/ totem_he.kicad_pcb >/dev/null
K kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-oval-format alternate \
  --generate-map --map-format gerberx2 -o production/files/ totem_he.kicad_pcb >/dev/null
(cd production/files && zip -q ../THE_gerbers.zip *)
ls production
