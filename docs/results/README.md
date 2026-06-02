# Promoted Result Evidence

This folder contains small, committed evidence files for promoted or decision-critical runs. Large checkpoints, full `samples.jsonl` files, and generated training outputs remain under ignored `outputs/`.

Every result promoted in the README should have a config path, output path, summary, sample comparison when applicable, and conclusion.

## Current Baseline

| Run | Source Output | Exact | Strict Final Line | Trailing Text | Why It Matters |
| --- | --- | ---: | ---: | ---: | --- |
| Boundary SFT v4 source-final-line 384 stop-aware | `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_512` | 429/512 | 361/512 | 0/512 | Current promoted 3B branch; no observed exact loss and much cleaner final-line format. |
| Boundary SFT v4 source-final-line 128 gate | `outputs/evals/cloud_3b_boundary_sft_v4_source_finalline_strict_stopaware_384_128` | 107/128 | 86/128 | 0/128 | Matches the previous 128-example exact score with better answer-contract format. |
| 7B base strict stop-aware full test split | `outputs/evals/cloud_7b_strict_stopaware_384_full` | 1164/1319 | 1296/1319 | 0/1319 | Full GSM8K no-adapter reference for 7B work. |
| 7B base strict stop-aware 512 check | `outputs/evals/cloud_7b_strict_stopaware_384_512` | 455/512 | 502/512 | 0/512 | Larger no-adapter check after rejecting 7B boundary SFT. |
| 7B base strict stop-aware 128 gate | `outputs/evals/cloud_7b_strict_stopaware_384_128` | 114/128 | 125/128 | 0/128 | 7B baseline for the source-final-line transfer test. |
| 7B source-final-line boundary SFT 128 gate | `outputs/evals/cloud_7b_boundary_sft_v2_source_finalline_strict_stopaware_384_128` | 109/128 | 127/128 | 0/128 | Rejected: small final-line gain, -5 exact answers vs 7B base. |
| Previous boundary SFT 384 stop-aware | `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_128` | 107/128 | 62/128 | 0/128 | Previous promoted baseline. |
| Previous boundary SFT 384 stop-aware 512 check | `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_512` | 427/512 | 257/512 | 0/512 | Larger held-out comparison baseline for v4. |
| Boundary SFT 384 raw | `outputs/evals/cloud_3b_boundary_sft_strict_384_128` | 107/128 | 59/128 | 6/128 | Shows the 384-token budget recovers exact answers, but raw generation still trails. |
| Cleanup GRPO 384 stop-aware | `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_384_128` | 103/128 | 65/128 | 0/128 | Cleaner format, but loses 4 exact answers vs the baseline. |
| Cleanup GRPO 384 raw | `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_384_128` | 103/128 | 64/128 | 4/128 | Confirms cleanup mostly trades exactness for answer-contract cleanliness. |
| Boundary SFT 128 stop-aware | `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_128` | 100/128 | 53/128 | 0/128 | Earlier promoted result before the 384-token sensitivity check. |
| Train-512 pseudo-label pass | `outputs/evals/cloud_3b_train512_strict_final_stopaware_pseudo` | 382/512 | 220/512 | 0/512 | Source pass for boundary-SFT data filtering. |

## Files

- `boundary_sft_v4_source_finalline_384_stopaware/`: current promoted v4 summaries, failure analyses, and comparisons for the 128 gate and 512 check.
- `7b_base_strict_stopaware_384/`: 7B no-adapter summaries and failure analyses for the 512-example check and full GSM8K test split.
- `7b_source_finalline_boundary_sft_128/`: 7B base, pseudo-label, source-final-line dataset, adapter gate, and base-vs-adapter comparison evidence.
- `boundary_sft_v2_scaleup_diagnostics/`: decision-critical evidence for rejected v2/v3 scale-up branches and the stricter v4 dataset filter.
- `current_promoted_baseline/`: previous summary and failure analysis for boundary SFT 384 stop-aware.
- `boundary_sft_384_raw/`: raw-generation control for the same adapter and token budget.
- `cleanup_grpo_384_stopaware/`: cleanup-GRPO 384 stop-aware summary plus comparison against the current baseline.
- `cleanup_grpo_384_raw/`: raw cleanup-GRPO 384 summary plus comparison against boundary SFT raw 384.
- `boundary_sft_128_stopaware/`: earlier boundary-SFT result and comparison against the base stop-aware eval.
- `train512_pseudo_labels/`: pseudo-label generation summary used to build the first boundary-SFT dataset.

## Reproducibility Notes

These files are evidence snapshots, not the full generated artifacts. The full local outputs include `samples.jsonl`, logs, adapter checkpoints, and checksums under ignored `outputs/`.

Before promoting a new result:

1. Run the eval from a checked-in config.
2. Save `summary.json`, `failure_analysis.json`, and any comparison report into `docs/results/`.
3. Update the README and `docs/runs/experiment_ledger.md`.
4. Keep large checkpoints and full sample files out of Git.
