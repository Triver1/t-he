// Carrying case: a frame shaped like the keyboard outline, open at both faces, with a hinged lid on each.
// The left half goes in from below keycaps-up, the right half from above upside down; turned over, the right half's
// outline is the left's, so one pocket fits both. A ledge runs around the main block's deck: each half's deck chamfer
// seats against a 45 degree wedge, the two wedges mirrored about the frame's mid height so both halves centre
// themselves, and the keycaps reach through the opening to face each other gap_t apart, whichever way the case is
// held. Each lid hangs on two lift-off hinges, far apart along the top long edge so a knock on the lid loads them
// little: a printed bar between two frame knuckles, and a hook on the lid whose slot opens towards the lid's outer
// face. Closed, the slot faces away from the frame, so the lid cannot come off; opened to about 90 degrees, the hook
// slides sideways off the bar. Nothing flexes and there is no separate pin. The hinge axis runs outside the edge's
// middle tab, so no part of the lid swings into the frame. A lip under the lid locates it in
// the frame, in the space below the half and clear of its feet, and stops short of the hinge side, where it would hit
// the wall as the lid swings. On the straight run of the thumb side a ridge on the lip clicks into a groove in the
// wall: the wall flexes along its layers to let it pass, and a fingernail slot over it lifts the lid. Closed, the lid compresses the half's rubber feet by squeeze
// against the wedge. The top lid is engraved with the name, the bottom one with the cat.
// The frame prints upright as modelled, the lids outside face down; no supports.
// Texture: export lid2d() as an SVG, then run wall_texture.py outline.svg wall_texture.scad
// Export: openscad --enable=roof -D 'part="none"' -D 'case_part="frame"'      -o stl/totemhe_carry_frame.stl carry_case.scad
//         openscad --enable=roof -D 'part="none"' -D 'case_part="lid_top"'    -o stl/totemhe_carry_lid_top.stl carry_case.scad
//         openscad --enable=roof -D 'part="none"' -D 'case_part="lid_bottom"' -o stl/totemhe_carry_lid_bottom.stl carry_case.scad
case_part = "assembly";   // "frame" | "lid_top" | "lid_bottom" | "assembly"
include <totem_he_case.scad>
use <cat.scad>
use <wall_texture.scad>

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
texture    = true;   // faceted scales on the outside, from wall_texture.py

/* [Lid lip and latch] */
lip_clear  = 0.15;              // lip to frame wall
lip_h      = 2.5;               // stops short of the half's underside, z_feet
lip_t      = 1.5;
lead_in    = 0.3;               // the lip's tip is this much narrower, to find the opening
latch_x    = [61, 77];          // along the thumb side's straight run, opposite the middle of the hinges
latch_edge = -91.83;            // that run's pocket edge, y
latch_h    = 0.5;               // the ridge stands this far out of the lip; the wall gives latch_h - lip_clear
latch_z    = 1.3;               // its peak, above the lid's inner face
groove_d   = 0.6;
slot_h     = 0.8;               // fingernail slot in the lid's inner face, over the latch

/* [Hinges] */
hinge_x    = [12, 107];         // start of each hinge, on the top edge's straight runs either side of the tab
hinge_wall = 0.94;              // the frame's outer face along those runs, y
hinge_len  = 20;
knuckle_r  = 2.5;
knuckle_gap = 0.4;              // between the hook and the frame knuckles either side of it
bar_d      = 3.2;               // the frame's bar, which the lid's hook turns on
hook_clear = 0.2;
hook_r     = 4.0;               // around the bar, so the hook's two arms beside the slot stay over 2 mm thick

z_feet  = bumper_h - squeeze;                               // lower half's PCB bottom above the bottom face
z_deck1 = z_feet + z_top;                                   // lower half's deck, facing up
z_caps  = z_feet + z_plate_top + keycap_h;                  // lower half's keycap tops
z_deck2 = z_caps + gap_t + keycap_h - deck_above_plate;     // upper half's deck, facing down
frame_h = z_deck2 + z_top + z_feet;
z_slope = z_deck1 - chamfer - fit;                          // the lower band's underside, on the deck chamfer

