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

## Completed 7B Source-Final-Line Boundary SFT

Do not use `configs/cloud_7b_grpo.yaml` as the next 7B experiment. Do not port the rejected unfiltered 3B v2 recipe directly.

The guarded 7B source-final-line script was run without `--eval-512`:

```bash
bash scripts/run_gpu_7b_boundary_sft_v2_source_finalline.sh --approved-after-3b-v4
```

Result:

- 7B base 128 gate: `114/128` exact, `125/128` strict final line, `0/128` trailing
- 7B train pseudo-label pass: `1918/2048` exact, `2012/2048` strict final line, `0/2048` trailing
- source-final-line dataset: `1895/2048` selected
- 7B source-final-line adapter 128 gate: `109/128` exact, `127/128` strict final line, `0/128` trailing
- sample comparison vs base: 2 exact wins, 7 exact losses
- tolerant numeric rescore: adapter moves to `110/128`, still below the base `114/128`

Conclusion: rejected. The 7B base model already follows the answer contract well, so this SFT branch mostly adds reasoning drift for only two additional strict-final-line cases.

## Completed 7B Base 512/Full Eval

The stronger no-adapter 7B baseline is complete. Reproduce the 512-example check with:

```bash
bash scripts/run_gpu_7b_base_eval.sh
```

Reproduce the full GSM8K test split with:

```bash
bash scripts/run_gpu_7b_base_eval.sh --full
```

These use the strict prompt, 384-token generation budget, stop-aware postprocessing, and the tolerant numeric scorer from `rlvr_lab.rewards.answers_match`.

Results:

- 512 check: `455/512` exact, `502/512` strict final line, `0/512` trailing
- full test split: `1164/1319` exact, `1296/1319` strict final line, `0/1319` trailing

Conclusion: the 7B base policy is the current 7B reference. Do not spend more GPU on boundary SFT unless the target changes beyond final-line cleanup.

## Next Phase: 7B Error Analysis

Before launching another training run, inspect the full-test failures and decide whether the project needs broader eval coverage or a genuinely new training objective. A useful next step is to summarize the wrong examples by failure type and compare the base 7B full-test failures against the rejected 7B adapter's 128-gate losses.

## 7B Commands For Reproduction

Run the 7B base 128-example comparison baseline first:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_7b_strict_stopaware_384_128.yaml
```

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

Compare adapter samples against the 7B base model:

```bash
uv run python -m rlvr_lab.compare_samples \
  outputs/evals/cloud_7b_strict_stopaware_384_128 \
  outputs/evals/cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128 \
  --baseline-label 7b-base-384 \
  --candidate-label 7b-boundary-sft-v2-source-finalline-384 \
  --output outputs/evals/cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128/comparison_vs_7b_base_384_128.md
```

Or run the guarded end-to-end script:

```bash
bash scripts/run_gpu_7b_boundary_sft_v2_source_finalline.sh --approved-after-3b-v4
```

Do not add `--eval-512` for the rejected adapter unless there is a diagnostic reason. With this flag, the script runs both the 7B base 512 eval and the adapter 512 eval, then writes the base-vs-adapter comparison:

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
