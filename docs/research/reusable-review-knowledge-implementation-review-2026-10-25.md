# Reusable review knowledge: implementation readiness review

Reviewed 2026-10-25 against `reusable-review-knowledge@923e14c9` in
`.claude/worktrees/reusable-review-knowledge`, and the revised plan at `develop@779f9330`.
This review ran local checks only. It changed no implementation, packet, bank or evaluation input,
and launched no model-backed session.

**Verdict:** the foundation and recipe are close to ready. Fix the shell instructions and precedent
trace before completing the two transport smokes. Acquisition can then proceed while the evaluation
fixes below are implemented. The 54-review batch still depends on acquisition, twelve source checks,
human inspection and any bounded repair, frozen banks, and the remaining preflight. Those are planned
stages, not evidence that the implementation needs another redesign.

## Findings

Paths below are relative to the reviewed worktree. All code findings are P2: concrete corrections
within the existing design. R5 also resolves an ambiguity in my plan; it should not be treated as an
unambiguous requirement the implementation agent ignored.

### R1. The documented direct commands do not run in standard zsh

`results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/PROTOCOL.md:175–188`
explicitly says zsh, defines the scalar `R="ape/bin/python -m src.mathlib_review.review.cli"`, and
invokes `$R session`, `$R report`, `$R plan`, etc. Standard zsh does not split an unquoted scalar into
command words. A local `zsh -fc 'R="printf ok"; $R'` reproduces `command not found: printf ok`.
The first smoke command consequently fails before invoking the CLI. Expansion inside a quoted
`/bin/bash -c` string is a different case; it does not fix the direct commands.

Use a shell function for direct invocations, an explicitly expanded zsh command array, or instructions
that consistently use bash. Check both direct calls and detached command construction with a stub
executable, without loading credentials or calling a model. This is a launch-instruction fix, not a
request for another launcher.

### R2. Floating-point accumulation can change the qualification result on exact ties

`.../eval/analyze.py:83–103` adds each `n_X(g)/3` as a float, then uses strict `>` and `<=` comparisons
for useful and wrong counts and useful share. Equal numbers of delivered concerns can have unequal
floating-point sums depending on how they are distributed across concerns.

Reproduced through the actual `arm_sums` function:

| Arm | Wrong concern deliveries | Computed expected wrong count |
|---|---|---:|
| B | Six concerns, one delivery each | 1.9999999999999998 |
| C | Three concerns, two deliveries each | 2.0 |

These are six wrong deliveries each, but C fails the "no higher" comparison against B. The same
problem can create a strict useful-count gain when the exact totals tie, or disturb useful-share
comparisons. This affects the investment decision, not merely printed formatting.

Accumulate integer delivery counts first, compare those counts and integer cross-products for share,
and divide only for presentation. Add regressions for differently distributed ties and for primary
gains offset by losses so equal net usefulness never passes the strict improvement clause.

### R3. Precedent search applies the exclusion but does not record it

`src/ape/tasks/lean_tasks/formal_math/review/context_tools.py:370–380` omits
`also_excluded_prs` from the successful precedent trace; the refusal trace omits it too. Zulip uses
the existing `_also_excluded(scope)` helper. Meanwhile `.../eval/export.py:220–222` treats any call
without the six-target field as a call made without the exclusion, and the review-smoke checkpoint
requires the field.

A local stub of `PrecedentIndex.shared()` confirmed that all six exclusions reach `index.search`,
while the resulting trace contains no `also_excluded_prs`. The export audit therefore reports a
false missing-exclusion failure for every precedent call. This is not evidence that the store leaks
target outcomes; the filtering path itself passes the exclusion.

Use the existing helper in both precedent trace paths, and cover successful/empty and refused
calls. The live smoke can then check what the protocol actually promises before paid review runs.

### R4. Repair/recheck coverage and costs disappear from part of the export

`.../eval/export.py:232–242` gathers producers from the final full-bank spec and adds only the
original `task-rrk_check_v1`. `:277–283` uses the same restricted producer set for usage. The supported
repair path can therefore use repaired entries and replacement checks without the exporter requiring
the recheck producer to be complete or including its tokens. If all entries are repaired, the original
acquisition producer also disappears from resource accounting because no final bank section refers
to it. Work already spent is still part of the experiment's cost.

The protocol separately asks the operator to put rechecks in the feedback command's `--after` list;
that is useful, but does not make the export's coverage and usage claims true. Record the actual
acquisition, initial-check, repair and recheck plan/producer references once and use that list for
both coverage and accounting. Reuse `session_coverage` and `scheduled_task_tokens`; no new execution
system is needed. Test one repaired entry with a missing replacement check and ensure export refuses,
then confirm both original and replacement work remain in the usage record.

