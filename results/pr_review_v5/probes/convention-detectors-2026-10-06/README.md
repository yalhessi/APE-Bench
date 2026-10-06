# Convention detectors, measured alone: dot notation first (pre-registered 2026-10-06, before the detector exists)

`docs/plans/2026-10-03-after-structure.md` §2 (conventions as detectors in the packet) and the
second half of step 3 of `docs/research/codebase-redesign-2026-10.md` (the producer seam,
`src/mathlib_review/producers/`). This file fixes what the first detector is, how it is measured
and how it is read, before it is written or run.

## Why dot notation first

The census (`results/pr_review_v5/adjudications/conventions-census-v1`, reader A, 1,833 asks on
973 validation-window PRs, disjoint from every evaluation set) files **29 asks on 13 PRs** under
P057 ("a namespaced function or lemma applied to a term of that namespace's type is written with
dot notation (`x.f`)", rank 11 of 410 entries) and 4 under P034 (leading-dot). The primed-name
conventions (P113, P211) hold 9 asks on 9 PRs between them; generated families (P201) 11 on 10.
Dot notation recurs most, and it has a shape a deterministic check can state.

## The detector, fixed here

`dot_notation`, two shapes, both over the change graph only (no model, no corpus, no gold), and
only on code the PR adds:

1. **Placement (P108 / P057).** A declaration the PR adds or renames whose conclusion asserts a
   predicate `H …` (`conventions/situations.py::predicate_head`) and whose leaf name is
   `h_of_rest`, `h` being `H`'s last component with its first letter lowered: the fact names the
   form inside the predicate's namespace, `H.of_rest`.
2. **Method call (P057).** In a line the PR adds inside a changed declaration, an application
   `N.lemma x` where `x` is an explicit binder of that declaration whose type's head has the same
   last component as `N`: the fact names the form `x.lemma`.

A fact says what the code is and what the dotted form would be. It never says a maintainer would
ask for it.

## Sets, and what each can say

| set | PRs | asks | control PRs | role |
|---|---|---|---|---|
| dev (`configs/probe_sets/dev_medium_0_3_0.yaml`) | 15 | 47 | 33304, 33315, 33438 | **in-sample**: the two dev dot-notation asks (33294, `d0038`, `d0039`) were read while choosing the convention |
| validation small12 (`val_small12.yaml`) | 11 | 30 | 26185, 32080, 34935 | out of sample; asks not read |
| post-cutoff (`postcutoff_2026_07_08_v1.yaml`) | 10 | 16 | 41271, 41280, 41314, 42238 | out of sample; asks not read |

At the census rate (33 of 1,833 asks, 1.8%) the two out-of-sample sets hold about **0.8**
dot-notation asks between them, so **recall is not read out of sample here**. What they can say
is what the section would add to a packet: its volume, its emission on clean PRs, and whether its
facts are right.

## Measures

`cli producer bench --producer dot_notation --set <set> --out <this dir>/<set>`: facts per PR,
facts on control PRs, asks located (sharing a change target with a fact). Then by hand, every
fact on every set: is the dotted form it names *valid as written* (the binder's type is in the
namespace the lemma lives in; the predicate's namespace is the one the conclusion names) -- valid,
not asked for -- and, for every located ask, is the fact the ask.

## Reading rule, fixed before the detector exists

- **In-sample check.** Both dev asks located, each with a fact that states the ask's dotted form.
  A miss is a defect, fixed before the other sets are read, and reported as such.
- **The section is packet-ready** when, on validation small12 and post-cutoff each:
  - control emission is **at most 1.0 fact per control PR** (one Opus solo pass emits about 1.0
    finding per control PR on dev; a section that says more than that about clean code is noise);
  - and, pooled over both sets, **at least half the facts are valid as written** by the hand read.
- **Too noisy** if either fails; the shape that failed is named, and the section does not enter a
  packet.
- Recall waits for a set with enough dot-notation asks: the census PRs, which need change graphs
  built (`docs/todo/README.md` gets the entry if this one passes).

## The footprint threshold (redesign step 3)

The detector lands in at most **three `src/` files, one test fixture, and no hub edit**
(`runner.py`, `cli.py`, the task bases, `schema`).

## Amendment 1 (2026-10-06, after the in-sample check, before any out-of-sample set was run)

**The in-sample check, as it came out.** On dev, 7 facts on 2 of 15 PRs, 0 on the three control
PRs. `d0038` (33294) is located with the fact that states its ask exactly
(`IsFundamentalSequence.of_isNormal`). `d0039` (33294, `rw [Order.IsNormal.map_iSup h …]` ->
`h.map_iSup`) is **missed**, and the miss is a limit of the shape, not a bug: `h` there is bound
by a `fun h =>` inside the proof, so its type is known only after elaboration, and shape 2 reads
the declaration's binders. Five other facts on 33294 state the same move (`Order.IsNormal.map_*
H` -> `H.map_*`) where `H` *is* a binder, on lines no maintainer commented on -- the asked
transformation, at its siblings. Typing proof-local names by guesswork would trade the precision
bar for one ask, so the shape stays as fixed; closing the miss needs the elaborated local context,
which is the try-it battery's (after-structure §3). Reading continues with this limit stated.

**Validity is checked by Lean where it can be.** Several `H` are typed `Ordinal.IsNormal`, not
`Order.IsNormal`, and whether `H.map_sSup` then resolves is Lean's to say. So a method-call fact
(P057) counts as *valid as written* when the one-line edit it names compiles in the PR's reviewed
workspace (`cli tool lean_verify_edit`, line mode, the line with `N.lemma x` replaced by
`x.lemma`), and as invalid when it does not. A placement fact (P108) is a rename, which a compile
cannot judge, so it is read: the predicate's namespace exists and the dotted name is not already
declared (`cli tool declaration_search`). The pooled half-valid bar is unchanged.
