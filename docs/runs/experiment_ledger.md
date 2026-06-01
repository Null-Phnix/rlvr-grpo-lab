# Experiment Ledger

This ledger tracks promoted experiments only. Scratch outputs, smoke checks, and generated artifacts stay under `outputs/` and are ignored by git.

## Cloud 3B GSM8K Strict-Final-Line Runs

Held-out eval: `configs/eval_cloud_3b_strict_final_128.yaml`, 128 GSM8K test examples.

| Run | Train Config | Checkpoint / Adapter | Eval Output | Exact | Strict Final Line | Trailing Text | Avg Chars | Conclusion |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Base 3B strict prompt | n/a | `Qwen/Qwen2.5-3B-Instruct` | `outputs/evals/cloud_3b_strict_final_128_baseline` | 91/128 | 1/128 | 101/128 | 845.41 | Strong loose exact accuracy, bad answer contract. |
| Rationale SFT warmup | `configs/cloud_3b_rationale_sft_warmup_pilot.yaml` | `outputs/cloud_3b_rationale_sft_warmup_pilot` | `outputs/evals/cloud_3b_post_rationale_sft_pilot_128` | 81/128 | 122/128 | 0/128 | 269.34 | Fixed contract, damaged exact accuracy. |
| SFT -> GRPO pilot | `configs/cloud_3b_strict_grpo_after_rationale_sft_pilot.yaml` | `outputs/cloud_3b_strict_grpo_after_rationale_sft_pilot/checkpoint-100` | `outputs/evals/cloud_3b_post_strict_grpo_pilot_128` | 87/128 | 122/128 | 0/128 | 278.55 | Recovered some exact accuracy while preserving format. |
| SFT -> GRPO resume 500 | `configs/cloud_3b_strict_grpo_resume_pilot_500.yaml` | `outputs/cloud_3b_strict_grpo_after_rationale_sft_pilot/checkpoint-500` | `outputs/evals/cloud_3b_post_strict_grpo_resume_pilot_500_128` | 87/128 | 123/128 | 0/128 | 281.06 | Exact plateau; 3 wins and 3 losses vs checkpoint 100. |
| Checkpoint 500 -> final-line exact reward | `configs/cloud_3b_final_line_exact_grpo_after_500.yaml` | `outputs/cloud_3b_final_line_exact_grpo_after_500/checkpoint-100` | `outputs/evals/cloud_3b_final_line_exact_grpo_after_500_128` | 87/128 | 124/128 | 0/128 | 266.80 | Cleaner and shorter, but exact still plateaued; 3 wins and 3 losses vs checkpoint 500. |
| Base 3B -> final-line exact GRPO step 50 | `configs/cloud_3b_base_final_line_exact_grpo_pilot.yaml` | `outputs/cloud_3b_base_final_line_exact_grpo_pilot/checkpoint-50` | `outputs/evals/cloud_3b_base_final_line_exact_grpo_pilot_step50_128` | 84/128 | 2/128 | 69/128 | 838.60 | Early-stopped: no length collapse, but sparse final-line reward did not teach the contract and exact dropped 7 vs base. |
| Base 3B -> contract-curriculum GRPO step 150 | `configs/cloud_3b_contract_curriculum_grpo.yaml` | `outputs/cloud_3b_contract_curriculum_grpo/checkpoint-150` | `outputs/evals/cloud_3b_contract_curriculum_grpo_150_128` | 81/128 | 2/128 | 93/128 | 825.80 | Dense marker reward stayed learnable, but clean stopping did not emerge; 6 wins and 16 losses vs base. |

## Candidate Next Runs

| Run | Config | Starting Point | Purpose | Run Status |
| --- | --- | --- | --- | --- |
| Base 3B final-line exact GRPO pilot | `configs/cloud_3b_base_final_line_exact_grpo_pilot.yaml` | `Qwen/Qwen2.5-3B-Instruct` + fresh LoRA | Test whether direct GRPO can preserve base reasoning while learning the final-line contract without recreating the SFT length collapse. | Early-stopped at step 50 |
| Base 3B contract-curriculum GRPO | `configs/cloud_3b_contract_curriculum_grpo.yaml` | `Qwen/Qwen2.5-3B-Instruct` + fresh LoRA | Add a denser contract reward before strict final-line exactness, so the model can get signal for answer-marker placement and stopping without compressing reasoning. | Complete |
| Stop-aware base-policy branch | `configs/eval_cloud_3b_strict_final_stopaware_128.yaml`, `configs/eval_cloud_3b_minimal_final_stopaware_128.yaml` | `Qwen/Qwen2.5-3B-Instruct` | Change generation or prompt boundaries so the model can terminate after the answer line before spending more GRPO on stopping rewards. | Eval configs ready |

## Current Read

The rationale-SFT branch taught the output contract but appears to have capped held-out exact accuracy below the base strict-prompt model. Longer GRPO and final-line exact reward both improved formatting details without moving exact accuracy.

The direct base-policy GRPO run did not reproduce the SFT length collapse: average completion length stayed near the base model. It also did not learn the strict final-line contract. Training metrics stayed at `final_line_exact_accuracy=0` through checkpoint 50, with completions usually clipped at the 384-token cap. Held-out exact accuracy fell from 91/128 to 84/128. This points to reward sparsity, not just SFT forgetting: strict final-line exactness is too rare under the base policy to drive useful contract learning by itself.

