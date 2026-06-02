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
| Boundary SFT self-distillation | `configs/cloud_3b_boundary_sft_warmup.yaml` | `outputs/cloud_3b_boundary_sft_warmup` | `outputs/evals/cloud_3b_boundary_sft_strict_128` | 100/128 | 51/128 | 5/128 | 488.16 | Succeeds: exact +9 vs base raw, trailing -96, strict-final-line +50. |
| Boundary SFT -> cleanup GRPO step 40 | `configs/cloud_3b_boundary_sft_cleanup_grpo.yaml` | `outputs/cloud_3b_boundary_sft_cleanup_grpo/checkpoint-40` | `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_128` | 100/128 | 57/128 | 3/128 | 477.59 | Preserves boundary-SFT exact accuracy, trims 2 raw trailing cases, and gains 6 strict-final-line cases; step 20 was rejected at 98/128 exact. |

## Cloud 3B Stop-Aware Evals

These runs use the base model with generation postprocessing only. They do not train or change model weights.

| Run | Eval Config | Eval Output | Exact | Strict Final Line | Trailing Text | Avg Chars | Conclusion |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Base 3B strict stop-aware eval | `configs/eval_cloud_3b_strict_final_stopaware_128.yaml` | `outputs/evals/cloud_3b_strict_final_stopaware_128` | 91/128 | 58/128 | 0/128 | 515.46 | Preserves base exact accuracy, removes all trailing text, and gains 57 strict-final-line cases. |
| Base 3B minimal stop-aware eval | `configs/eval_cloud_3b_minimal_final_stopaware_128.yaml` | `outputs/evals/cloud_3b_minimal_final_stopaware_128` | 80/128 | 57/128 | 0/128 | 690.27 | Removes trailing text but loses 11 exact answers vs strict stop-aware. |
| Boundary SFT strict stop-aware eval | `configs/eval_cloud_3b_boundary_sft_strict_stopaware_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_128` | 100/128 | 53/128 | 0/128 | 480.88 | Confirms boundary-SFT exact gain is preserved after clipping the remaining raw trailing text. |
| Boundary cleanup GRPO step 40 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_128` | 100/128 | 57/128 | 0/128 | 477.29 | Keeps the accepted cleanup checkpoint exact score while removing all remaining post-answer text. |

## Cloud 3B 384-Token Sensitivity Evals

These runs test whether the 256-token eval budget clipped correct completions.

| Run | Eval Config | Eval Output | Exact | Strict Final Line | Trailing Text | Avg Chars | Conclusion |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Boundary SFT 384 raw eval | `configs/eval_cloud_3b_boundary_sft_strict_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_strict_384_128` | 107/128 | 59/128 | 6/128 | 512.19 | Larger budget recovers 7 exact cases but adds one raw trailing case vs the 256-token boundary SFT eval. |
| Boundary SFT 384 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_128` | 107/128 | 62/128 | 0/128 | 494.98 | Best current exact score with clean stopping. |
| Boundary cleanup GRPO step 40 384 raw eval | `configs/eval_cloud_3b_boundary_sft_cleanup_grpo_40_strict_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_384_128` | 103/128 | 64/128 | 4/128 | 497.66 | Improves over its 256-token eval, but is exact-worse than boundary SFT at the same budget. |
| Boundary cleanup GRPO step 40 384 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_384_128` | 103/128 | 65/128 | 0/128 | 494.20 | Gains 3 strict-final-line cases vs boundary SFT 384 stop-aware, but loses 4 exact answers. |
| Boundary SFT v2 step 100 384 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_v2_strict_stopaware_384_128.yaml` + `--adapter-path outputs/cloud_3b_boundary_sft_v2/checkpoint-100` | `outputs/evals/cloud_3b_boundary_sft_v2_step100_strict_stopaware_384_128` | 105/128 | 59/128 | 0/128 | 539.91 | Earlier checkpoint reduced overtraining damage, but still missed the boundary-SFT baseline. |
| Boundary SFT v2 step 200 384 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_v2_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_v2_strict_stopaware_384_128` | 101/128 | 65/128 | 0/128 | 493.95 | Rejected: larger unfiltered self-distillation drifted exact accuracy downward. |
| Boundary SFT v3 marker-line 384 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_v3_markerline_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_v3_markerline_strict_stopaware_384_128` | 104/128 | 100/128 | 0/128 | 493.88 | Proved marker-line target shape matters, but traded away exact accuracy. |
| Boundary SFT v4 source-final-line 384 stop-aware eval | `configs/eval_cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_128` | 107/128 | 86/128 | 0/128 | 541.79 | Matches the previous exact baseline while gaining 24 strict-final-line cases. |

