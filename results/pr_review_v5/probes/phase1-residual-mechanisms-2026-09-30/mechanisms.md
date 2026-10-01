# Phase 1 result (2026-09-30): the residual asks are missed by judgement on objects the reviewers did look at

141 (ask, reviewer) pairs over the 67 residual asks, two blind readers each, eight reader
transcripts audited clean. **The readers' label sets are disjoint on 0 of 141 pairs.** Counts are
asks where both readers gave the label (any reviewer), out of 67; `mechanisms.py` reproduces every
number.

## The table

| mechanism | asks (both readers) | either reader | share of 67 |
|---|---|---|---|
| `attempted_concluded_fine` | 40 | 51 | 60% |
| `filed_elsewhere` | 40 | 43 | 60% |
| `attempted_opposite` | 25 | 25 | 37% |
| `knowledge_convention` | 25 | 32 | 37% |
| `try_it_not_tried` | 19 | 21 | 28% |
| `analogue_not_compared` | 6 | 13 | 9% |
| `pr_level_or_history` | 5 | 5 | 7% |
| `never_attempted` | **4** | 5 | **6%** |
| `not_reachable_from_code` | 3 | 4 | 4% |
| `ask_unclear` | 3 | 4 | 4% |
| `verified_withheld` | **2** | 6 | **3%** |

Reachable (per pair, both readers): yes 114, unclear 12, disagree 12, no 3.

By reviewer family the shape is the same. Claude on the 37 asks nobody reaches: concluded fine 19,
filed elsewhere 21, opposite 17, convention 13, try-it 5, PR-level 4. gpt_5.2 carried on the 30 asks
only Claude reaches: concluded fine 15, filed elsewhere 14, try-it 12, opposite 8, convention 8,
never attempted 2.

## What it says

**Coverage is not the problem.** In 63 of the 67 residual asks every reviewer that missed the ask
had read, searched or compiled the object it is about. The four exceptions: an import-cost question
(d0007), a file whose only read failed on a path (d0039), and two PR-description asks (v0053, v0056).
Most misses sit on an object the reviewer also filed something else about (60%).

**Withholding is not the problem either.** Two asks: X1 and X2 compiled `(by simpa using h)` on
v0093 and did not file it, and both Claude sessions left 41930's description issue as "PR metadata
only". This agrees with Phase 3.1: out of sample, what the newer models withheld was not what
maintainers asked.

**The misses are judgement on an attended object**, concluded fine (60%) or changed differently
(37%): another name for the right diagnosis (`Dense.ciSup_eq_ciSup_subtype` for `Dense.ciSup`,
`_of_le` for `_anti`), another golf of the right proof (`split_ifs` where `grind` was asked, explicit
terms where `positivity`/`gcongr` were), deleting what the maintainer wanted improved. Two
input-side mechanisms account for most of that judgement:

- **`knowledge_convention`, 25 asks.** Registration and generation mechanisms the reviewers show no
  sign of knowing (`to_fun`, `mk_iff`, `grind` tags, `OrderDual` derivations); naming conventions
  (`_left`/`_right` argument position, short names under a `Dense.` namespace, `toLinearMap_` for the
  coercion, where `naming_norm` counted `coe_` 48 to 9 and misled all three reviewers on d0045);
  binder and section style (`variable ... in`, explicit universe binders); the AI-disclosure policy.
  By family: naming 6, interface 5, derive-don't-restate 5.
- **`try_it_not_tried`, 19 asks.** Decidable by one compile that no reviewer ran: "can `positivity` do
  this", "can `gcongr` do this", `simpa using h`, "does the old proof not work?", "a one-liner using
  `infinite_pigeonhole_card_lt`", the `grind` golfs, the `OrderDual` one-liners. 14 of them are
  proof asks (F1). This is the mechanical class `remaining-misses-kind.md` found the closer battery
  reaches.

`analogue_not_compared` (6) and `pr_level_or_history` (5) also meet the five-ask bar; `never_attempted`
(4) and `verified_withheld` (2) do not.

## Consequences for the plan (the rules written before the readers ran)

- **Phase 2 (the lead + arms path under carried reasoning) is not funded.** Its premise was that
  coverage forcing might be the lever; coverage is 6% of the residual. The arms' other possible
  contribution, specialist knowledge, is Phase 3.3's lever and is tested there directly. The arms
  stay in the tree; nothing is shelved on this evidence.
- **Phase 3.2, try-it, is next**, 19 asks: the closer battery run over every changed proof and
  side goal (standard finishers: `simp`, `simpa`, `positivity`, `gcongr`, `grind`, `omega`,
  `norm_num`, `exact?`), its compiled outcomes given to the reviewer as evidence, and the brief
  saying that an automation that closes a goal is a request. Mechanical, decidable, and the same
  for both reviewer families.
- **Phase 3.3, conventions, 25 asks**, from the census codebook, with the scope the census found
  (conventions vary by area). The `naming_norm` failure on d0045 is a tool defect to fix first: a
  count that tells three reviewers the wrong prefix is worse than no count.
- `analogue_not_compared` and `pr_level_or_history` are funded in principle and wait behind those two.

**Altitude.** Labels are two readers' judgements from the transcripts and notes, not measurements.
Their agreement is high (no disjoint pair; 12 reachability disagreements in 141). Validation's
two readers were different models (see README). The shares describe the residual of one gpt_5.2
carried run and two Claude sessions per PR on three sets.