The contract-curriculum run made the intermediate marker reward dense enough to learn from, but did not solve the actual stopping problem. Training ended with `conversation_leak_rate=0.05`, but `final_line_exact_accuracy=0` and `contract_clean_stop_rate=0`. Held-out exact accuracy fell to 81/128, strict final-line format stayed at 2/128, and the sample comparison showed 6 wins and 16 losses vs base. The dominant failure mode is still continuing after a correct answer marker, sometimes by repeating prompt instructions.

Stop-aware postprocessing confirms this is primarily a termination problem. Truncating each completion after the first `#### <number>` marker keeps exact accuracy unchanged while removing trailing text. On the base eval, strict final-line format improves from 1/128 to 58/128 with exact still 91/128. On the contract-curriculum eval, strict final-line format improves from 2/128 to 66/128 with exact still 81/128. The next useful test is a prompt/generation-boundary eval, not more reward-only GRPO.

Phnixbox can run tiny 3B stop-aware evals on the RTX 4060, but only at the edge of VRAM with CPU offload. A 16-example strict-final stop-aware smoke took 4m12s and scored 6/16 exact, 8/16 strict final line, 0/16 trailing text. A 16-example minimal-final stop-aware smoke took 2m06s and scored 7/16 exact, 3/16 strict final line, 0/16 trailing text. Treat these as hardware/procedure checks, not promoted model results. The 4060 is fine for smoke tests; 128+ example 3B sweeps and training should still use rented GPU.

## Base-Policy GRPO Success Criteria

The base model solved 91/128 held-out examples, but 77 of those 91 correct completions had trailing text after a final-answer marker and 69 included a `Human:` continuation. The next run should not optimize for brevity. It should preserve the useful reasoning while learning to stop after the final answer line.

The base-policy run outcome:

- held-out exact accuracy fell from 91/128 to 84/128
- strict final-line format moved only from 1/128 to 2/128
- average completion length stayed stable, 845.41 -> 838.60 chars
- sample comparison showed 6 wins and 13 losses vs the base eval

Primary checks for the next base-policy run:

- held-out exact accuracy should stay near or above the base model's 91/128
- strict final-line format should improve substantially over the base model's 1/128
- average completion length should not collapse toward the 266-281 character adapter range unless exact accuracy is preserved
- compare against the base eval and manually inspect base-correct examples that the new run loses

Contract-curriculum run command:

```bash
~/.local/bin/uv run python -m rlvr_lab.train_grpo \
  --config configs/cloud_3b_contract_curriculum_grpo.yaml
```

Contract-curriculum comparison:

```bash
~/.local/bin/uv run python -m rlvr_lab.compare_evals \
  outputs/evals/cloud_3b_strict_final_128_baseline/summary.json \
  outputs/evals/cloud_3b_contract_curriculum_grpo_150_128/summary.json
```

```bash
~/.local/bin/uv run python -m rlvr_lab.compare_samples \
  outputs/evals/cloud_3b_strict_final_128_baseline \
  outputs/evals/cloud_3b_contract_curriculum_grpo_150_128 \
  --baseline-label base \
  --candidate-label contract-curriculum-150 \
  --output outputs/evals/cloud_3b_contract_curriculum_grpo_150_128/comparison_vs_base.md
```

Stop-aware analysis:

```bash
~/.local/bin/uv run python -m rlvr_lab.analyze_samples \
  outputs/evals/cloud_3b_strict_final_128_baseline \
  --output outputs/evals/cloud_3b_strict_final_128_baseline/failure_analysis.json
```

```bash
~/.local/bin/uv run python -m rlvr_lab.analyze_samples \
  outputs/evals/cloud_3b_contract_curriculum_grpo_150_128 \
  --output outputs/evals/cloud_3b_contract_curriculum_grpo_150_128/failure_analysis.json
```

Phnixbox 3B stop-aware smoke:

```bash
~/.local/bin/uv run --extra train python -m rlvr_lab.eval_model \
  --config configs/eval_phnixbox_3b_strict_final_stopaware_smoke.yaml
```

```bash
~/.local/bin/uv run --extra train python -m rlvr_lab.eval_model \
  --config configs/eval_phnixbox_3b_minimal_final_stopaware_smoke.yaml
```

Required comparisons:

```bash
~/.local/bin/uv run python -m rlvr_lab.compare_evals \
  outputs/evals/cloud_3b_strict_final_128_baseline/summary.json \
  outputs/evals/cloud_3b_base_final_line_exact_grpo_pilot_step50_128/summary.json
```

```bash
~/.local/bin/uv run python -m rlvr_lab.compare_samples \
  outputs/evals/cloud_3b_strict_final_128_baseline \
  outputs/evals/cloud_3b_base_final_line_exact_grpo_pilot_step50_128 \
  --baseline-label base \
  --candidate-label base-grpo-step50 \
  --output outputs/evals/cloud_3b_base_final_line_exact_grpo_pilot_step50_128/comparison_vs_base.md
```
