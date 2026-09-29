# Construction demonstration: do the design's passes 3 and 4 produce the misses? (2026-09-29)

Written before any reviewer ran. This is the demonstration `docs/research/review-coordination-design-2026-09.md`
§10 states before any build, and the closing step of `docs/todo/remaining-misses-kind.md`: for the
largest artifact class, show on real misses that constructing the artifact exposes the ask.

## PRs and asks

**Selection rule**, from `results/pr_review_v5/adjudications/coordination-design-check-2026-09-29/pass_labels.jsonl`:
the three validation small12 PRs holding the most asks that `pr5_val_small12_minus30714_lead_rep1`
did not reach (neither matcher credited) and that are labelled pass 3 or 4, ties broken by holding
misses in both passes. That gives 34091 (4), 30458 (4) and 32875 (3); 30641 ties 32875 at 3 but its
misses are pass 4 only.

**The 11 asks the rule is read on** (the lead run reached none of them):

| PR | ask | pass | construction (planning label) |
|---|---|---|---|
| 34091 | v0105 | 4 | a one-liner from a sibling lemma |
| 34091 | v0106, v0107, v0108 | 3 | binders |
| 30458 | v0060, v0061 | 3 | binders and section layout |
| 30458 | v0062, v0063 | 4 | the pre-PR proof |
| 32875 | v0090, v0091 | 3 | registration against siblings |
| 32875 | v0092 | 4 | the idiomatic rewrite |

The PRs' other 5 round-1 asks (32875 v0093-v0095, 34091 v0109-v0110) are matched and reported, but
are not in the rule. No reviewer sees any ask.

## Conditions

- **K, the design's passes 3 and 4.** Per run, a pass-3 reviewer (`brief_K3.md`) and then a pass-4
  reviewer (`brief_K4.md`) given pass 3's `constructions.json` and never its findings or notes, as
  the design's first chaining rule requires. Two runs, K1 and K2; each run is two sessions. A run's
  findings are pass 3's and pass 4's together.
- **X, the control.** `brief_X.md`: the generalist brief the complement probe used
  (`SYSTEM_PROMPT_V12`'s checklist), with the same packet. Four runs, paired as (X1, X2) and
  (X3, X4) before any run, so that a control replicate is two sessions, as a K run is.
- **Shared by both:** `pr.md`, `diff.patch`, and `model.md`, the pass-0 model `build_model.py`
  renders from the release's input and derived files only. So the difference between conditions is
  the construction protocol and the pass split, not the model. Tools: `./ptool`, the arms' own tools
  through `cli tool`, compiling against each PR's reviewed workspace (`5dbc173`) with reads gated
  at the retrieval cutoff. The wrapper, not the reviewer, logs every call to `calls.jsonl`.
- **Reviewers:** Claude subagents (`claude-opus-5-5`), one per session, told to read only their own
  directory, to call tools only through `./ptool`, and not to use git, the web or any other path.

**Deviations from the design, stated:** pass 1 (intent and roles) is not run; pass 2 has no objects
on these PRs; passes 5 and 6 are not run; pass 0 lacks library candidates, the two censuses and
open-PR overlap (the design's §11 says they are not built); the reviewers are Claude, not `gpt_5.2`.

## Matching

Two blind matchers (Claude subagents) with `matcher_rubric.md`. Per PR the six reviewer sets (X1-X4,
K1, K2) are shuffled to R1-R6 by `blinding_SEALED.json`, and each finding is stripped to `target`,
`claim`, `requested_change` and `severity`.

## Reading rule

On each matcher, on the 11 asks:
- `K_r`: the asks some finding of run r `reached`; `K_stable = K1 ∩ K2`.
- `P_1 = X1 ∪ X2`, `P_2 = X3 ∪ X4`; `X_stable = P_1 ∩ P_2`.

**The constructions are supported if all hold on both matchers:**
1. `|K_stable| ≥ 3`, and for each such ask, in each run, the reaching finding cites a construction
   whose compile is in that run's `calls.jsonl`;
2. `|K_stable| − |X_stable| ≥ 2`;
3. K files no more findings per PR per run than an X pair does per PR per replicate (means over the
   three PRs).

Anything less reads "the constructions, as briefed, did not produce these misses beyond what the
current brief produces with the same model and tools", with the untried designs listed.

**Also read, not pre-registered:** unions and partials; the 5 other asks; which construction reached
each ask; pass 3 against pass 4; compiles attempted and passed; single sessions.

## Caveats stated before the run

- **The reviewer may have seen these PRs.** All three were created between 2025-06 and 2026-03,
  inside Claude's training window (`docs/research/facet-brief-probe-2026-09.md`, caveat). Absolute
  reach says nothing about reviewing ability; the comparison between conditions on one model stands
  at probe altitude, which is why X exists.
- **Brief provenance.** `brief_K3.md` names instance-implicit binders, section structure and
  `variable`s (item 5) and sibling registration (item 4); `brief_K4.md` names the pre-PR proof (item
  3). The design took these constructions from a declaration's anatomy and from the finding
  mechanisms of 2026-09-26, which were labelled on these misses. A K gain on v0106-v0108,
  v0060-v0061, v0090-v0091 or v0062-v0063 is therefore weaker evidence than one on v0105 or v0092,
  and results are reported per ask. The control's checklist names binder and attribute rewrites
  generically. No four-word sequence is shared between any brief or model and the 16 asks' prose
  (checked before sealing). No brief names a tactic.
- **The author chose the rule after reading the asks,** and labelled the passes (one reader).
- **n is small:** 11 asks, two replicates per condition.

**Cost:** Claude session time only; no pipeline spend.
