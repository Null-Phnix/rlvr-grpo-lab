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

The pilot used `Qwen/Qwen2.5-3B-Instruct`, 128 held-out GSM8K test examples, and a 512-example train subset.

## Results

| Run | Exact | Exact Accuracy | Strict Final Line | Trailing Text | Missing | Avg Chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base 3B strict prompt | 91/128 | 71.09% | 1/128 | 101/128 | 0/128 | 845.41 |
| Rationale SFT warmup | 81/128 | 63.28% | 122/128 | 0/128 | 0/128 | 269.34 |
| SFT -> GRPO pilot | 87/128 | 67.97% | 122/128 | 0/128 | 0/128 | 278.55 |
| SFT -> GRPO resume 500 | 87/128 | 67.97% | 123/128 | 0/128 | 0/128 | 281.06 |

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

## Interpretation

This was a useful first rental run.

The base 3B model already had strong loose exact-answer accuracy, but it failed the output contract: almost every formatted answer had trailing text. Rationale SFT fixed the final-line contract but cost 10 exact answers. The 100-step GRPO continuation recovered 6 of those exact answers while preserving the strict final-line behavior.

The 500-step GRPO resume preserved the output contract and improved strict final-line format by one example, but it did not improve held-out exact accuracy over checkpoint 100. It traded 3 wins for 3 losses against checkpoint 100 on the 128-example slice, while remaining 4 exact answers below the base strict-prompt model.

The result does not beat the base model on loose exact accuracy yet, but it creates a much better RLVR starting point: clean answer extraction, no trailing text, no missing answers, and dense enough reward signal. Longer GRPO alone appears to plateau under the current reward weights, so the next run should tune the reward/objective before scaling to 7B.

## Next Steps

- inspect the checkpoint-100 vs checkpoint-500 win/loss examples before changing model size
- tune reward weights or sampling so exact-answer reward has more room to move after the output contract is learned
- keep strict final-line reward and trailing penalty, but avoid letting format dominate the objective
- run a larger held-out eval only after a reward change produces a clear 128-example improvement

Do not scale this exact recipe to 7B yet.
