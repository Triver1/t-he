# THE

A wired, hall-effect split keyboard on TOTEM's layout (GEIGEIGEIST/TOTEM rev 0.3, CC BY-NC-SA 4.0) scaled to MX
spacing, for MX-style magnetic switches (Gateron KS-20 class) and a Seeed XIAO RP2040 per half.

## Parts per half

| Part | Where |
| --- | --- |
| Shell, 3D printed deck-down, no supports | `case/stl/totemhe_shell_<side>.stl` |
| Plate with standoffs and the thumb-wing wall, printed top-down, no supports | `case/stl/totemhe_plate_<side>.stl` |
| PCB, the base of the stack, all parts on the switch side | `pcb/out/<side>/pcbs/totem_he_<side>.kicad_pcb` |
| PCB mock with component blocks for fit tests | `case/stl/totemhe_pcbmock_<side>.stl` |
| 4x M2 x 10 screws, from under the PCB through standoff and plate into the deck; >= 1.5 mm bumpers under the PCB | |

Stack: PCB 1.6, plate top 5.0 above the PCB, deck 6.0 above the plate. 12.6 mm tall, 6.6 at the thumb wing.
Both halves are separate files; the print files are turned over for printing (a rotation, so left stays left).

## Electronics

Same scheme as Boardloaf-HE: a linear hall sensor under every stem magnet, read through 74HC4051 muxes by the
XIAO's ADC. No diodes, no matrix. Per half: 19x SLSS49E-3 (SOT-23, LCSC C2904393), 22x 100 nF 0805,
3x 74HC4051 SOIC-16, 1x XIAO RP2040, 1x PJ-320A TRRS. Wiring, mux assignment and firmware notes are in
`pcb/README.md`. `pcb/netcheck.py` verifies every pad's net against that design; `pcb/pcbfit.py` verifies the
board against the case geometry. Both pass for both halves.

Compatibility, checked against the datasheets:

- SLSS49E-3 runs from 3 to 12 V, so the XIAO's 3.3 V is in range; its output swings around half the supply, inside
  the RP2040's 3.3 V ADC range. SOT-23 pins are 1 VDD, 2 GND, 3 Vout (Boardloaf-HE's symbol has 2 and 3 swapped).
- 74HC4051 runs from 2 to 6 V; select lines and analog path are at 3.3 V.
- XIAO RP2040: D0-D2 are the three ADC inputs, D4/D5/D8 the select lines, D6/D7 the UART for the split link.
  3V3 powers sensors and muxes and feeds the other half over the TRRS tip, as TOTEM's wired build does.
  D3, D9, D10 and 5V are unconnected.
- TRRS: tip VCC, ring 1 TX, ring 2 RX, sleeve GND. Both halves are wired the same, so the firmware swaps TX and
  RX on one side (QMK: `SERIAL_USART_PIN_SWAP`).

## Still to do

- Route the PCBs by hand (the generated boards have all nets and placements but no traces). Copy a `.kicad_pro`
  from `pcb/mkpro.py` next to the board so KiCad loads the design rules.
- Firmware: Boardloaf-HE's QMK fork with this pin map and key count.
- Print the mock and the plate and fit-test them in the shell before ordering boards.

## Regenerating

Case: `openscad --enable=roof -D 'part="shell"' -D 'side="left"' -o stl/totemhe_shell_left.stl case/totem_he_case.scad`
(OpenSCAD 2025 or newer for `roof()`; parts: shell, plate, pcb, assembly). PCB: `pcb/build.sh` (Ergogen in a Node
container). Key positions, holes, XIAO and TRRS come from `case/totem_geometry.scad`; the case and the PCB read the
same file, so a layout change flows to both.
