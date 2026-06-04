# RLVR GRPO Lab v1 Report

Status: v1 research run complete. The remaining work is broader eval coverage, release tagging, and optional project-page packaging.

## Summary

This project built a config-driven RLVR/GRPO/SFT experiment harness for reasoning-model post-training. The goal was not to reproduce DeepSeek-R1. The narrower question was whether small, inspectable post-training runs could teach a model to obey a strict final-answer contract without damaging the reasoning behavior that made the base model useful.

The main result is a split finding:

- On `Qwen/Qwen2.5-3B-Instruct`, answer-boundary self-distillation helped. The promoted source-final-line boundary SFT branch scored `429/512` exact with `361/512` strict final-line answers and `0/512` trailing-text cases.
- On `Qwen/Qwen2.5-7B-Instruct`, the same boundary-SFT recipe was rejected. The base 7B model already followed the answer contract well, and SFT reduced exact accuracy on the 128-example gate.

The full 7B no-adapter reference is now:

| Model / Run | Eval Size | Exact | Strict Final Line | Trailing Text | Avg Chars |
| --- | ---: | ---: | ---: | ---: | ---: |
| 7B base strict stop-aware, 128 gate | 128 | 114/128 | 125/128 | 0/128 | 450.89 |
| 7B base strict stop-aware, 512 check | 512 | 455/512 | 502/512 | 0/512 | 434.59 |
| 7B base strict stop-aware, full GSM8K test split | 1319 | 1164/1319 | 1296/1319 | 0/1319 | 436.98 |

## Research Question

The working question was:

Can a lightweight post-training pipeline improve final-answer boundary behavior while preserving or improving math exact accuracy?

The answer depends on the starting policy. For 3B, boundary behavior was a real weakness and targeted self-distillation improved the model. For 7B, boundary behavior was already mostly solved, so applying the same pressure mainly introduced reasoning drift.

## Harness

The repo includes:

- GRPO training with LoRA adapters
- format-SFT training for answer-boundary experiments
- strict final-line exact rewards
- trailing-text and role-leak analysis
- stop-aware generation/eval postprocessing
- tolerant numeric answer scoring for near-equivalent decimal forms
- sample-level comparison tooling for wins, losses, and formatting regressions
- committed evidence snapshots under `docs/results/`
- ignored full artifacts under `outputs/`

All promoted results have a config path, an output path, compact summary JSON, and a ledger entry.

## Experiment Progression

| Branch | Key Result | Read |
| --- | --- | --- |
| Base 3B strict prompt | `91/128` exact, `1/128` strict final line, `101/128` trailing | The base model could solve many problems but failed the output contract. |
| Gold/rationale SFT warmup | `81/128` exact, `122/128` strict final line, `0/128` trailing | Format improved, but exact accuracy dropped. |
| SFT -> GRPO pilots | plateaued at `87/128` exact | GRPO recovered some exactness but did not undo the SFT damage. |
| Base 3B direct GRPO | `84/128` exact, `2/128` strict final line | Sparse final-line reward did not teach the contract. |
| Boundary SFT | `100/128` exact at 256 tokens, then `107/128` at 384 tokens | Model-native boundary self-distillation worked. |
| Boundary SFT v4 source-final-line | `429/512` exact, `361/512` strict final line | Promoted 3B branch: no observed exact regression and much cleaner final-line behavior. |
| 7B source-final-line SFT | `109/128` exact vs base `114/128` | Rejected: cleaner format did not justify exact loss. |
| 7B base full eval | `1164/1319` exact, `1296/1319` strict final line | Current 7B reference; no adapter needed for the answer boundary. |

## Findings

1. Output-format learning can fight reasoning quality.

The rationale-SFT branch showed this directly. It made the model shorter and cleaner, but exact accuracy dropped from `91/128` to `81/128`. Later GRPO improved the adapter to `87/128`, but it never recovered the base score.

2. Stop-aware evaluation separated termination failures from reasoning failures.

For the 3B base model, stop-aware postprocessing preserved exact accuracy while removing trailing text. This showed that many examples already contained a usable answer marker; the model just kept talking after it.

3. Boundary self-distillation was the first successful 3B training intervention.

Training on exact-correct, model-native completions clipped at the answer marker improved the 3B model without replacing its reasoning style with short gold rationales. The stricter source-final-line filter became the promoted 3B branch.

4. More data was not automatically better.

