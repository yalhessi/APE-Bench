# The specialists were already asked the maintainers' questions (2026-09-23)

Phase 0 of `docs/plans/2026-09-23-work-enumeration.md`, the two free reads meant to size problem 1
(*"the specialists do not map onto maintainer work"*) before anything is built. Nothing was run
and nothing was spent. Every count is from committed artifacts: the three held-out lead reps
(`pr5_A_lead_heldout12_v2_rep{1,2,3}`), the three solo reps (`pr5_B_solo_ape_heldout12_v2_rep*`)
and the four-PR fanout pair (`pr5_F_fanout_stage1_rep1`, `pr5_F_fanout_forced_stage1_rep1`), read
through `report.buckets`, the judge audits' `semantic_report.json` / `semantic_matches.jsonl`, and
each run's `arm_pool.jsonl` (the record of the prompt every arm was actually sent).

## Conclusion first

**The question text is not where the specialists lose.** For 17 of the 23 counted held-out
obligations some specialist's brief, as sent, directs it to the specific check the maintainer asked
for — in seven of those cases in text written after earlier runs on these same PRs. What stands
between those briefs and a hit is measured, and it is two things:

1. **The lead did not run the arm.** In 33 of 60 obligation-reps where a brief asks the question,
   the arm holding it was pruned — 25 of them went unhit. This includes the easiest asks in the set,
   the ones the generalist found: both "remove the axioms" obligations on 33149 (`correctness`
   pruned in all three reps), the Parseval duplicate (`duplication` and `api_reuse` pruned 3/3), the
   docstring typo on 33321 (`docs` pruned 3/3), and both dot-notation asks on 33294 (`naming` and
   `api_reuse` pruned 3/3).
2. **The arm ran, with the question in its prompt, and stayed silent** — 18 of 60, 15 unhit — for
   reasons its own sentence names: an evidence tool's bar, the compile gate, or a judgement that the
   code was fine.

This argues **for** the ceiling the plan builds (no pruning, a verdict per target,
`verify_edits_if_present`), and **against** one clause of the plan's Phase 1 gate: a list derived
out of sample cannot be required to beat, on these PRs, briefs that were in part written from them.

## 1. The briefs ask the held-out questions, and the arms were sent them

Two readers, both models. The first labelled each counted obligation by whether some brief, as
sent, directs an arm to the specific check the maintainer asked for (`full`), only to a generic
version of it (`partial`), or not at all (`none`). The second was told to refute each label,
default to the more conservative one, and check every claim against the recorded prompt rather than
the current source. It made one downgrade and four arm corrections; the text uses its version.

| | full | partial | none |
|---|---|---|---|
| first reader | 18 | 3 | 2 |
| **second reader** | **17** | **4** | **2** |

- **none:** 695ae9fd (move declarations into `namespace Complex`) and 5ffba48e (a predicate used as a
  `Set` through defeq). No brief asks about namespace placement or definitional hygiene.
- **partial:** 6b02b611 (`round_eq'` → `round_eq_div`: `naming`'s working instruction is a *prefix*
  count, and "if … the name already follows the convention, submit nothing" — `round_eq'` already
  has `round_`); 7f098f6a and 8e276803 (dot notation, named by no brief); e8e02821 (which case split
  to make: golf covers the reuse, not the choice).
- **full**, with the corrections: 8d887ce4 is a *naming* ask, not a generality one — the
  maintainer's suggestion changes only the name, so gold's "typeclass-polymorphic" claim is
  mis-extracted; 073625ed is `proof_golf` alone (`proof_idiom` says "This is NOT golf"); 55f65304 is
  `family_design` (contested: that brief also says to ignore single-declaration defects), with
  `generality` only partial.

Judge-free, verified against `arm_pool.jsonl`: in `pr5_A_lead_heldout12_v2_rep1`, **107** arm
prompts carry `family_design`'s "every member fixed to `2` where `k` would do" and "A GENERATED
FORM WRITTEN BY HAND", and **147** carry `docs`' "auxiliary ordering" and "stops mid-thought";
`pr5_F_fanout_stage1_rep1` carries the same text in **11** and **19**. Each arm's recorded system
prompt is identical across the three v2 reps. The `correctness` prompt as sent says "`sorry`,
`admit`, or an axiom the repository does not accept" (a fixed-string search misses it only because
the recorded prompt breaks the line between "an" and "axiom"). All 1,206 arm rows of the first run
also carry the contract line "Submitting nothing is a correct and common outcome".

**Much of that text was written from these PRs.** Every sentence below predates the v2 runs (each
first commit is an ancestor of `a96b5afb`), and several were added *after* earlier runs on this
same PR set:

