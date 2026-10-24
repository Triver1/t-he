# Tot-HE-m PCB

Hall-effect version of TOTEM's layout at MX spacing. `totem_he.kicad_pcb` holds both halves side by side, so one
order covers both; open `totem_he.kicad_pro` beside it so KiCad loads the design rules. Both halves are placed and
routed (see Mux placement and routing).

The board is generated with Ergogen: `./build.sh` rebuilds it from the case geometry, `mux_map.json` and the
footprint modules in `footprints/`, then checks it. See "Generating the board" below.

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

## Mux placement and routing

Each half has one mux per finger group, on the underside between the columns it serves: IC1 takes the outer,
pinky and ring keys (ADC_A, D0), IC2 middle and index (ADC_B, D2), IC3 inner and thumbs (ADC_C, D1). Its position
and angle are the `at` entry in `mux_map.json`, chosen with at least 1 mm clear of every pad and peg hole. The
channels follow the order the sensors sit around the mux, so the sensor lines fan in without crossing; where that
needs a hand-set order, `mux_map.json` marks the mux `fixed`. The firmware has a channel map for each half.

The routing is hand-designed and written out in `routes.py`: every trace as waypoints, 45 degree bends, sensor
patterns in each switch's own frame. `build.sh` applies it, so a regenerated board comes out routed.

| Layer | Nets |
| --- | --- |
| Underside | Signals: each sensor's output fanning into its mux, the bus from the XIAO along the top edge (data, select lines, two mux outputs) up through the notch above the middle-top key, short power stubs at each part |
| Top | 3.3 V and ground as two interleaved combs: a 3.3 V rail along the top edge with a tooth down each column, ground teeth up each column joined by a rail along the bottom edge; no fills |

Every switch has two tented vias in its footprint (3.3 V right of the sensor, ground left), so each sensor reaches
both combs. Where a bus line branches to IC1 or IC2, it takes a via up and runs on the top layer between the power
teeth; on the right half, IC2's output and the data line each hop one stretch on top the same way. 0.25 mm
signals, 0.4 mm power stubs, 0.5 mm rails.

`route.py` (run as `./r`) is the tool the routing was drawn with: `./r view [x0 y0 x1 y1]` draws a region with
open connections dashed, `./r open` lists them, `./r track`, `./r via`, `./r delete` and `./r undo` edit, and
`./r drc` summarises. To change the routing, edit `routes.py` and run `./build.sh`.

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

XIAO pins: D0, D1, D2 read the three muxes (IC1, IC3, IC2). D8, D9, D10 drive the shared select lines S0 to S2.
D7 is the split link, one half-duplex wire on TRRS ring 2; D3 to D6 and 5V are unconnected. 3V3 powers the sensors and
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

## Generating the board

```bash
./build.sh
```

replaces `totem_he.kicad_pcb` with a freshly generated, routed board (`./build.sh other.kicad_pcb` writes elsewhere).
It runs Ergogen, KiCad and OpenSCAD in Docker:

1. `gen_config.py` writes `config.yaml` for Ergogen. Key, XIAO, jack and hole positions come from
   `../case/totem_geometry.scad`; the right half is the left mirrored about `halves.AXIS_X`, each part turned to minus
   its angle but not mirrored. Each mux's position is the `at` entry in `mux_map.json` (board x, y, angle, per
   half); the script works out its channels and writes them back to `mux_map.json`. Every net gets its half's
   prefix (`L/`, `R/`).
2. Ergogen builds both halves into one board from `config.yaml` and the modules in `footprints/` (switch with its
   sensor and capacitor, mux, XIAO, TRRS jack, mounting hole).
3. `finish.py` renumbers the right half (S101, IC101, ...) and saves the board in KiCad 8's format.
4. `set_edge.py` adds both outlines from the case's PCB shape (`openscad -D 'part="pcb"'`).
5. `mkpro.py` writes the design rules, `netcheck.py` checks the nets, `gen_mock.py` writes the PCB mock's part list.

Generating discards any routing, so change the layout before routing; after that, edit the board in KiCad.
`set_edge.py pcb2d.svg <in> <out>` also works on a routed board, for outline changes, and prints how far the edge
moved. Write the `.kicad_pro` (`mkpro.py`) before filling any pours, or KiCad fills to its default 0.5 mm edge
clearance instead of 0.25 mm.
