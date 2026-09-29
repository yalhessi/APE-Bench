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

---

## Result (2026-09-29): the rule fails on criterion 2, on both matchers

All 24 reviewer sessions and both matchers ran. The reviewer outputs were committed before any
matching (`2bd0d96`), and `unblind.py` applies the rule above to `match/matches.{1,2}.json`.

| | matcher 1 | matcher 2 |
|---|---|---|
| K stable, of the 11 (union) | 5 (6) | 6 (7) |
| X stable, of the 11 (union) | 5 (5) | 6 (6) |
| 1. K stable ≥ 3, each backed by a logged compile | holds | holds |
| 2. K stable − X stable ≥ 2 | **fails (0)** | **fails (0)** |
| 3. K findings per PR per run ≤ X pair's | holds (9.0 vs 15.7) | holds |
| **supported** | **no** | **no** |

**Per ask, on the 11 asks in the rule:**
- **Reached by all six reviewer sets, both matchers:**
  - the three instance-binder asks on 34091 (v0106-v0108): K by pass 3's binder check and usage;
  - the two pre-PR-proof asks on 30458 (v0062, v0063): K by pass 4's pre-PR proof.
  - All five are provenance-flagged in the caveats above.
- **Split between the matchers:** the `simpa` ask on 32875 (v0092). Matcher 2 credits K1, K2, X2 and
  X4. Matcher 1 credits none, because the reviewers rewrote the step with a different tactic. The
  two matchers agree on 80 of 96 cells, and all 16 disagreements are 32875's three golf asks.
- **Reached by one set only:** `grind` tagging (v0090), by K2.
- **Reached by no one:**
  - the one-liner from a sibling (v0105): partial in K1 and X3;
  - the section layout (v0060, v0061): partial everywhere, since every reviewer kept some
    subsections;
  - "same here" (v0091).

**Other reads:**
- K filed 54 findings against X's 94, over 12 sessions each. K's unmatched findings were 49 against
  70 (matcher 1) and 35 against 50 (matcher 2).
- K compiled more: 340 against 264.
- K reached fewer of all 16 asks per replicate (5-9 against 7-10), because it reviews no prose, and
  both docstring asks on 34091 are prose.

## What it means, at probe altitude (first reading; superseded by the second reading below)

1. **The constructions, as briefed, produced these misses no more often than the current brief did,
   with the same model and tools.** That is the rule's reading. It is one comparison: three PRs, two
   replicates, Claude reviewers.
2. **The control is the larger result.** With the plain generalist brief, Claude reached five or six
   of the eleven asks, stably. The pipeline's lead run reached none of them. The pipeline's
   whole-PR solo baseline on `gpt_5.2` (`val-small12-2026-09-25/match_solo`) holds the same tools
   and has no work units and no pruning. It too reached none of the five binder and pre-PR-proof
   asks.
   - So for these asks the miss is not coordination, work units or the lead's pruning. It is the
     reviewer model and harness (Claude and a Claude agent, against `gpt_5.2` with reasoning off in
     `ape_agent`), or recall: every PR here is inside Claude's training window.
   - The packets also differ: X had the pass-0 model and solo did not.
   - This probe cannot separate these causes. `docs/todo/reviewer-model-gap.md` states the test.
3. **The residue no brief reached is 4-5 asks:** the one-liner from a sibling, the section layout
   (two asks), and `grind` tagging (two asks). It is the class the constructions were written for,
   and they did not reach it either.

**Designs not yet tried:**
- the same comparison on PRs created after the reviewer's cutoff;
- the constructions on the pipeline's own model;
- X without the pass-0 model;
- constructions aimed at the residue: a sibling-lemma search, and a layout diff against the file's
  previous form;
- passes 1, 2, 5 and 6.

## Deviations during the run, recorded

- **The shared scratchpad.** Reviewers wrote snippet files into the session scratchpad, which every
  subagent can reach.
  - Two K pass-3 sessions shared a folder name with a K session on another PR, and reran from
    private folders. They report seeing file names only.
  - The round-1 feedback file sat in that scratchpad until the first report. It was then removed,
    and regenerated for the matchers with the same digest.
  - No tool result in any session contains text from the asks, and no session names another's
    directory (`audit_transcripts.txt`).
  - Pass-4 sessions launched after the first report were told to keep temporary files in their own
    `tmp/`.
- **Condition cues.** K findings cited construction ids ("as pass 3's c13 compiled"). These were
  redacted mechanically for every reviewer before matching (`build_match_inputs.py`).
- **The matchers** each wrote a helper script in the shared parent directory. Neither read the
  other's directory, the index or the seal.

## Second reading (2026-09-29), with corrections

A second review of the first reading's conclusions against the artifacts: the lead run's delegations
and abstentions on the two units, the solo run's findings, the K construction logs, and what the X
sessions did. Both the first reading and the first draft of this critique over-claimed. Corrections
to each are marked.

