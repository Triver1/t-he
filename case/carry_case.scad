// Carrying case: a frame shaped like the keyboard outline, open at both faces, with a push-in lid on each.
// The left half goes in from below keycaps-up, the right half from above upside down; turned over, the right half's
// outline is the left's, so one pocket fits both. A ledge runs around the main block's deck: each half's deck chamfer
// seats against a 45 degree wedge, the two wedges mirrored about the frame's mid height so both halves centre
// themselves, and the keycaps reach through the opening to face each other gap_t apart, whichever way the case is
// held. A lip under each lid plugs into the frame in the space below the half, clear of its feet; ribs on the lip
// squash against the wall to hold the lid, and a fingernail slot at each side lifts it off. Closed, the lid compresses
// the half's rubber feet by squeeze against the wedge. The top lid is engraved with the name, the bottom one with the
// cat. The frame prints upright as modelled, the lids outside face down; no supports.
// Fit test: case_part="fit_test" prints three corners of a lid, one per lip_clear in fit_clears; try them on the
// frame's top tab, then set lip_clear to the one that grips.
// Texture: export lid2d() as an SVG, then run wall_waves.py outline.svg wall_waves.scad
// Export: openscad --enable=roof -D 'part="none"' -D 'case_part="frame"'      -o stl/totemhe_carry_frame.stl carry_case.scad
//         openscad --enable=roof -D 'part="none"' -D 'case_part="lid_top"'    -o stl/totemhe_carry_lid_top.stl carry_case.scad
//         openscad --enable=roof -D 'part="none"' -D 'case_part="lid_bottom"' -o stl/totemhe_carry_lid_bottom.stl carry_case.scad
//         openscad --enable=roof -D 'part="none"' -D 'case_part="fit_test"'   -o stl/totemhe_carry_fit_test.stl carry_case.scad
case_part = "assembly";   // "frame" | "lid_top" | "lid_bottom" | "fit_test" | "assembly"
include <totem_he_case.scad>
use <cat.scad>
use <wall_waves.scad>

/* [Keyboard] */
bumper_h = 3.0;    // rubber feet under the PCB
keycap_h = 19.0;   // plate top to the top of the tallest keycap; measure it, profiles differ by several mm
squeeze  = 0.2;    // the lids compress the feet this much

/* [Case] */
fit        = 0.8;   // clearance around each half
gap_t      = 1.5;   // between the two halves' keycap tops
cap_clear  = 0.3;   // ledge opening beyond the deck's keycap pockets
ledge_w    = 4.5;   // height of the lower wedge, also the reach of its 45 degree underside
wedge_r    = 2.4;   // reach of the upper wedge, which needs a 45 degree face on both sides to print without supports
wall_t     = 2.4;
lid_t      = 2.0;
engrave    = 0.6;
texture    = true;   // thin wave lines on the outside, from wall_waves.py

/* [Lid lip] */
lip_clear  = 0.15;              // lip to frame wall
lip_h      = 2.5;               // stops short of the half's underside, z_feet
lip_t      = 1.5;
lead_in    = 0.3;               // the lip's tip is this much narrower, to find the opening
rib_h      = 0.25;              // past lip_clear, so a rib squashes rib_h - lip_clear against the wall
rib_w      = 1.0;
rib_pitch  = 20;
slot_h     = 0.8;               // fingernail slot in the lid's inner face
slot_y     = [-38, -22];
fit_clears = [0.10, 0.15, 0.20];

z_feet  = bumper_h - squeeze;                               // lower half's PCB bottom above the bottom face
z_deck1 = z_feet + z_top;                                   // lower half's deck, facing up
z_caps  = z_feet + z_plate_top + keycap_h;                  // lower half's keycap tops
z_deck2 = z_caps + gap_t + keycap_h - deck_above_plate;     // upper half's deck, facing down
frame_h = z_deck2 + z_top + z_feet;
z_slope = z_deck1 - chamfer - fit;                          // the lower band's underside, on the deck chamfer

