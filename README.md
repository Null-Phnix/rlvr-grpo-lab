# RLVR GRPO Lab

Config-driven RLVR/GRPO post-training experiments for reasoning models, with verifiable math rewards, strict answer-contract evals, and sample-level error analysis.

This is not presented as a DeepSeek-R1 reproduction. The goal is narrower and more useful: build an inspectable training/eval harness, run cheap local smoke tests, then scale the same workflow to rented GPUs for 3B/7B experiments.

## Current Promoted Baseline

**Boundary SFT v4 source-final-line + strict stop-aware 384-token eval** is the current promoted baseline.

- 128-example gate: `107/128` exact, `86/128` strict final line, `0/128` trailing text.
- 512-example check: `429/512` exact, `361/512` strict final line, `0/512` trailing text.
- Artifact: `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512/summary.json`
- Public evidence: [`docs/results/boundary_sft_v4_source_finalline_384_stopaware/summary_512.json`](docs/results/boundary_sft_v4_source_finalline_384_stopaware/summary_512.json)
- Reason: it matches the previous 128-example exact score, improves the 512-example exact score by 2 answers, and substantially improves strict final-line format without reintroducing trailing text.

Do not scale `configs/cloud_7b_grpo.yaml` as the next 7B experiment. It is a legacy GRPO config that does not reflect the current boundary-SFT lesson. The next rented-GPU work should port the source-final-line boundary-SFT recipe to 7B, not the older unfiltered v2 scale-up.

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
| Boundary SFT raw eval | 100/128 | 51/128 | 5/128 | 488.16 | Self-distilled boundary adapter improves exact and mostly learns to stop. |
| Boundary SFT stop-aware eval | 100/128 | 53/128 | 0/128 | 480.88 | Confirms answer quality gain is not a trailing-text artifact. |
| Boundary SFT -> cleanup GRPO step 40 raw eval | 100/128 | 57/128 | 3/128 | 477.59 | Light cleanup GRPO preserves exact, improves final-line format, and trims raw trailing cases. |
| Boundary SFT -> cleanup GRPO step 40 stop-aware eval | 100/128 | 57/128 | 0/128 | 477.29 | Same exact score with clean post-answer termination. |
| Boundary SFT 384-token stop-aware eval | 107/128 | 62/128 | 0/128 | 494.98 | Larger eval budget recovers clipped correct answers; best current exact score. |
| Boundary cleanup GRPO 384-token stop-aware eval | 103/128 | 65/128 | 0/128 | 494.20 | Cleaner final-line format, but loses 4 exact answers vs boundary SFT at the same token budget. |
| Boundary SFT v2 2048-data step 200 | 101/128 | 65/128 | 0/128 | 493.95 | Larger unfiltered self-distill data overfit/drifted; rejected. |
| Boundary SFT v2 2048-data step 100 | 105/128 | 59/128 | 0/128 | 539.91 | Better than step 200 but still below the baseline. |
| Boundary SFT v3 marker-line rewrite | 104/128 | 100/128 | 0/128 | 493.88 | Big final-line gain, but exact accuracy regressed. |
| Boundary SFT v4 source-final-line | 107/128 | 86/128 | 0/128 | 541.79 | Matches baseline exact and improves final-line format; promoted after 512-example check. |

The current conclusion is that this rationale-SFT adapter chain learned the output contract but plateaued below the base model's loose exact accuracy. Longer GRPO and stricter final-line correctness did not move held-out exact accuracy. Starting fresh from the base 3B policy avoided the SFT length collapse, but strict final-line exactness was too sparse to learn directly. Adding dense marker/curriculum rewards kept marker correctness learnable during training, but did not teach clean stopping and worsened held-out exact accuracy.

On the 512-example held-out check, the previous boundary-SFT baseline scored `427/512` exact and `257/512` strict final line. The v4 source-final-line adapter scored `429/512` exact and `361/512` strict final line. The exact delta is small, so the conservative claim is no observed exact-accuracy loss with a much cleaner answer contract.

Detailed records:

- [Experiment ledger](docs/runs/experiment_ledger.md)
- [Promoted result evidence](docs/results/README.md)
- [Boundary SFT technical note](docs/technical_notes/boundary_sft.md)
- [Next GPU runbook](docs/runbooks/next_gpu_runs.md)
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

