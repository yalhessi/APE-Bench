# Four suspicious specialist decisions, replayed five times each (2026-09-16)

The first use of decision-turn replay (`docs/todo/replay-decision-turn.md`,
`src/mathlib_review/review/replay.py`). Four arm sessions from `pr5_A_lead_heldout12_v2_rep1`,
each cut just before its first `submit_candidates` call, re-sampled five times under the `null`
condition — nothing changed, the whole investigation held byte-identical. Run
`pr5_replay_null_first_submit_candidates_case4b_v2_rep1`: 20 samples, **$0.32 billed / $0.66
nominal**, ~4 minutes, no tool drift, every sample verified as started from its sealed prefix.

## Why these four

Chosen by reading the run, not by sampling: the two PR-33149 sessions disagree with each other
about the same file, and the two PR-33337 sessions are among the 23 of 89 specialist invocations
whose filed/abstained outcome differs across the three v2 reps. Selection is in-sample and
deliberately so — this is a case study of decisions someone had already found surprising.

| session | recorded decision | 5 replays |
|---|---|---|
| `wu:1c5956b98c096a64f567d656#correctness` (33149) | abstain `belongs_to_another_concern` | **5/5 abstain**, same reason |
| `wu:1e94e402e9bf04c7094996fd#docs` (33149) | filed, 1 anchor | **5/5 filed**, same `documentation_gap` |
| `wu:1f9cf7865fe0948dfc6e47f8#naming` (33337) | abstain `below_my_bar` | **2/5 filed**, 3/5 abstain (`below_my_bar` ×2, `already_correct` ×1) |
| `wu:1f9cf7865fe0948dfc6e47f8#style` (33337) | filed, 1 anchor | 5/5 filed, **2 anchors every time** |

## What the four say

**1. The naming miss is a decision-stage coin flip, and the gold answer was already in the
prefix.** Gold for 33337 asks to rename `coe_starProjection_eq_isComplProjection` to
`toLinearMap_starProjection_eq_isComplProjection`. Two of the five replays propose exactly that
name; the other three abstain *citing the same `naming_norm` verdict* — "`toLinearMap_` 21 vs
`coe_` 7, emerging not established". Identical evidence, opposite decisions, ~40% of the time
the maintainer's own rename. This isolates to the decision what
`dead-ends.md` ("Specialists as the coverage floor", amended 2026-09-14) measured end to end at
0.20 → 0.50 issue recall under forcing: no investigation difference is needed to explain the
miss, and the 3-rep instability at this invocation ([0,1,0]) needs no explanation beyond
decision noise. Cost to establish: **$0.07** on this one session.

**2. The abstention *label* is less stable than the abstention.** The same prefix yields
`below_my_bar` twice and `already_correct` once, and the `already_correct` detail is a bar
judgment in disguise ("no blocking naming change is supported"). Abstention reasons are read in
this project as diagnoses of why arms are silent; at least one in three of these labels is not
reproducible at the decision turn.

**3. A stable decision can still be the wrong one, and replay tells them apart.** The
`correctness` arm compiled a file whose key analytic steps are `axiom`s — a claimed
Navier–Stokes global-regularity result — recorded "extensive use of axioms", and abstained as
`belongs_to_another_concern` **5/5, with the same reason every time**. That is not sampling
noise to be fixed with reps; it is the arm's reading of its contract, and it is the kind of
thing a prompt or contract condition can be tested against cheaply (the `docs` arm on the same
PR filed about those same axioms 5/5). Replay's value here is the negative: no amount of
re-running will surface this finding.

**4. Style claims are reproducible in site and unreproducible in direction.** Every replay filed
the recorded blank-line candidate plus a second one at a neighbouring site, where the recording
filed one. At that second site, one sample asks to **remove** a blank line while three ask to
**insert** one — a contradiction at the same target from the same prefix. `model_confidence`
across these is 0.58–0.74, i.e. uninformative about the contradiction.

## Caveats

- n=5 per session, four hand-picked sessions, one source rep. Every rate here is ±large; the
  `style` "2 anchors 5/5 vs 1 recorded" difference is suggestive, not established.
- A replayed decision sits on an investigation shaped by the old contract, so none of this says
  what a changed contract would have made the arm *look at*.
- These are submission-level comparisons (filed/abstained, reason, anchors, candidate keys). No
  judge ran; nothing here is a recall number.
