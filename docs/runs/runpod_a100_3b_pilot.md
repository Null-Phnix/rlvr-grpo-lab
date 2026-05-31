# RunPod A100 3B Pilot

Date: 2026-05-30

Provider: RunPod

GPU: 1x NVIDIA A100-SXM4-80GB

Image: `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`

Workspace: `/workspace/rlvr-grpo-lab`

Local artifact bundle: `runpod_3b_pilot_artifacts.tgz`

## Environment Notes

The image shipped with Torch 2.4.1, which was too old for the installed Transformers/PEFT stack. The pod venv was upgraded to:

- Python: 3.11.10
- Torch: 2.8.0+cu128
- Transformers: 5.9.0
- TRL: 1.5.1
- PEFT: 0.19.1
- Datasets: 4.8.5

`torchvision` and `torchaudio` were removed from the disposable pod image because their preinstalled 2.4.1 builds conflicted with Torch 2.8.0 imports.

## Pilot Configs

- Baseline eval: `configs/eval_cloud_3b_strict_final_128.yaml`
- Rationale SFT: `configs/cloud_3b_rationale_sft_warmup_pilot.yaml`
- GRPO continuation: `configs/cloud_3b_strict_grpo_after_rationale_sft_pilot.yaml`
- GRPO resume continuation: `configs/cloud_3b_strict_grpo_resume_pilot_500.yaml`
- Final-line exact reward branch: `configs/cloud_3b_final_line_exact_grpo_after_500.yaml`
- Proposed base-policy reward branch: `configs/cloud_3b_base_final_line_exact_grpo_pilot.yaml`

The pilot used `Qwen/Qwen2.5-3B-Instruct`, 128 held-out GSM8K test examples, and a 512-example train subset.

## Results

| Run | Exact | Exact Accuracy | Strict Final Line | Trailing Text | Missing | Avg Chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base 3B strict prompt | 91/128 | 71.09% | 1/128 | 101/128 | 0/128 | 845.41 |
| Rationale SFT warmup | 81/128 | 63.28% | 122/128 | 0/128 | 0/128 | 269.34 |
| SFT -> GRPO pilot | 87/128 | 67.97% | 122/128 | 0/128 | 0/128 | 278.55 |
| SFT -> GRPO resume 500 | 87/128 | 67.97% | 123/128 | 0/128 | 0/128 | 281.06 |
| Checkpoint 500 -> final-line exact reward | 87/128 | 67.97% | 124/128 | 0/128 | 0/128 | 266.80 |

## Training

Rationale SFT:

- `max_steps`: 120
- `train_runtime`: 85.93 seconds
- `train_loss`: 0.3028
- output: `outputs/cloud_3b_rationale_sft_warmup_pilot`

GRPO:

- `max_steps`: 100
- `train_runtime`: 1086 seconds
- output: `outputs/cloud_3b_strict_grpo_after_rationale_sft_pilot/checkpoint-100`
- final logged batches had exact-answer reward around 0.65-0.85
- strict final-line reward was usually 0.95-1.0
- trailing penalty stayed at 0 in logged batches
- clipping was usually 0, with occasional spikes on long completions

GRPO resume:

- resumed from: `outputs/cloud_3b_strict_grpo_after_rationale_sft_pilot/checkpoint-100`
- `max_steps`: 500
- `train_runtime`: 5473 seconds
- `train_loss`: 0.003864
- output: `outputs/cloud_3b_strict_grpo_after_rationale_sft_pilot/checkpoint-500`

Final-line exact reward branch:

- started from: `outputs/cloud_3b_strict_grpo_after_rationale_sft_pilot/checkpoint-500`
- `max_steps`: 100
- `train_runtime`: 1321 seconds
- `train_loss`: 0.00483
- output: `outputs/cloud_3b_final_line_exact_grpo_after_500/checkpoint-100`
- reward weights: correctness `1.0`, final-line correctness `3.0`, format `0.0`, final-line format `0.1`, trailing penalty `0.5`

## Interpretation

This was a useful first rental run.

The base 3B model already had strong loose exact-answer accuracy, but it failed the output contract: almost every formatted answer had trailing text. Rationale SFT fixed the final-line contract but cost 10 exact answers. The 100-step GRPO continuation recovered 6 of those exact answers while preserving the strict final-line behavior.

The 500-step GRPO resume preserved the output contract and improved strict final-line format by one example, but it did not improve held-out exact accuracy over checkpoint 100. It traded 3 wins for 3 losses against checkpoint 100 on the 128-example slice, while remaining 4 exact answers below the base strict-prompt model.

The final-line exact reward branch also preserved the output contract and shortened completions, but it did not improve held-out exact accuracy. It traded 3 wins for 3 losses against checkpoint 500, improved strict final-line format by one example, and stayed 4 exact answers below the base strict-prompt model.

The result does not beat the base model on loose exact accuracy yet, but it creates a much better RLVR starting point: clean answer extraction, no trailing text, no missing answers, and dense enough reward signal. Longer GRPO and a stricter final-line correctness reward both appear to plateau from the current rationale-SFT warmup, so the next run should change the warmup or starting policy before scaling to 7B.

## Error Analysis

A checkpoint-100 vs checkpoint-500 comparison report was generated at `outputs/evals/cloud_3b_post_strict_grpo_resume_pilot_500_128/comparison_vs_checkpoint100.md`.

The 500-step checkpoint had 3 wins and 3 losses against checkpoint 100. The losses were not format failures; they were cleanly formatted wrong answers. One win reached the correct final answer through brittle intermediate reasoning, so this setup should not be treated as a reasoning-quality win just because the final-answer metric is flat.

A checkpoint-500 vs final-line exact reward comparison report was generated at `outputs/evals/cloud_3b_final_line_exact_grpo_after_500_128/comparison_vs_checkpoint500.md`.

The final-line exact reward branch also had 3 wins and 3 losses against checkpoint 500. Its losses were again reasoning errors, not trailing-text failures. This suggests the current bottleneck is the policy/reasoning distribution after warmup, not the final answer line parser.

## Next Steps

- branch the next experiment from the base 3B model instead of the rationale-SFT checkpoint, using LoRA plus final-line exact reward from the start
- keep strict final-line reward and trailing penalty, but avoid spending more runs on this exact warmup branch
- consider a better warmup dataset that preserves base-model reasoning quality while teaching only the final-line answer contract
- run a larger held-out eval only after a reward change produces a clear 128-example improvement

Do not scale this exact recipe to 7B yet.
