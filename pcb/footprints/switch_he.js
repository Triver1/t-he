// MX-style hall-effect switch: two 1.75 mm holes for the plastic side pegs, and on the underside (B) a SOT-23
// linear hall sensor centred under the stem magnet with its 100 nF 0805 capacitor. The B pads are the sensor's
// land pattern seen from below. Pin order 1 VCC, 2 OUT, 3 GND (DRV5055, SS39ET). Two tented 0.3 mm vias take power
// to the top layer, where VCC and GND run: one right of pins 1 and 2 (VCC), one left of pin 3 (GND).
// Nets: VCC, GND, OUT (the sensor output, one net per key)
module.exports = {
  params: {
    designator: 'S',
    VCC: { type: 'net', value: 'VCC' },
    OUT: { type: 'net', value: 'OUT' },
    GND: { type: 'net', value: 'GND' },
  },
  body: p => {
    // a net left at its placeholder name (the parameter's own name) stays unconnected
    const net = n => ["VCC", "OUT", "GND"].includes(n.name) ? '' : n.str
    return `
  (footprint "totemhe:switch_he"
    (layer "F.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 5.6 ${p.r}) (layer "B.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (pad "" np_thru_hole circle (at -5.08 0 ${p.r}) (size 1.75 1.75) (drill 1.75) (layers "*.Cu" "*.Mask"))
    (pad "" np_thru_hole circle (at 5.08 0 ${p.r}) (size 1.75 1.75) (drill 1.75) (layers "*.Cu" "*.Mask"))
    (pad "1" smd roundrect (at 1.05 -0.95 ${p.r}) (size 1.69 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.VCC)})
    (pad "2" smd roundrect (at 1.05 0.95 ${p.r}) (size 1.69 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.OUT)})
    (pad "3" thru_hole circle (at -2.2 1.9 ${p.r}) (size 0.6 0.6) (drill 0.3) (layers "*.Cu") ${net(p.GND)})
    (pad "1" thru_hole circle (at 2.5 2 ${p.r}) (size 0.6 0.6) (drill 0.3) (layers "*.Cu") ${net(p.VCC)})
    (pad "3" smd roundrect (at -1.05 0 ${p.r}) (size 1.69 0.6) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.GND)})
    (pad "C1" smd roundrect (at 0.2875 3.6 ${p.r}) (size 1.175 1.45) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.VCC)})
    (pad "C2" smd roundrect (at -1.7875 3.6 ${p.r}) (size 1.175 1.45) (layers "B.Cu" "B.Paste" "B.Mask") (roundrect_rratio 0.25) ${net(p.GND)})
    (fp_poly (pts (xy -7 -7) (xy 7 -7) (xy 7 7) (xy -7 7)) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS"))
    (fp_line (start -0.75 -1.6) (end 0.75 -1.6) (stroke (width 0.15) (type solid)) (layer "B.SilkS"))
    (fp_line (start 0.75 -1.6) (end 1.9 -1.6) (stroke (width 0.15) (type solid)) (layer "B.SilkS"))
    (fp_line (start -0.75 1.6) (end 0.75 1.6) (stroke (width 0.15) (type solid)) (layer "B.SilkS"))
    (fp_rect (start -2.7 2.5) (end 1.2 4.7) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS"))
    (fp_poly (pts (xy 1.1 2.6) (xy -2.6 2.6) (xy -2.6 4.6) (xy 1.1 4.6)) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
    (fp_poly (pts (xy 2.05 -1.7) (xy -2.05 -1.7) (xy -2.05 1.7) (xy 2.05 1.7)) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
  )`
  }
}
