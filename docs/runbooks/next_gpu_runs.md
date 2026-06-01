# Next GPU Runs

This runbook is ordered to avoid wasting rented GPU time on stale branches.

## Pod Setup

After cloning or syncing this repo on a pod, install the training environment:

```bash
bash scripts/bootstrap_remote.sh --train
```

The GPU scripts use `uv run python` by default. If the pod has a prebuilt venv that should be used instead, set `RLVR_PYTHON`:

```bash
export RLVR_PYTHON=/root/rlvr-venv/bin/python
```

## Current Promoted Baseline

Use this as the 3B model-selection baseline:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_128.yaml
```

Expected snapshot from the promoted run:

- output: `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_128`
- exact: `107/128`
- strict final line: `86/128`
- trailing text: `0/128`

Larger held-out check:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512.yaml
```

Expected snapshot:

- output: `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512`
- exact: `429/512`
- strict final line: `361/512`
- trailing text: `0/512`

The previous boundary-SFT baseline was `427/512` exact and `257/512` strict final line. Treat v4 as a contract-cleanliness promotion with no observed exact regression, not as a large exact-accuracy gain.

## Completed 3B Scale-Up

The unfiltered v2 2048-example scale-up is rejected:

- step 100: `105/128` exact, `59/128` strict final line
- step 200: `101/128` exact, `65/128` strict final line

The v3 marker-line rewrite branch is also rejected as a tradeoff:

- `104/128` exact, `100/128` strict final line

The promoted v4 branch uses:

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_3b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_3b_boundary_sft_train2048_source_finalline.jsonl \
  --require-source-final-line
```

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_3b_boundary_sft_v4_source_finalline.yaml
```

## Next Phase: 7B Source-Final-Line Boundary SFT

Do not use `configs/cloud_7b_grpo.yaml` as the next 7B experiment. Do not port the rejected unfiltered 3B v2 recipe directly.

Generate 7B pseudo-labels:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_7b_train2048_strict_final_stopaware_pseudo.yaml
```

Build the 7B SFT dataset:

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_7b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_7b_boundary_sft_train2048_source_finalline.jsonl \
  --require-source-final-line
```

Train the 7B adapter:

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_7b_boundary_sft_v2_source_finalline.yaml
```

Evaluate the 128-example gate:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128.yaml
```

Or run the guarded end-to-end script:

```bash
bash scripts/run_gpu_7b_boundary_sft_v2_source_finalline.sh --approved-after-3b-v4
```

Only add `--eval-512` after the 128-example gate is worth promoting:

```bash
bash scripts/run_gpu_7b_boundary_sft_v2_source_finalline.sh --approved-after-3b-v4 --eval-512
```

The 7B source-final-line script refuses to run without `--approved-after-3b-v4` so it is not launched by accident.

## Promotion Rules

- Never promote a metric without an artifact path.
- Never promote a checkpoint without a baseline comparison.
- Keep cleanup GRPO labeled as a format tradeoff unless it beats boundary SFT on exact accuracy at the same token budget.
- Keep large checkpoints and full generated samples out of Git.
- Commit small evidence snapshots under `docs/results/`.
- Record config, command, output dir, summary, sample comparison, and conclusion in the ledger.
