// TOTEM case for MX-style hall-effect switches, wired.
// Outline, key positions, mounting holes, XIAO and TRRS come from GEIGEIGEIST/TOTEM rev 0.3,
// scaled from Choc spacing (18 x 17 mm) to MX (19.05 mm) in totem_geometry.scad.
// Like TOTEM: the key field is sunk into a thick deck so the switch housings stay hidden, and a
// lower thumb wing leaves the thumb switches open at the front.
// Three parts, bottom to top: the all-SMD HE PCB is the base (bumpers taller than the screw heads), a flat
// switch plate with four standoffs sits on the PCB, and the shell drops over both. One M2 x 10 screw
// per corner goes up from under the PCB through the standoff and the plate into a pilot in the deck.
// The low wall around the thumb wing belongs to the plate, not the shell, so both parts print without
// supports: the shell deck-down (every opening goes straight through, the USB and TRRS openings are
// notches open at the wall bottom), the plate top-down with its wing wall and standoffs rising.
// Export (OpenSCAD 2025+ for roof()):  openscad --enable=roof -D 'part="shell"' -D 'side="left"' -o stl/totemhe_shell_left.stl totem_he_case.scad
//          openscad -D 'part="plate"' -D 'side="left"' -o stl/totemhe_plate_left.stl totem_he_case.scad
//          openscad -D 'part="pcb"'   -D 'side="left"' -o kicad/pcb_outline_left.dxf totem_he_case.scad

include <totem_geometry.scad>

part = "assembly";   // "shell" | "plate" | "pcb" | "assembly" | "none" (modules only, for files that include this one)
side = "left";       // "left" | "right"

/* [Stack, mm from desk] */
pcb_t            = 1.6;
plate_above_pcb  = 5.0;   // plate top above PCB top, MX standard
plate_t          = 1.5;
deck_above_plate = 6.0;   // wells the switches like TOTEM; 0 gives a flush plate

/* [Outline] */
wall      = 2.0;
pcb_clear = 0.4;
thumb_front = 10.3;  // cavity edge in front of each thumb, from the key centre
side_trim   = 1.0;   // pulls the inner side in from TOTEM's edge
rim_extra = 3.125;   // grows the cavity square to 22.25 around the E and shift keys: a 3.5 mm deck rim, 2.2 mm of flat beside the chamfer
corner_r  = 1.7;     // outer corners of the shell; TOTEM's edge arcs give about 3.4 here, this is half
chamfer   = 1.3;     // 45 degree chamfer on the deck's top edge (needs OpenSCAD with roof())

/* [Parts] */
switch_cut = 14.0;
xiao       = [21.0, 17.8];   // XIAO RP2040 on top of the PCB like TOTEM's, castellations soldered flat, USB-C towards -x
xiao_t     = 1.2;            // its board; the USB-C receptacle is 3.2 tall on top of it and overhangs its edge by 1.3
xiao_usb_z = xiao_t + 1.6;   // USB-C centre above the PCB top
usb_plug   = [12.8, 7.0];    // plug overmold, reaches in to the XIAO through the outer wall
trrs_body  = [6.2, 12.4];    // MJ-4PP-9
trrs_h     = 5.4;
trrs_d     = 6.0;
standoff_d = 4.4;            // on the plate underside, PCB top to plate bottom
screw_d    = 2.4;            // M2 clearance through PCB, standoff and plate
insert     = false;          // true: M2 heat-set inserts in the deck instead of self-tapping screws
pilot_d    = insert ? 3.2 : 1.7;
pilot_depth = deck_above_plate - 1.5;
plate_clear = 0.2;
seam_clear  = 0.1;           // between the shell and the plate's wing wall
wing_inset  = 0.4;           // the wing wall's front faces sit this far inside the shell outline, so the seam reads as a step;
                             // along the straight inner side the wall stays flush, so that line stays unbroken
// Every visible edge around a thumb sits this far from its centre: the plate's front and outer edges, and the shell
// walls beside and behind the thumbs (their seam puts the shell face at exactly this distance).
thumb_well  = thumb_front + wall - wing_inset;
thumb_back  = thumb_well - seam_clear;   // the wing's edge behind and beside the thumbs
thumb_side  = thumb_well - wall;         // cavity edge behind the outer thumb, so its tab's back meets the well
pocket_skin = 1.2;

