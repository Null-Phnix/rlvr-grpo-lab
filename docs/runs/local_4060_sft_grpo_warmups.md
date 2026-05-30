# Local 4060 SFT + GRPO Warmups

Date: 2026-05-30

Remote: `phnixbox`

Workspace: `/home/phnix/Documents/CODEX-MAC/rlvr-grpo-lab`

## Goal

Find a local path that fixes answer formatting before spending rented GPU time on larger models.

## Prompt-Only Fast Evals

After replacing angle-bracket placeholders like `#### <number>` with concrete examples like `#### 42`, 32-example evals looked like this:

| Run | Prompt | Exact | Loose Final | Strict Final Line | Trailing Text | Missing | Avg Chars |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base fast | `think_answer` | 1/32 | 2/32 | 0/32 | 2/32 | 0/32 | 443.91 |
| Base strict | `strict_final_line` | 2/32 | 2/32 | 0/32 | 2/32 | 0/32 | 424.84 |
| Base final-only | `final_only` | 0/32 | 18/32 | 0/32 | 18/32 | 3/32 | 129.44 |

Prompting alone did not produce clean stopping. The `final_only` prompt produced many `####` markers, but they still had trailing text.

## Final-Only Format Warmup

Config: `configs/local_4060_format_sft_warmup.yaml`

This SFT warmup masks the prompt and trains only on `#### <gold answer>`.

Training result:

- `max_steps`: 60
- `train_runtime`: 13.45 seconds
- `train_loss`: 1.181
- checkpoint: `outputs/local_4060_format_sft_warmup`

Fast eval after SFT:

| Run | Exact | Loose Final | Strict Final Line | Trailing Text | Missing | Avg Chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SFT warmup, 32 examples | 1/32 | 17/32 | 17/32 | 0/32 | 9/32 | 4.38 |

## Final-Only SFT -> GRPO

Config: `configs/local_4060_final_only_grpo_after_sft.yaml`

Training result:

- `max_steps`: 20
- `train_runtime`: 20.61 seconds
- checkpoint: `outputs/local_4060_final_only_grpo_after_sft/checkpoint-20`
- completions were short, terminated, and not clipped
- several training batches had nonzero exact-answer reward

Full 128-example eval:

| Run | Exact | Loose Final | Strict Final Line | Trailing Text | Missing | Avg Chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base final-only | 3/128 | 75/128 | 0/128 | 75/128 | 11/128 | 131.67 |
| Final-only SFT -> GRPO | 9/128 | 128/128 | 128/128 | 0/128 | 0/128 | 7.22 |
| Original `think_answer` baseline | 9/128 | 4/128 | 0/128 | 4/128 | 0/128 | 455.40 |

The final-only chain solved the format and stopping problem without losing exact accuracy against the original baseline, but it did not improve math.

## Rationale SFT -> GRPO

Configs:

- `configs/local_4060_rationale_sft_warmup.yaml`
- `configs/local_4060_strict_grpo_after_rationale_sft.yaml`

The rationale SFT warmup uses GSM8K rationales and keeps the strict final-line prompt.

Rationale SFT result:

- `max_steps`: 60
- `train_runtime`: 25.38 seconds
- `train_loss`: 0.4108
- fast eval: 3/32 exact, 14/32 strict final-line, 1/32 trailing text

Rationale GRPO result:

- `max_steps`: 20
- `train_runtime`: 155.1 seconds
- many training batches had exact-answer reward
- format reward was usually dense during training
- fast eval: 3/32 exact, 13/32 strict final-line, 1/32 trailing text

The rationale branch had healthier training rewards, but the 20-step local continuation did not beat the SFT checkpoint on held-out fast eval.

## Takeaways

- The reward/eval harness now detects the failure mode that mattered: loose markers with trailing text.
- The final-only SFT -> GRPO branch is the clean format-control baseline.
- The rationale branch is the better rented-GPU candidate because it preserves reasoning, but it needs larger model scale and more than 20 local GRPO steps.
- Do not spend rented GPU time on prompt-only format fixes. The prompt-only path failed locally.
- For cloud runs, start with 3B rationale SFT -> GRPO, not 7B from scratch. Move to 7B only after the 3B run improves exact accuracy while keeping strict final-line rate high.