## Cloud 3B 512-Example Held-Out Checks

| Run | Eval Config | Eval Output | Exact | Strict Final Line | Trailing Text | Avg Chars | Conclusion |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Boundary SFT v1 384 stop-aware 512 eval | `configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_512.yaml` | `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_512` | 427/512 | 257/512 | 0/512 | 483.66 | Larger check for the previous promoted 3B baseline. |
| Boundary SFT v4 source-final-line 384 stop-aware 512 eval | `configs/eval_cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512.yaml` | `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512` | 429/512 | 361/512 | 0/512 | 539.36 | Promoted: no observed exact loss and +104 strict-final-line cases vs v1 on the 512-example check. |

## Cloud 7B Source-Final-Line Transfer

| Run | Eval Config | Eval Output | Exact | Strict Final Line | Trailing Text | Avg Chars | Conclusion |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 7B base 384 stop-aware 128 eval | `configs/eval_cloud_7b_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_7b_strict_stopaware_384_128` | 114/128 | 125/128 | 0/128 | 450.89 | Strong baseline; 7B already has clean answer-boundary behavior. |
| 7B base 384 stop-aware 512 eval | `configs/eval_cloud_7b_strict_stopaware_384_512.yaml` | `outputs/evals/cloud_7b_strict_stopaware_384_512` | 455/512 | 502/512 | 0/512 | 434.59 | Larger no-adapter check stayed stable after the SFT branch was rejected. |
| 7B base 384 stop-aware full GSM8K eval | `configs/eval_cloud_7b_strict_stopaware_384_full.yaml` | `outputs/evals/cloud_7b_strict_stopaware_384_full` | 1164/1319 | 1296/1319 | 0/1319 | 436.98 | Full test-split no-adapter reference for 7B work. |
| 7B source-final-line train pseudo-label pass | `configs/eval_cloud_7b_train2048_strict_final_stopaware_pseudo.yaml` | `outputs/evals/cloud_7b_train2048_strict_final_stopaware_pseudo` | 1918/2048 | 2012/2048 | 0/2048 | 426.56 | Clean pseudo-label source; source-final-line filter kept 1895 examples. |
| 7B source-final-line boundary SFT 128 eval | `configs/eval_cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128.yaml` | `outputs/evals/cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128` | 109/128 | 127/128 | 0/128 | 418.04 | Rejected: +2 strict-final-line cases but -5 exact answers vs 7B base. |

## Candidate Next Runs

| Run | Config | Starting Point | Purpose | Run Status |
| --- | --- | --- | --- | --- |
| Base 3B final-line exact GRPO pilot | `configs/cloud_3b_base_final_line_exact_grpo_pilot.yaml` | `Qwen/Qwen2.5-3B-Instruct` + fresh LoRA | Test whether direct GRPO can preserve base reasoning while learning the final-line contract without recreating the SFT length collapse. | Early-stopped at step 50 |
| Base 3B contract-curriculum GRPO | `configs/cloud_3b_contract_curriculum_grpo.yaml` | `Qwen/Qwen2.5-3B-Instruct` + fresh LoRA | Add a denser contract reward before strict final-line exactness, so the model can get signal for answer-marker placement and stopping without compressing reasoning. | Complete |
| Stop-aware base-policy branch | `configs/eval_cloud_3b_strict_final_stopaware_128.yaml`, `configs/eval_cloud_3b_minimal_final_stopaware_128.yaml` | `Qwen/Qwen2.5-3B-Instruct` | Change generation or prompt boundaries so the model can terminate after the answer line before spending more GRPO on stopping rewards. | Strict stop-aware complete; minimal rejected |
| Boundary SFT self-distillation | `configs/cloud_3b_boundary_sft_warmup.yaml` | `Qwen/Qwen2.5-3B-Instruct` + strict stop-aware pseudo-labels | Train EOS after the correct `####` boundary using base-model exact-correct completions instead of short gold rationales or sparse reward-only GRPO. | Complete; best adapter so far |
| Boundary SFT -> cleanup GRPO | `configs/cloud_3b_boundary_sft_cleanup_grpo.yaml` | `outputs/cloud_3b_boundary_sft_warmup` | Preserve the 100/128 exact score while removing the remaining 5 raw trailing cases and recovering final-line format. | Complete; checkpoint 40 accepted, checkpoint 20 rejected |
| Boundary SFT larger held-out eval | `configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_512.yaml` | `outputs/cloud_3b_boundary_sft_warmup` | Check whether the promoted 107/128 baseline holds on a 512-example held-out set before more training. | Complete |
| Boundary SFT v2 | `configs/cloud_3b_boundary_sft_v2.yaml` | `Qwen/Qwen2.5-3B-Instruct` + 2048 strict stop-aware pseudo-labels | Scale the successful boundary-SFT recipe before any 7B work. | Rejected at step 100 and step 200 |
| Boundary SFT v3 marker-line | `configs/cloud_3b_boundary_sft_v3_markerline.yaml` | `Qwen/Qwen2.5-3B-Instruct` + 2048 exact marked pseudo-labels with forced marker line | Test whether target-shape normalization fixes final-line format. | Rejected as exact/format tradeoff |
| Boundary SFT v4 source-final-line | `configs/cloud_3b_boundary_sft_v4_source_finalline.yaml` | `Qwen/Qwen2.5-3B-Instruct` + 2048 pseudo-labels filtered to natural final-line targets | Preserve exact while improving final-line format. | Promoted |
| 7B source-final-line boundary SFT | `configs/cloud_7b_boundary_sft_v2_source_finalline.yaml` | `Qwen/Qwen2.5-7B-Instruct` + source-final-line pseudo-label filter | Port the v4 lesson to 7B after the 3B v4 result. | Rejected at 128 gate |
| 7B base 512/full eval | `configs/eval_cloud_7b_strict_stopaware_384_512.yaml`, `configs/eval_cloud_7b_strict_stopaware_384_full.yaml` | `Qwen/Qwen2.5-7B-Instruct` | Establish a no-adapter 7B reference after rejecting boundary SFT transfer. | Complete |