$fn = 48;
eps = 0.01;

z_pcb_bot   = 0;
z_pcb_top   = pcb_t;
z_plate_top = z_pcb_top + plate_above_pcb;
z_plate_bot = z_plate_top - plate_t;
z_top       = z_plate_top + deck_above_plate;
U = 19.05;

alphas = [for (k = totem_keys) if (k[3] == 0) k];
thumbs = [for (k = totem_keys) if (k[3] == 1) k];

// Where the fronts of two neighbouring thumbs meet, as a distance along the second thumb's x axis from its centre.
function rot2(a, v) = [v[0] * cos(a) - v[1] * sin(a), v[0] * sin(a) + v[1] * cos(a)];
function front_meet(k1, k2, h) = let (p1 = [k1[0], k1[1]] + rot2(k1[2], [0, -h]), d1 = rot2(k1[2], [1, 0]),
                                      p2 = [k2[0], k2[1]] + rot2(k2[2], [0, -h]), d2 = rot2(k2[2], [1, 0]), w = p2 - p1)
  (w[0] * d1[1] - w[1] * d1[0]) / (d1[0] * d2[1] - d1[1] * d2[0]);
// Thumb 1's outer wall stands about as far from its key as the corners between the thumbs do (thumb_corner). It is
// a shell wall and a pressed keycap drops past the deck into the well, so it keeps the main keys' pocket clearance.
thumb_corner = -front_meet(thumbs[1], thumbs[2], thumb_well);
thumb_end    = max(thumb_corner, (U + 0.2) / 2);
// The outer thumb's outer side is a plate edge, a little inside the front margin, so the two margins read alike.
thumb3_side  = thumb_well - 0.4;
// cavity (and PCB) edge on that side: at least the 1 mm around the switch cutout every key gets, and exactly far
// enough that the tucked outline lands on thumb3_side
thumb_outer = max(switch_cut / 2 + 1, thumb3_side - wall + wing_inset);

module rect(x0, y0, x1, y1) { translate([x0, y0]) square([x1 - x0, y1 - y0]); }
module at_key(k) { translate([k[0], k[1]]) rotate(k[2]) children(); }

// Collapses the arcs in TOTEM's edge into sharp corners: shrink and regrow with sharp offsets removes convex
// arcs up to R, grow and shrink removes concave ones. Features narrower than 2R would vanish; none are.
module sharp2d(R = 1.5) { offset(delta = -R) offset(delta = R) offset(delta = R) offset(delta = -R) children(); }

