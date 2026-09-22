// Seeed XIAO RP2040 on top of the board like TOTEM's, its castellations soldered flat to oval pads that reach
// 0.1 mm past its edge. No cutout: the RP2040 XIAO has nothing on its underside. USB-C is at the top (local -y).
// Pads 1-7 are D0-D6 down the left side, 8-14 are D7, D8, D9, D10, 3V3, GND, 5V up the right side.
module.exports = {
  params: {
    designator: 'MCU',
    side: 'F',
    D0: { type: 'net', value: 'D0' }, D1: { type: 'net', value: 'D1' }, D2: { type: 'net', value: 'D2' }, D3: { type: 'net', value: 'D3' },
    D4: { type: 'net', value: 'D4' }, D5: { type: 'net', value: 'D5' }, D6: { type: 'net', value: 'D6' }, D7: { type: 'net', value: 'D7' },
    D8: { type: 'net', value: 'D8' }, D9: { type: 'net', value: 'D9' }, D10: { type: 'net', value: 'D10' },
    V3: { type: 'net', value: 'V3' }, GND: { type: 'net', value: 'GND' }, V5: { type: 'net', value: 'V5' },
  },
  body: p => {
    const L = p.side
    // a pin left at its placeholder name (D3, V5, ...) gets no net, so KiCad shows it unconnected
    const net = n => /^(D\d+|V5|V3)$/.test(n.name) ? '' : n.str
    const left = [p.D0, p.D1, p.D2, p.D3, p.D4, p.D5, p.D6], right = [p.D7, p.D8, p.D9, p.D10, p.V3, p.GND, p.V5]
    const labels = ['D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', '3V3', 'GND', '5V']
    let pads = ''
    for (let i = 0; i < 7; i++) {
      const y = -7.62 + 2.54 * i
      pads += `
    (pad "${i + 1}" thru_hole oval (at -7.62 ${y} ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(left[i])})
    (pad "${14 - i}" thru_hole oval (at 7.62 ${y} ${p.r}) (size 2.75 1.8) (drill 1) (layers "*.Cu" "*.Mask") ${net(right[6 - i])})
    (fp_text user "${labels[i]}" (at -4.4 ${y} ${p.r}) (layer "${L}.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1)) (justify right)))
    (fp_text user "${labels[13 - i]}" (at 4.4 ${y} ${p.r}) (layer "${L}.SilkS") (effects (font (size 0.6 0.6) (thickness 0.1)) (justify left)))`
    }
    return `
  (footprint "totemhe:xiao_rp2040"
    (layer "${L}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 -10.2 ${p.r}) (layer "${L}.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15))))
    (fp_rect (start -8.9 -10.5) (end 8.9 10.5) (layer "Dwgs.User") (stroke (width 0.12) (type solid)) (fill none))
    (fp_rect (start -4.5 -10.5) (end 4.5 -7.3) (layer "Dwgs.User") (stroke (width 0.12) (type solid)) (fill none))
    (fp_rect (start -9.4 -11) (end 9.4 11) (layer "${L}.CrtYd") (stroke (width 0.05) (type solid)) (fill none))${pads}
  )`
  }
}
