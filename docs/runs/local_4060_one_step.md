# Local 4060 One-Step Smoke

Date: 2026-05-30

Remote: `phnixbox`

Workspace: `/home/phnix/Documents/CODEX-MAC/rlvr-grpo-lab`

## Environment

- OS: CachyOS Linux
- GPU: NVIDIA GeForce RTX 4060, 8188 MiB
- Driver: 595.71.05
- Python: 3.12.12 via `uv`
- Torch: 2.12.0+cu130
- TRL: 1.5.1
- Transformers: 5.9.0
- PEFT: 0.19.1
- bitsandbytes: 0.49.2

## Command

```bash
/home/phnix/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/local_4060_one_step.yaml
```

## Result

The full GRPO smoke path completed successfully:

- loaded GSM8K through `datasets`
- loaded `Qwen/Qwen2.5-0.5B-Instruct`
- initialized LoRA GRPO training
- generated completions on CUDA
- evaluated exact-answer and final-format rewards
- wrote checkpoint artifacts to `outputs/local_4060_one_step`

Key metrics from the one-step run:

- `train_runtime`: 3.583 seconds
- `train_steps_per_second`: 0.279
- `completions/mean_length`: 64
- `completions/clipped_ratio`: 1
- `reward`: 0
- `exact_answer_accuracy`: 0

Zero reward is expected for this smoke. The goal was trainer correctness, CUDA availability, and artifact creation, not quality.
