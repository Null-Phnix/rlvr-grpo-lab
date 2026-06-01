#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/gpu_run_lib.sh

require_path \
  outputs/cloud_3b_boundary_sft_warmup \
  "Mirror the current boundary SFT adapter onto this pod before running the larger baseline eval."

run_eval_config configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_512.yaml

if [ "${1:-}" = "--full" ]; then
  run_eval_config configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_full.yaml
fi
