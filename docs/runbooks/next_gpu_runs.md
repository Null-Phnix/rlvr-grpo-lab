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
  --config configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_128.yaml
```

Expected snapshot from the promoted run:

- output: `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_128`
- exact: `107/128`
- strict final line: `62/128`
- trailing text: `0/128`

## Phase 1: Larger 3B Baseline Eval

Run the current boundary-SFT adapter on a larger held-out set before new training:

```bash
bash scripts/run_gpu_3b_baseline_eval.sh
```

Optional full test-set sweep:

```bash
bash scripts/run_gpu_3b_baseline_eval.sh --full
```

Promote the 512/full result only after adding `summary.json`, `failure_analysis.json`, and a comparison report to `docs/results/`.

## Phase 2: Boundary SFT v2

Generate a larger pseudo-label set:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_train2048_strict_final_stopaware_pseudo.yaml
```

Build the v2 SFT dataset:

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_3b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_3b_boundary_sft_train2048.jsonl
```

Train the v2 adapter:

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_3b_boundary_sft_v2.yaml
```

Eval v2 on the 128-example gate:

```bash
bash scripts/run_gpu_3b_boundary_sft_v2.sh
```

If v2 matches or beats the current `107/128` exact baseline, run the 512-example eval:

```bash
bash scripts/run_gpu_3b_boundary_sft_v2.sh --eval-512
```

## Phase 3: 7B Boundary SFT

Start 7B only after the 3B v2 result is understood. Do not use `configs/cloud_7b_grpo.yaml` as the next 7B experiment.

Generate 7B pseudo-labels:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_7b_train2048_strict_final_stopaware_pseudo.yaml
```

Build the 7B SFT dataset:

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_7b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_7b_boundary_sft_train2048.jsonl
```

Train the 7B adapter:

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_7b_boundary_sft_v1.yaml
```

Evaluate the 7B adapter:

```bash
bash scripts/run_gpu_7b_boundary_sft_v1.sh --approved-after-3b
```

The 7B script refuses to run without `--approved-after-3b` so it is not launched by accident.

## Promotion Rules

- Never promote a metric without an artifact path.
- Never promote a checkpoint without a baseline comparison.
- Keep cleanup GRPO labeled as a format tradeoff unless it beats boundary SFT on exact accuracy at the same token budget.
- Keep large checkpoints and full generated samples out of Git.
- Commit small evidence snapshots under `docs/results/`.
- Record config, command, output dir, summary, sample comparison, and conclusion in the ledger.
