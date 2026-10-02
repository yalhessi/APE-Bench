# The ensemble's union, read from the four Opus passes on disk (2026-10-02)

The free reading of Layer 2 in `docs/plans/2026-10-01-beyond-the-solo-baseline.md` §4, under the
rule `docs/todo/ensemble-union-reading.md` stated before anything was judged. Four Opus 5.x
passes on the 15 dev PRs exist under the project harness, each judged on the held-out 12
(23 obligations, judge v9): H-claude reps 1 and 2 (`probe_dev_opus55_contract2_claude_sub_rep{1,2}`,
7 and 7), Opus 5 (`probe_dev_opus5_contract2_claude_sub_rep1`, 8) and hygiene rep 1
(`probe_dev_opus55_contract2_hygiene_claude_sub_rep1`, 9). Their findings were unioned by
`cli report union` into the derived run `union_dev_opus_4pass_v1` (`e97d5e18`) and judged once
(`1282eb4d`; $0.81 billed, 112 anchored pairs, 336 samples, 0 retries, the same judge identity
`0711a6c0` as the four audits). Nothing was generated.

Regenerate: `ape/bin/python results/pr_review_v5/probes/ensemble-union-2026-10-02/reading.py`
writes `reading.md`; `conditions.json` is `cli report conditions --condition passes=<the four>
--condition union=union_dev_opus_4pass_v1`.

**What the union is.** 381 findings in, 375 out: only the identical ask folds (the grouping key
of `merge_findings`, which recurs across runs for 6 findings), and the suppression step that
demotes alternatives at one anchor never runs, since that is selection. Each finding carries
`passes_agreeing`, the number of passes that filed something of its `finding_key` (site and issue
kind), as a label: 45 findings at k=1, 40 at 2, 69 at 3, 221 at 4, over 137 keys (45, 20, 23, 49).
Admission is carried from each pass's own merge and not recomputed; the judge scores every finding
(pre-publication), as it does for the four passes.

## The reading under the rule

| | judged issue recall | control findings (33304, 33315) | per control PR | rule |
|---|---|---|---|---|
| H-claude rep 1 | 7 of 23 | 1, 1 | 1.0 | - |
| H-claude rep 2 | 7 | 0, 2 | 1.0 | - |
| Opus 5 | 8 | 4, 4 | 4.0 | - |
| hygiene rep 1 | 9 | 1, 1 | 1.0 | - |
| passes: mean / union / stable | 7.75 (0.337) / 11 / 6 | | | |
| **union of the four, judged** | **12 of 23 (0.522)** | **6, 8** | **7.0** | recall met (≥ 10); emission **not** (≤ 2.0) |

**The union of the four is not a lever, as built.** Its recall clears the bar by two; its control
emission is three and a half times the bar. The todo pre-stated what to do in that case: read the
K=2 and K=3 subsets, flagged as chosen after the fact.

Beside it: reachable recall 0.667 (8 of 12), resolution recall 9 of 23, gold alignment 0.104 (39
of 375 findings hit something), 90 of the 375 paired at a gold anchor. 33149 (AI-generated) holds
67 of the 375 and all 3 of its obligations are hit by every pass.

## The spine: each pass, their audits' union, the union run's own audit

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
| `7f098f6a` | | . | . | . | . | . | . |
| `7fef913e` | 33145 | loc | loc | . | loc | . | **HIT** |
| `8d887ce4` | 33145 | loc | loc | loc | loc | . | loc |
| `8e276803` | | . | . | . | . | . | . |
| `bd8a8d8c` | 33145 | HIT | HIT | HIT | HIT | HIT | HIT |
| `c9739efc` | 33321 | loc | loc | loc | loc | . | loc |
| `cc44bb99` | 33305 | HIT | HIT | HIT | HIT | HIT | HIT |
| `ce7b5d2e` | | . | . | . | . | . | . |
| `e83e6544` | 33145 | HIT | HIT | HIT | HIT | HIT | HIT |
| `e8e02821` | 33145 | loc | loc | HIT | loc | HIT | HIT |
| `f54010d8` | 33149 | HIT | HIT | HIT | HIT | HIT | HIT |

