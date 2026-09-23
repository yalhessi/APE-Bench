# What forcing unlocks, and why the naming arm is silent (2026-09-22)

Generation-side, after the ruling that publication questions are selection questions and that the
generator comes first. Free: a re-reading of two runs already on disk, `pr5_F_fanout_stage1_rep1`
and its forced twin `pr5_F_fanout_forced_stage1_rep1`, plus the release's naming gold.

## Forcing works through one arm, mostly

Same 173 invocations, same 4 pull requests. Empty submissions go **142 → 17**, findings **49 → 179**,
and gold-matched findings **2 → 7** over **2 → 5** obligations.

The two the unforced run got were the generalist on 33337 and `duplication` on 33145. The five added
by forcing:

| arm | PR | the ask it produced |
|---|---|---|
| `naming` | 33337 | rename `coe_starProjection_eq_isComplProjection` to `toLinearMap_starProjection_…` |
| `naming` | 33145 | rename `Dense.continuous_upperBounds` to `Dense.upperBounds_image` |
| `naming` | 33145 | rename `Dense.continuous_lowerBounds` to `Dense.lowerBounds_image` |
| `correctness` | 33421 | give `round_eq'` a descriptive unprimed name |
| `duplication` | 33145 | deduce `Dense.continuous_inf'` from its dual by `simpa` |

**Three of the five come from `naming`, which produced nothing at all unforced.** That matches the
silence read: `naming` has the best hit rate of any arm (3 hits in 7 findings across the three
held-out reps) and files least. It is not short of judgement. It is being talked out of speaking.

## What talks it out of speaking

Two things, and neither is the arm's bar.

**1. Its evidence tool answers a narrower question than maintainers ask.**
`naming_norm` counts *leaf prefixes* — `leaf_prefix` is `leaf.split("_", 1)[0]`
(`naming_norm.py:122`) — and its verdict compares the dominant prefix for a subject against the
current one. Taking the release's four naming-labelled gold obligations plus 33145's rename pair:

| ask | current → wanted | a prefix count can express it? |
|---|---|---|
| 33421 `round_eq'` → `round_eq_div` | `round` → `round` | **no**, the change is in the suffix |
| 33294 `isFundamentalSequence_of_isNormal` → `IsFundamentalSequence.of_isNormal` | flat → dot notation | **no**, it is a namespace move, not a prefix |
| 33337 `coe_…` → `toLinearMap_…` (×2) | `coe` → `toLinearMap` | yes |
| 33145 `continuous_upperBounds` → `upperBounds_image` | `continuous` → `upperBounds` | yes |

So on this small set **two of the maintainer's naming asks are not the question the tool answers**,
at any threshold. No value of `MIN_SUPPORT_RATIO` makes a prefix counter see a suffix convention or
a dot-notation move.

**2. On the asks it can express, it answered correctly and the answer was read as silence.**
For 33337 the tool returned `toLinearMap_` leading 21 to 7 — `emerging`, which its own description
calls "advisory at most". The arm wrote: *"is against an emerging `toLinearMap_` prefix (21 vs 7)
but not established, so I'm not requesting a rename."* Forced, the same arm produced the gold
rename. The signal was present, correct, and below a bar that converts it to nothing.

**And the zero branch tells the arm something false.** When `subject.token is None or
subject.confidence != "high" or population is None` (`context_tools.py:623`), all three return the
same sentence: *"The corpus has no counted opinion about this declaration's subject … Submit
nothing on naming."* Only the third of those is a fact about the corpus; the first two are the tool
failing to resolve a subject. Across the three held-out reps **477 of 632 `naming_norm` calls
(75.5%) return an empty result**, and nothing distinguishes which of the three causes fired.

## What this says to do, and what it does not

It is a generator finding, so the work is on what the arm can see and what it is told about it:

1. **Split the zero branch** so a subject the tool could not parse is reported as a tool limitation
   rather than as a corpus verdict, and does not carry "submit nothing". Free, and already item 1 of
   `docs/todo/specialist-arm-contents.md`.
2. **Decide what an `emerging` verdict licenses.** The tool says advisory, the arm's prompt says
   advisory, and the submission contract that is appended last says nothing about advisory at all.
   This is the norm-store maturity question, §D2 of `pr-review-v5-principled-design.md`, never built.
3. **Cover the asks the tool cannot express.** Suffix conventions and dot-notation/namespace moves
   are two of the four naming golds here. A prefix counter is the wrong shape for both.

It does **not** say to publish more of what the arms already file. That is selection, it is parked,
and on this evidence the generator has headroom that no ranking can reach: the arm that produced
three of the five forced-only hits produced *nothing* unforced.

## Caveats

- **One unreplicated pair of runs**, 4 pull requests, 10 obligations, one judge pass.
  `forbid_abstention` has never been run a second time.
- **The size of the gain depends on the judge's aggregation rule**, recomputed here from
  `sample_votes.jsonl`: forcing takes obligations hit from **2 → 5** on a majority of the three
  judge samples and from **2 → 3** unanimously, against 2 → 2 unforced under either rule. Six of
  the forced run's 68 voted pairs are split votes, against two of the unforced run's 34. The
  direction is the same under both rules and the headline halves under the stricter one, so quote
  the rule with the number.
- **Four naming gold obligations** (six rename-shaped asks counting 33145's pair). The 2-of-4 split
  is a description of this release, not a rate.
- Forcing is a diagnostic, not a design: it took control-PR emission 1 → 36 on the one control in
  that set. Nothing here proposes shipping it.
- The 477 empty `naming_norm` calls are counted from `context_trace.jsonl`; the three causes were
  not separated, because that needs the tool re-run against each call's workspace.

## Evidence

- Runs `pr5_F_fanout_stage1_rep1`, `pr5_F_fanout_forced_stage1_rep1` and their audits;
  `pr5_A_lead_heldout12_v2_rep{1,2,3}` for the trace counts; release `dev-medium-0.3.0`.
- `src/mathlib_review/evidence/operators/naming_norm.py` (`leaf_prefix`, `MIN_SUPPORT`,
  `MIN_SUPPORT_RATIO`), `src/ape/tasks/lean_tasks/formal_math/review/context_tools.py:600-660`.
- `docs/research/specialist-silences-2026-09.md`, `docs/todo/specialist-arm-contents.md`.

## What to buy when paid runs resume

Queued for after the provider change, in order. Nothing here is a selection experiment.

1. **`forbid_abstention` replicated** — rep2 and rep3 on the same four pull requests, then the
   other eight held-out ones. It is the only thing that turns 0.20 → 0.50 into a rate, and every
   claim in this file rests on one pair of runs. The config exists
   (`ReviewDataset.forbid_abstention`) and the runner already warns that it is diagnostic only.
2. **`ask_without_fix`** (`configs/v5_replay_ask_without_fix.yaml`, built and priced at $2.66 on
   the gold-site population plus $0.07 on the control one). It is the intermediate between "may
   abstain" and "must submit": the arm may file the maintainer's ask when it cannot make the fix
   compile. Read against its null on the same prefixes, and against the control population, which
   is what `--select control-abstentions` exists for.
3. **A rep with the corrected `naming_norm`** — the split zero branch changes what a future call
   tells the arm, and the arm's behaviour under it is not knowable from recordings made before it.
   This is the one that tests whether the naming arm speaks when its tool stops instructing silence.

The provider change resets what a recorded prefix can be replayed against: a replay pins the model
from its source run, so the recorded sessions here are replayable only while that model is
reachable. Anything that needs the old recordings should be run before the switch or accepted as
lost.

