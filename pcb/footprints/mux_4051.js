// 74HC4051 8:1 analog mux, SOIC-16 on hand-solder pads (0.45 mm longer than KiCad's), with a 100 nF 0805 cap across VCC/GND at the pin-1/16 end, on the chip's axis so it lands the same way on both halves.
// Pins: 1 Y4, 2 Y6, 3 Z (common), 4 Y7, 5 Y5, 6 E, 7 VEE, 8 GND, 9 S2, 10 S1, 11 S0, 12 Y3, 13 Y0, 14 Y1, 15 Y2, 16 VCC.
// E and VEE are tied to GND. Unused Y inputs get their own local net.
module.exports = {
  params: {
    designator: 'IC',   // 'U' would be read by Ergogen as its 19.05 mm unit
    side: 'F',
    include_cap: true,
    VCC: { type: 'net', value: 'VCC' },
    GND: { type: 'net', value: 'GND' },
    Z: { type: 'net', value: 'Z' },
    S0: { type: 'net', value: 'S0' },
    S1: { type: 'net', value: 'S1' },
    S2: { type: 'net', value: 'S2' },
    Y0: { type: 'net', value: 'Y0' }, Y1: { type: 'net', value: 'Y1' }, Y2: { type: 'net', value: 'Y2' }, Y3: { type: 'net', value: 'Y3' },
    Y4: { type: 'net', value: 'Y4' }, Y5: { type: 'net', value: 'Y5' }, Y6: { type: 'net', value: 'Y6' }, Y7: { type: 'net', value: 'Y7' },
  },
  body: p => {
    const L = p.side
    const pins = [p.Y4, p.Y6, p.Z, p.Y7, p.Y5, p.GND, p.GND, p.GND, p.S2, p.S1, p.S0, p.Y3, p.Y0, p.Y1, p.Y2, p.VCC]
    let pads = ''
    for (let i = 0; i < 16; i++) {
      const x = i < 8 ? -2.7 : 2.7, y = i < 8 ? -4.445 + 1.27 * i : 4.445 - 1.27 * (i - 8)
      pads += `
    (pad "${i + 1}" smd roundrect (at ${x} ${y} ${p.r}) (size 2.4 0.6) (layers "${L}.Cu" "${L}.Paste" "${L}.Mask") (roundrect_rratio 0.25) ${pins[i].str})`
    }
    let s = `
  (footprint "totemhe:mux_4051"
    (layer "${L}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 -6.3 ${p.r}) (layer "${L}.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15))))
    (fp_rect (start -1.95 -4.95) (end 1.95 4.95) (layer "${L}.Fab") (stroke (width 0.1) (type solid)) (fill none))
    (fp_line (start -1.95 -5.2) (end -3.7 -5.2) (layer "${L}.SilkS") (stroke (width 0.15) (type solid)))
    (fp_circle (center -1.2 -3.9) (end -0.9 -3.9) (layer "${L}.SilkS") (stroke (width 0.15) (type solid)) (fill solid))
    (fp_rect (start -4.1 -5.2) (end 4.1 5.2) (layer "${L}.CrtYd") (stroke (width 0.05) (type solid)) (fill none))${pads}`
    if (p.include_cap) s += `
    (fp_rect (start -1.9 -8.35) (end 1.9 -6.35) (layer "${L}.CrtYd") (stroke (width 0.05) (type solid)) (fill none))
    (pad "C1" smd roundrect (at -1.0375 -7.35 ${p.r}) (size 1.175 1.45) (layers "${L}.Cu" "${L}.Paste" "${L}.Mask") (roundrect_rratio 0.25) ${p.VCC.str})
    (pad "C2" smd roundrect (at 1.0375 -7.35 ${p.r}) (size 1.175 1.45) (layers "${L}.Cu" "${L}.Paste" "${L}.Mask") (roundrect_rratio 0.25) ${p.GND.str})`
    return s + `
  )`
  }
}