// TOTEM's board edge, grown where the larger MX housings overhang it.
module pcb2d() {
  difference() {
    intersection() {
      offset(r = -2) offset(r = 2) union() {
        sharp2d() polygon(totem_pcb_edge);
        for (k = totem_keys) at_key(k) square(switch_cut + 0.6, center = true);
      }
      offset(delta = -pcb_clear) cavity2d();
    }
    for (h = totem_holes) translate(h) circle(d = 2.2);
  }
}
// Like TOTEM, each thumb sits in its own tab square to the key, so the front is straight segments
// and the outer thumb's corner steps out past the side. Added after the closing to keep those corners sharp.
// Neighbouring tabs run 14 mm out, past the point where their front edges cross, so the fronts meet in one corner;
// shorter tabs left a 0.3 mm step there.
module thumb_tab(k, x0 = -10, x1 = thumb_side) at_key(k) rect(x0, -thumb_front, x1, thumb_side);
module cavity_raw2d() {
  union() {
    offset(delta = -3) offset(delta = 3) union() {
      difference() {
        offset(delta = pcb_clear) sharp2d() polygon(totem_pcb_edge);
        rect(totem_side_x + pcb_clear - side_trim, -200, 300, 50);
        for (k = thumbs) at_key(k) rect(-14, -40, 14, -thumb_front);
        at_key(thumbs[2]) rect(thumb_outer, -40, 40, thumb_side);   // TOTEM's own outer-thumb corner
      }
      // the E and shift pockets sit closest to the edge; a wider cavity there keeps a flat rim beside the chamfer
      for (k = totem_keys) at_key(k) square(switch_cut + 2 + (k == alphas[2] || k == alphas[15] ? 2 * rim_extra : 0), center = true);
    }
    for (i = [0 : 2]) thumb_tab(thumbs[i], i == 0 ? -10 : -14, i == 2 ? thumb_outer : 14);
  }
}
// the inner side is one straight line; the outer thumb's tab stops at it instead of stepping out
module cavity2d() { intersection() { cavity_raw2d(); rect(-100, -200, totem_side_x + pcb_clear - side_trim, 50); } }
module outline2d() { offset(r = corner_r) offset(delta = wall - corner_r) cavity2d(); }
// the plate's wing keeps the outer thumb's full tab, which steps out past the shell's straight inner side;
// its corners stay sharp so its faces line up with the shell's wall ends
module outline_wing2d() { offset(delta = wall) cavity_raw2d(); }
// The plate's part of the outline: the thumb wing, tucked in all along its exposed front, with the outer thumb's
// outer side at thumb3_side. Only the outer tab's back edge stays flush, since it continues the shell's wall end;
// that strip stops at the outer side, so the corner there is one clean corner.
module wing_tucked2d() {
  back = thumb_side + wall;   // the outer tab's back edge, from the key centre
  intersection() {
    wing2d();
    union() {
      offset(delta = -wing_inset) outline_wing2d();
      intersection() { outline_wing2d(); at_key(thumbs[2]) rect(-40, back - wing_inset - 0.01, thumb3_side, back + 40); }
    }
    at_key(thumbs[2]) rect(-300, -300, thumb3_side, 300);   // the outer thumb's outer side
  }
}

// Thumb wing: lowered to plate level from just behind the thumbs to the front edge.
// Behind the outer thumb the wall continues the step in the outer side, so its whole tab is lowered.
// Under the two inner bottom keys (V and B) the wing opens into the key field, so the deck has no web there.
function inner_x() = totem_side_x + pcb_clear - side_trim + wall;   // the shell's straight inner side
// y where the outer thumb tab's back edge crosses the shell's straight inner side
// y where the outer thumb's back edge crosses the vertical line x
function back_y(x) = let (t = thumbs[2], h = thumb_back, u = (x - t[0] + h * sin(t[2])) / cos(t[2])) t[1] + u * sin(t[2]) + h * cos(t[2]);
function wing_end_y() = back_y(inner_x());
// Thumb wing: lowered to plate level from just behind the thumbs to the front edge. Behind the outer thumb the
// wall continues the step in the outer side, so its whole tab is lowered. Under V and B the wing opens into the key field.
module wing2d() {
  ox = alphas[14][0] + U / 2 + 0.1;   // the V/B opening's inner edge
  oy = back_y(ox);                    // where the outer thumb's back edge meets that edge
  intersection() {
    outline_wing2d();
    difference() {
      offset(delta = -1) offset(delta = 1) union() {
        // every thumb's back stands at thumb_back; thumb 1's outer wall at thumb_end
        for (i = [0 : 2]) at_key(thumbs[i]) rect(i == 0 ? -(thumb_end - seam_clear) : -(U / 2 + 1.2), -60, U / 2 + 8, thumb_back);
        rect(alphas[13][0] - U / 2 - 0.1, thumbs[0][1], ox, alphas[13][1]);
        // on the inner side the shell wall ends square to the side, where the outer tab's back edge meets it
        rect(thumbs[2][0], -200, 300, wing_end_y());
        polygon([[ox, oy], [inner_x(), wing_end_y()], [inner_x(), -150], [ox, -150]]);
      }
      // behind the outer thumb the deck edge is its back edge, one straight line from the opening's corner to the
      // wall end: filled below it, cut above it
      polygon([[ox, oy], [inner_x(), wing_end_y()], [inner_x() + 10, wing_end_y()], [inner_x() + 10, -40], [ox, -40]]);
    }
  }
}

