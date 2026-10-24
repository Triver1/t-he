# Tot-HE-m firmware (QMK)

QMK keyboard definition for Tot-HE-m: XIAO RP2040 per half, three 74HC4051 muxes, 19 linear
hall sensors per half, half-duplex serial over one TRRS wire. The scan follows Boardloaf-HE's port (Cipulot / byungyoonc):
one ADC pin per mux, shared select lines, row = mux, column = channel. The key logic follows Hector: each key
measures its rest reading at boot, reads deflection in either direction so magnet polarity does not matter, and
learns its full travel the first time it is pressed.

```bash
./build.sh
```

`build.sh` runs `gen_firmware.py`, copies `qmk/the_he` into a QMK checkout (cloned on first run, about 500 MB of
submodules) and compiles in `ghcr.io/qmk/qmk_cli`. Output: `uf2/the_he_default.uf2`, `uf2/the_he_diag.uf2`.

## Generated from the boards

`gen_firmware.py` reads both halves from `../pcb/totem_he.kicad_pcb` and writes
`qmk/the_he/he_map.h` (pins, which channels carry a sensor, key names) and `qmk/the_he/keyboard.json` (matrix
size and a layout placed from the board's key positions). It follows each sensor output to its mux channel and
each mux to a XIAO pin, and stops without writing anything if a connection is unusable:

- every mux: VCC on pin 16, GND, VEE and E (active low) on GND, common Z on a XIAO pin with an ADC (GP26 to 29),
  S0 to S2 on the same three XIAO pins in the same order as the other muxes
- every sensor output on exactly one mux input, no two keys on one channel, all 19 keys present
- XIAO 3V3 on VCC, 5V unconnected, TRRS tip VCC and sleeve GND, ring 2 on a XIAO pin (the half-duplex link, D7)
- both halves on the same XIAO pins, no net shared between them, and both in agreement with `mux_map.json`

Pin data: 74HC4051 from the Nexperia datasheet (rev 12, table 2), XIAO RP2040 from the Seeed wiki.

## Flashing

Hold BOOT while plugging a half in (or double-tap RESET once QMK is on it), then flash each half once with its
handedness, since the board has no handedness pin:

```bash
qmk flash -kb the_he -km default -bl uf2-split-left
```

and `-bl uf2-split-right` on the other half. `QK_BOOT` is on both outer keys of layer 1.

## Wiring test

Flash `the_he_diag.uf2` on one half at a time, plug that half in alone, and run `qmk console`. Every five
seconds it prints each sensor's mux, channel, key name, rest reading and a verdict; a sensor that idles near a
rail (below 150 or above 870 of 1023, where a DRV5055 rests near 512) is flagged, which is how a
wrong sensor pinout or a dry joint shows up. Pressing a key prints its name, so a key that reports under another
name has its sensor on the wrong channel.

## Settings

`config.h`: actuation at 45 % of each key's learned travel, release at 30 %, never below 25 counts; 150 counts
of travel assumed until a key has been pressed once. No rapid trigger or VIA configuration yet.