**What the experiment varied.** Both conditions had the pass-0 model, the whole PR, the arms' tools
and no pruning. The experiment varied only the construction brief and the pass split. It did not vary
coordination, so it cannot say whether coordination is a bottleneck for the pipeline.

**The control constructed unprompted.** The X sessions made 264 compiles across 12 sessions.
- X1 on 30458 reached the pre-PR-proof asks by compiling each original proof against the new
  statement. That is pass 4's `pre_pr_proof` construction, unbriefed.
- X1 on 34091 reached the binder asks with a caller search and a compile of the instance-binder
  versions of all three lemmas. That is pass 3's usage and binder check.
- So the rule compared briefed construction against spontaneous construction by a model that already
  does it. It cannot show whether constructing helps. It shows the brief is redundant for this model.

**The headroom was set against a different reviewer.** "Unreached" meant unreached by `gpt_5.2`'s lead
run. Claude with the plain brief reached 5-6 of the 11 stably, so criterion 2 had to be met on the
remaining 5-6, most of which are not visible from the file at base (below).

**Where the pipeline lost the five asks every Claude set reached.** *Corrected: the first draft of this
critique put two of them on pruning.* All five were lost at an arm's decision:
- 34091, the binder asks: `generality` and `style` ran and declined. `style` checked line breaks,
  indentation and `by` blocks, and the generalist filed four other findings on the unit.
- 30458, the pre-PR-proof asks: the lead pruned `proof_golf` and `proof_idiom`. But the generalist ran
  there and declined ("the new proofs are already in the concise, idiomatic `obtain` style"), and
  `generality` and `style` declined too.
- Every arm that ran held `lean_verify_edit`, and none replayed a proof or compiled a binder change.

So pruning added a loss at two of the five. The cause is the arm's initiative to construct, which is
what the align-decisions plan already located. The first reading's "the misses are the reviewer
model's, not coordination's" does not follow: model, harness, packet and recall are confounded with
it, and coordination was not varied.

**The design's family closure did run and did find things.** *Corrected: the first draft of this
critique said it found nothing, from a miscount.*
- Pass 3 stated 15 twins and 11 compiled. Five pass-3 findings rest on a twin. On 30458, both K runs
  found the right-cancel form of `#s ≤ #(s / s)` missing.
- None of the five matches a round-1 ask. Gold is a lower bound, so they are unaligned, not wrong.
- Pass 4 cited pass 3's constructions in 13 of its constructions. No rule hit rested on that.
- The selection rule chose PRs whose rule asks were binders, registration and proofs. So the sibling
  class, 27 of the 31 labelled sibling asks and the design's main target, was not in the rule.

**The residue no condition reached is of two other kinds.** *Corrected: the first draft of this critique
called the layout ask a preference with no regularity.*
- **The layout asks (v0060, v0061)** ask for `variable … in` over subsections. At 30458's base that
  idiom is in 1,129 of 6,947 Mathlib files (2,695 lines), 20 of 141 in `Algebra/Group`, 1 of 13 in
  `Algebra/Group/Pointwise`, and 0 in the file. It is a library idiom against the file's local
  practice: a scope conflict, which the maintainer resolved for the library. K2's pass 3 flagged the
  nesting and was matched partial.
- **The `grind` asks (v0090, v0091):** `Data/Finset/Image.lean` holds 18 `grind` uses at base and
  `Data/Rat/Lemmas.lean` none, against 137 files library-wide. This is an emerging migration: the
  first ask has a file regularity behind it and was reached once, and the second has none.
- **The sibling one-liner (v0105):** K's pass 4 found the pre-PR proof fails on the new statement, and
  the library's `Finite.exists_infinite_fiber` needs an import. The ask may not be satisfiable as
  stated. That is unverified.

**Recall.** Where the maintainers' suggestion was specific (the `variable … in` form, `simpa using`,
the named lemma), no Claude session reproduced it. The reached asks are the generic ones. That fits
capability better than memory. It is not proof.

**The corrected reading, at probe altitude** (three PRs, two replicates, Claude reviewers):
1. With a capable agent that holds compile and the whole PR, briefing the constructions and splitting
   the passes added no reach on these 11 asks, and filed 43% fewer findings.
2. Whether coordination is a bottleneck for the pipeline is untested here.
3. The gap between Claude and the pipeline on the mechanical asks is real. It sits at the arm's
   decision to construct, and its causes (model, harness, packet, recall) are confounded.
4. The unreached residue is a scope conflict and an emerging migration. That is convention knowledge
   (`docs/todo/conventions-nature.md`), not construction.

**What would test the design where it applies:**
- the construction briefs on `gpt_5.2`, the reviewer that did not construct;
- family closure on PRs whose misses are sibling-class;
- a reviewer whose training does not cover the PRs.

