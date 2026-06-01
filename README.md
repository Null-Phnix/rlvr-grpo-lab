# RLVR GRPO Lab

Config-driven RLVR/GRPO post-training experiments for reasoning models, with verifiable math rewards, strict answer-contract evals, and sample-level error analysis.

This is not presented as a DeepSeek-R1 reproduction. The goal is narrower and more useful: build an inspectable training/eval harness, run cheap local smoke tests, then scale the same workflow to rented GPUs for 3B/7B experiments.

## What This Repo Contains

- GRPO training entrypoint with LoRA adapter support
- optional SFT warmup path for answer-format experiments
- verifiable GSM8K-style exact-answer rewards
- strict final-line answer rewards and trailing-text penalties
- config files for local RTX 4060 smoke runs and RunPod A100 3B pilots
- eval outputs with `summary.json` and `samples.jsonl`
- sample-level comparison tooling for wins/losses and formatting regressions
- run notes and an experiment ledger for promoted experiments

## Current Findings

The first serious cloud run used `Qwen/Qwen2.5-3B-Instruct` on a RunPod A100-SXM4-80GB with a 512-example GSM8K training subset and a 128-example held-out eval.

| Run | Exact | Strict Final Line | Trailing Text | Avg Chars | Read |
| --- | ---: | ---: | ---: | ---: | --- |
| Base 3B strict prompt | 91/128 | 1/128 | 101/128 | 845.41 | Strong loose exact accuracy, bad output contract. |
| Rationale SFT warmup | 81/128 | 122/128 | 0/128 | 269.34 | Format fixed, exact accuracy dropped. |
| SFT -> GRPO pilot | 87/128 | 122/128 | 0/128 | 278.55 | Recovered some exact accuracy. |
| SFT -> GRPO resume 500 | 87/128 | 123/128 | 0/128 | 281.06 | Exact plateaued. |
| Checkpoint 500 -> final-line exact reward | 87/128 | 124/128 | 0/128 | 266.80 | Cleaner and shorter, exact still plateaued. |
| Base 3B -> final-line exact GRPO step 50 | 84/128 | 2/128 | 69/128 | 838.60 | No length collapse, but contract did not learn. |
| Base 3B -> contract-curriculum GRPO step 150 | 81/128 | 2/128 | 93/128 | 825.80 | Dense marker reward stayed learnable, but clean stopping still failed. |
| Base 3B strict stop-aware eval | 91/128 | 58/128 | 0/128 | 515.46 | Preserves base exact accuracy and removes trailing text without training. |
| Base 3B minimal stop-aware eval | 80/128 | 57/128 | 0/128 | 690.27 | Worse exact accuracy; not the next baseline. |

The current conclusion is that this rationale-SFT adapter chain learned the output contract but plateaued below the base model's loose exact accuracy. Longer GRPO and stricter final-line correctness did not move held-out exact accuracy. Starting fresh from the base 3B policy avoided the SFT length collapse, but strict final-line exactness was too sparse to learn directly. Adding dense marker/curriculum rewards kept marker correctness learnable during training, but did not teach clean stopping and worsened held-out exact accuracy.

Detailed records:

- [Experiment ledger](docs/runs/experiment_ledger.md)
- [RunPod A100 3B pilot notes](docs/runs/runpod_a100_3b_pilot.md)

## Latest Base-Policy Experiment

Run config:

```bash
~/.local/bin/uv run python -m rlvr_lab.train_grpo \
  --config configs/cloud_3b_base_final_line_exact_grpo_pilot.yaml
```

Eval it with:

```bash
~/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_strict_final_128.yaml \
  --adapter-path outputs/cloud_3b_base_final_line_exact_grpo_pilot/checkpoint-50 \
  --output-dir outputs/evals/cloud_3b_base_final_line_exact_grpo_pilot_step50_128
```

This run asked whether direct GRPO from the base 3B model can preserve the base model's reasoning quality while learning the strict final-line answer contract. It was early-stopped at checkpoint 50 because training metrics stayed at `final_line_exact_accuracy=0` and completions were usually clipped at the 384-token cap. The held-out eval was worse than base exact accuracy, so the next branch should use a denser contract curriculum rather than more steps of the same sparse final-line reward.

## Contract-Curriculum Result

The contract-curriculum run used dense rewards for correct answer markers, conversation-role leakage, and final-answer progress:

```bash
~/.local/bin/uv run python -m rlvr_lab.train_grpo \
  --config configs/cloud_3b_contract_curriculum_grpo.yaml
```

Training confirmed the dense signal was active: marker correctness stayed nonzero, and conversation leakage fell by the final training row. Held-out eval still failed the actual contract: only 2/128 examples had strict final-line format, and exact accuracy fell to 81/128. The model often emitted a correct `####` answer and then continued, sometimes by repeating prompt instructions. The next run should not spend more GPU on this reward mix; it needs a generation/stop-token or prompt-boundary intervention before more GRPO.

## Stop-Aware Analysis

The current failure mode is measurable without another training run:

```bash
~/.local/bin/uv run python -m rlvr_lab.analyze_samples \
  outputs/evals/cloud_3b_contract_curriculum_grpo_150_128 \
  --output outputs/evals/cloud_3b_contract_curriculum_grpo_150_128/failure_analysis.json
```

Oracle stop-after-marker analysis keeps exact accuracy unchanged while removing trailing text. On the base eval, it moves strict final-line format from 1/128 to 58/128 with exact still 91/128. On the contract-curriculum eval, it moves strict final-line format from 2/128 to 66/128 with exact still 81/128. That means the model often has a usable marked answer; the missing piece is termination.

The promoted A100 eval confirms the oracle read. `configs/eval_cloud_3b_strict_final_stopaware_128.yaml` keeps exact accuracy at 91/128, moves strict final-line format from 1/128 to 58/128, and removes all 101 trailing-text cases. `configs/eval_cloud_3b_minimal_final_stopaware_128.yaml` removes trailing text too, but drops exact accuracy to 80/128. The strict prompt plus stop-aware postprocessing is the current strongest base-policy baseline.

Stop-aware eval configs:

```bash
~/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_strict_final_stopaware_128.yaml
```

```bash
~/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_minimal_final_stopaware_128.yaml
```

## Hardware Plan

- MacBook: editing, docs, reward/eval development
- Linux RTX 4060 8GB: CUDA smoke tests with 0.5B/1.5B models
- rented GPU: 3B/7B runs once the local loop and reward objective are stable

## Remote Bootstrap

From this directory on the Linux box:

```bash
bash scripts/bootstrap_remote.sh
```

That installs `uv` into `~/.local/bin` if needed, installs Python through `uv`, and syncs the dev dependencies.

For the full training stack:

```bash
~/.local/bin/uv sync --extra train --extra dev
```

## Sanity Checks

```bash
~/.local/bin/uv run python scripts/doctor.py
~/.local/bin/uv run ruff check .
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

## Analysis Tools

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

Do not start with 7B blindly. Use the cloud 7B config only after the 3B base-policy branch improves held-out exact accuracy while keeping strict final-line format high.

```bash
~/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/cloud_7b_grpo.yaml
```

Adjust batch sizes and `num_generations` based on the actual GPU.