Every obligation some pass hit is hit in the union's audit (11), and one more: `7fef913e`
(33145, the `Dense.ciInf'` via the order dual ask), which is hygiene rep 1's finding at that
anchor, judged miss in its own audit and hit here. **The +1 over the spine is a judge flip on
identical text, not a union effect.** A one-member union finding is its source finding verbatim,
so the two audits can be compared pair by pair: of the 110 (finding, obligation) pairs both hold,
the judge gave the same verdict on 106 (0.96). The four flips: H55r1 at `e83e6544` hit to miss
(the obligation stays hit through the other passes), M5 at `e83e6544` miss to hit, H55r2 at
`e8e02821` miss to hit (M5 had hit it), Hyg1 at `7fef913e` miss to hit (the new one). So the
union's judged count is 12 with the flip and 11 without; both are reported, as the rule asked.
The ten obligations no Opus cell reaches (`consistency.py`) stay unreached: the union adds nothing
the passes did not already say.

## The K=2 and K=3 subsets, chosen after the fact

Read off the same audit through `union_report.json`'s `members` map (which runs filed each union
finding), so no second judge call: a subset's finding is its source finding verbatim, except for
the 6 folded sentences, whose representative differs from its siblings by case and whitespace.

| subset | findings | judge-paired | hit obligations, union audit | hit, the passes' own audits | control findings (33304, 33315) | per control PR | distinct claims per control PR | rule |
|---|---|---|---|---|---|---|---|---|
| K=2, H-claude reps 1+2 | 192 | 47 | **9** of 23 | 8 | 1, 3 | **2.0** | 1.5 | recall not met (9 < 10); emission met, at the bar |
| K=3, + hygiene rep 1 | 283 | 70 | **12** of 23 | 10 | 2, 4 | **3.0** | 1.5 | recall met; emission not |
| K=4, all four | 375 | 90 | **12** of 23 | 11 | 6, 8 | **7.0** | 4.0 | recall met; emission not |

