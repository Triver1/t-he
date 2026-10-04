# THE PCB

Hall-effect version of TOTEM's layout at MX spacing. `totem_he.kicad_pcb` holds both halves side by side, so one
order covers both; open `totem_he.kicad_pro` beside it so KiCad loads the design rules. Both halves are placed and
netted but not routed: route them by hand.

## Layout

| Face | Parts |
| --- | --- |
| Front (top) | Switches, XIAO RP2040 (soldered flat on its castellations over plated holes), PJ-320A TRRS jack |
| Back (underside) | 19 sensors, 19 sensor capacitors, 3 muxes and their capacitors |

- The sensors sit under the board, on the face opposite the switches, like HE60. The SOT-23 pads are
  Boardloaf-HE's 1.69 x 0.6 mm, which are easy to hand-solder.
- The right half is the left mirrored about x = `AXIS_X` in `halves.py`, 5 mm from the left's inner edge. Each
  part is turned to minus its angle but not mirrored, so every land pattern stays correct and both halves put the
  same parts on the same faces. USB-C faces the outer edge on each half.
- References: S1 to S19, IC1 to IC3, MCU1, TRRS1 and H1 to H4 on the left; the right adds 100 (S101, IC101, ...).
  Nets carry their half's prefix (`L/VCC`, `R/VCC`), so the halves share no net and DRC treats them separately.
- The PJ-320A footprint has pads 2 (sleeve, GND), 3 (ring 2, DATA) and 4 (tip, VCC) in two mirrored columns, pad 4
  slotted to take the ring 1 leg as well, so the jack fits either way round.

Together the halves are 265 x 103 mm; each is 128.9 x 103.0 mm.

## Mux placement and vias

Each half has one mux per finger group, on the underside between the columns it serves: IC1 takes the outer,
pinky and ring keys (ADC_A, D0), IC2 middle and index (ADC_B, D1), IC3 inner and thumbs (ADC_C, D2). The channels
follow the order in which the sensors sit around the mux, so the 19 sensor lines fan in without crossing, and the
mux output (Z) points toward the XIAO. The right half's muxes keep their pinout while their placement is mirrored,
so its channel order differs; `mux_map.json` lists both halves and the firmware has a map for each.

Routing plan, per half:

| Layer | Nets |
| --- | --- |
| Underside | 19 sensor outputs to their mux, the 3 mux outputs to XIAO D0 to D2, 3.3 V to sensors and muxes, ground fill |
| Top | Select lines S0 to S2 from XIAO D4, D5, D8, and a ground fill that shields the analog traces below |

The XIAO's plated holes reach both layers. The vias are pads inside the footprints, so they move with their part:

- one ground via per sensor, between its GND pin and its capacitor's GND pad (19);
- three select vias just outside each mux's pins 9 to 11 (9), and one ground via beside its pin 7 (3).

That is 31 per half. The ground vias join the underside ground patches, which the 3.3 V and signal traces cut up,
to the top ground fill; where two patches end up joined anyway, one of their vias can go.

## Electronics

Same scheme as Boardloaf-HE.

| Part | Per half | Notes |
| --- | --- | --- |
| Linear hall sensor, SOT-23: TI DRV5055A3QDBZR (LCSC C266128) | 19 | Under each stem magnet. Pin 1 VCC, 2 OUT, 3 GND |
| 100 nF 0805 (C1711) | 22 | One per sensor and per mux |
| 74HC4051 SOIC-16 (C9386) | 3 | One per ADC input |
| XIAO RP2040 | 1 | Soldered flat, no headers. Its pads have 1.0 mm plated holes, so every pin reaches the underside without a via and solder wicks in. USB-C over the outer edge |
| PJ-320A TRRS | 1 | Tip VCC, ring 1 tied to tip, ring 2 DATA, sleeve GND |
| M2 plated holes | 4 | Case screws |

XIAO pins: D0, D1, D2 read the three muxes (ADC0 to 2). D4, D5, D8 drive the shared select lines. D6 is the split
link, one half-duplex wire on TRRS ring 2; D7, D3, D9, D10 and 5V are unconnected. 3V3 powers the sensors and
muxes and feeds the other half over the tip. Which key sits on which mux channel is in `mux_map.json`, per half.

DRV5055A3 (TI datasheet SBAS640C): 3.0 to 3.63 V, rests at 1.65 V, 15 mV/mT at 3.3 V, 2 mA typical and 4 mA
maximum, at least 10 nF on VCC (the 100 nF beside each sensor covers it). Under the board the sensor is 1.6 mm
further from the magnet than on top; the firmware learns each key's travel, so a smaller swing costs resolution,
not function. Before ordering a full set, check one part: 3.3 V on pin 1, ground on pin 3, and pin 2 near 1.65 V,
swinging when a magnet approaches.

## Checks

Run these in the KiCad 8 container, and again after routing:

- `netcheck.py` checks every pad's net against the design on each half, and that no net crosses between them: sensor pin order, each sensor output on
  its mux channel from `mux_map.json`, mux commons, select lines, enable and supply pins, the XIAO and the TRRS.
- `../firmware/gen_firmware.py` follows every connection the firmware relies on in each half, requires both halves
  on the same XIAO pins, and compares them with `mux_map.json`.
- `kicad-cli pcb drc --severity-all` currently reports only unconnected items (250, 125 per half), which routing clears.

## Ordering

```bash
./production.sh
```

writes Gerbers and an Excellon drill file to `production/files/`, zipped as `production/THE_gerbers.zip`. Run it
after routing, with DRC clean. An order of 5 gives 5 left and 5 right boards. JLCPCB counts the two outlines as two
designs and adds a fee for the second (their help page, "What Counts as Different Designs", gives no amount; the
quote shows it), so compare the quote with two separate orders. Settings: 2 layers, 1.6 mm FR-4, 1 oz copper; the defaults cover the rest (0.25 mm
tracks, 0.2 mm clearance, 0.3 mm vias). Choose "Remove order number", or JLCPCB prints one on the silkscreen. The
Gerbers follow JLCPCB's KiCad guide: Protel extensions, solder mask subtracted from silkscreen, one Excellon file
for plated and unplated holes, the alternate drill mode for the slotted TRRS pad.

## Changing the design

- Outline changes in `../case/totem_he_case.scad`: export `openscad -D 'part="pcb"' -o pcb2d.svg
  ../case/totem_he_case.scad`, then `set_edge.py pcb2d.svg <in> <out>` replaces both halves' Edge.Cuts and prints
  how far the edge moved.
- Key moves in `../case/totem_geometry.scad`: `move_keys.py <in> <out>` snaps every switch footprint on both halves
  to its key and prints what moved.
- `mkpro.py` writes `totem_he.kicad_pro` (design rules, 0.25 mm edge clearance). Write it before filling any
  pours, or KiCad fills to its default 0.5 mm.
- `gen_mock.py` regenerates the PCB mock's part list, `../case/mock_parts.scad`, from the left half.