## Current Read

The rationale-SFT branch taught the output contract but appears to have capped held-out exact accuracy below the base strict-prompt model. Longer GRPO and final-line exact reward both improved formatting details without moving exact accuracy.

The direct base-policy GRPO run did not reproduce the SFT length collapse: average completion length stayed near the base model. It also did not learn the strict final-line contract. Training metrics stayed at `final_line_exact_accuracy=0` through checkpoint 50, with completions usually clipped at the 384-token cap. Held-out exact accuracy fell from 91/128 to 84/128. This points to reward sparsity, not just SFT forgetting: strict final-line exactness is too rare under the base policy to drive useful contract learning by itself.

The contract-curriculum run made the intermediate marker reward dense enough to learn from, but did not solve the actual stopping problem. Training ended with `conversation_leak_rate=0.05`, but `final_line_exact_accuracy=0` and `contract_clean_stop_rate=0`. Held-out exact accuracy fell to 81/128, strict final-line format stayed at 2/128, and the sample comparison showed 6 wins and 16 losses vs base. The dominant failure mode is still continuing after a correct answer marker, sometimes by repeating prompt instructions.

Stop-aware postprocessing confirms this is primarily a termination problem. Truncating each completion after the first `#### <number>` marker keeps exact accuracy unchanged while removing trailing text. On the base eval, strict final-line format improves from 1/128 to 58/128 with exact still 91/128. On the contract-curriculum eval, strict final-line format improves from 2/128 to 66/128 with exact still 81/128. The next useful test is a prompt/generation-boundary eval, not more reward-only GRPO.

The promoted A100 stop-aware eval confirms the oracle analysis. Strict stop-aware has zero exact wins and zero exact losses vs the original base eval: exact stays 91/128, strict final-line format improves by 57 examples, trailing text falls from 101/128 to 0/128, and average completion length falls from 845.41 to 515.46 chars. Minimal-final stop-aware is worse for this model: it gets 13 exact wins but 24 exact losses vs base, for 80/128 exact overall. The next baseline should use the strict prompt with stop-aware postprocessing; minimal-final should not be used for the next training branch.

Phnixbox can run tiny 3B stop-aware evals on the RTX 4060, but only at the edge of VRAM with CPU offload. A 16-example strict-final stop-aware smoke took 4m12s and scored 6/16 exact, 8/16 strict final line, 0/16 trailing text. A 16-example minimal-final stop-aware smoke took 2m06s and scored 7/16 exact, 3/16 strict final line, 0/16 trailing text. Treat these as hardware/procedure checks, not promoted model results. The 4060 is fine for smoke tests; 128+ example 3B sweeps and training should still use rented GPU.

The next training branch is boundary SFT self-distillation. It should generate 512 strict-prompt train-split completions with stop-aware postprocessing, keep only examples that are exact-correct and have a correct `####` marker, then SFT the model on those clipped model-native completions plus EOS. This directly trains the answer boundary while preserving the base model's own reasoning distribution. It avoids the previous rationale-SFT failure mode, where gold rationales compressed output length and cost exact accuracy, and it avoids more reward-only GRPO before the boundary is learnable.

