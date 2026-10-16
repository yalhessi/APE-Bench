# Enforcement at departures: are conventions applied at 5%, or do most departures get fixed? (2026-10-16)

Pre-registered before the script runs. The user (2026-10-16): the tension between "pinning the
convention sentence to the ask gives the largest gains" and "conventions are raised at 5% of the places
they apply" is the heart of the problem, and "it just works this way" is a bad explanation; a project as
mature as Mathlib cannot run on rules applied 5% of the time, so the 5% is more likely a measurement of
our constructs than of maintainers.

## Already answered?

- `docs/questions.md`, "Do deterministic convention detectors carry asks?": dot notation 16% of its 49
  census asks stated exactly, 8.8% of facts at an ask; primed names 5 of 9; validity by hand 19 of 20 (dot
  notation v3) and 20 of 20 (primed names). The facts are the departures this probe follows to merge.
- `docs/questions.md`, "Delivered as guarded rules pinpointed at places": on 16 census PRs a model
  flagged 205 places for ten rules, 6 at a round-1 ask (2.9%); per rule 1 in 20 to 1 in 400. **That is
  the 5%.** Its "applies" is a model reading our sentence; its "raised" is a round-1 ask on this PR.
- `docs/questions.md`, "Asked at every changed place": "departs" at 0.28 of decoy pairs and 0.30 of
  the PR's own conventions, the same rate, so a model's departure verdict at an unasked place carries
  no information about departures.
- `docs/questions.md`, "Can naming asks be read off the corpus?": merged Mathlib conforms at 0.94
  (membership lemma names) and 0.91 (inequalities). The library conforms where it can be counted.
- `docs/dead-ends.md`, "Convention detectors closed as a recall lever" (the tail) and
  "Linter-as-convention-oracle" (a check decides its own question, not a convention's demand). This
  probe uses the detectors as a *population of departures*, not as an oracle of asks.
- `docs/research/conventions-dossiers-review-2026-10.md` §3: the round split on reading "the author
  conformed later" as revealed preference (keep) or as migration noise (reject). This probe is that
  signal, measured.
- `docs/todo/adjudication-rubric.md`: whether unasked departures would be welcome is the open
  adjudication; the merge is the one gold-free arbiter on disk.

## The question

The 5% conflates three things: (1) the convention applies and the code already conforms; (2) our
sentence is broader than the convention maintainers hold, so the place is not in its scope; (3) a real
departure nobody asked about. Only (3) is under-enforcement. Measure, for conventions that can be
counted, what happens to a **departure** present at the reviewed head by the time the PR is merged.

## Population

The detector facts on the census PRs: `convention-detectors-2026-10-06/census/dot_notation_v3/facts.jsonl`
(182: P057 "write `h.lemma`", P108 "place the lemma in the predicate's namespace") and
`census/primed_names/facts.jsonl` (101: P113 "name the differing term, not a prime"). 283 facts on 154
PRs, 51 on control PRs (no round-1 ask at all). Each carries PR, path, line, declaration, convention
and `located_asks` (round-1 asks on the same change target). Hand validity: 19 of 20 and 20 of 20.

## Method (deterministic; `survival.py`)

For each fact: the merged commit is `git log -1 --grep='(#<pr>)'` in the Mathlib clone (HEAD
2026-05-14). The merged file is `git show <sha>:<path>`; if absent, the declaration is located in the
merged tree by name. Outcome per fact:

- **P057 (a call `Prefix.lemma arg`):** `survived` if the call still appears in the merged file;
  `fixed_dotted` if it does not and `arg.lemma` appears; `fixed_other` if neither (the code was
  rewritten or removed).
- **P108 (a name `isFoo_of_bar` beside its namespace):** `survived` if a declaration with that leaf
  exists at merge; `fixed_renamed` if not and the dotted form exists; `gone` if neither.
- **P113 (a primed name beside its sibling):** `survived` if a declaration with the primed leaf exists
  at merge; `fixed_renamed` if not and the unprimed sibling exists; `gone` if neither.
- `no_merge_commit`, `file_gone` where the merge or the file cannot be found; reported, not counted.

`fixed` = `fixed_dotted` + `fixed_renamed`; `fixed_other` and `gone` are reported apart (a rewrite
is not evidence about the convention). **Enforcement at departures** = fixed / (fixed + survived) over
checkable facts, by producer, split by: at a round-1 ask on the change (`located_asks` non-empty) or not,
and control PR or not.

## Reading rule, fixed now

1. **Validity of the method first.** Among facts at a located round-1 ask, fixed ≥ 80%. If a departure
   the maintainer asked about is not fixed by merge in the data, the method cannot see fixes (a rename
   the search misses, a moved declaration) and nothing further is read until that is understood.
2. **The main number, on unasked facts (no located ask), by producer and pooled:**
   - fixed ≥ 70%: departures are fixed even where no round-1 ask touched them (a later round, the
     author, CI, review outside the recorded threads). The 5% was a swollen denominator; conventions are
     applied, and the reviewer's job is to find true departures.
   - fixed ≤ 30%: maintainers let these departures through to merge. For these conventions the demand
     reading stands, or our sentence is broader than the real convention; the second half decides which.
   - between: undecided; the second half decides.
3. **Control PRs** (no asks at all) are the cleanest unasked stratum; reported apart.
4. **The second half, not run now:** the survivors read by two readers under each convention's motivation
   and scope, written out first: a departure under the convention as maintainers hold it, or excluded
   by its scope (a private helper, a deliberate local form, a pattern the namespace follows). The
   excluded share is the construct error of our sentence; ≥ 50% means the 5%'s denominator was
   mostly ours.

## Limits

Three conventions with a countable shape, head entries; nothing here reads the tail. `fixed_other`
cannot be attributed. A fix by merge does not say who fixed it or why (round 2, the author, CI); the
PR store's later rounds can split that afterwards. The clone ends 2026-05-14, so PRs merged after it
read `no_merge_commit`.