module footprint2d() union() { outline2d(); wing_tucked2d(); }
module pocket2d() offset(delta = fit) footprint2d();
module lid2d() offset(r = wall_t) pocket2d();
axis = [6.61 + knuckle_gap + knuckle_r, knuckle_r];          // hinge axis, y and z in the face's own frame below; past
                                                              // the lid's top tab (y 6.61)
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

// Hinges and latch are drawn for the bottom face, where the frame is z >= 0 and the lid z <= 0; at_faces() repeats
// them mirrored for the top face.
module at_faces() { children(); translate([0, 0, frame_h]) mirror([0, 0, 1]) children(); }
// a profile in y and z, swept along x from x0 to x1
module along_x(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
function third(i) = [(hinge_len + 2 * knuckle_gap) / 3 * i, (hinge_len + 2 * knuckle_gap) / 3 * (i + 1) - knuckle_gap];
// tangent to the face, joined to the wall by a 45 degree web on the side away from the face
module frame_knuckle2d() hull() {
  translate(axis) circle(knuckle_r, $fn = 36);
  translate([hinge_wall - 1, 0]) square([1, axis[1] + knuckle_r + (axis[0] - hinge_wall)]);
}
// a column from the lid's outer face up around the bar, joined to the lid's edge; the seat has a pointed top so it
// prints without supports, and the slot runs from it out through the outer face
module lid_hook2d() difference() {
  union() {
    hull() { translate(axis) circle(hook_r, $fn = 48); translate([axis[0] - hook_r, -lid_t]) square([2 * hook_r, 0.01]); }
    translate([hinge_wall - 1, -lid_t]) square([axis[0] - hinge_wall + 1, lid_t]);
  }
  r = bar_d / 2 + hook_clear;
  translate(axis) hull() { circle(r, $fn = 36); translate([0, r * sqrt(2)]) circle(0.01); }
  translate([axis[0] - r, -lid_t - 1]) square([2 * r, axis[1] + lid_t + 1]);
}
module frame_hinges() for (x = hinge_x) {
  for (i = [0, 2]) along_x(x + third(i)[0], x + third(i)[1]) frame_knuckle2d();
  along_x(x + third(0)[1] - 1, x + third(2)[0] + 1) translate(axis) circle(d = bar_d, $fn = 36);
}
module lid_hinges() for (x = hinge_x) along_x(x + third(1)[0], x + third(1)[1]) lid_hook2d();
module groove() along_x(latch_x[0] - 1, latch_x[1] + 1)
  polygon([[latch_edge + eps, latch_z - groove_d], [latch_edge - groove_d, latch_z], [latch_edge + eps, latch_z + groove_d]]);

module frame() union() {
  difference() {
    union() {
      linear_extrude(frame_h) difference() { lid2d(); pocket2d(); }
      wedge_lower();
      wedge_upper();
    }
    if (texture) wall_texture();
    at_faces() groove();
  }
  at_faces() frame_hinges();
}

// rises from z 0, the lid's inner face; cut back on the hinge side, where it would swing into the wall
module lip(clear) intersection() {
  union() {
    linear_extrude(lip_h - lead_in) difference() { offset(delta = -clear) pocket2d(); offset(delta = -clear - lip_t) pocket2d(); }
    translate([0, 0, lip_h - lead_in]) linear_extrude(lead_in) difference() { offset(delta = -clear - lead_in) pocket2d(); offset(delta = -clear - lip_t) pocket2d(); }
    along_x(latch_x[0], latch_x[1]) polygon([[latch_edge + clear + 0.2, latch_z - latch_h], [latch_edge + clear - latch_h, latch_z], [latch_edge + clear + 0.2, latch_z + latch_h]]);
  }
  translate([-50, -200, -1]) cube([300, axis[0] - 15 + 200, lip_h + 2]);
}
module nail_slot() translate([latch_x[0], latch_edge - wall_t - 2, -slot_h]) cube([latch_x[1] - latch_x[0], wall_t + 2 - 0.8, slot_h + eps]);
// inner face at z 0, lip upwards, outer face at -lid_t; lid() turns it to fit each face of the frame
module lid_body() {
  difference() {
    translate([0, 0, -lid_t]) linear_extrude(lid_t) lid2d();
    nail_slot();
  }
  lip(lip_clear);
  lid_hinges();
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
else if (case_part == "assembly") { color("#6a5acd") frame(); color("#8a7ae0") { lid(true); lid(false); } }
