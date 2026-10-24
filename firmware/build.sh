#!/bin/sh
# Checks the boards, regenerates the tables and builds the keymaps in QMK's Docker image: default, diag, typediag
# (types its test report into a text editor) and left/right (the default keymap with its side built in).
# usage: build.sh [path to a qmk_firmware checkout]   (cloned into ./qmk_firmware when omitted)
set -e; cd "$(dirname "$0")"
python3 gen_firmware.py
Q=${1:-qmk_firmware}
if [ ! -d "$Q" ]; then
  git clone -q --depth 1 https://github.com/qmk/qmk_firmware.git "$Q"
  git -C "$Q" submodule update --init --depth 1 lib/chibios lib/chibios-contrib lib/pico-sdk lib/printf lib/lufa
fi
rm -rf "$Q/keyboards/the_he" && cp -R qmk/the_he "$Q/keyboards/the_he"
# left and right builds: the default keymap with the half's side stored on first boot (EE_HANDS, no handedness pin)
for s in left right; do
  cp -R "$Q/keyboards/the_he/keymaps/default" "$Q/keyboards/the_he/keymaps/$s"
  printf '\n#define INIT_EE_HANDS_%s\n' "$(echo $s | tr a-z A-Z)" >> "$Q/keyboards/the_he/keymaps/$s/config.h"
done
docker run --rm -v "$(cd "$Q" && pwd)":/qmk_firmware -w /qmk_firmware ghcr.io/qmk/qmk_cli:latest \
  sh -c 'for k in default diag typediag left right; do qmk compile -kb the_he -km $k || exit 1; done'
mkdir -p uf2 && for k in default diag typediag left right; do cp "$Q/the_he_$k.uf2" uf2/; done
