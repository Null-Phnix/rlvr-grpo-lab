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
~/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/local_4060_smoke.yaml
```

This config is intentionally conservative. It is for correctness, logging, and memory profiling, not leaderboard scores.

## Cloud 7B Run

Use the cloud config only after the smoke run is stable:

```bash
~/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/cloud_7b_grpo.yaml
```

Adjust batch sizes and `num_generations` based on the actual GPU.
