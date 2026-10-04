#!/bin/sh
# Checks the boards, regenerates the tables and builds both keymaps in QMK's Docker image.
# usage: build.sh [path to a qmk_firmware checkout]   (cloned into ./qmk_firmware when omitted)
set -e; cd "$(dirname "$0")"
python3 gen_firmware.py
Q=${1:-qmk_firmware}
if [ ! -d "$Q" ]; then
  git clone -q --depth 1 https://github.com/qmk/qmk_firmware.git "$Q"
  git -C "$Q" submodule update --init --depth 1 lib/chibios lib/chibios-contrib lib/pico-sdk lib/printf lib/lufa
fi
rm -rf "$Q/keyboards/the_he" && cp -R qmk/the_he "$Q/keyboards/the_he"
docker run --rm -v "$(cd "$Q" && pwd)":/qmk_firmware -w /qmk_firmware ghcr.io/qmk/qmk_cli:latest \
  sh -c 'qmk compile -kb the_he -km default && qmk compile -kb the_he -km diag'
mkdir -p uf2 && cp "$Q"/the_he_default.uf2 "$Q"/the_he_diag.uf2 uf2/
