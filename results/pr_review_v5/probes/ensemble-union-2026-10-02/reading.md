## 1. The rule, on `union_dev_opus_4pass_v1` (judge v4-semantic-v3-v9-rubric, gpt_5_mini, identity `0711a6c01265`)

- judged issue recall: **12 of 23** (0.522); rule: at least 10 -> MET
- control emission: **14 findings over 2 control PRs, 7.0 per PR** (union_report: {'33304': 6, '33315': 8}); rule: at most 2.0 -> NOT MET
- **the union of the four is NOT a lever, as built** under the pre-stated rule; the K=2 and K=3 subsets are read below, chosen after the fact
- volume: 375 findings, 90 judge-paired at 112 anchored pairs; coverage complete: True; reachable recall 0.667; resolution recall 0.391; gold alignment 0.104

## 2. The spine: each pass, the union of their audits, the union run's own audit

| obligation | PR | H55r1 | H55r2 | M5 | Hyg1 | passes' union | union run |
|---|---|---|---|---|---|---|---|
| `073625ed` | 33285 | HIT | HIT | HIT | HIT | HIT | HIT |
| `0bb42bd2` | 33321 | loc | loc | loc | loc | . | loc |
| `38e72250` | 33421 | loc | loc | . | loc | . | loc |
| `3dacf72e` | 33149 | HIT | HIT | HIT | HIT | HIT | HIT |
| `55f65304` | 33421 | . | loc | loc | . | . | loc |
| `57bcc9fd` | 33117 | loc | loc | loc | loc | . | loc |
| `585e5e0b` | 33285 | . | . | . | HIT | HIT | HIT |
| `5ffba48e` | 33321 | loc | HIT | loc | HIT | HIT | HIT |
| `61f68eed` | 33149 | HIT | . | . | . | HIT | HIT |
| `64e1164f` | 33337 | loc | loc | loc | loc | . | loc |
| `695ae9fd` | 33362 | . | . | HIT | HIT | HIT | HIT |
| `6b02b611` | 33421 | . | loc | . | . | . | loc |
| `7f098f6a` |  | . | . | . | . | . | . |
| `7fef913e` | 33145 | loc | loc | . | loc | . | HIT |
| `8d887ce4` | 33145 | loc | loc | loc | loc | . | loc |
| `8e276803` |  | . | . | . | . | . | . |
| `bd8a8d8c` | 33145 | HIT | HIT | HIT | HIT | HIT | HIT |
| `c9739efc` | 33321 | loc | loc | loc | loc | . | loc |
| `cc44bb99` | 33305 | HIT | HIT | HIT | HIT | HIT | HIT |
| `ce7b5d2e` |  | . | . | . | . | . | . |
| `e83e6544` | 33145 | HIT | HIT | HIT | HIT | HIT | HIT |
| `e8e02821` | 33145 | loc | loc | HIT | loc | HIT | HIT |
| `f54010d8` | 33149 | HIT | HIT | HIT | HIT | HIT | HIT |

- hit per pass: 7, 7, 8, 9; passes' union 11; stable (all four) 6; union run judged 12
- moved: hit by some pass, missed in the union run's audit: 0 -- 
- moved: hit in the union run's audit, by no pass: 1 -- `7fef913e`

## 3. The K=2 and K=3 subsets, read off the union audit through `members` (chosen after the fact)

