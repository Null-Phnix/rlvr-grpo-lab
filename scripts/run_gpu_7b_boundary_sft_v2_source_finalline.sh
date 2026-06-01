#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" != "--approved-after-3b-v4" ]; then
  echo "Refusing to run 7B source-final-line boundary SFT without explicit approval." >&2
  echo "Run this only after reviewing the promoted 3B v4 result:" >&2
  echo "  bash scripts/run_gpu_7b_boundary_sft_v2_source_finalline.sh --approved-after-3b-v4" >&2
  exit 2
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/gpu_run_lib.sh

run_eval_config configs/eval_cloud_7b_train2048_strict_final_stopaware_pseudo.yaml

run_logged build_cloud_7b_boundary_sft_train2048_source_finalline \
  run_python_module rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_7b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_7b_boundary_sft_train2048_source_finalline.jsonl \
  --require-source-final-line
checksum_dataset_artifacts outputs/datasets/cloud_7b_boundary_sft_train2048_source_finalline.jsonl

run_logged cloud_7b_boundary_sft_v2_source_finalline \
  run_python_module rlvr_lab.train_format_sft \
  --config configs/cloud_7b_boundary_sft_v2_source_finalline.yaml
checksum_adapter_dir outputs/cloud_7b_boundary_sft_v2_source_finalline

run_eval_config configs/eval_cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128.yaml

if [ "${2:-}" = "--eval-512" ]; then
  run_eval_config configs/eval_cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_512.yaml
fi
