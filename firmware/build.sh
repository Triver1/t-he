#!/bin/sh
# Checks the boards, regenerates the tables and builds the keymaps in QMK's Docker image: default, diag, typediag
# (types its test report into a text editor), left/right (the default keymap with its side built in), via, and
# via_left/via_right (VIA support with the side built in).
# usage: build.sh [path to a qmk_firmware checkout]   (cloned into ./qmk_firmware when omitted)
set -e; cd "$(dirname "$0")"
python3 gen_firmware.py
Q=${1:-qmk_firmware}
if [ ! -d "$Q" ]; then
  git clone -q --depth 1 https://github.com/qmk/qmk_firmware.git "$Q"
  git -C "$Q" submodule update --init --depth 1 lib/chibios lib/chibios-contrib lib/pico-sdk lib/printf lib/lufa
fi
rm -rf "$Q/keyboards/tot_he_m" && cp -R qmk/tot_he_m "$Q/keyboards/tot_he_m"
# left and right builds: the default and via keymaps with the half's side stored on first boot (EE_HANDS, no handedness pin)
for s in left right; do
  for k in default via; do
    d=$([ $k = default ] && echo $s || echo ${k}_$s)
    cp -R "$Q/keyboards/tot_he_m/keymaps/$k" "$Q/keyboards/tot_he_m/keymaps/$d"
    printf '\n#define INIT_EE_HANDS_%s\n' "$(echo $s | tr a-z A-Z)" >> "$Q/keyboards/tot_he_m/keymaps/$d/config.h"
  done
done
docker run --rm -v "$(cd "$Q" && pwd)":/qmk_firmware -w /qmk_firmware ghcr.io/qmk/qmk_cli:latest \
  sh -c 'for k in default diag typediag left right via via_left via_right; do qmk compile -kb tot_he_m -km $k || exit 1; done'
mkdir -p uf2 && for k in default diag typediag left right via via_left via_right; do cp "$Q/tot_he_m_$k.uf2" uf2/; done
