# The filing decision: a contract the harness enforces, and a stage boundary

**Status** — open, 2026-10-12, **for a fresh session**; designed and adversarially reviewed, nothing
built, nothing run. The write-up with the round's verdicts is
`docs/research/filing-decision-design-2026-10-12.md` (§9–§12) and `filing-decision-design-2026-10-12/`.
**Cost** — the generator runs are free (DeepSeek on `first`, ~35 min a rep); the seal and the matchers
are about 0.5–1M subscription tokens on the primary account, the user's call.

**Motivating example.** Every ask of P14 and D12 read against six DeepSeek sessions
(`results/pr_review_v5/probes/ask-reading-2026-10-12/`, 93 asks, 558 rows): 1 miss in 558 was at a
place the reviewer had not read; at most misses it names the maintainer's concern and clears it
("`[Infinite β]` would be idiomatic ... Meh. Not a finding", v0106 DX3; "with their original proofs
compile ... a maintainer likely wouldn't reject them", v0062 DX1). Hand-coded, the grounds are worth
(27 rows), a plurality or a tool's count (22), the file's siblings (13), a check not run or run on the
wrong candidate (26), **nothing stated (13)**; a guess about maintainers is 6. The same paragraph that
ranks conventions over the reviewer's judgement already ran (`CONVENTIONS_PRECEDENCE`) and was routed
around 85 times of 177 held sentences. Every record result that moved this model's filings changed what
the submission may contain (forced abstention 0.20→0.50; `target_verdicts`; D1; S2 1→5 of 13); every
rule about grounds read null (F +0.03, G +0.000). Of 66 missed asks, 9–17 need a fact the reviewer
lacked; the rest are the filing decision.

**What would close it.** The pre-registered experiment of the write-up's §11: G (stage 1: the D1 cell
contract with the extended question axis, `conforms` refusable without a tool-call id, a quoted line or a
cited convention; the negative guard; `ask_author` legal; no withholding; candidates stored with typed
evidence and `would_clear_on`), All(G) and A(G) (the authority order as an offline policy over the stored
candidates), three reps, one seal, both matchers with a question form. Bars: All(G) ≥ 24 of the 37
inadmissible-`K` asks and ≥ 8 of the 32 never-reached core; A(G) keeps ≥ 80% of All(G)'s reach under
AP's yield guard and D1's ≤ 2.0 findings a control PR; below 16 of 37 the contract suppresses naming
and this entry moves to `dead-ends.md`. R (the order stated in-line) only if bar 1 passes.

**Start here.**
- read: `docs/research/filing-decision-design-2026-10-12.md` §9–§12 (the design that survived, and
  what was dropped), then `filing-decision-design-2026-10-12/alternative-design.md` §1 (the boundary and
  the typed evidence) and `review-generality.md` §3 (the volume sizing);
  `results/pr_review_v5/probes/ask-reading-2026-10-12/PROTOCOL.md` and `readings/aggregate.md` (the
  rows); `src/ape/tasks/lean_tasks/formal_math/review/structured.py` (the cell contract and the hand-back
  mechanism to make `conforms` refusable); `src/mathlib_review/analysis/probes.py:424-456` (S2's
  disposition paragraph and the precedence paragraph, the two rules this generalises);
  `docs/plans/2026-10-06-generation-without-suppression.md` (the `ask_author` form, line 142, and the
  volume bars); `.claude/rules/mathlib-review.md` (adding a design is three edits; a knob on task data).
- run (no spend): `ape/bin/python -m src.mathlib_review.review.cli plan --config
  configs/designs/structured_dev_local.yaml --run-name probe_dev_structured_check` to see the D1 design's
  preflight on the local tier (adjust the config name to the one on disk); `ape/bin/python
  results/pr_review_v5/probes/ask-reading-2026-10-12/aggregate.py` to regenerate the tables.
- bounded by: the 2026-09-22 selection ruling (stage 2 is selection, named as such, after a generator
  measured uncapped; `.claude/rules/mathlib-review.md`); `docs/dead-ends.md` "Linter-as-convention-oracle"
  (a check decides the question it was written for, never a convention's demand) and "Convention
  detectors closed as a recall lever" (the tail); the judge's rule that a question is false
  (`judge/protocol.py:65`), which must change before `ask_author` can score; the matchers' lack of a
  question form; `docs/todo/conventions-dossiers-exams.md` (its drop rule is met; understanding was not
  the bottleneck).

**Evidence** — the reading `54918b99`..`e1487575`; the draft `de7425b6`; the round `1af9b72e`,
`6ba6c020`, `9395bfb6`, `32babd96`; the design after the round `6756a48d`.

**Risk** — a reviewer forbidden to clear may name less (bar 1 is written for this); the published set
may be the places test again (the guards are written for this); the rank-2 sources (a mechanism
catalogue, the deprecation stream, analogue retrieval) do not exist, so the asks that need a fact stay
out of reach; every number is one reading on in-sample sets, with inter-reader agreement 25 of 30.
