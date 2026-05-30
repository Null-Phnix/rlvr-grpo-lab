# Local 4060 Final-Line Smoke

Date: 2026-05-30

Remote: `phnixbox`

Workspace: `/home/phnix/Documents/CODEX-MAC/rlvr-grpo-lab`

Code commit: `b2d5ff8`

## Change

Added two stricter format signals:

- `final_line_format_reward`: rewards only when the last non-empty line is exactly `#### <number>`
- `trailing_text_penalty`: penalizes completions that continue after the first `#### <number>` marker

The eval harness now reports `final_line_format_rate` and `trailing_text_rate` alongside the older loose `final_format_rate`.

## Command

```bash
/home/phnix/.local/bin/uv run accelerate launch \
  --config_file configs/accelerate_single_gpu.yaml \
  -m rlvr_lab.train_grpo \
  --config configs/local_4060_final_line_smoke.yaml
```

Post-train eval:

```bash
/home/phnix/.local/bin/uv run python -m rlvr_lab.eval_model \
  --config configs/eval_local_4060.yaml \
  --adapter-path outputs/local_4060_final_line_smoke/checkpoint-12 \
  --output-dir outputs/evals/local_4060_post_final_line_smoke
```

## Training Result

- `max_steps`: 12
- `train_runtime`: 89.64 seconds
- `train_steps_per_second`: 0.134
- checkpoint: `outputs/local_4060_final_line_smoke/checkpoint-12`
- `completions/mean_length`: 192
- `completions/clipped_ratio`: 1.0

The run produced some nonzero correctness and loose-format rewards, but `final_line_format_reward` stayed at 0 during training.

## Eval Comparison

Historical samples were rescored with the new final-line metrics.

| Run | Examples | Exact Correct | Exact Accuracy | Loose Final Count | Loose Final Rate | Final-Line Count | Final-Line Rate | Trailing Count | Trailing Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 128 | 9 | 7.03125% | 4 | 3.125% | 0 | 0% | 4 | 3.125% |
| Format-weighted smoke | 128 | 6 | 4.6875% | 12 | 9.375% | 1 | 0.78125% | 11 | 8.59375% |
| Final-line smoke | 128 | 9 | 7.03125% | 4 | 3.125% | 0 | 0% | 4 | 3.125% |

## Observations

- The new reward path is wired and tested, but 12 local GRPO steps did not create clean final-line behavior.
- The short final-line run recovered baseline exact accuracy, but did not improve over baseline.
- The earlier format-weighted run generated more `####` markers, but almost all of them had trailing text.
- Full 128-example adapter eval took about 9 minutes, so fast iteration should use a smaller eval slice before milestone comparisons.
- Completion clipping is still the core bottleneck: every training completion hit `max_completion_length=192`.

## Next Fixes

- Add a 32-example eval config for fast iteration.
- Try a stricter prompt that explicitly says the final line must be the last output line.
- Consider a tiny format-only warmup before math GRPO so the final-line reward is not mostly zero.
- Keep the stop-after-answer penalty, but combine it with shorter completion pressure or an EOS-focused reward.
