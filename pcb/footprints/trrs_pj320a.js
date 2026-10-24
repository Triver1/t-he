// PJ-320A 3.5 mm TRRS jack, through-hole. Pads 2 (sleeve), 3 (ring 2) and 4 (tip, slotted so it also takes the
// ring 1 leg) in two mirrored columns, so the jack fits either way round. Based on ceoloide/ergogen-footprints
// (MIT, see LICENSE).
// Nets: TP (tip), R2 (ring 2), SL (sleeve)
module.exports = {
  params: {
    designator: 'TRRS',
    SL: { type: 'net', value: 'SL' },
    R2: { type: 'net', value: 'R2' },
    TP: { type: 'net', value: 'TP' },
  },
  body: p => {
    // a net left at its placeholder name (the parameter's own name) stays unconnected
    const net = n => ["SL", "R2", "TP"].includes(n.name) ? '' : n.str
    return `
  (footprint "totemhe:trrs_pj320a"
    (layer "F.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 14.6 ${p.r}) (layer "F.SilkS") ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15))))
    (pad "" np_thru_hole circle (at 0 1.6 ${p.r}) (size 1.5 1.5) (drill 1.5) (layers "*.Cu" "*.Mask"))
    (pad "" np_thru_hole circle (at 0 8.6 ${p.r}) (size 1.5 1.5) (drill 1.5) (layers "*.Cu" "*.Mask"))
    (pad "2" thru_hole oval (at -2.3 3.2 ${p.r}) (size 1.6 2.2) (drill oval 0.9 1.5) (layers "*.Cu" "*.Mask") ${net(p.SL)})
    (pad "2" thru_hole oval (at 2.3 3.2 ${p.r}) (size 1.6 2.2) (drill oval 0.9 1.5) (layers "*.Cu" "*.Mask") ${net(p.SL)})
    (pad "3" thru_hole oval (at -2.3 6.2 ${p.r}) (size 1.6 2.2) (drill oval 0.9 1.5) (layers "*.Cu" "*.Mask") ${net(p.R2)})
    (pad "3" thru_hole oval (at 2.3 6.2 ${p.r}) (size 1.6 2.2) (drill oval 0.9 1.5) (layers "*.Cu" "*.Mask") ${net(p.R2)})
    (pad "4" thru_hole oval (at -2.3 10.75 ${p.r}) (size 1.6 3.3) (drill oval 0.9 2.6) (layers "*.Cu" "*.Mask") ${net(p.TP)})
    (pad "4" thru_hole oval (at 2.3 10.75 ${p.r}) (size 1.6 3.3) (drill oval 0.9 2.6) (layers "*.Cu" "*.Mask") ${net(p.TP)})
    (fp_line (start -3.4 0.6) (end -3.4 12.9) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
    (fp_line (start 3.4 0.6) (end 3.4 12.9) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
    (fp_line (start -3.4 12.9) (end 3.4 12.9) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  )`
  }
}
