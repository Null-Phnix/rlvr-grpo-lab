#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/gpu_run_lib.sh

run_eval_config configs/eval_cloud_7b_strict_stopaware_384_512.yaml

if [ "${1:-}" = "--full" ]; then
  run_eval_config configs/eval_cloud_7b_strict_stopaware_384_full.yaml
fi