| subset | findings | judge-paired | hit obligations (union audit) | hit obligations (passes' own audits) | control findings (33304, 33315) | per control PR | rule |
|---|---|---|---|---|---|---|---|
| K=2, H-claude reps 1+2 | 192 | 47 | **9** of 23 | 8 | 1, 3 | 2.0 | not, as built |
| K=3, + hygiene rep 1 | 283 | 70 | **12** of 23 | 10 | 2, 4 | 3.0 | not, as built |
| K=4, all four | 375 | 90 | **12** of 23 | 11 | 6, 8 | 7.0 | not, as built |

## 4. Agreement as a label: hit rate by `passes_agreeing` over judge-paired union findings (no cut)

**all scored PRs** (90 paired findings)

| k (passes agreeing on site and kind) | paired findings | hit | rate | distinct obligations hit |
|---|---|---|---|---|
| 1 | 6 | 3 | 0.50 | 4 |
| 2 | 6 | 4 | 0.67 | 3 |
| 3 | 14 | 4 | 0.29 | 3 |
| 4 | 64 | 28 | 0.44 | 8 |

- within-PR AUC of k: **0.482** over 2 PRs holding both a hit and a non-hit (221 ordered pairs)

**without 33149** (75 paired findings)

| k (passes agreeing on site and kind) | paired findings | hit | rate | distinct obligations hit |
|---|---|---|---|---|
| 1 | 4 | 1 | 0.25 | 1 |
| 2 | 4 | 2 | 0.50 | 1 |
| 3 | 11 | 1 | 0.09 | 1 |
| 4 | 56 | 20 | 0.36 | 6 |

- within-PR AUC of k: **0.482** over 2 PRs holding both a hit and a non-hit (221 ordered pairs)

| PR | paired findings | hit | k distribution of paired findings | enters the AUC |
|---|---|---|---|---|
| 33117 | 16 | 0 | {1: 2, 3: 6, 4: 8} | no |
| 33145 | 30 | 11 | {3: 2, 4: 28} | yes |
| 33149 | 15 | 15 | {1: 2, 2: 2, 3: 3, 4: 8} | no |
| 33285 | 5 | 5 | {1: 1, 4: 4} | no |
| 33305 | 4 | 4 | {4: 4} | no |
| 33321 | 8 | 2 | {4: 8} | yes |
| 33337 | 4 | 0 | {4: 4} | no |
| 33362 | 2 | 2 | {2: 2} | no |
| 33421 | 6 | 0 | {1: 1, 2: 2, 3: 3} | no |

- over every union finding, paired or not: k distribution {1: 45, 2: 40, 3: 69, 4: 221}; identical-ask folds 6 of 381

## 5. The judge against itself: one-member union findings are their source finding verbatim

- same (finding, obligation) pairs judged in both audits: 110; same verdict 106 (0.96); hit -> miss 1, miss -> hit 3; pairs the source audit did not hold 0
  - H55r1 `e83e6544`: hit -> miss
  - H55r2 `e8e02821`: miss -> hit
  - Hyg1 `7fef913e`: miss -> hit
  - M5 `e83e6544`: miss -> hit

## 5b. The 14 control-PR findings, as filed: the union's price, read per PR

| PR | k | passes (site and kind) | members | family / kind | asks |
|---|---|---|---|---|---|
| 33304 | 3 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | Hyg1 | other / style_norm_violation | While re-wrapping, change the names to the real ones, e.g. ``` In `Mathlib/CategoryTheory/Localization/Predica... |
| 33304 | 3 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | Qualify the three names as `Functor.IsLocalization.of_equivalence_target`, `Functor.IsLocalization.of_equivale... |
| 33304 | 3 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | H55r1 | other / style_norm_violation | In the module docstring, replace `Localization.of_equivalence_target` with `Functor.IsLocalization.of_equivale... |
| 33304 | 1 | probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | On line 703 change ``and combined with `colimit.ext` we rely on these lemmas`` to ``and combined with `colimit... |
| 33304 | 1 | probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | Extend the module docstring to cover the `Under` instance as well, e.g. replace lines 10-17 with:  ``` /-!  # ... |
| 33304 | 1 | probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | On line 14 write ``canonical isomorphism `preservesLimitIso : G.obj (limit F) ≅ limit (F ⋙ G)`.``, and on line... |
| 33315 | 4 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_claude_sub_rep2, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | H55r2 | other / style_norm_violation | Replace ``See `Mathlib/Data/Fintype/Basic.lean`.`` with ``See `Mathlib/Data/Fintype/Defs.lean`.`` |
| 33315 | 4 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_claude_sub_rep2, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | Hyg1 | other / style_norm_violation | Replace "See `Mathlib/Data/Fintype/Basic.lean`." with "See `Mathlib/Data/Fintype/Defs.lean`." on line 38. |
| 33315 | 4 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_claude_sub_rep2, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | On line 38 change `See `Mathlib/Data/Fintype/Basic.lean`.` to `See `Mathlib/Data/Fintype/Defs.lean`.` |
| 33315 | 4 | probe_dev_opus55_contract2_claude_sub_rep1, probe_dev_opus55_contract2_claude_sub_rep2, probe_dev_opus55_contract2_hygiene_claude_sub_rep1, probe_dev_opus5_contract2_claude_sub_rep1 | H55r1 | other / style_norm_violation | Change "See `Mathlib/Data/Fintype/Basic.lean`." to "See `Mathlib/Data/Fintype/Defs.lean`." |
| 33315 | 2 | probe_dev_opus55_contract2_claude_sub_rep2, probe_dev_opus5_contract2_claude_sub_rep1 | H55r2 | other / style_norm_violation | Reword the note so it no longer describes future work, e.g.: "For the analogous construction on finitely-suppo... |
| 33315 | 2 | probe_dev_opus55_contract2_claude_sub_rep2, probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | On lines 16-17 write `List.Nat.antidiagonal n`, `Multiset.Nat.antidiagonal n`, and `Finset.antidiagonal n`. |
| 33315 | 1 | probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | Replace line 21 with `* `HMul.hMul`/`*`: multiplication of two matrices, see `Matrix.mul_apply``. |
| 33315 | 1 | probe_dev_opus5_contract2_claude_sub_rep1 | M5 | other / style_norm_violation | Rewrite lines 41-46: drop the `inclusion` bullet (point to `Mathlib/Data/Set/Inclusion.lean` instead), and rep... |
- K=2, H-claude reps 1+2: control findings 1, 3 (2.0 per PR) are 1, 2 distinct site-and-kind claims (1.5 per PR)
- K=3, + hygiene rep 1: control findings 2, 4 (3.0 per PR) are 1, 2 distinct site-and-kind claims (1.5 per PR)
- K=4, all four: control findings 6, 8 (7.0 per PR) are 4, 4 distinct site-and-kind claims (4.0 per PR)

## 6. Per PR

| PR | union findings | H55r1 | H55r2 | M5 | Hyg1 | obligations | hit (union audit) |
|---|---|---|---|---|---|---|---|
| 33066 | 28 | 7 | 9 | 7 | 5 |  |  |
| 33098 | 43 | 13 | 11 | 9 | 11 |  |  |
| 33117 | 33 | 11 | 8 | 9 | 7 | 1 |  |
| 33145 | 34 | 10 | 9 | 8 | 9 | 5 | 4 |
| 33149 | 67 | 19 | 18 | 13 | 18 | 3 | 3 |
| 33285 | 20 | 5 | 5 | 4 | 6 | 2 | 2 |
| 33294 | 31 | 7 | 9 | 7 | 8 |  |  |
| 33304 (control) | 6 | 1 | 0 | 4 | 1 |  |  |
| 33305 | 10 | 3 | 2 | 2 | 3 | 1 | 1 |
| 33315 (control) | 8 | 1 | 2 | 4 | 1 |  |  |
| 33321 | 40 | 10 | 9 | 10 | 11 | 3 | 1 |
| 33337 | 4 | 1 | 1 | 1 | 1 | 1 |  |
| 33362 | 15 | 3 | 3 | 5 | 4 | 1 | 1 |
| 33421 | 27 | 6 | 9 | 6 | 6 | 3 |  |
| 33438 | 9 | 2 | 2 | 3 | 2 |  |  |
