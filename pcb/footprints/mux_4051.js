// 74HC4051 8-channel analog mux, SOIC-16 on the underside (B), with its 100 nF 0805 capacitor next to pin 16 (VCC).
// Pins 6-8 (E, VEE, GND) share a copper strip. Its power vias are placed in routes.py, next to the power rails.
// Nets: VCC, GND, Z (common, to an ADC pin), S0-S2, Y0-Y7 (channel inputs; a channel left at its own name is unused)
module.exports = {
  params: {
    designator: 'IC',
    VCC: { type: 'net', value: 'VCC' },
    GND: { type: 'net', value: 'GND' },
    Z: { type: 'net', value: 'Z' },
    S0: { type: 'net', value: 'S0' },
    S1: { type: 'net', value: 'S1' },
    S2: { type: 'net', value: 'S2' },
    Y0: { type: 'net', value: 'Y0' },
    Y1: { type: 'net', value: 'Y1' },
    Y2: { type: 'net', value: 'Y2' },
    Y3: { type: 'net', value: 'Y3' },
    Y4: { type: 'net', value: 'Y4' },
    Y5: { type: 'net', value: 'Y5' },
    Y6: { type: 'net', value: 'Y6' },
    Y7: { type: 'net', value: 'Y7' },
  },
  body: p => {
    // a net left at its placeholder name (the parameter's own name) stays unconnected
    const net = n => ["VCC", "GND", "Z", "S0", "S1", "S2", "Y0", "Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7"].includes(n.name) ? '' : n.str
    return `
  (footprint "totemhe:mux_4051"
    (layer "F.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0.55 0 ${p.r + 90}) (layer "B.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (pad "1" smd roundrect (at -2.7 4.445 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y4)})
    (pad "2" smd roundrect (at -2.7 3.175 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y6)})
    (pad "3" smd roundrect (at -2.7 1.905 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Z)})
    (pad "4" smd roundrect (at -2.7 0.635 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y7)})
    (pad "5" smd roundrect (at -2.7 -0.635 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y5)})
    (pad "6" smd roundrect (at -2.7 -1.905 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.GND)})
    (pad "7" smd roundrect (at -2.7 -3.175 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.GND)})
    (pad "8" smd roundrect (at -2.7 -4.445 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.GND)})
    (pad "8" smd rect (at -2.7 -3.175 ${p.r}) (size 2.4 3.14) (layers "B.Cu") ${net(p.GND)})
    (pad "9" smd roundrect (at 2.7 -4.445 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.S2)})
    (pad "10" smd roundrect (at 2.7 -3.175 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.S1)})
    (pad "11" smd roundrect (at 2.7 -1.905 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.S0)})
    (pad "12" smd roundrect (at 2.7 -0.635 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y3)})
    (pad "13" smd roundrect (at 2.7 0.635 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y0)})
    (pad "14" smd roundrect (at 2.7 1.905 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y1)})
    (pad "15" smd roundrect (at 2.7 3.175 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.Y2)})
    (pad "16" smd roundrect (at 2.7 4.445 ${p.r}) (size 2.4 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.VCC)})
    (pad "C1" smd roundrect (at 1.0375 7.35 ${p.r}) (size 1.175 1.45) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.VCC)})
    (pad "C2" smd roundrect (at -1.0375 7.35 ${p.r}) (size 1.175 1.45) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.GND)})
    (fp_line (start -1.95 5.2) (end -3.7 5.2) (stroke (width 0.15) (type solid)) (layer "B.SilkS"))
    (fp_circle (center -1.2 3.9) (end -0.9 3.9) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS"))
    (fp_line (start -1.95 5.2) (end 1.95 5.2) (stroke (width 0.15) (type solid)) (layer "B.SilkS"))
    (fp_line (start -1.95 -5.2) (end 1.95 -5.2) (stroke (width 0.15) (type solid)) (layer "B.SilkS"))
    (fp_rect (start -2.05 6.25) (end 2.05 8.45) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS"))
    (fp_rect (start -1.9 8.35) (end 1.9 6.35) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
    (fp_rect (start -4.1 5.2) (end 4.1 -5.2) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
    (fp_rect (start -1.95 4.95) (end 1.95 -4.95) (stroke (width 0.1) (type solid)) (fill none) (layer "B.Fab"))
  )`
  }
}
