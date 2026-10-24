// Plated M2 mounting hole for the case screws (2.2 mm drill). Based on ceoloide/ergogen-footprints (MIT).
module.exports = {
  params: {
    designator: 'H',
  },
  body: p => {
    // a net left at its placeholder name (the parameter's own name) stays unconnected
    const net = n => [].includes(n.name) ? '' : n.str
    return `
  (footprint "totemhe:mounting_hole_plated"
    (layer "F.Cu")
    ${p.at}
    (property "Reference" "${p.ref}" (at 0 3.7 ${p.r}) (layer "F.SilkS") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
    (pad "" thru_hole circle (at 0 0 ${p.r}) (size 3.8 3.8) (drill 2.2) (layers "*.Cu" "*.Mask"))
    (fp_circle (center 0 0) (end -2.35 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS"))
    (fp_circle (center 0 0) (end -2.15 0) (stroke (width 0.05) (type solid)) (fill none) (layer "B.CrtYd"))
    (fp_circle (center 0 0) (end -2.15 0) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
  )`
  }
}