The unfiltered 2048-example 3B boundary-SFT scale-up regressed exact accuracy. The useful improvement came from filtering target shape, not just increasing dataset size.

5. The 3B fix did not transfer to 7B.

The 7B base model already scored `125/128` strict final-line on the first gate. The 7B source-final-line adapter gained only two strict final-line cases and lost exact answers. After tolerant numeric rescoring, it was still below base.

6. Remaining 7B errors are mostly math errors, not boundary errors.

On the full 7B base eval, `155/1319` examples were exact-wrong. The failure taxonomy puts `149/155` wrong examples in `wrong_math_clean_contract`: they had a final-line answer and no trailing text, but the answer was wrong. Only `6/155` wrong examples were boundary/extraction cases. The remaining gap is therefore not mainly a final-answer-contract problem.

7. Bootstrap checks support conservative claims.

Paired bootstrap checks were added for the decision-critical comparisons:

| Comparison | Metric | Delta | 95% Bootstrap CI |
| --- | --- | ---: | ---: |
| 3B v4 source-final-line vs 3B v1 boundary SFT, 512 examples | exact | +2/512 | [-11, +15] |
| 3B v4 source-final-line vs 3B v1 boundary SFT, 512 examples | strict final line | +104/512 | [+81, +127] |
| 7B source-final-line SFT vs 7B base, 128 examples after tolerant rescore | exact | -4/128 | [-10, +1] |
| 7B source-final-line SFT vs 7B base, 128 examples after tolerant rescore | strict final line | +2/128 | [-2, +6] |

This is why the 3B v4 result is framed as a strong formatting improvement with no observed exact regression, not as an accuracy breakthrough. It is also why the 7B adapter stays rejected: its exact delta is negative and its format gain is small.

## What Failed

These failures are part of the result:

- naive format SFT overcompressed output and hurt exact accuracy
- GRPO after the damaged SFT branch plateaued
- direct base-policy GRPO did not learn strict final-line behavior from sparse reward
- cleanup GRPO traded exact accuracy for slightly cleaner formatting at the 384-token budget
- unfiltered 2048-example self-distillation regressed
- 7B boundary SFT was unnecessary and harmful relative to the base model

## What Worked

The useful method was source-final-line boundary SFT for the 3B model:

1. Generate strict-prompt, stop-aware pseudo-labels from the base model.
2. Keep only exact-correct samples with a correct answer marker.
3. Further require that the source completion already places the answer marker on the final line.
4. Train a LoRA adapter to emit EOS at that model-native boundary.
5. Evaluate with the same strict prompt, 384-token budget, and stop-aware postprocessing.

This made the 3B model cleaner without observed exact loss on the 512-example held-out check.

## Reproducibility

Primary promoted 3B eval:

```bash
uv run python -m rlvr_lab.eval_model \
  --config configs/eval_cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512.yaml
```

7B base 512 check:

```bash
bash scripts/run_gpu_7b_base_eval.sh
```

7B base full GSM8K test split:

```bash
bash scripts/run_gpu_7b_base_eval.sh --full
```

Relevant evidence:

- `docs/results/boundary_sft_v4_source_finalline_384_stopaware/`
- `docs/results/7b_source_finalline_boundary_sft_128/`
- `docs/results/7b_base_strict_stopaware_384/`
- `docs/runs/experiment_ledger.md`
- `docs/results/boundary_sft_v4_source_finalline_384_stopaware/bootstrap_vs_boundary_sft_v1_512.json`
- `docs/results/7b_source_finalline_boundary_sft_128/bootstrap_adapter_vs_base_rescore_tol1e9.json`
- `docs/results/7b_base_strict_stopaware_384/failure_taxonomy_full.json`
- `docs/reports/sample_gallery.md`

## Limitations

The project currently evaluates GSM8K only. Small 128-example gates are useful for fast decisions, but small deltas should not be overclaimed. The 512-example and full-test 7B evals reduce that risk for the 7B base reference, but broader benchmarks are needed before making claims about general reasoning improvement.

The 3B v4 result is best framed as answer-contract improvement with no observed exact regression on the 512-example check, not as a large accuracy breakthrough.

## Next Work

The next work should be broader evaluation and release polish, not another blind training run:

1. Evaluate the final 3B and 7B policies on at least one non-GSM8K benchmark.
2. Tag a v0.1 release once the README/report are final.
3. Package the result for `phnix.dev` with the report, sample gallery, and evidence links.
