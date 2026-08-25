# v8 rubric verdict: adopt it — it removes the noise floor, but it did not fix the error

*2026-08-05. 18 pairs (3 reps × 6) of the 0.9.0 stable smoke, `gpt_5_mini`,
`max_tokens=4000 / thinking_budget_tokens=3000`, `sample_count=3`. Complete coverage
(18/18). Compared against the v7.1 task arm — same model, same harness, rubric as the only
variable. Report: `rubric-comparison.json`.*

## Headline

| | v7.1 | v8 |
|---|---|---|
| split-vote pairs (judge disagrees with itself) | 4/18 | **0/18** |
| self-agreement ceiling | 90.1% | **100%** |
| `issue_match` verdicts | 9/18 | 9/18 |
| `resolution_match` verdicts | 4/18 | 5/18 |
| `issue=True, resolution=False` (two-level separation) | 5 | 4 |
| levels collapsed | no | no |

**The noise floor collapsed.** If the v7.1 split rate (22%) still held, observing 0 splits
in 18 pairs has probability ≈ 0.011, so this is a real drop rather than a lucky draw —
with the caveat that n = 18 is small.

## Predictions, scored honestly

Registered in advance in `audits/judge-prompt-regression.md`:

| prediction | outcome |
|---|---|
| bimodality falls | **PASS** — 4 splits → 0, ceiling 90.1% → 100% |
| `issue=True, resolution=False` appears | n/a for `gpt_5_mini` (it already produced 5; now 4). This prediction was about `gpt_5.2`, which has not been re-run. |
| the stable error flips to `issue=False` | **FAIL — it did not flip** |

## The failed prediction is the important result

`…e373aeb72a4b` votes are **[0, 3, 0] under both rubrics** — identical. The rep-2 pair
still returns `issue=True`, now unanimously, with the explicit "a rename when the ask is a
proof change is false" clause and the reviewed code both in front of it.

Its v8 reason:

> "The candidate targets the same lemma (`Metric.card_maximalSeparatedSet`) and proposes
> renaming it to `encard_maximalSeparatedSet` and updating downstream uses (**including
> `coveringNumber_le_packingNumber`**), which achieves the maintainer's requested
> transformation."

This is a different, more defensible argument than v7.1's — and it is not obviously wrong.
The gold ask's own text names `encard_maximalSeparatedSet`, i.e. the *renamed* form, so
the maintainer's requested proof rewrite **presupposes the rename**. The candidate asks
for exactly that rename and says it will update `coveringNumber_le_packingNumber`. Under
"a different fix for the same problem may still issue-match", a judge can reasonably call
that the same underlying problem.

So my earlier characterisation of this as a clear judge error was too confident. Restating
it accurately: **this pair is a genuine rubric-boundary case about whether a prerequisite
rename counts as the same issue as the proof rewrite that depends on it.** It needs a human
ruling, not a prompt fix. The rubric cannot settle it because the rubric is what is
ambiguous.

## What v8 actually did

v8 changed **3 of 18** verdicts, all on the two previously bimodal obligations, and all in
the `resolution_match` dimension only:

| | v7.1 | v8 |
|---|---|---|
| rep1 `…4bfe0de1d5f6` | (True, True) | (True, False) |
| rep1 `…0898b0478443` | (True, False) | (True, True) |
| rep3 `…0898b0478443` | (True, False) | (True, True) |

On the watch pairs, every 2-of-3 became 3-of-3 **in the direction the majority already
pointed** (`0898b0478443`: [2,0,2] → [3,0,3]; `4bfe0de1d5f6`: [3,2,2] → [3,3,3]).

That is the precise, limited claim to make: **v8 made the judge confident about the
conclusions it was already reaching by majority. It did not change those conclusions.** The
coin flips were resolved toward the majority side, not adjudicated on the merits.

## Verdict: adopt v8

1. **Reproducibility is now free.** A 100% self-agreement ceiling means the ±12.5pp
   noise floor at n = 8 that forced the Phase 9 re-reading essentially disappears for
   future measurements. This is the single most valuable outcome — it is what makes small
   denominators readable at all.
2. **The metric barely moved.** `issue_match` is 9/18 under both rubrics; only the
   `resolution_match` dimension shifted, by one net verdict. v8 is not a stealth
   redefinition of recall, which is the risk that made this change worth gating.
3. **It is better-founded.** The judge now sees the code and is given the clauses the v3
   rubric had; its reasoning on the contested pair is visibly better even where the verdict
   is unchanged.

Caveats that stay attached:

- **v8 numbers are comparable only to v8 numbers.** Phase 9 and all earlier results stay
  measured under v7.1-as-implemented and are not re-scored.
- **The 100% ceiling is measured on 18 pairs from one PR.** It should be re-measured
  whenever the pair set changes materially — do not treat "the judge is deterministic" as a
  standing property.
- **One rubric-boundary case remains open** and is not a defect to fix in the prompt.

## Next

1. **Re-run `gpt_5.2` under v8.** Its collapse (`issue==resolution` on 18/18, zero
   two-level verdicts) is now the strongest candidate for a prompt-omission artefact,
   because the clause instructing that verdict was absent from v7.1 and is present in v8.
   If it separates the levels under v8, it becomes the better judge on every axis measured:
   deterministic *and* correctly two-level.
2. **Get a human ruling on `…e373aeb72a4b`**: does a prerequisite rename issue-match a
   proof rewrite that presupposes it? Whatever the answer, encode it as a worked example in
   the next rubric version rather than leaving it to inference.
3. **Update the noise floor carried into the roadmap** from ±12.5pp at n = 8 to
   approximately zero *for v8-scored comparisons* — while keeping the old figure attached
   to every v7.1-scored result already reported.
