#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
source scripts/gpu_run_lib.sh

run_eval_config configs/eval_cloud_3b_train2048_strict_final_stopaware_pseudo.yaml

run_logged build_cloud_3b_boundary_sft_train2048 \
  run_python_module rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_3b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_3b_boundary_sft_train2048.jsonl
checksum_dataset_artifacts outputs/datasets/cloud_3b_boundary_sft_train2048.jsonl

run_logged cloud_3b_boundary_sft_v2 \
  run_python_module rlvr_lab.train_format_sft \
  --config configs/cloud_3b_boundary_sft_v2.yaml
checksum_adapter_dir outputs/cloud_3b_boundary_sft_v2

run_eval_config configs/eval_cloud_3b_boundary_sft_v2_strict_stopaware_384_128.yaml

if [ -d outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_128 ]; then
  run_python_module rlvr_lab.compare_samples \
    outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_128 \
    outputs/evals/cloud_3b_boundary_sft_v2_strict_stopaware_384_128 \
    --baseline-label boundary-sft-v1-384 \
    --candidate-label boundary-sft-v2-384 \
    --output outputs/evals/cloud_3b_boundary_sft_v2_strict_stopaware_384_128/comparison_vs_boundary_sft_v1_384.md
  checksum_eval_dir outputs/evals/cloud_3b_boundary_sft_v2_strict_stopaware_384_128
else
  echo "Skipping v1 comparison: baseline samples are not present on this machine." >&2
fi

if [ "${1:-}" = "--eval-512" ]; then
  run_eval_config configs/eval_cloud_3b_boundary_sft_v2_strict_stopaware_384_512.yaml
fi
