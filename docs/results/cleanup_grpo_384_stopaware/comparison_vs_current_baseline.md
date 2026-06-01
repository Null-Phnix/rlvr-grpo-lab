# Sample Comparison

Baseline: `outputs/evals/cloud_3b_boundary_sft_strict_stopaware_384_128/samples.jsonl`
Candidate: `outputs/evals/cloud_3b_boundary_sft_cleanup_grpo_40_strict_stopaware_384_128/samples.jsonl`

## Summary

- compared examples: 128
- boundary-sft-384-stopaware exact: 107/128
- cleanup-grpo-40-384-stopaware exact: 103/128
- wins: 0 []
- losses: 4 [14, 28, 75, 108]
- same correct: 103
- same wrong: 21
- final-line format wins: 11 [13, 36, 37, 48, 53, 55, 56, 65, 89, 94, 108]
- final-line format losses: 8 [8, 14, 19, 35, 69, 87, 92, 107]

## Wins

None.

## Losses

### Index 14

- ground truth: `60`
- boundary-sft-384-stopaware answer: `60` correct=True
- cleanup-grpo-40-384-stopaware answer: `60.00000000000001` correct=False
- problem: In a dance class of 20 students, 20% enrolled in contemporary dance, 25% of the remaining enrolled in jazz dance, and the rest enrolled in hip-hop dance. What percentage of the entire students enrolled in hip-hop dance?
- boundary-sft-384-stopaware completion: Let's calculate the number of students in each category step by step. 1. **Contemporary Dance**: - 20% of 20 students = \(0.20 \times 20 = 4\) students 2. **Remaining Students After Contemporary Dance**: - Total students - Students in contemporary dance = \(20 - 4 = 16\) students 3. **Jazz Dance**: - 25% of the remaining 16 students = \(0.25 \times 16 = 4...
- cleanup-grpo-40-384-stopaware completion: Let's calculate the number of students in each category step by step. 1. **Contemporary Dance**: - 20% of 20 students = \(0.20 \times 20 = 4\) students 2. **Remaining Students After Contemporary Dance**: - Total students - Students in contemporary dance = \(20 - 4 = 16\) students 3. **Jazz Dance**: - 25% of the remaining 16 students = \(0.25 \times 16 = 4...

### Index 28

- ground truth: `25`
- boundary-sft-384-stopaware answer: `25` correct=True
- cleanup-grpo-40-384-stopaware answer: `35` correct=False
- problem: Henry made two stops during his 60-mile bike trip. He first stopped after 20 miles. His second stop was 15 miles before the end of the trip. How many miles did he travel between his first and second stops?
- boundary-sft-384-stopaware completion: Henry traveled from mile 0 to mile 20, and then continued until mile 60. However, we need to find out how many miles he traveled between his first and second stops. His second stop was 15 miles before the end, so he traveled \(60 - 15 = 45\) miles from the start of his second stop to the end of his trip. Since he stopped after 20 miles, the distance trave...
- cleanup-grpo-40-384-stopaware completion: Henry traveled 35 miles between his first and second stops. #### 35

### Index 75

- ground truth: `60`
- boundary-sft-384-stopaware answer: `60` correct=True
- cleanup-grpo-40-384-stopaware answer: `7.5` correct=False
- problem: Luke is spending time at the beach building sandcastles. He eventually notices that each level of a sandcastle will have half the square footage as the level below it. If he makes a 4 leveled sandcastle where the top level has a square footage of 16, what is the average square footage of a level?
- boundary-sft-384-stopaware completion: Let's denote the square footage of the top (4th) level as \(16\). According to the problem, each subsequent level has half the square footage of the level above it. - The 4th level (top level) has \(16\) square feet. - The 3rd level has \(16 \times 2 = 32\) square feet. - The 2nd level has \(32 \times 2 = 64\) square feet. - The 1st level has \(64 \times ...
- cleanup-grpo-40-384-stopaware completion: Let's denote the square footage of the top (4th) level as \(16\). According to the problem, each subsequent level has half the square footage of the level above it. - The 4th level (top level): \(16\) square feet. - The 3rd level: \(\frac{16}{2} = 8\) square feet. - The 2nd level: \(\frac{8}{2} = 4\) square feet. - The 1st level: \(\frac{4}{2} = 2\) squar...

### Index 108

- ground truth: `50`
- boundary-sft-384-stopaware answer: `50` correct=True
- cleanup-grpo-40-384-stopaware answer: `7.5` correct=False
- problem: Henry is making cookies for a local baking competition. He wants to make twice as many as he did last year. When he finishes baking, he realizes he actually baked 15 more cookies than he meant to. He drops 5 of his cookies as he is putting them out to cool, and now has a total of 110 cookies. How many cookies did Henry bake last year?
- boundary-sft-384-stopaware completion: Let \( x \) be the number of cookies Henry intended to bake this year. According to the problem, he actually baked twice as many as he intended, plus an additional 15 cookies. Therefore, we can write: \[ x + 15 = 2x \] Solving for \( x \): \[ 15 = 2x - x \] \[ 15 = x \] So, Henry intended to bake 15 cookies this year. Since he ended up with 110 cookies af...
- cleanup-grpo-40-384-stopaware completion: Let \( x \) be the number of cookies Henry intended to bake this year. According to the problem, he actually baked twice as many as he intended, plus an additional 15 cookies. Therefore, we can write: \[ x + 15 = 2x \] Solving for \( x \): \[ 15 = 2x - x \] \[ 15 = x \] So, Henry intended to bake 15 cookies this year. Since he ended up with 110 cookies af...