## Boundary SFT Result

This branch uses strict-prompt base-model completions as self-distillation data, keeps only exact-correct examples with a correct `####` marker, truncates each completion at that marker, and trains the adapter to emit EOS immediately after the boundary.

The train pseudo-label pass generated 512 strict stop-aware train-split completions. The filter kept 350 boundary examples. The trained adapter improved held-out exact accuracy from 91/128 to 100/128. Raw trailing text fell from 101/128 to 5/128; stop-aware eval removed those remaining 5 without changing exact accuracy.

Generate pseudo-labels on a rented GPU:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_train512_strict_final_stopaware_pseudo.yaml
```

Build the boundary SFT dataset:

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_3b_train512_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_3b_boundary_sft_train512.jsonl
```

Train the boundary adapter:

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_3b_boundary_sft_warmup.yaml
```

Evaluate both raw stopping and stop-aware exactness:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_strict_128.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_strict_stopaware_128.yaml
```

This adapter became the starting point for a light cleanup-GRPO branch.

## Boundary SFT v4 Result

The 2048-example scale-up showed that more pseudo-labels are not automatically better. The initial v2 dataset kept every exact, marked-correct pseudo-label, including many completions where the `####` marker appeared inline inside the last reasoning sentence. That step-200 adapter fell to `101/128` exact. The step-100 checkpoint recovered to `105/128`, still below the previous `107/128` baseline.

Two stricter variants tested the data-shape hypothesis:

- v3 rewrote every correct marker onto its own final line. It reached `100/128` strict final line, but exact fell to `104/128`.
- v4 kept only pseudo-labels that already had a natural final answer line. It selected `932/2048` examples, matched the previous `107/128` exact gate, and improved strict final-line format from `62/128` to `86/128`.

The 512-example check promoted v4:

- previous boundary SFT: `427/512` exact, `257/512` strict final line, `0/512` trailing
- v4 source-final-line: `429/512` exact, `361/512` strict final line, `0/512` trailing

Build the v4 dataset:

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_3b_train2048_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_3b_boundary_sft_train2048_source_finalline.jsonl \
  --require-source-final-line
```

Train and evaluate:

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_3b_boundary_sft_v4_source_finalline.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512.yaml
```

## Boundary Cleanup GRPO Result

This branch starts from `outputs/cloud_3b_boundary_sft_warmup`, keeps the strict prompt, and applies a low-learning-rate 40-step GRPO pass with correctness still dominant and moderate final-line/trailing rewards:

```bash
uv run python -m rlvr_lab.train_grpo \
  --config configs/cloud_3b_boundary_sft_cleanup_grpo.yaml
```

Checkpoint 20 was rejected: exact accuracy fell to 98/128 and raw trailing stayed at 5/128. Checkpoint 40 is the current cleanup winner. It preserves the boundary SFT score at 100/128 exact, improves strict final-line format from 51/128 to 57/128 on raw generation, and reduces raw trailing text from 5/128 to 3/128. Stop-aware eval keeps the same 100/128 exact and 57/128 final-line score with 0/128 trailing cases.

Evaluate the accepted checkpoint:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_cleanup_grpo_40_strict_128.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_128.yaml
```

Sample-level comparison against boundary SFT shows 5 exact wins and 5 exact losses, so this should be treated as output-contract cleanup, not an accuracy gain. The useful next step is to inspect the remaining 3 raw trailing cases and the 5 lost examples before adding more reward pressure.

A 384-token sensitivity eval found an important cap effect. Boundary SFT improves from 100/128 to 107/128 exact under the larger budget, while cleanup GRPO improves from 100/128 to 103/128. At the fair 384-token budget, cleanup has 0 exact wins and 4 exact losses vs boundary SFT; it only wins on final-line format. The best current accuracy baseline is therefore boundary SFT with strict stop-aware 384-token eval, not the cleanup adapter.

384-token control configs:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_128.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_384_128.yaml
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

For the full training stack on a rented GPU:

```bash
bash scripts/bootstrap_remote.sh --train
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