No subset is a lever under the rule. K=2 sits on the boundary of both halves: 9 against 10, and
2.0 against 2.0, with its ninth obligation (`e8e02821`) resting on the H55r2 flip above; in the
passes' own audits it is 8, which is what the todo recorded for two reps of one configuration.
K=3 clears recall with the help of two flips (10 in the passes' own audits) and fails emission
at 3.0. Opus 5 alone contributes 8 of the union's 14 control findings; without it the union
emits 3.0 per control PR, still above the bar.

## Agreement as a label, with no cut

The selection-signal todo's close condition is "the same table on a run set not used to find
it": cross-rep agreement, measured on the lead reps in `docs/research/code-review-systems-survey-2026-09.md`
§1, separated hits at 0.70 and 0.89 in the 2-of-2 bucket against 0.18 and 0.22 in the 0-of-2
bucket (within-PR AUC 0.706 to 0.892). These four passes postdate that analysis and were not used
to find it. Over the 90 judge-paired union findings, hit = the judge's majority `issue_match`
against any paired obligation:

| k (passes agreeing on site and kind) | paired findings | hit | rate | distinct obligations hit |
|---|---|---|---|---|
| 1 | 6 | 3 | 0.50 | 4 |
| 2 | 6 | 4 | 0.67 | 3 |
| 3 | 14 | 4 | 0.29 | 3 |
| 4 | 64 | 28 | 0.44 | 8 |

Within-PR AUC of k: **0.482**, over the 2 PRs that hold both a hit and a non-hit among their
paired findings (33145 and 33321; 221 ordered pairs). Without 33149 the rates are 0.25, 0.50,
0.09, 0.36 and the AUC is unchanged, since all 15 of 33149's paired findings hit and it enters no
pair. **On these passes the label does not separate hits: the rate is not monotone in k and the
within-PR AUC is chance.**

Why, as far as this reading can see: at a gold anchor, agreement is saturated. The passes anchor
at almost every gold change (the `loc` rows of the spine), so a finding paired to gold nearly
always has k=4, whatever it asks there: 64 of the 90 paired findings, and in the two PRs that
enter the AUC 36 of 38 (33145: 28 of 30; 33321: 8 of 8). A label that is constant where the
question is asked cannot order anything there. The lead reps the signal was found on had per-site
arms whose agreement varied at gold anchors; whole-PR passes of one model family, sharing 49 to 65
percent of their targets, do not vary there. What this does not test: agreement measured on a
finer identity (the exact ask recurs 6 times in 381, so nothing is there to read), or on passes
decorrelated across model families (gpt-5.5 under Codex or APE-Agent is not among the four).
Reported as a label's property; no cut, ranking or gate is proposed (the ruling of 2026-09-22).

| PR | paired findings | hit | k of the paired findings | enters the AUC |
|---|---|---|---|---|
| 33117 | 16 | 0 | 1: 2, 3: 6, 4: 8 | no |
| 33145 | 30 | 11 | 3: 2, 4: 28 | yes |
| 33149 | 15 | 15 | 1: 2, 2: 2, 3: 3, 4: 8 | no |
| 33285 | 5 | 5 | 1: 1, 4: 4 | no |
| 33305 | 4 | 4 | 4: 4 | no |
| 33321 | 8 | 2 | 4: 8 | yes |
| 33337 | 4 | 0 | 4: 4 | no |
| 33362 | 2 | 2 | 2: 2 | no |
| 33421 | 6 | 0 | 1: 1, 2: 2, 3: 3 | no |

## The price, read per PR: what the 14 control findings are

Every one is `style_norm_violation` on docstring or comment wording (`reading.md` §5b lists them).

- **33315 (8 findings, 4 claims).** All four passes ask for the same thing in four spellings:
  the module doc's "See `Mathlib/Data/Fintype/Basic.lean`" should read `Defs.lean` (k=4). Two
  passes file two different asks at one further site (k=2), and Opus 5 files two more alone.
- **33304 (6 findings, 4 claims).** Three passes ask, three ways, to qualify
  `of_equivalence_target` as `Functor.IsLocalization.of_equivalence_target` in the module doc
  (k=3); Opus 5 files three docstring edits alone.

So the union's emission is 7.0 findings per control PR and 4.0 distinct claims per control PR.
The exact-ask fold does not recognise one ask in four phrasings, and the judge, which pairs at the
anchor, counts them as four findings too. A maintainer would read them as one comment. Whether the
rule's unit should be the finding or the claim is a decision this reading does not make; the rule
was stated in findings and is read in findings. Both numbers are above 2.0 for K=4 either way;
for K=3 the claim count is 1.5.

## What this does and does not say

- **Does say.** Unioning four solo Opus passes recovers exactly what the passes' own audits
  recovered (11 of 23, read as 12 under a fresh judge pass that flipped 4 of 110 verdicts), at
  a control emission that adds up as the todo feared: 7.0 findings per control PR, 4.0 claims.
  The pass-agreement label does not separate hits on these passes, because it is saturated at
  gold anchors. The judge's self-agreement on identical text is 0.96 here (the project's working
  figure was about 0.90).
- **Does not say.** Anything about validation or post-cutoff PRs: this is dev, inside the Opus
  models' training window, and the plan's confirmation step (blind matchers on small12 and the
  post-cutoff set) was not done. Anything about three ensemble repetitions: this is one union of
  four single reps, and the rule in plan §5 is stated for the mean over three. Anything about
  decorrelation by design: these passes vary model version and tool hygiene, not reading order or
  a second round, which the plan's Layer 2 names as the decorrelators.
- **Plan consequence.** §4 Layer 3 (the refutation-only critic) is "built only if Layer 2's
  union raises control emission past its rule". It has, on this reading. Whether to build it, or
  first change the union's fold so that one ask in several phrasings is one finding (which is a
  change to what reaches the judge, not to what reaches a maintainer), is recorded as the open
  decision in `docs/todo/ensemble-union-reading.md`.

## Files

- `reading.py`, `reading.md`: the reading, regenerable from the committed run and audits.
- `conditions.json`: `cli report conditions` over the four passes and the union: the funnel
  (mean 7.75, union 0.478, stable 0.261 against the union run's 0.522), control emission per
  repetition, and the exclusive set (`7fef913e`, union only).
- The derived run: `results/pr_review_v5/runs/union_dev_opus_4pass_v1/` (`findings.jsonl`,
  `union_report.json` with the `members` map, `stages.jsonl` with the `union` and `judge` rows).
- The audit: `results/pr_review_v5/audits/union-dev-opus-4pass-v1/`.
