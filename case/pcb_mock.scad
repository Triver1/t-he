// Fit-test mock of the HE PCB: the board with every component as a block, sized from the datasheets.
// Print it and drop it into the shell and plate to check clearances before ordering boards. Part positions come from
// mock_parts.scad (gen_mock.py): the XIAO and TRRS jack on the switch side, the sensors, capacitors and muxes underneath.
// Export: openscad -D 'part="none"' -D 'side="left"' -o stl/totemhe_pcbmock_left.stl pcb_mock.scad
side = "left";
include <totem_he_case.scad>
include <mock_parts.scad>

module block(size, z0 = 0) translate([-size[0] / 2, -size[1] / 2, z0]) cube(size);
// underside parts: mirrored the way the board's B pads are (left-right about the part's position), built downward
module under(p) translate([p[1], p[2], z_pcb_bot + 0.05]) mirror([0, 0, 1]) mirror([1, 0, 0]) rotate(p[3]) children();
module part(p) {
  if (p[0] == "switch_he" || p[0] == "mux_4051") under(p) {
    if (p[0] == "switch_he") {
      block([2.9, 1.3, 1.1]);                                    // SOT-23 body, y is the switch's front
      translate([0.75, -3.6, 0]) block([2.0, 1.25, 0.9]);          // 0805 cap; KiCad local y is down, so flipped here
    } else if (p[0] == "mux_4051") {
      block([3.9, 9.9, 1.75]); block([6.0, 9.9, 0.3]);            // SOIC-16 body and lead span
      translate([0, 7.35, 0]) block([2.0, 1.25, 0.9]);
    }
  }
  else translate([p[1], p[2], z_pcb_top - 0.05]) rotate(p[3]) {   // sunk a hair into the board so the union has no coincident faces
    if (p[0] == "xiao_rp2040") {
      block([21.0, 17.8, xiao_t]);                                 // XIAO board on the PCB top
      translate([0, 7.3, xiao_t]) block([8.9, 7.35, 3.2]);         // USB-C, overhangs the board edge by 1.3
      translate([0, -2.5, xiao_t]) block([7.0, 7.0, 1.0]);         // RP2040 + shielding area
    } else if (p[0] == "trrs_pj320a") {
      translate([0, -6.0, 0]) block([6.0, 12.0, 5.0]);            // body behind the mouth
      translate([0, 1.0, 2.5]) rotate([90, 0, 0]) cylinder(d = 5.0, h = 2.2, center = true);
    }
  }
}
side_mirror() union() {
  translate([0, 0, z_pcb_bot]) linear_extrude(pcb_t) pcb2d();
  for (p = mock_parts) part(p);
}
