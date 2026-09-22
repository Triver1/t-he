// MX-style hall-effect switch (Gateron KS-20 class): no pins, two 1.75 mm leg holes, and a SOT-23
// linear hall sensor under the stem magnet with its 100 nF 0805 cap next to it, both on the switch side.
// Cap and sensor positions follow Boardloaf-HE (byungyoonc's TrueStrike42 footprint), which sit inside
// the housing's bottom recess. Pin order is the SLSS49E-3 datasheet's SOT-23 assignment: 1 VDD, 2 GND, 3 Vout.
// (Boardloaf-HE's KiCad symbol has pins 2 and 3 the other way round.)
//
// Nets: VCC, GND, OUT (the sensor output, one net per key)
// Params: side (F), sensor_pins ('VCC,GND,OUT' for pads 1,2,3), include_cap (true), leg_hole (1.75)
module.exports = {
  params: {
    designator: 'S',
    side: 'F',
    sensor_pins: 'VCC,GND,OUT',
    include_cap: true,
    leg_hole: 1.75,
    VCC: { type: 'net', value: 'VCC' },
    GND: { type: 'net', value: 'GND' },
    OUT: { type: 'net', value: 'OUT' },
  },
  body: p => {
    const nets = p.sensor_pins.split(',').map(n => p[n.trim()])
    const L = p.side
    const pad = (n, x, y, w, h, net) => `
    (pad "${n}" smd roundrect (at ${x} ${y} ${p.r}) (size ${w} ${h}) (layers "${L}.Cu" "${L}.Paste" "${L}.Mask") (roundrect_rratio 0.25) ${net.str})`
    let s = `
  (footprint "totemhe:switch_he"
    (layer "${L}.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 -7.6 ${p.r}) (layer "${L}.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15))))
    (fp_rect (start -7 -7) (end 7 7) (layer "Dwgs.User") (stroke (width 0.1) (type solid)) (fill none))
    (fp_rect (start -2.05 -1.7) (end 2.05 1.7) (layer "${L}.CrtYd") (stroke (width 0.05) (type solid)) (fill none))
    (pad "" np_thru_hole circle (at -5.08 0 ${p.r}) (size ${p.leg_hole} ${p.leg_hole}) (drill ${p.leg_hole}) (layers "*.Cu" "*.Mask"))
    (pad "" np_thru_hole circle (at 5.08 0 ${p.r}) (size ${p.leg_hole} ${p.leg_hole}) (drill ${p.leg_hole}) (layers "*.Cu" "*.Mask"))
    ${pad(1, -1.1375, -0.95, 1.325, 0.6, nets[0])}
    ${pad(2, -1.1375, 0.95, 1.325, 0.6, nets[1])}
    ${pad(3, 1.1375, 0, 1.325, 0.6, nets[2])}`
    if (p.include_cap) s += `
    (fp_rect (start -1.1 2.6) (end 2.6 4.6) (layer "${L}.CrtYd") (stroke (width 0.05) (type solid)) (fill none))
    ${pad('C1', -0.2875, 3.6, 1.175, 1.45, p.VCC)}
    ${pad('C2', 1.7875, 3.6, 1.175, 1.45, p.GND)}`
    return s + `
  )`
  }
}