module footprint2d() union() { outline2d(); wing_tucked2d(); }
module pocket2d() offset(delta = fit) footprint2d();
module lid2d() offset(r = wall_t) pocket2d();
// over the deck only: clear of the keycap pockets and of the thumb wing, which sits lower at plate level
module ledge2d() offset(delta = 0.8) offset(delta = -0.8) difference() {
  pocket2d();
  offset(delta = cap_clear) key_field2d();
  offset(delta = 0.5) wing2d();
}
// the lower half's seat: flat on top, its underside rising 45 degrees inwards from the wall
module wedge_lower() difference() {
  translate([0, 0, z_slope]) linear_extrude(ledge_w) ledge2d();
  translate([0, 0, z_slope - eps]) roof() pocket2d();
}
// the lower seat mirrored about mid height, its top falling 45 degrees inwards, with a 45 degree underside to a 0.6 tip
module wedge_upper() {
  z1 = frame_h - z_slope;
  z0 = z1 - 2 * wedge_r - 0.6;
  difference() {
    translate([0, 0, z0]) linear_extrude(z1 - z0) ledge2d();
    translate([0, 0, z0 - eps]) roof() pocket2d();
    translate([0, 0, z1 + eps]) mirror([0, 0, 1]) roof() pocket2d();
  }
}

module frame() difference() {
  union() {
    linear_extrude(frame_h) difference() { lid2d(); pocket2d(); }
    wedge_lower();
    wedge_upper();
  }
  if (texture) wall_waves();
}

// diagonal stripes cut the ribs out of a ring around the lip, so every wall gets some whatever its direction
// the extra stripe gives the two short walls of the frame's top tab a rib each, for the fit test
module rib_stripes2d() {
  rotate(37) for (i = [-20 : 20]) translate([i * rib_pitch, -300]) square([rib_w, 600]);
  translate([-300, 0]) square([600, rib_w]);
}
// rises from z 0, the lid's inner face
module lip(clear) {
  linear_extrude(lip_h - lead_in) difference() { offset(delta = -clear) pocket2d(); offset(delta = -clear - lip_t) pocket2d(); }
  translate([0, 0, lip_h - lead_in]) linear_extrude(lead_in) difference() { offset(delta = -clear - lead_in) pocket2d(); offset(delta = -clear - lip_t) pocket2d(); }
  linear_extrude(lip_h - lead_in - 0.4) intersection() {
    difference() { offset(delta = rib_h - clear) pocket2d(); offset(delta = -clear - 0.1) pocket2d(); }
    rib_stripes2d();
  }
}
// across the wall on both long sides, stopping short of the pocket so the lip stays whole
module nail_slots() for (x = [[inner_x() + fit + 0.8, inner_x() + fit + wall_t + 1], [-2, 8.2 - fit - 0.8]])
  translate([x[0], slot_y[0], -slot_h]) cube([x[1] - x[0], slot_y[1] - slot_y[0], slot_h + eps]);
// inner face at z 0, lip upwards, outer face at -lid_t; lid() turns it to fit each face of the frame
module lid_body(clear = lip_clear) {
  difference() {
    translate([0, 0, -lid_t]) linear_extrude(lid_t) lid2d();
    nail_slots();
  }
  lip(clear);
}
module lid(top) difference() {
  translate([0, 0, top ? frame_h : 0]) mirror([0, 0, top ? 1 : 0]) lid_body();
  translate([0, 0, top ? frame_h + lid_t - engrave : -lid_t - eps]) linear_extrude(engrave + eps) lid_art(top);
}
module lid_art(top) translate([66, 0]) if (top) {
  translate([0, -42]) text("Tot-HE-m", size = 13, font = "DejaVu Sans:style=Bold", halign = "center", valign = "center");
  translate([0, -56]) text("hall effect split", size = 5, font = "DejaVu Sans", halign = "center", valign = "center");
} else mirror([1, 0, 0]) translate([0, -45]) scale(45) cat2d();   // read from below

if (case_part == "frame") frame();
else if (case_part == "lid_top") rotate([180, 0, 0]) translate([0, 0, -frame_h - lid_t]) lid(true);
else if (case_part == "lid_bottom") translate([0, 0, lid_t]) lid(false);
else if (case_part == "fit_test") for (i = [0 : len(fit_clears) - 1]) translate([0, i * 22, lid_t]) difference() {
  intersection() { lid_body(fit_clears[i]); translate([48, -10, -lid_t - 1]) cube([41, 19, 10]); }
  translate([68, -5, -lid_t - eps]) linear_extrude(engrave + eps) mirror([1, 0, 0]) text(str(round(fit_clears[i] * 100)), size = 5, font = "DejaVu Sans:style=Bold", halign = "center", valign = "center");
}
else if (case_part == "assembly") { color("#6a5acd") frame(); color("#8a7ae0") { lid(true); lid(false); } }
