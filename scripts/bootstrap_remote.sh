#!/usr/bin/env bash
set -euo pipefail

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
"${UV_CMD}" sync --extra dev

echo
echo "Dev workspace ready."
echo "For training dependencies, run:"
echo "${UV_CMD} sync --extra train --extra dev"
