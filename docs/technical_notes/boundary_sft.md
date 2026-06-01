# Boundary SFT Technical Note

Boundary SFT is the current best training direction in this repo. The current promoted variant is source-final-line boundary SFT: train only on exact pseudo-labels whose answer marker already appears as the final line.

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

Previous promoted result:

- exact: `107/128`
- strict final line: `62/128`
- trailing text: `0/128`
- artifact snapshot: `docs/results/current_promoted_baseline/summary.json`

Cleanup GRPO at the same 384-token budget scored `103/128` exact and `65/128` strict final line. That is a format tradeoff, not the current accuracy baseline.

## 2048-Example Scale-Up

The 2048-example pseudo-label pass used:

- pseudo-label config: `configs/eval_cloud_3b_train2048_strict_final_stopaware_pseudo.yaml`
- pseudo-label output: `outputs/evals/cloud_3b_train2048_strict_final_stopaware_pseudo`
- result: `1770/2048` exact, `1051/2048` strict final line, `0/2048` trailing

The first v2 scale-up kept all exact, marked-correct pseudo-labels:

- dataset: `outputs/datasets/cloud_3b_boundary_sft_train2048.jsonl`
- selected: `1657/2048`
- step 100 eval: `105/128` exact, `59/128` strict final line
- step 200 eval: `101/128` exact, `65/128` strict final line

This showed that larger unfiltered self-distillation was not enough. Many selected targets had a correct `####` marker inline in the final reasoning sentence, so they were exact but did not teach the strict final-line contract cleanly.

The v3 marker-line rewrite branch forced every selected marker onto its own final line:

- dataset: `outputs/datasets/cloud_3b_boundary_sft_train2048_markerline.jsonl`
- selected: `1657/2048`
- eval: `104/128` exact, `100/128` strict final line

That confirmed the target-shape hypothesis but showed a clear exactness tradeoff.

The v4 source-final-line branch kept only pseudo-labels that naturally satisfied the final-line contract:

- dataset: `outputs/datasets/cloud_3b_boundary_sft_train2048_source_finalline.jsonl`
- selected: `932/2048`
- 128 gate: `107/128` exact, `86/128` strict final line, `0/128` trailing
- 512 check: `429/512` exact, `361/512` strict final line, `0/512` trailing

Compared with the previous boundary-SFT 512 check, v4 is `+2` exact and `+104` strict final-line cases. The exact delta is small, so treat v4 as a contract-cleanliness improvement with no observed exact regression, not as a large accuracy gain.

## Next Experiment

Port the v4 source-final-line recipe to 7B before revisiting GRPO:

1. Generate 2048 7B train-split pseudo-labels with strict prompt and stop-aware postprocessing.
2. Build the dataset with `rlvr_lab.build_boundary_sft_data --require-source-final-line`.
3. Train a 7B boundary-SFT adapter.
4. Gate it on a 128-example strict stop-aware 384-token eval.
5. Run the 512-example check only if the 128 gate matches or beats the current 3B v4 read.

Do not continue cleanup-GRPO reward pressure unless the explicit goal is to trade exact accuracy for slightly cleaner final-line formatting.
