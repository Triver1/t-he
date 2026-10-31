// Open mold for the silicone foam layer between the PCB and the switch plate, cast from expanding silicone foam (e.g.
// Smooth-On Soma Foama): the foam's inverse and nothing more. A floor under the foam only, and thin walls around its
// outline and around every hole it needs (each switch housing with notches for its plate clips, the four standoffs,
// the XIAO window and the TRRS jack), all foam_t tall; inside the holes there is no floor at all.
// Pour the mixed foam in, let it rise and cure, then slice it flush with the wall tops using a long blade.
// Export: openscad -D 'part="none"' -D 'mold="mold"' -D 'side="left"' -o stl/totemhe_foam_mold_left.stl foam_mold.scad
side = "left";
mold = "mold";       // "mold" | "foam" (the cast piece, for checking) | "assembly"
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
floor_t = 1.0;
wall_t  = 1.2;   // three 0.4 mm extrusion widths

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

module mold() {
  linear_extrude(floor_t) offset(delta = wall_t) foam2d();
  linear_extrude(floor_t + foam_t) difference() { offset(delta = wall_t) foam2d(); foam2d(); }
}

side_mirror() {
  if (mold == "mold") mold();
  else if (mold == "foam") linear_extrude(foam_t) foam2d();
  else {
    color("#8a8a8e") mold();
    color("#e8e2d0", 0.6) translate([0, 0, floor_t]) linear_extrude(foam_t) foam2d();
  }
}