Boundary SFT succeeded. The pseudo-label pass scored 382/512 exact and the filter kept 350 exact marked-answer examples. The boundary adapter scored 100/128 exact on raw strict eval, with strict final-line format 51/128 and trailing text 5/128. Its stop-aware eval also scored 100/128 exact, strict final-line 53/128, and trailing text 0/128. Compared with the original base raw eval, the adapter has 15 sample-level wins, 6 losses, and +9 exact overall. Compared with base strict stop-aware, it again has 15 wins, 6 losses, and +9 exact overall. This is the first branch that improves exact accuracy while substantially improving the output contract.

The boundary cleanup GRPO branch partially succeeded. Checkpoint 20 was rejected because it fell to 98/128 exact and did not reduce raw trailing text. Checkpoint 40 preserved 100/128 exact, improved raw strict final-line format from 51/128 to 57/128, and reduced raw trailing text from 5/128 to 3/128. Stop-aware eval of checkpoint 40 kept 100/128 exact, 57/128 strict final-line format, and 0/128 trailing text. Sample comparison vs boundary SFT shows 5 exact wins and 5 exact losses, so this is a contract-cleanup result rather than an accuracy gain. Before spending more GPU, inspect the 3 remaining raw trailing cases and the 5 boundary-SFT-correct examples lost by cleanup GRPO.

The 384-token sensitivity eval changed the model-selection conclusion. The 256-token eval was clipping some correct completions. With `max_new_tokens=384`, boundary SFT rose to 107/128 exact and cleanup GRPO rose to 103/128 exact. At this fair larger budget, cleanup GRPO had 0 exact wins and 4 losses vs boundary SFT, while improving strict final-line format from 62/128 to 65/128 under stop-aware eval. Do not continue this cleanup-GRPO reward mix unless the goal is explicitly to trade exact accuracy for final-line cleanliness.

The 2048-example scale-up separated useful data filtering from harmful target drift. The unfiltered v2 dataset selected 1657 exact marked-answer examples, but the resulting adapter lost exact accuracy: 105/128 at step 100 and 101/128 at step 200. V3 forced every selected answer marker onto its own line and reached 100/128 strict final line, but exact fell to 104/128. V4 instead kept only source completions that naturally had the answer marker as the final line, selecting 932 examples. That preserved the 107/128 exact gate, improved final-line format to 86/128, and then scored 429/512 exact with 361/512 strict final-line cases on the larger held-out check. A paired bootstrap check against the previous 512-example boundary-SFT baseline gives exact delta `+2/512` with 95% CI `[-11, +15]`, and strict-final-line delta `+104/512` with CI `[+81, +127]`. The current promoted 3B branch is therefore source-final-line boundary SFT, framed as a stable answer-contract improvement rather than a proven exact-accuracy gain.

The 7B transfer test rejected a simple port of the 3B v4 recipe. The 7B base model scored 114/128 exact and 125/128 strict final line under the same strict stop-aware 384-token gate, so the answer-boundary problem was already mostly solved. Source-final-line SFT selected 1895 clean pseudo-labels and made the answer contract slightly cleaner, but exact fell to 109/128. After tolerant numeric scoring, the adapter is still only 110/128, below the base model. The paired bootstrap check gives exact delta `-4/128` with CI `[-10, +1]` and strict-final-line delta `+2/128` with CI `[-2, +6]`. The 7B base model then scored 455/512 exact on the larger check and 1164/1319 exact on the full GSM8K test split, with zero trailing text in both runs. Full-test taxonomy shows `149/155` wrong examples are clean-contract math errors, not boundary errors. The next 7B work should be broader benchmark coverage, not more boundary SFT pressure.

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

Promoted A100 stop-aware evals:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_strict_final_stopaware_128.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_minimal_final_stopaware_128.yaml
```

Boundary SFT branch:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_train512_strict_final_stopaware_pseudo.yaml
```

```bash
uv run python -m rlvr_lab.build_boundary_sft_data \
  outputs/evals/cloud_3b_train512_strict_final_stopaware_pseudo \
  --output outputs/datasets/cloud_3b_boundary_sft_train512.jsonl
```

```bash
uv run python -m rlvr_lab.train_format_sft \
  --config configs/cloud_3b_boundary_sft_warmup.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_strict_128.yaml
```

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_strict_stopaware_128.yaml
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
