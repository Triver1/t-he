# Tot-HE-m

A wired, hall-effect split keyboard on TOTEM's layout (GEIGEIGEIST/TOTEM rev 0.3, CC BY-NC-SA 4.0) scaled to MX
spacing, for MX-style magnetic switches (Gateron KS-20 class) and a Seeed XIAO RP2040 per half.

## Files

| Part | Where |
| --- | --- |
| Shell, 3D printed deck-down, no supports | `case/stl/totemhe_shell_<side>.stl` |
| Plate with standoffs and the thumb-wing wall, printed top-down, no supports | `case/stl/totemhe_plate_<side>.stl` |
| PCB, the base of the stack, both halves side by side in one file (placed and netted, to be routed by hand) | `pcb/totem_he.kicad_pcb` (see `pcb/README.md`) |
| PCB order files for JLCPCB, written by `pcb/production.sh` after routing | `pcb/production/THE_gerbers.zip` |
| PCB mock with component blocks for fit tests | `case/stl/totemhe_pcbmock_<side>.stl` |
| QMK firmware, tables generated from the board | `firmware/`, prebuilt in `firmware/uf2/` |

Stack: PCB 1.6, plate top 5.0 above the PCB, deck 6.0 above the plate. 12.6 mm tall, 6.6 at the thumb wing.
The case halves are separate files; the print files are turned over for printing (a rotation, so left stays left).

## Bill of materials

| Item | Per half | Total | Notes |
| --- | ---: | ---: | --- |
| PCB, 2 layers, 1.6 mm | 1 | 2 | Both halves in one file: an order of 5 gives 5 of each, `pcb/production/THE_gerbers.zip`. JLCPCB adds a fee for the second design |
| Linear hall sensor, SOT-23 | 19 | 38 | TI DRV5055A3QDBZR, LCSC C266128 (SLSS49E-3, C2904393, is out of stock); any 49E-class part wired 1 VCC, 2 OUT, 3 GND fits |
| Capacitor 100 nF, 0805 | 22 | 44 | One per sensor, one per mux; LCSC C1711 |
| 74HC4051 analog mux, SOIC-16 | 3 | 6 | LCSC C9386 (74HC4051D,653) |
| Seeed XIAO RP2040 | 1 | 2 | Soldered flat on its castellations over plated holes, no headers: headers would lift it into the plate |
| TRRS jack PJ-320A | 1 | 2 | Datasheet LCSC C7501806 |
| MX-style magnetic switch, Gateron KS-20 class | 19 | 38 | No pins; clips into the 1.5 mm plate |
| MX keycap, 1u | 19 | 38 | |
| M2 x 10 screw | 4 | 8 | See below |
| Rubber bumper | 4 or more | 8 or more | Taller than the parts under the PCB (2.5 mm or more) |
| Shell, printed | 1 | 2 | |
| Plate, printed | 1 | 2 | |
| TRRS cable, 4 conductor | | 1 | |
| USB-C cable | | 1 | |

### Screws

Four M2 x 10 machine screws per half, one per mounting hole. Each goes up from under the PCB, through the PCB
(1.6 mm), the plate's standoff (3.5 mm) and the plate (1.5 mm), and cuts its own thread in a 1.7 mm pilot hole
in the deck, 4.5 mm deep. That leaves 3.4 mm of thread in the deck and 1.1 mm spare at the bottom of the hole,
so 10 mm is the length to buy: an 8 mm screw holds by 1.4 mm of thread, a 12 mm one bottoms out.

The heads sit under the PCB, next to the sensors and muxes. The SOIC-16 muxes stand 1.75 mm and the SOT-23
sensors about 1.1 mm, so the bumpers need 2.5 mm or more; any head up to a pan head (1.6 mm, ISO 7045) clears that.

For screws that come out often, set `insert = true` in `case/totem_he_case.scad`: the deck then takes M2 heat-set
inserts in a 3.2 mm hole instead of the pilot, with the same M2 x 10 screws; pick inserts no longer than 4.5 mm.

## Electronics

Same scheme as Boardloaf-HE: a linear hall sensor under every stem magnet, read through 74HC4051 muxes by the
XIAO's ADC. No diodes, no matrix. Per half: 19x DRV5055A3 (SOT-23, LCSC C266128), 22x 100 nF 0805,
3x 74HC4051 SOIC-16, 1x XIAO RP2040, 1x PJ-320A TRRS. The switches, XIAO and jack go on top and the sensors,
capacitors and muxes underneath, on both halves. `pcb/README.md` has the layout, wiring and ordering notes.
`pcb/netcheck.py` checks every pad's net on each half, and `firmware/gen_firmware.py` reads the mux assignment back
out of both halves and compares it with `pcb/mux_map.json`.

Compatibility, checked against the datasheets:

- DRV5055A3 runs from 3.0 to 3.63 V, so the XIAO's 3.3 V is in range; its output sits at 1.65 V with no field and
  swings around it, inside the RP2040's 3.3 V ADC range. It is wired 1 VCC, 2 OUT, 3 GND (TI datasheet SBAS640C),
  the SOT-23 order this footprint uses; `pcb/README.md` has the details.
- 74HC4051 runs from 2 to 6 V; select lines and analog path are at 3.3 V.
- XIAO RP2040: D0-D2 are the three ADC inputs, D8-D10 the select lines, D7 the half-duplex split link.
  3V3 powers sensors and muxes and feeds the other half over the TRRS tip, as TOTEM's wired build does.
  D3 to D6 and 5V are unconnected. That puts both halves on one XIAO regulator: 38 sensors at 2 mA typical
  (4 mA maximum at 3.3 V) plus two RP2040s is about 130 mA typical, 200 mA worst case, against the 500 mA Seeed
  gives for the 3V3 pin.
- TRRS: tip VCC (ring 1 tied to it), ring 2 DATA, sleeve GND. One wire carries the link both ways, so both
  halves are wired the same and a turned-over board needs no swap.

## Still to do

- Firmware: tune actuation on real switches; rapid trigger and VIA settings are not implemented yet.
- Print the mock and the plate and fit-test them in the shell before ordering boards.
- Check the routing in KiCad (`pcb/routes.py` has the plan), then run `pcb/production.sh`.
- Confirm the sensor pinout on one part before ordering 40 of them.
- Flash the XIAO before final assembly: its BOOTSEL button is unreachable once the plate and shell are on, so
  keep a `QK_BOOT` key in the keymap.

## Regenerating

Case: `openscad --enable=roof -D 'part="shell"' -D 'side="left"' -o case/stl/totemhe_shell_left.stl case/totem_he_case.scad`
(OpenSCAD 2025 or newer for `roof()`; parts: shell, plate, pcb, assembly). PCB mock: `pcb_mock.scad` with
`-D 'part="none"'`. Key positions, holes, XIAO and TRRS come from `case/totem_geometry.scad`. The case reads it
directly; the PCB is generated from it with Ergogen (`pcb/build.sh`). PCB order files: `pcb/production.sh`.
Firmware: `firmware/build.sh`. Everything runs in Docker (OpenSCAD, Ergogen, KiCad 8, QMK).

The viewer, `case/totem-he-case.html`, shows both halves with a separate material for the top shell and the plate
(matte filament, Bambu Lab Galaxy Nebulae, matte or polished aluminium, each with its colours), keycap profile
(Cherry, DSA, LSA), keycap colour, and a few ready-made combinations.
