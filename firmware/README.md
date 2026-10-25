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
`qmk/the_he/he_map.h` (pins, which channels carry a sensor, key names), `qmk/the_he/keyboard.json` (matrix
size and a layout placed from the board's key positions) and `via/tot-he-m.json` (the same layout for VIA, with
the actuation menu). It follows each sensor output to its mux channel and
each mux to a XIAO pin, and stops without writing anything if a connection is unusable:

- every mux: VCC on pin 16, GND, VEE and E (active low) on GND, common Z on a XIAO pin with an ADC (GP26 to 29),
  S0 to S2 on the same three XIAO pins in the same order as the other muxes
- every sensor output on exactly one mux input, no two keys on one channel, all 19 keys present
- XIAO 3V3 on VCC, 5V unconnected, TRRS tip VCC and sleeve GND, ring 2 on a XIAO pin (the half-duplex link, D7)
- both halves on the same XIAO pins, no net shared between them, and both in agreement with `mux_map.json`

Pin data: 74HC4051 from the Nexperia datasheet (rev 12, table 2), XIAO RP2040 from the Seeed wiki.

## Flashing

Hold BOOT while plugging a half in (or double-tap RESET once QMK is on it); the XIAO mounts as the RPI-RP2 drive.
Drag `uf2/the_he_left.uf2` onto the left half and `uf2/the_he_right.uf2` onto the right: each stores its side on
first boot, since the board has no handedness pin. With the QMK CLI, `qmk flash -kb the_he -km default -bl
uf2-split-left` (or `-right`) does the same. To reach the bootloader from the keyboard, hold Esc and press T or Y
(layer 3), or press Z X C V or M , . / together. `uf2/the_he_first.uf2` is the first build that ran on the board
(before the calibration, averaging and glitch filtering), kept as a fallback.

## Wiring test

Flash `the_he_diag.uf2` on one half at a time, plug that half in alone, and run `qmk console`. Every five
seconds it prints each sensor's mux, channel, key name, rest reading and a verdict; a sensor that idles near a
rail (below 150 or above 870 of 1023, where a DRV5055 rests near 512) is flagged, which is how a
wrong sensor pinout or a dry joint shows up. Pressing a key prints its name, so a key that reports under another
name has its sensor on the wrong channel.

Without the QMK CLI, flash `the_he_typediag.uf2` instead and focus a text editor with a US (ABC) layout: about
three seconds after boot it types each sensor's rest reading, noise and verdict, then asks for every key to be
pressed once and, 45 s later, types each key's lowest and highest reading, swing, press count and the order in
which presses were detected. The keys send nothing while it runs.

## VIA

Flash `uf2/the_he_via_left.uf2` and `uf2/the_he_via_right.uf2` (or `the_he_via.uf2` on a half that already knows
its side). In VIA (usevia.app, in a Chromium-based browser), turn on "Show Design tab" under Settings, load
`via/tot-he-m.json` in the Design tab, then connect the half that is plugged in. The keymap tab edits all layers;
the Hall effect tab sets, in 0.1 mm of key travel:

- Actuation point, 1.0 to 3.8 mm (default 2.0)
- Release point, 0.8 mm up to 0.2 mm shallower than the actuation point (default 1.6)
- Rapid trigger, off by default. When on, a key still fires first at the actuation point, then lets go as soon as
  it rises by the release sensitivity from its deepest point and fires again as soon as it sinks by the press
  sensitivity, until it comes back above the release point. Both sensitivities 0.2 to 2.0 mm (default 0.3)

Changes apply at once and are saved to the USB half's EEPROM; that half sends them to the other half every half
second, so both halves always use the USB half's values. Depths come from a model of the magnet's field: the hall
output grows with the inverse cube of the magnet's distance, so the reading barely moves in the first millimetre
and races near the bottom. The scan maps each key's share of its full swing to a depth with that model
(he_matrix.c, depth_lut), using the travel (4.0 mm) and the magnet-to-sensor gap at the bottom (HE_GAP_DMM, 2.0 mm,
an estimate) from config.h; if keys fire deeper than set, raise the gap, if shallower, lower it. The sensor noise
sets the shallowest usable actuation at about 1 mm: a key never fires before its reading moves 15 counts. A key
that has not been pressed since boot assumes a full swing of 350 counts until it learns its own. On Linux VIA needs
read and write access to the keyboard's hidraw device (a udev rule for vendor `746d`, product `7e57`). VIA refuses
QMK's placeholder vendor id 0xFEED, hence 0x746D ("tm", unassigned in usb.ids).

## Controller layer

Layer 4 turns W A S D into an analog stick: the keyboard also shows up as a USB gamepad, and each axis is the depth
of one key minus the opposite one, so a light press walks and a full press runs, and A with D cancel out. The stick
starts at the first movement a key makes: at boot each key's resting noise is measured, and the stick's depth is
counted from the edge of it, so it rises from 0 as soon as the reading can be told apart from rest and is full at
3.8 mm, just short of bottom-out. Hold Esc and press G to toggle it (the same on the way out); every other key
falls through to layer 0 and types as usual. In VIA the four stick keycodes are under Custom as Stick up, left,
down and right, so the stick can go on any keys, and QMK's gamepad buttons JS_0 to JS_15 can be put on keys with
the Any key. The Controller layer menu adds an optional dead zone (0 to 2.0 mm, default 0) and sets the depth for
full deflection. The stick runs on the USB half and reads that half's keys only, so with W A S D on the left the
left half has to be the one plugged in. It is a generic HID gamepad, not an Xbox controller: Linux and Steam take
it as it is, Windows games that only accept XInput need Steam Input or a mapper.

## Keymap

`keymaps/default` (and `keymaps/via`, the same layout as VIA's starting point) is the Ferris Sweep ZMK config
(Triver1/zmk-config) without home-row mods. Layer 0 is QWERTY with Ctrl and Alt on the outer bottom keys, and on the
thumbs, left to right: Shift, Space, Esc (hold: layer 3) | Enter (hold: layer 2), Backspace (hold: layer 1), GUI.
Layer 1 has symbols on the top row, digits on the home row and brackets and programming symbols below; layer 2 the
F-keys, arrows, Home/End, Delete and the modifiers under the left hand; layer 3 the bootloader (T, Y), print screen,
volume and brightness, and the controller layer toggle (G). Layer-taps decide after 180 ms with permissive hold. I + O
together is Backspace.

## Settings

`config.h`: defaults and limits for the actuation and release depths and rapid trigger (VIA changes the live
values, see above), the depth model's travel and gap, and the noise floors: 15 counts to fire, 8 to release, and a
separate 40 counts for the glitch filter that drops a scan where most keys jumped at once. A key learns its travel
from its first confirmed press.
