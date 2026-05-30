# Local 4060 Prompt + Format Sweep

Date: 2026-05-30

Remote: `phnixbox`

Workspace: `/home/phnix/Documents/CODEX-MAC/rlvr-grpo-lab`

## Prompt Sweep

| Prompt / Run | Examples | Exact Correct | Exact Accuracy | Final Format Count | Final Format Rate | Avg Completion Chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `think_answer` baseline | 128 | 9 | 7.03125% | 4 | 3.125% | 455.40 |
| `plain` | 128 | 1 | 0.78125% | 0 | 0% | 468.66 |
| `answer_first` | 128 | 1 | 0.78125% | 0 | 0% | 366.95 |

The original `think_answer` prompt is still the best of the tested prompt modes.

## Format-Weighted GRPO Smoke

Config: `configs/local_4060_format_smoke.yaml`

Changes from the first GRPO smoke:

- kept `prompt_style: think_answer`
- raised `max_completion_length` from 128 to 256
- raised `format_weight` from 0.2 to 2.0

Training runtime:

- `train_runtime`: 239.2 seconds
- `train_steps_per_second`: 0.105
- checkpoint: `outputs/local_4060_format_smoke/checkpoint-25`

## Eval Comparison

| Run | Examples | Exact Correct | Exact Accuracy | Final Format Count | Final Format Rate | Avg Completion Chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 128 | 9 | 7.03125% | 4 | 3.125% | 455.40 |
| First GRPO smoke | 128 | 8 | 6.25% | 4 | 3.125% | 456.31 |
| Format-weighted smoke | 128 | 6 | 4.6875% | 12 | 9.375% | 450.38 |

## Observations

- Stronger format reward moved the target behavior: final-format count improved from 4 to 12.
- Exact accuracy regressed from 9/128 to 6/128, so the format gain did not translate into better math.
- Training rewards were much denser than the first smoke, with many batches showing nonzero format and correctness rewards.
- Completions still clipped at `max_completion_length=256` on almost every training step. Length remains a primary bottleneck.
- Some formatted completions continue after `#### <answer>`, for example adding `Final answer:` or another explanation. The next reward should prefer stopping immediately after the final answer.

## Next Fixes

- Add a stop-after-final-answer reward or penalty for text after the `#### <answer>` line.
- Add a concise prompt mode that explicitly says no explanation after the final line, but validate it with eval before training.
- Consider format SFT on a tiny synthetic set before GRPO, or a GRPO curriculum that starts with format-only examples.
- Add a stricter eval metric for `final_line_is_answer`, separate from merely containing a `####` marker.
- Keep local 0.5B runs as harness/debug experiments; move quality experiments to 1.5B/3B or rented GPU once output format is under control.
