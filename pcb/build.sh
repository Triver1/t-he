#!/bin/sh
# Generates config.yaml per half and runs Ergogen in a Node container. Output: out/<side>/
set -e
cd "$(dirname "$0")"
for side in left right; do
  /private/tmp/claude-501/-Users-tristan-Library-Application-Support-Claude-scratch-workspaces-1d799a2a-83a8-44e7-b3f6-0ede92584158-b533ac2d-be48-4c85-b5ea-c72372695c15-scratch-2026-09-21-cebd1e/ab84f27d-d236-483c-bcbb-faa68eef32d0/scratchpad/venv/bin/python gen_config.py $side /private/tmp/claude-501/-Users-tristan-Library-Application-Support-Claude-scratch-workspaces-1d799a2a-83a8-44e7-b3f6-0ede92584158-b533ac2d-be48-4c85-b5ea-c72372695c15-scratch-2026-09-21-cebd1e/ab84f27d-d236-483c-bcbb-faa68eef32d0/scratchpad
  rm -rf out/$side
  docker run --rm -v "$PWD":/w -w /w node:20 sh -c "npm i -g ergogen@4 >/dev/null 2>&1; ergogen . -o out/$side --debug 2>&1 | grep -v '^    at' | tail -3"
  cp config.yaml out/$side/config.yaml
done
