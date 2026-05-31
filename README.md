# RLVR GRPO Lab

Local-first RLVR/post-training workspace for reasoning models.

The immediate goal is not to claim a DeepSeek-R1 reproduction. The goal is to build a clean, inspectable GRPO loop with verifiable rewards, run it on tiny models locally, then scale the exact same harness to rented GPUs for 3B/7B experiments.

## Hardware Plan

- MacBook: editing, docs, reward/eval development.
- Linux RTX 4060 8GB: CUDA smoke tests with 0.5B/1.5B models.
- Rented GPU: final 3B/7B runs once the loop is stable.

## First Milestone

Train a small Qwen base/instruct model on GSM8K-style prompts using:

- exact-answer math reward
- format reward
- small max completion length
- LoRA adapter training
- reproducible config files

Expected artifact:

- baseline eval
- 20-100 step GRPO smoke run
- post-run eval
- reward curves and sample completions
- notes on reward hacking/failure cases

## Remote Bootstrap

From this directory on the Linux box:

```bash
bash scripts/bootstrap_remote.sh
```

That installs `uv` into `~/.local/bin` if needed, installs Python 3.12 through `uv`, and syncs the dev dependencies.

For the full training stack:

```bash
~/.local/bin/uv sync --extra train --extra dev
```

## Sanity Checks

```bash
~/.local/bin/uv run python scripts/doctor.py
~/.local/bin/uv run pytest
```

## Local 4060 Smoke Run

After syncing the train extras:

```bash
~/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_local_4060.yaml
```

```bash
~/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/local_4060_smoke.yaml
```

This config is intentionally conservative. It is for correctness, logging, and memory profiling, not leaderboard scores.

Evaluate the LoRA checkpoint after training:

```bash
~/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_local_4060.yaml \
  --adapter-path outputs/local_4060_smoke/checkpoint-25 \
  --output-dir outputs/evals/local_4060_post_smoke
```

Compare two eval summaries:

```bash
~/.local/bin/uv run python -m rlvr_lab.compare_evals \
  outputs/evals/local_4060_baseline/summary.json \
  outputs/evals/local_4060_post_smoke/summary.json
```

Compare sample-level wins/losses and write a Markdown report:

```bash
~/.local/bin/uv run python -m rlvr_lab.compare_samples \
  outputs/evals/cloud_3b_post_strict_grpo_resume_pilot_500_128 \
  outputs/evals/cloud_3b_final_line_exact_grpo_after_500_128 \
  --baseline-label checkpoint-500 \
  --candidate-label final-line-exact \
  --output outputs/evals/cloud_3b_final_line_exact_grpo_after_500_128/comparison_vs_checkpoint500.md
```

Prompt sweep configs:

```bash
~/.local/bin/uv run python -m rlvr_lab.eval_model --config configs/eval_local_4060_plain.yaml
~/.local/bin/uv run python -m rlvr_lab.eval_model --config configs/eval_local_4060_answer_first.yaml
```

## Cloud 7B Run

Use the cloud config only after the smoke run is stable:

```bash
~/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/cloud_7b_grpo.yaml
```

Adjust batch sizes and `num_generations` based on the actual GPU.
