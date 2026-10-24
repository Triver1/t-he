// Seeed XIAO RP2040 on the top, soldered flat on its castellations over 1.0 mm plated holes, so every pin
// reaches both layers. USB-C toward local -y (the board edge). Pads 1-7 are D0-D6, 8-14 are D7, D8, D9, D10, 3V3, GND, 5V.
// A pin left at its own name (D3, V5, ...) gets no net.
module.exports = {
  params: {
    designator: 'MCU',
    D0: { type: 'net', value: 'D0' },
    D1: { type: 'net', value: 'D1' },
    D2: { type: 'net', value: 'D2' },
    D3: { type: 'net', value: 'D3' },
    D4: { type: 'net', value: 'D4' },
    D5: { type: 'net', value: 'D5' },
    D6: { type: 'net', value: 'D6' },
    D7: { type: 'net', value: 'D7' },
    D8: { type: 'net', value: 'D8' },
    D9: { type: 'net', value: 'D9' },
    D10: { type: 'net', value: 'D10' },
    V3: { type: 'net', value: 'V3' },
    GND: { type: 'net', value: 'GND' },
    V5: { type: 'net', value: 'V5' },
  },
  body: p => {
    // a net left at its placeholder name (the parameter's own name) stays unconnected
    const net = n => ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10", "V3", "GND", "V5"].includes(n.name) ? '' : n.str
    // underside pin labels: the net a pin carries, or its own name when unconnected
    const lab = (n, own) => net(n) ? n.name.split('/').pop() : own
    return `
  (footprint "totemhe:xiao_rp2040"
    (layer "F.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 11.7 ${p.r}) (layer "F.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" thru_hole oval (at -7.62 -7.62 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D0)})
    (pad "2" thru_hole oval (at -7.62 -5.08 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D1)})
    (pad "3" thru_hole oval (at -7.62 -2.54 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D2)})
    (pad "4" thru_hole oval (at -7.62 0 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D3)})
    (pad "5" thru_hole oval (at -7.62 2.54 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D4)})
    (pad "6" thru_hole oval (at -7.62 5.08 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D5)})
    (pad "7" thru_hole oval (at -7.62 7.62 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D6)})
    (pad "8" thru_hole oval (at 7.62 7.62 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D7)})
    (pad "9" thru_hole oval (at 7.62 5.08 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D8)})
    (pad "10" thru_hole oval (at 7.62 2.54 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D9)})
    (pad "11" thru_hole oval (at 7.62 0 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.D10)})
    (pad "12" thru_hole oval (at 7.62 -2.54 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.V3)})
    (pad "13" thru_hole oval (at 7.62 -5.08 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.GND)})
    (pad "14" thru_hole oval (at 7.62 -7.62 ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(p.V5)})
    (fp_rect (start -4.5 -10.5) (end 4.5 -7.9) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS"))
    (fp_rect (start -9.2 -10.5) (end 9.2 10.5) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS"))
    (fp_text user "USB" (at 0 -9.2 ${p.r}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
    (fp_text user "XIAO RP2040" (at 0 0 ${p.r + 90}) (layer "F.SilkS") (effects (font (size 1.2 1.2) (thickness 0.18))))
    (fp_rect (start -9.4 -11) (end 9.4 11) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
    (fp_text user "${lab(p.D0, 'D0')}" (at -3.6 -7.62 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D1, 'D1')}" (at -3.6 -5.08 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D2, 'D2')}" (at -3.6 -2.54 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D3, 'D3')}" (at -3.6 0 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D4, 'D4')}" (at -3.6 2.54 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D5, 'D5')}" (at -3.6 5.08 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D6, 'D6')}" (at -3.6 7.62 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.V5, '5V')}" (at 3.6 -7.62 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.GND, 'GND')}" (at 3.6 -5.08 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.V3, '3V3')}" (at 3.6 -2.54 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D10, 'D10')}" (at 3.6 0 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D9, 'D9')}" (at 3.6 2.54 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D8, 'D8')}" (at 3.6 5.08 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
    (fp_text user "${lab(p.D7, 'D7')}" (at 3.6 7.62 ${p.r}) (layer "B.SilkS") (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))
  )`
  }
}
