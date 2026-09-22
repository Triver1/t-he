"""Runs inside the KiCad container (python3 with pcbnew).
prep:   route.py prep   <in.kicad_pcb> <out.kicad_pcb> <out.dsn>   design rules for the router, Specctra export
finish: route.py finish <in.kicad_pcb> <in.ses> <out.kicad_pcb>   import the routed session
fill:   route.py fill   <in.kicad_pcb> -        <out.kicad_pcb>   fill the GND zones addzones.py appended
The rules DRC uses live in the project file, written by mkpro.py. JLCPCB 2-layer limits: 0.127 mm trace and
clearance, 0.3 mm drill. Used with margin: 0.25 mm tracks, 0.2 mm clearance, 0.6 / 0.3 vias, 0.25 mm to the edge.
"""
import sys
import pcbnew
from pcbnew import FromMM


mode, src = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)

if mode == 'prep':
    ds = board.GetDesignSettings()
    nc = ds.m_NetSettings.m_DefaultNetClass   # what the DSN export reads; VCC and GND route at this width too
    nc.SetClearance(FromMM(0.2)); nc.SetTrackWidth(FromMM(0.25)); nc.SetViaDiameter(FromMM(0.6)); nc.SetViaDrill(FromMM(0.3))
    board.Save(sys.argv[3])
    print('dsn export', pcbnew.ExportSpecctraDSN(board, sys.argv[4]))
elif mode == 'finish':
    print('ses import', pcbnew.ImportSpecctraSES(board, sys.argv[3]))
    board.Save(sys.argv[4])
else:
    # zones were appended as text by addzones.py: creating them through this API crashes in the container
    narrow = [x for x in board.GetTracks() if x.GetClass() == 'PCB_TRACK' and x.GetWidth() < FromMM(0.2)]
    for x in narrow: x.SetWidth(FromMM(0.2))   # the session import leaves a few segments at 0.187 mm; 0.2 keeps their clearance legal
    print('widened', len(narrow), 'tracks')
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(sys.argv[4])
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
    print('tracks', len(tracks), 'vias', len(vias), 'zones', board.Zones().size())
