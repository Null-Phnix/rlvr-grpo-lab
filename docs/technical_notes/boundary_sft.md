# Boundary SFT Technical Note

Boundary SFT is the current best training direction in this repo.

## Problem

The base 3B model often solves GSM8K problems but does not respect the answer contract. On the original strict-prompt eval it scored `91/128` exact, but produced trailing text in `101/128` examples and only `1/128` strict final-line answer.

Naive format SFT fixed the contract but damaged exact accuracy. GRPO variants after that recovered some exactness but plateaued. Direct base-policy GRPO did not learn the strict final-line contract reliably enough from sparse reward.

## Intervention

Boundary SFT uses the base model's own strict-prompt completions as the training distribution:

1. Generate train-split completions with strict prompt and stop-aware postprocessing.
2. Keep only examples that are exact-correct and have a correct `####` marker.
3. Truncate completion text at the answer marker.
4. Train a LoRA adapter on those clipped model-native completions plus EOS.

This trains the model to stop at a boundary it already knows how to produce, without replacing its reasoning style with short gold rationales.

## Current Evidence

The first boundary-SFT run used:

- pseudo-label config: `configs/eval_cloud_3b_train512_strict_final_stopaware_pseudo.yaml`
- dataset builder: `rlvr_lab.build_boundary_sft_data`
- SFT config: `configs/cloud_3b_boundary_sft_warmup.yaml`
- promoted eval: `configs/eval_cloud_3b_boundary_sft_strict_stopaware_384_128.yaml`

Promoted result:

- exact: `107/128`
- strict final line: `62/128`
- trailing text: `0/128`
- artifact snapshot: `docs/results/current_promoted_baseline/summary.json`

Cleanup GRPO at the same 384-token budget scored `103/128` exact and `65/128` strict final line. That is a format tradeoff, not the current accuracy baseline.

## Next Experiment

Boundary SFT v2 should scale the same idea before any 7B work:

1. Generate 2048 train-split pseudo-labels with `configs/eval_cloud_3b_train2048_strict_final_stopaware_pseudo.yaml`.
2. Build `outputs/datasets/cloud_3b_boundary_sft_train2048.jsonl`.
3. Train with `configs/cloud_3b_boundary_sft_v2.yaml`.
4. Eval first on `configs/eval_cloud_3b_boundary_sft_v2_strict_stopaware_384_128.yaml`.
5. Promote only if it beats or matches the current baseline on exact accuracy, then run the 512-example eval.

Do not continue cleanup-GRPO reward pressure unless the explicit goal is to trade exact accuracy for slightly cleaner final-line formatting.
