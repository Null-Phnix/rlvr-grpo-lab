# Local 4060 Eval + GRPO Smoke

Date: 2026-05-30

Remote: `phnixbox`

Workspace: `/home/phnix/Documents/CODEX-MAC/rlvr-grpo-lab`

## Commands

Baseline eval:

```bash
/home/phnix/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_local_4060.yaml
```

GRPO smoke:

```bash
/home/phnix/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/local_4060_smoke.yaml
```

Post-train eval:

```bash
/home/phnix/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_local_4060.yaml \
  --adapter-path outputs/local_4060_smoke/checkpoint-25 \
  --output-dir outputs/evals/local_4060_post_smoke
```

## Results

| Run | Examples | Exact Correct | Exact Accuracy | Final Format Rate | Avg Completion Chars |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 128 | 9 | 7.03125% | 3.125% | 455.40 |
| Post-GRPO smoke | 128 | 8 | 6.25% | 3.125% | 456.31 |

Training runtime:

- `train_runtime`: 126.6 seconds
- `train_steps_per_second`: 0.197
- checkpoint: `outputs/local_4060_smoke/checkpoint-25`

## Observations

- The full eval -> train -> post-eval loop works on the RTX 4060.
- The 25-step run did not improve eval quality; it lost one exact-correct answer on the 128-example slice.
- Rewards were sparse but not completely dead. A few train batches had nonzero correctness or format reward.
- Final-format compliance is weak: only 4 of 128 eval completions used the required `#### <answer>` format before and after training.
- Training completions clipped at `max_completion_length=128` on every step, so the current prompt/config encourages long answers and may suppress useful reward signal.
- Baseline and post-train samples are often text-identical, which is expected for a short LoRA smoke with sparse reward.

## Next Fixes

- Add progress output to eval runs so long adapter evals are easier to monitor.
- Reduce verbosity pressure in the prompt or use a shorter answer-first prompt.
- Add a stronger format curriculum before relying on exact math reward.
- Try `max_completion_length=256` for training or explicitly reward shorter final-answer completions.
- Keep this 0.5B setup as a harness test, then move meaningful learning experiments to a larger model or rented GPU.