| brief sentence | obligation | closeness | first commit |
|---|---|---|---|
| `family_design`: "every member fixed to `2` where `k` would do" | 55f65304, 38e72250 | verbatim shape | `3828243`, 2026-09-07 |
| `family_design`: "Repeated `fun_*`/`comp_*` variants … produced by an attribute" | 57bcc9fd | verbatim shape | `3828243` |
| `family_design`: "If `foo_sup` and `foo_inf` both exist … through `OrderDual`" | bd8a8d8c, 7fef913e, e83e6544 | verbatim shape | `3828243` |
| `docs`: "When the index set is finite this reduces to the …" | c9739efc | verbatim shape | `3828243` |
| `docs`: "an auxiliary ordering … an 'Implementation details' note" | 0bb42bd2 | verbatim shape | `3828243` |
| `naming`: "21 use `toLinearMap_` and 7 use `coe_`" and the conclusion-subject rule | ce7b5d2e, 64e1164f | verbatim shape | `4d655e8`, 2026-09-13 |
| shared footer: "renamed and reproved through `OrderDual`" | e83e6544 | verbatim shape | `3828243` |
| `correctness`: "`sorry`, `admit`, or an axiom the repository does not accept" | 3dacf72e, f54010d8 | paraphrase | `70b1961`, 2026-08-25 |
| `proof_idiom`: "proving the dual statement from scratch instead of dualizing via `OrderDual`" | dual halves of the 33145 asks | paraphrase | `70b1961` |

`3828243` is a checkpoint commit whose own config comments report an earlier run on this PR set,
and `4d655e8`'s body cites "On 33337 … `toLinearMap_` 21 to 7". So seven of the seventeen `full`
labels — 38e72250, 55f65304, 57bcc9fd, 0bb42bd2, ce7b5d2e, 64e1164f, 8d887ce4 — rest only on text
written after looking at these asks. The rest have older, independent support: the axioms, the
Parseval duplicate, both golfs, line length, and the dual halves of the 33145 asks.

## 2. What the arm holding the question did

`report.buckets` cells for the three lead reps, filtered to the arms whose brief asks each
obligation (second reader's arms, `full` or `partial`). Twenty obligations are in the join — the
release's one non-hittable obligation, 0bb42bd2, is not — so 60 obligation-reps:

| the arm holding the question | obligation hit | obligation missed | total |
|---|---|---|---|
| **pruned** by the lead | 8 (by another arm) | **25** | **33** |
| **ran and was silent** | 3 | **15** | **18** |
| ran and filed | 7 | 2 | 9 |

Of the **42** misses, **25** are the right question never asked because its arm did not run, and
**15** are the right question asked and declined. Restricted to `full` labels: 24 pruned, 15
silent, 9 filed. On the four fanout PRs, where nothing is pruned, the arm filed at 2 of 10
obligations and was silent at 8; forced, 6 and 4.

What the silent arms wrote, in the cases that decide the reading:

- **An evidence tool's bar.** `naming` on 33421, silent in 4 of 5 runs: "Ran `naming_norm` on …
  `round_eq'` …; all use the dominant `round_` prefix". Forced, it filed.
- **The compile gate.** `family_design` under forcing on 33421's repeated `Tendsto (2 * ·)`: "The
  evaluation harness required a verification-backed candidate (with compiling
  declaration_name/new_declaration edit)". The same arm, with "every member fixed to `2` where `k`
  would do" in its prompt, ran at 55f65304 in all five runs and examined a different family.
- **A judgement that the code was fine.** `family_design` on 33117, silent in all three runs, having
  "Looked for missing counterparts … and for opportunities to derive the new `Meromorphic.*` lemmas
  systematically", never finding `@[to_fun]`.

The pruning is not incidental: in lead rep 1 the lead pruned 1,089 specialist rows ("not selected
by the lead" on 1,087) and ran 117 (78 mandatory, 39 chosen).

## 3. What the generalist answers

Every obligation the generalist hit in the lead reps — 64e1164f (naming), c9739efc (docstring
typo), 3dacf72e and f54010d8 (axioms), e83e6544 (naming), 57bcc9fd (`@[to_fun]`) — is one a
specialist brief also asks. **The generalist's lead is not breadth of questions.** It files where
the specialist holding the same question was not run or was run and stayed silent, and it works
under a different contract: `submission_verification_policy: none` against the specialists'
`verify_checkable_edits`, and "there is no quota" against "a wrong finding costs this review far
more than a silence does".

## What this changes in the plan

- **The Phase 1 gate's clause "strictly above the current briefs" is mis-specified.** The current
  briefs ask 17 (full) to 21 (with partial) of 23, partly because they were written from these asks;
  a list derived out of sample cannot be required to beat an in-sample one on the sample. The ≥ 80%
  clause survives as the check that a gold-independent list reaches the asks at all.
- **The losses the ceiling removes are the measured ones.** No lead removes the 25 pruned misses; a
  verdict per target and `verify_edits_if_present` address the named reasons for the 15 silent ones.
  That can be tested with the *current* briefs, which isolates the contract from the question list;
  the corpus-derived list is what would make a result on these burned PRs mean something outside
  them.

## Caveats

- One release, 23 counted obligations, the "burned" development set; counts of a few are
  descriptions, not rates.
- The brief-asks labels are model readings, not human ones. The second reader also found that every
  user prompt ends with a generic 8-item "maintainer ask checklist" (item 7: "scope: move, split,
  expose, privatize, or remove code that is misplaced"); counting it would move 695ae9fd to
  `partial`. It was not counted, because it is the same for every arm.
- "Ran and was silent" is about the arm whose brief asks the question; other arms at the same site
  are ignored here, as `report silences` already covers them.
- The generalist's contract differs in two ways at once (no compile gate, no licence for silence),
  and nothing here separates them.
