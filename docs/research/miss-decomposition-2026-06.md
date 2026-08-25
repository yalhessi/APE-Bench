# Miss decomposition: is the wall selection or coverage?

*2026-06-19. Pure analysis over existing predictions — no new API calls (all topical
judgments served from the frozen `gpt_5_mini` matcher cache; 0 uncached pairs). Reproduce with
`python -m src.datasets.pr_review_v2.miss_decompose`; raw numbers in
[predictions/miss_decomposition.json](../../inputs/pr_review_v2/predictions/miss_decomposition.json).*

## The question

The headline result (progress report §6) is that no single setting recovers maintainer findings
both reliably and precisely. The natural next lever is a **selector** over a flooded candidate
pool — but that only helps if the gold the agents miss is *in the pool, unselected*. If instead the
missed gold was **never generated**, the lever is better generation (retrieval, exhaustive
enumeration), not selection. This analysis decides which.

For each anchored gold finding, against a pool of predicted findings, classify it:

- **COVERED** — a prediction lands at the gold location (same file, within ±10 lines) **and** passes
  the topical gate (same concern). This is the recall hit.
- **LOCATED-MISS** — a prediction lands at the gold location but **none** passes the topical gate.
  The generator *reached the exact spot* and raised something else. → **SELECTION gap.**
- **UNTOUCHED** — no prediction lands anywhere near the gold location. The pool never surfaced a
  candidate there. → **COVERAGE gap.**

`UNTOUCHED` is pure geometry (judge-independent); `COVERED`/`LOCATED-MISS` split a located pair by
the frozen topical judge.

## Result

115 anchored gold findings. "miss" = located-miss + untouched.

| pool | recall | covered | located-miss | untouched | **selection / miss** | coverage / miss |
|---|---:|---:|---:|---:|---:|---:|
| gpt_5.4 holistic | 10% | 12 | 13 | 90 | 13% | 87% |
| gpt_5.2 holistic | 31% | 36 | 40 | 39 | 51% | 49% |
| gpt_5.4 composed | 11% | 13 | 25 | 77 | 25% | 75% |
| gpt_5.2 composed | 12% | 14 | 21 | 80 | 21% | 79% |
| gpt_5.4 union (hol+comp) | 20% | 23 | 28 | 64 | 30% | 70% |
| gpt_5.2 union (hol+comp) | 37% | 42 | 42 | 31 | 58% | 42% |
| **grand union (all 6 runs)** | **47%** | **54** | **39** | **22** | **64%** | 36% |

**The single most important number: across everything we have ever generated, 93 of 115 gold
findings (81%) have a prediction sitting at their exact location.** Only **22 (19%) are untouched.**
Of the 61 misses, **64% are selection gaps** (right place, wrong concern) and **36% are coverage
gaps**.

The trend across rows is the mechanism: a conservative single agent (gpt_5.4 holistic) misses almost
everything as *untouched* (87% of its miss) — it simply doesn't flag much. As generation gets more
eager / pooled, untouched collapses (87% → 36% of miss) and the residual converts to *located-miss*:
more spots get touched, but the agent raises a different concern than the maintainer there. **More
generation does not run out of locations to hit; it runs into the wrong-concern wall.**

## By stratum (grand union)

| stratum | gold | covered | located-miss | untouched | untouched rate |
|---|---:|---:|---:|---:|---:|
| V1 | 2 | 1 | 1 | 0 | 0% |
| V2 (golf/dup/generality) | 56 | 23 | 24 | 9 | **16%** |
| V3 (naming/docs/style) | 53 | 27 | 14 | 12 | **23%** |
| V4 | 4 | 3 | 0 | 1 | 25% |

V2 — the verifiable stratum — is now **84% located** (only 9/56 untouched): pooling the eager model
and the verified checkers fills almost all V2 *coverage*; what remains is selection (the agent golfs
a different line than the maintainer, or flags a name-typo where the maintainer wanted a proof golf).
V3 conventions are the **stickier coverage gap** (23% untouched) — naming/namespace suggestions on
declarations nobody flagged at all, which no agent systematically enumerates.

## What each gap looks like

**LOCATED-MISS (selection) — generator on the exact declaration, different concern:**

- `IsSheafFor.lean:811` — maintainer wants a proof golf (`simp [← FunctorToTypes.map_comp_apply, …]`);
  all three nearby predictions flag a **typo in the theorem name** (`Compabible`). Same decl, the
  agent picked the superficial issue.
- `SchwartzSpace.lean:108` — maintainer: "rename this to `contDiff`"; agent: same lemma, but
  flags `protected`, a one-line proof, and redundancy instead.
- `Indecomposable.lean:50` — maintainer questions a defeq abuse in the *definition*; agent flags a
  docstring **typo** ("crystallogrphic") on the same decl.

These are the calibration wall in miniature: the candidate exists at the right place; the model
weights the wrong concern. A selector trained/prompted on which concern a maintainer escalates is
exactly the lever — and retrieval would not touch these.

**UNTOUCHED (coverage) — nothing generated nearby:**

- `HomotopyCat.lean:500` — "we already have `Cat.isTerminalOfUniqueOfIsDiscrete`" (a duplication the
  dup checker *should* catch — a retrieval target).
- `Round.lean:51` "How about `round_eq_div`?", `Schwarz.lean:58` "move these onto the `Complex`
  namespace", `Currying.lean:115` "add the corresponding `Full`/`Faithful` instances" — naming /
  namespace / API-completeness conventions on declarations no agent flagged at all.

The untouched bucket is dominated by V3 conventions that require *enumerating every new declaration*
and checking it against a convention, plus a few genuine duplications (retrieval targets).

## Implication for the next experiment

1. **Selection is the bigger lever, and it is well-posed.** 64% of misses (and 81% of all gold) are
   reachable — the candidate is already at the maintainer's exact line. Build the selector / concern-
   prioritizer first; it operates on candidates that demonstrably exist. The honest framing matches
   the user's constraint: deploy it as an *in-review priority policy* (weight which concern at a
   touched location to escalate), not a wasteful post-hoc filter.
2. **Coverage is the smaller, V3-flavored residual (19%).** Retrieval / inventory-enumeration earns
   its keep on the untouched bucket — mostly naming/namespace conventions on un-flagged declarations,
   plus a few true duplications. Worth doing, but second, and aimed at V3-convention enumeration +
   dup retrieval specifically, not as the primary move.
3. **Caveat — the split leans even more toward selection than shown.** `untouched` is judge-
   independent geometry (solid), but some `located-miss` pairs are arguably the *same* problem the
   topical judge split on a fine line (e.g. `Pointwise.lean:232`, both about the `n=0` case). If the
   judge is even slightly strict, real selection share is higher, not lower. The 19% untouched floor
   is the robust number.
