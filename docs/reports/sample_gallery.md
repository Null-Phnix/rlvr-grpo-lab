# Representative Sample Gallery

This gallery summarizes sample-level behavior for the promoted and rejected branches. It is meant for human review: enough detail to show what changed, while keeping full generated completions in ignored `outputs/` artifacts.

Source evidence:

- [`docs/results/boundary_sft_v4_source_finalline_384_stopaware/comparison_vs_boundary_sft_v1_384_512.md`](../results/boundary_sft_v4_source_finalline_384_stopaware/comparison_vs_boundary_sft_v1_384_512.md)
- [`docs/results/7b_source_finalline_boundary_sft_128/comparison_vs_7b_base_384_128.md`](../results/7b_source_finalline_boundary_sft_128/comparison_vs_7b_base_384_128.md)
- [`docs/results/7b_base_strict_stopaware_384/failure_taxonomy_full.json`](../results/7b_base_strict_stopaware_384/failure_taxonomy_full.json)

## 3B Source-Final-Line Wins

The promoted 3B v4 branch did not produce a large exact-accuracy jump over the previous boundary-SFT baseline. The important result is that it preserved exactness while making the answer boundary much cleaner. These examples show the kind of math errors it did fix.

| Index | Problem Gist | Previous Boundary SFT | v4 Source-Final-Line | Read |
| ---: | --- | ---: | ---: | --- |
| 261 | Convert two thirds of 9,300 pennies into dollars. | `6200` | `62` | v1 counted pennies but forgot cents-to-dollars conversion. |
| 293 | Add game points, with an extra point for every player over 20. | `82` | `83` | v1 missed that Mike also had over 20 points. |
| 358 | Daily pocket-money savings after buying lollipops for 5 days. | `5` | `20` | v1 computed one part of the money flow but dropped the 5-day savings step. |

## 3B Source-Final-Line Losses

The branch also introduced regressions, so the claim stays conservative: cleaner contract with no observed exact loss on the 512-example check, not a broad accuracy breakthrough.

| Index | Problem Gist | Previous Boundary SFT | v4 Source-Final-Line | Read |
| ---: | --- | ---: | ---: | --- |
| 43 | Chips serving size under a remaining calorie budget. | `48` | `240` | v4 confused whole-bag calories with the remaining serving amount. |
| 108 | Work backward from overbaked and dropped cookies. | `50` | `15` | v4 got trapped in an intermediate intended-cookie variable. |
| 124 | Already-stamped letters before adding one third of 60 letters. | `10` | `50` | v4 added to the final pile instead of subtracting newly stamped letters. |

## Why The 7B Adapter Was Rejected

The 3B boundary recipe did not transfer cleanly to `Qwen/Qwen2.5-7B-Instruct`. The base 7B model was already strong at the output contract, so boundary SFT mostly added reasoning drift.

| Index | Problem Gist | 7B Base | 7B Boundary SFT | Read |
| ---: | --- | ---: | ---: | --- |
| 17 | Annual salary from 35 teaching hours and 15 coaching hours per week. | `57500` | `72500` | Adapter used 50 hours as teaching time instead of 35. |
| 37 | Sell lego sets, buy games, convert leftover money back into unsold sets. | `2` | `0` | Adapter computed leftover money but failed the final unit conversion. |
| 51 | Sail out for 3 hours at 10 mph, return at 6 mph. | `5` | `5.000000000000001` | This was a numeric-equivalence artifact, not a real reasoning loss; tolerant rescore fixes it. |

The adapter did have two exact wins on the 128-example gate:

| Index | Problem Gist | 7B Base | 7B Boundary SFT | Read |
| ---: | --- | ---: | ---: | --- |
| 46 | Infer package size after placing post-it notes on 220 cups. | `197` | `163` | Adapter fixed the inventory equation. |
| 85 | Count quilt blocks from vacations per year across ages 23 to 34. | `48` | `44` | Adapter avoided the inclusive-year off-by-one. |

The rejection was still the right call: after tolerant numeric rescoring, the adapter was `110/128` exact vs the base model's `114/128`, with only `+2/128` strict final-line examples.

## 7B Full-Test Failure Shape

The full 7B base eval makes the next research direction clear. On GSM8K full test, the base model scored `1164/1319` exact with `1296/1319` strict final-line answers and `0/1319` trailing-text cases.

| Bucket | Count | Read |
| --- | ---: | --- |
| Correct, clean contract | 1147 | Main success mode. |
| Correct but marker not on final line | 16 | Mostly formatting polish, not reasoning. |
| Correct without marker | 1 | Extractable but off contract. |
| Wrong math, clean contract | 149 | Dominant remaining failure mode. |
| Wrong marker not on final line | 2 | Boundary/extraction issue. |
| Wrong missing marker | 4 | Boundary/extraction issue. |
| Wrong with trailing text | 0 | Stop-aware boundary is not the bottleneck. |

Representative wrong-clean-contract examples:

| Index | Problem Gist | Prediction | Ground Truth | Read |
| ---: | --- | ---: | ---: | --- |
| 2 | House-flip profit after purchase, repairs, and value increase. | `195` | `70000` | Clean answer line, wrong economic arithmetic. |
| 7 | Download restart after 40 percent progress and a 20-minute delay. | `120` | `160` | Clean answer line, missed restart cost. |
| 12 | Lemon tree break-even year with yearly revenue and maintenance. | `12` | `13` | Clean answer line, off-by-one break-even reasoning. |

Representative boundary/extraction failures:

| Index | Bucket | Prediction | Ground Truth | Read |
| ---: | --- | ---: | ---: | --- |
| 87 | Wrong missing marker | `1.6` | `9360` | No final marker; extracted an intermediate value. |
| 147 | Wrong marker not final line | `15` | `75` | Marker existed but was not a clean final-line answer. |
| 464 | Wrong marker not final line | `2` | `6` | Boundary failure plus wrong answer on a race-position problem. |

The next useful 7B work is therefore not more answer-boundary training. It should target reasoning errors or benchmark coverage.
