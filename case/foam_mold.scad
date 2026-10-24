// Two-part mold for the silicone foam layer between the PCB and the switch plate, cast from expanding silicone
// foam (e.g. Smooth-On Soma Foama). The base is a tray in the foam's outline with an island for every hole the foam
// needs: each switch housing (with notches for its plate clips), the four standoffs, the XIAO window and the TRRS
// jack. The lid rests on the islands, so the holes come out clean and the foam exactly foam_t thick; the foam's
// overflow leaves through the vents. Pins on the standoff islands locate the lid.
// Pour the mixed foam into the base, put the lid on, clamp or weigh it down, let it cure, then trim the vent sprues.
// Export: openscad -D 'part="none"' -D 'mold="base"' -D 'side="left"' -o stl/totemhe_foam_mold_base_left.stl foam_mold.scad
//         openscad -D 'part="none"' -D 'mold="lid"'  -D 'side="left"' -o stl/totemhe_foam_mold_lid_left.stl foam_mold.scad
side = "left";
mold = "base";       // "base" | "lid" | "foam" (the cast piece, for checking) | "assembly"
include <totem_he_case.scad>

/* [Foam] */
gap         = plate_above_pcb - plate_t;   // PCB top to plate underside, 3.5 mm
squeeze     = 0.3;                         // extra thickness, so the plate compresses the foam slightly
foam_t      = gap + squeeze;
edge_inset  = 0.3;                         // foam edge inside the PCB edge
sw_hole     = switch_cut + 0.4;            // switch bottom housing below the plate
clip_w      = 6.0;                         // MX top-housing clips, under the plate on the switch's north and south sides
clip_reach  = sw_hole / 2 + 0.8;
standoff_hole = standoff_d + 0.8;
min_web     = 0.8;

/* [Mold] */
floor_t   = 2.0;
mold_wall = 6.0;
lid_t     = 4.0;
pin_d     = 2.4;
pin_h     = 3.0;
vent_d    = 2.0;
vent_pitch = 14.0;

module switch_hole2d() {
  square(sw_hole, center = true);
  for (s = [-1, 1]) translate([0, s * clip_reach / 2]) square([clip_w, clip_reach], center = true);
}
module outline2d() { offset(delta = -edge_inset) pcb2d(); }
// drops strips narrower than 2 * min_web (the edge beside the XIAO window and the jack), which would tear on demoulding
module foam2d() {
  offset(delta = min_web) offset(delta = -min_web) difference() {
    outline2d();
    for (k = totem_keys) at_key(k) switch_hole2d();
    for (h = totem_holes) translate(h) circle(d = standoff_hole);
    translate(totem_xiao) square([xiao[0] + 3, xiao[1] + 3], center = true);   // the plate's XIAO window
    offset(delta = 0.3) trrs_pocket2d();                                         // the plate's TRRS cutout
  }
}

module base() {
  difference() {
    linear_extrude(floor_t + foam_t) offset(delta = mold_wall) outline2d();
    translate([0, 0, floor_t]) linear_extrude(foam_t + 1) foam2d();
  }
  for (h = totem_holes) translate([h[0], h[1], floor_t + foam_t - eps]) cylinder(d = pin_d, h = pin_h);
}
module vents2d() {
  intersection() {
    offset(delta = -1) foam2d();
    for (x = [-10 : vent_pitch : 160], y = [-120 : vent_pitch : 10]) translate([x, y]) circle(d = vent_d);
  }
}
module lid() {
  difference() {
    linear_extrude(lid_t) offset(delta = mold_wall) outline2d();
    translate([0, 0, -1]) linear_extrude(lid_t + 2) vents2d();
    for (h = totem_holes) translate([h[0], h[1], -1]) cylinder(d = pin_d + 0.4, h = lid_t + 2);
  }
}

side_mirror() {
  if (mold == "base") base();
  else if (mold == "lid") lid();                            // prints as it is, flat side down
  else if (mold == "foam") linear_extrude(foam_t) foam2d();
  else {
    color("#8a8a8e") base();
    color("#e8e2d0", 0.6) translate([0, 0, floor_t]) linear_extrude(foam_t) foam2d();
    color("#4a6fa5", 0.5) translate([0, 0, floor_t + foam_t + 8]) lid();
  }
}
