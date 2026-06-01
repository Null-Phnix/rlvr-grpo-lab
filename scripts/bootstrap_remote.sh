#!/usr/bin/env bash
set -euo pipefail

INSTALL_TRAIN=false
if [ "${1:-}" = "--train" ]; then
  INSTALL_TRAIN=true
  shift
fi

UV_BIN="${HOME}/.local/bin/uv"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"

if ! command -v uv >/dev/null 2>&1 && [ ! -x "${UV_BIN}" ]; then
  curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
  sh /tmp/uv-install.sh
fi

if command -v uv >/dev/null 2>&1; then
  UV_CMD="uv"
else
  UV_CMD="${UV_BIN}"
fi

"${UV_CMD}" python install 3.12
if [ "${INSTALL_TRAIN}" = true ]; then
  "${UV_CMD}" sync --locked --extra train --extra dev
else
  "${UV_CMD}" sync --locked --extra dev
fi

echo
if [ "${INSTALL_TRAIN}" = true ]; then
  echo "Training workspace ready."
else
  echo "Dev workspace ready."
  echo "For training dependencies, run:"
  echo "bash scripts/bootstrap_remote.sh --train"
fi