If no repair occurs this defect does not affect that campaign, but the advertised repair path should
be fixed before it is needed. Smokes and matching can be added to total cost when their outcomes are
available; this export necessarily precedes matching.

### R5. Specify whether C may advance after failing the ordinary-review comparison

`.../eval/analyze.py:122–123` selects C when B qualifies against A and C qualifies against B, even
when C does not qualify against A. The stable-primary-gain rule is not transitive. The actual
`qualifies` and `decide` functions reproduce this case with three useful primary concerns:

| Concern | n_A | n_B | n_C |
|---|---:|---:|---:|
| First family | 1 | 2 | 3 |
| Second family | 0 | 2 | 0 |
| Third family | 2 | 0 | 2 |

B has two stable primary gains over A, C has two over B, but C has only one over A. All findings are
useful, totals increase, and the wrong/share/contrary guards do not prevent this. The reader prints
"C supersedes B" despite the failed C–A qualification.

My plan's prose did not explicitly settle this combination, while its full-bank decision-table row
requires qualification against both A and B. My recommendation is to require C–A as well as C–B to
prefer C, and otherwise retain qualifying B. State that explicitly in the plan and protocol and test
this concrete combination before results exist. An intentional different policy is possible, but
should be chosen now rather than inferred from a favourable result later.

## What passed and what has not been demonstrated

- **209 targeted tests passed** in 18.80 seconds: the study's tests, retrieval gate, both stores,
  context operations, solo/config bindings, frame subset support and review-run coverage checks.
  This was not a rerun of the complete branch suite.
- Both release groups' ordinary-review dry plans completed. Each resolves its three target cutoffs,
  all three reviewed workspaces, available toolchains, and the 4M-per-review / 12M-per-run limits.
  My shell intentionally did not load credentials; the dry plans reported the expected login warning.
- The acquisition plan loads with six packets and the recipe has twelve check assignments. Resolving
  all six arm configs reproduces `built.json`; only `context_file` differs within each release group.
- The saved preflight has a compiled outcome and zero errors for each target's changed-file check.
  I inspected those records; I did not repeat the Lean compiles.
- A local audit found no post-K `updated_at` among 180 directly cited PR comment/review records.
  This is a specific date check, not a claim that every source inference has been independently
  adjudicated or every indirect contamination route ruled out.
- **The matching allocation is consistent as written:** the command defaults to one batch containing
  all six PRs and all reviewer labels, with two replicas at 3M each. It is not one Task per review.
  Changing the batch size would require rechecking that allocation.

The fixes above were identified with additional local counterexamples, despite the targeted tests
passing. No acquisition output, source-check response, frozen bank, final review, matcher result or
human usefulness label yet exists for this experiment, according to the reviewed artifacts.

## Research limits that do not block the developmental run

The selection report discloses three earlier model-assisted source-search sessions and target-steered
search prompts. This is stronger selection than choosing concern topics alone. A positive result
could justify a fresh test with target-independent source/target selection; it would not itself
establish deployable transfer. The implementation record's broad "nothing model-backed ran" should
be read narrowly as no experimental acquisition/check/review/matching run; `SELECTION.md` records
the preparatory search sessions and their approximate usage.

The opportunity targets exercise E1, E3 and E5. The contrary targets exercise E2, E4 and E5; E6 has no
whole-PR target. Thus only E5 has both an opportunity and contrary whole-PR target under the same
entry. Every entry has reserved source checks, and the whole bank is shared by every review, but
results should not claim whole-review positive/negative transfer for all six entries. This disclosed
scope does not require restarting selection for the present developmental question.

The revised expected usage is 73–136M processed tokens without repairs, higher than the plan's
provisional range. The record explains it from the chosen targets' prior usage. This is an operating
choice for the user, not a software defect or a reason to change models mid-comparison.

## Order of work

1. Correct R1 and R3, then run the existing acquisition and review transport smokes. A smoke validates
   transport, containment, finalization and exclusions, not review quality.
2. Run acquisition and source checks. Inspect claims against their cited packet inputs and each
   reserved case, preserve uncertainty, and use the documented bounded repair/replacement process.
   R2, R4 and R5 can be resolved alongside this work.
3. Freeze the accepted compact/full banks and lineage; complete the arm preflight before launching
   the 54 final reviews. No architectural expansion is needed.
4. Once all reviews are complete, export finalized findings, run canonical matching, label the full
   usefulness panel, group materially equivalent concerns and read the corrected decision analysis.
   The inspection clause remains a human decision after those results, not an automatic promotion.

Foundation integration is already present on the reviewed topic branch. Merging into develop is not
required to run there, and this review does not merge it or remove the main checkout's untracked files.
