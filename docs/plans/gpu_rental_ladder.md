# GPU Rental Ladder

Date: 2026-05-30

## Current Local Gate

Local 4060 experiments established two branches:

- Format-control branch: `final_only` SFT -> GRPO gives 128/128 strict final-line format on the 128-example eval, but does not improve math beyond the original 0.5B baseline.
- Reasoning branch: GSM8K-rationale SFT -> GRPO gives useful training rewards, but the 0.5B local run is too small/short to improve held-out eval.

## First Rented Run

Use a single high-memory GPU for a 3B reasoning run before trying 7B.

Configs:

- SFT warmup: `configs/cloud_3b_rationale_sft_warmup.yaml`
- GRPO continuation: `configs/cloud_3b_strict_grpo_after_rationale_sft.yaml`
- Eval: `configs/eval_cloud_3b_strict_final.yaml`

Commands:

```bash
uv sync --extra train --extra dev
uv run python -m rlvr_lab.eval_model --config configs/eval_cloud_3b_strict_final.yaml
uv run python -m rlvr_lab.train_format_sft --config configs/cloud_3b_rationale_sft_warmup.yaml
uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/cloud_3b_strict_grpo_after_rationale_sft.yaml
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_strict_final.yaml \
  --adapter-path outputs/cloud_3b_strict_grpo_after_rationale_sft/checkpoint-500 \
  --output-dir outputs/evals/cloud_3b_post_strict_grpo
```

## Promotion Gates

Move from 3B to 7B only if the 3B run shows:

- exact accuracy improves over the 3B strict-prompt baseline
- strict final-line rate stays above 90%
- trailing-text rate stays below 5%
- completion clipping is below 20%
- train logs show nonzero exact-answer reward on many batches, not just format reward

## If The 3B Run Fails

Do not scale the same setup blindly. Fix the local/cloud harness first:

- increase rationale SFT warmup examples or steps
- lower final-line reward if it suppresses reasoning
- raise `max_completion_length` if clipping appears
- increase `num_generations` if reward standard deviation is often zero
- add a small held-out train-split eval so the cloud run can be checked before the full test eval

## Research Split

Keep two branches separate:

- Engineering branch: SFT warmup -> GRPO, optimized for stable behavior and useful results.
- RL-only branch: base model -> GRPO with no SFT, used later for the cleaner research claim.

The engineering branch is the right first rental target because it validates the infrastructure and gives a better chance of a meaningful curve before spending on 7B experiments.