// Keycap pockets of the main block, sunk into the deck.
module key_field2d() { offset(r = -1) offset(r = 1) for (k = alphas) at_key(k) square(U + 0.2, center = true); }
// notch open at the wall bottom, so the shell prints deck-down without a bridged hole
module usb_tunnel() {
  x_usb = totem_xiao[0] - xiao[0] / 2;
  hull() for (dz = [0, -10])
    translate([-wall - 5, totem_xiao[1], z_pcb_top + xiao_usb_z + dz]) rotate([0, 90, 0])
      linear_extrude(x_usb + wall + 5) offset(r = 1.5) square([usb_plug[1] - 3, usb_plug[0] - 3], center = true);
}
module trrs_pocket2d() { translate([totem_trrs[0], totem_trrs[1] - trrs_body[1] / 2 + 3]) square([trrs_body[0] + 0.6, trrs_body[1] + 6], center = true); }
// notch open at the wall bottom, so the shell prints deck-down without a bridged hole
module trrs_hole() {
  hull() for (dz = [0, -10])
    translate([totem_trrs[0], totem_trrs[1], z_pcb_top + trrs_h / 2 + dz]) rotate([-90, 0, 0]) cylinder(d = trrs_d, h = 30);
}

module shell() {
  difference() {
    intersection() {
      linear_extrude(z_top) outline2d();
      // the chamfer runs along the outer perimeter only; the wing cut goes square through it
      union() { linear_extrude(z_top - chamfer) outline2d(); translate([0, 0, z_top - chamfer]) roof() outline2d(); }
    }
    // PCB and plate slide in from below
    translate([0, 0, -1]) linear_extrude(z_plate_top + 1) cavity2d();
    translate([0, 0, z_plate_top - eps]) linear_extrude(deck_above_plate + 1) key_field2d();
    // the whole wing column: its low wall is part of the plate
    translate([0, 0, -1]) linear_extrude(z_top + 2) offset(delta = seam_clear) wing2d();
    // room above the plate line for the TRRS jack, under a solid deck
    translate([0, 0, -1]) linear_extrude(z_top - pocket_skin + 1) intersection() { trrs_pocket2d(); cavity2d(); }
    for (h = totem_holes) translate([h[0], h[1], z_plate_top - eps]) cylinder(d = pilot_d, h = pilot_depth);
    usb_tunnel();
    trrs_hole();
  }
}

module plate() {
  difference() {
    union() {
      translate([0, 0, z_plate_bot]) linear_extrude(plate_t) offset(delta = -plate_clear) cavity2d();
      translate([0, 0, z_plate_bot]) linear_extrude(plate_t) wing_tucked2d();
      linear_extrude(z_plate_top) difference() { wing_tucked2d(); cavity2d(); }   // the thumb wing's wall
      for (h = totem_holes) translate([h[0], h[1], z_pcb_top]) cylinder(d = standoff_d, h = plate_above_pcb - plate_t + eps);
    }
    for (k = totem_keys) translate([0, 0, z_plate_bot - 1]) linear_extrude(plate_t + 2) at_key(k) square(switch_cut, center = true);
    for (h = totem_holes) translate([h[0], h[1], z_pcb_top - 1]) cylinder(d = screw_d, h = plate_above_pcb + 2);
    translate([0, 0, z_plate_bot - 1]) linear_extrude(plate_t + 2) offset(delta = 0.3) trrs_pocket2d();
    // room to reach the XIAO's castellations and USB-C
    translate([totem_xiao[0], totem_xiao[1], z_plate_bot - 1]) linear_extrude(plate_t + 2) square([xiao[0] + 3, xiao[1] + 3], center = true);
  }
}

module side_mirror() { if (side == "right") mirror([1, 0, 0]) children(); else children(); }

side_mirror() {
  // print orientation is a 180 degree turn, never a mirror: a mirror would swap the halves
  if (part == "shell" || part == "top") rotate([180, 0, 0]) translate([0, 0, -z_top]) shell();        // deck-down for printing
  else if (part == "plate") rotate([180, 0, 0]) translate([0, 0, -z_plate_top]) plate();               // top-down, standoffs up
  else if (part == "pcb") pcb2d();
  else if (part == "none") {}
  else {
    color("#26262a") shell();
    color("#8a8a8e") plate();
    color("#161718") translate([0, 0, z_pcb_bot]) linear_extrude(pcb_t) pcb2d();
  }
}
