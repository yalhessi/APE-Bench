# Review as a demonstrated change

**Status** — open; written 2026-10-18 for a fresh session, from the 2026-10-16..18 thread (the 5% probes, their
four adversarial reviews, and a manual reading of the free reviewer's transcripts). The first deliverable of
that session is the plan file under `docs/plans/`, after an adversarial review of the design itself; nothing
is built or run yet.
**Cost** — no spend for the premise check and the free reviewer's reps (DeepSeek-V4.1-Flash on `first`, about
35 min a rep, $0); sealing and matching a rep costs subscription tokens on the primary account (about 0.5-1M
a seal in the filing-decision write-up), which is the user's call.

## The heart of the problem, as measured

The reviewer does not fail at finding places or at knowing conventions. It fails at the decision it makes at
the place, and that decision carries no information about what maintainers ask.

- At 65 of 66 missed asks the free reviewer read the place; at about half it named the maintainer's concern
  and dropped it, on worth (27 rows), a plurality in the corpus (22), the file's siblings (13), a check not run
  or run on the wrong candidate (26), or nothing stated (13) (`docs/questions.md`, "On what grounds does the
  free reviewer drop a concern"; `probes/ask-reading-2026-10-12`). Of the 66, 35 lacked no knowledge, 14 lacked
  only the belief that maintainers enforce the convention here, about 14 lacked a fact.
- Every reviewer measured, on every model and harness, hits about one ask per ten findings; recall follows how
  many findings it files; selection signals sit at chance (`docs/questions.md`, "Does any reviewer aim better";
  `docs/dead-ends.md`, selection). The reviewer's "would a maintainer care" is noise.
- Maintainers decide the other way round. They ask when they have the fix in hand: 39 of the 93 evaluation
  asks and 856 of 1,917 census asks are a suggestion block; 43 of the 56 finishing-tactic asks. Their stated
  grounds are a principle or a fact, rarely taste (`probes/stated-grounds-2026-10-16`). Fixes happen only when
  asked, and asked fixes get made (8 of 9, 5 of 5, 12 of 15 across three probes). Their silence is attention
  and economy (`probes/stage-h-departures-2026-10-16`, `probes/attention-practice-2026-10-17`), and the economy
  is resolved by asking only when the fix costs the author one click.
- Construction with verification finds the change where judgement says "conforms": stage H's checkers, told
  to build up to six candidates and compile each, found a compiling shorter form at 12 open places in 2-8 tool
  calls each, where note-free readers had called most of them conforming; the closer battery produced 8 of 15
  missed asks verbatim (`probes/closer-battery-2026-09-26`).
- By hand, 2026-10-18 (compile probes in scratch, 5-10 s each): at PR 33285 the reviewer wrote "could be golfed
  further to `simpa only ... using ...`? Hmm. Not a finding"; its candidate fails (the hypothesis was never
  introduced), the maintainer's one-line term compiles. At PR 32875 the maintainer's `simpa [this] using ...`
  compiles; the reviewer's "`rw [this]` would be more idiomatic" compiles but is no golf, and its other
  compression fails. No solo session compiled anything at either place, though each session runs
  `lean_verify_edit` about six times elsewhere (454 calls in 78 sessions). At the `grind` asks (PR 32875) the
  reviewer found the Zulip policy thread and still filed the opposite: the signal was in hand, the direction
  misread.

## The design, in five lines

1. The unit of review is a **demonstrated change**: a concrete edit the reviewer has constructed and verified,
   with the principle it serves (shorter; consistent with the scope's form; more general; derived from an
   existing API).
2. At a place the reviewer's question is never "would a maintainer want this". It is "is there a better form
   by this scope's current practice, and can I produce it and verify it".
3. Knowledge enters as the **target** of construction: the census entry's form, the file's or area's own
   practice, what was recently adopted. Convention texts are calibrated against maintainers' merged code before
   they become targets (the 5% thread's one design output).
4. Verification decides filing: a change that verifies and improves is filed as the suggestion the maintainer
   would have written; a concern whose change cannot be built after a bounded number of tries is dropped with
   the failures as its ground. Worth is not a legal ground anywhere.
5. Economy is left to the maintainer, who receives a one-click suggestion, which is how maintainers ask.

Built as a harness contract, not prose: extend `filing_contract.py` (its `Cell`, `Evidence`, `EvidenceEdit`
types exist) so that a candidate is filed only with a verified construction attached, `conforms` keeps design
G's evidence rule, and a named concern without a verified construction is recorded as unbuilt with its failed
attempts (stored per sample, never filed). Prose did not move the free model (the precedence paragraph, the
filing contract's authority order); a contract did.

## Why it is untried

| design on record | worth decision | change built and verified | result |
|---|---|---|---|
| solo; the conventions section; the exact rule at the place (stage G) | kept | no | the reviewer verified a passing check and overrode 8 of 10 ("Mathlib does not require these") |
| forced filing, design G (`dead-ends.md`) | removed | no | partials: 14 of 37, 4.9 findings a control PR |
| the per-place engine (`probes/conventions-places-2026-10-09`) | removed | no | 0.55 reach at 68 filings a PR |
| the closer battery, mechanical sweeps (`review-mechanical-sweeps.md`) | no reviewer | yes | 8 of 15 verbatim on targeted edits; never run blind |
| stage H's checkers | no reviewer | yes, up to six tries | the shorter form at 12 places readers called conforming |

The empty cell: the reviewer chooses the places and names the concern (it does this well), the harness
requires the change built and verified, and filing follows from verification, not from a worth guess. Design
G's own reopening condition is "a design changes what the reviewer knows at the partial-only places"; a
compiled candidate is exactly that.

## Ceiling, stated first

Of the 93 evaluation asks (`probes/ask-reading-2026-10-12/asks_all.tsv`), 66 are a code edit a reviewer could
construct and verify (families proof 20, naming 20, interface 8, formatting 6, derive 6, registration 4,
redundancy 2). Solo reaches 26 of them; the union of all seven conditions on disk reaches 52; 31 carry a
suggestion block. One free design reaching what now takes the union would move the wall from 37 to the low
fifties. The other 27 asks (documentation, PR level, statement and API design, generality) are out of its
reach and of everything tried: union 17, solo 11. Gold questions whose answer is "no" (three) will not be
credited by a verifying reviewer, and the matcher has no question form (filing-decision write-up, §8).

## What would falsify it, and the measurement of each

1. **The reviewer cannot build what it names.** Premise check, no model, a day: for the 31 asks some solo
   session named and dropped (8 proof golfs, 9 names, 6 interface, 8 other), construct the maintainer's fix and
   the reviewer's own quoted candidate in the reviewed workspace (compile; naming norm and precedent search).
   If the maintainer's fix verifies at two thirds or more and the reviewer's own at a third or less, the
   missing step is construction, not the check, and the contract must allow iteration (up to six candidates)
   and the battery's tools (`try?`, `exact?`, the closer list, the naming norm). Two of the 31 are done (above).
2. **Volume: built-and-verified changes at unasked places run several a PR and are unwanted.** Report findings
   a PR on ask PRs and on the control PRs, every one carrying its change. Adjudicate the control-PR findings
   two ways: by later merged code (did the suggested form appear at that place or its file within the clone's
   history), and by the user on a sample of 20 one-click suggestions. If more than half are judged unwanted,
   economy is the filter maintainers apply and the design floods; it is then rewritten with an explicit
   economy rule derived from the adjudicated sample, which is the first corpus for the negative half.
3. **Reach does not move** because the asks the reviewer drops are not the ones it can build. The run's own
   per-ask table says which.

## What would close it

The premise check (falsifier 1) first. Then three reps of the free reviewer on the 26 ask-reading PRs with
the contract, against solo's three reps on disk, one seal, the table's two blind matchers (the
`match`/`seal` pipeline the filing-contract probe used):
- **passes** if the per-rep mean on the 66 code-edit asks is at least 6 above solo's per-rep mean and the
  three-rep union reaches 35 or more of the 66 (half the gap from solo's 26 to the all-conditions union of 52);
- **dead end** if the per-rep gain is under 2 or the union under 30, written beside design G;
- between, the per-ask table decides what to change, and the volume reading (falsifier 2) is reported either
  way. Then the fresh 40-PR validation set (`configs/pr_review_v5_val_fresh40_local_ds41_contract2.yaml`) as
  the deciding set, which no design has touched.

## Start here

- read: this file; `docs/dead-ends.md` (design G, its untried list and reopening condition; selection; the
  per-place engine); `docs/research/filing-decision-design-2026-10-12.md` §10-12 (the surviving contract, the
  question form, the user's open decisions); `src/ape/tasks/lean_tasks/formal_math/review/filing_contract.py`
  and `structured.py` (the contract mechanism and the hand-back); `src/mathlib_review/review/toolbox.py` (the
  compile tool outside a run); `results/pr_review_v5/probes/ask-reading-2026-10-12/PROTOCOL.md`, `asks_all.tsv`
  and `readings/*.jsonl` (`behaviour == "K"` rows quote each dropped candidate; `grep_session.py` reads a
  transcript at a place); `results/pr_review_v5/probes/closer-battery-2026-09-26/battery.py` (one-edit compiles
  with `lake env lean`, `-Dexperimental.module=true` on Lean 4.26+ workspaces);
  `results/pr_review_v5/probes/stage-h-departures-2026-10-16/checker_prompt.md` (a construction brief that
  worked: up to six candidates, one compile at a time); `docs/todo/review-mechanical-sweeps.md` (the tools and
  the volume bound); `docs/todo/adjudication-rubric.md` (the adjudication socket for falsifier 2);
  `.claude/rules/mathlib-review.md` (the D1 subclass pattern, tool-path rules).
- run: `ape/bin/python -m src.mathlib_review.review.cli plan --config configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml --run-name <name>`
  is the free reviewer's preflight and spends nothing; the DeepSeek server is `sbatch
  /research/projects/proofedit/ya475/localmodel/serve_ds41.sbatch` then its two probes (`CLAUDE.md`, the
  self-hosted model). The two compile probes of 2026-10-18 are the pattern for falsifier 1 (a scratch copy of
  the reviewed file compiled from the workspace directory; never write into the shared workspace).
- bounded by: design G (forced filing without construction); the precedence paragraph and stage G (prose and a
  passing check do not override the reviewer's worth decision); the per-place engine (judgement at every place
  without verification); mechanical sweeps (the reviewer-free form, bounded to potential only); selection is
  refused, and dropping an unbuilt concern is generator-side; `recall_ceiling_before_spend` (the ceiling above
  is on the full labelled set, not on the cases that suggested the design); the matcher's missing question
  form.

**Evidence** — `probes/ask-reading-2026-10-12/asks_all.tsv`, `readings/`; `docs/questions.md` lines on what the
free reviewer does at the place, on what grounds it drops, whether any reviewer aims better, and the per-place
engine; stage H `checks/*.jsonl` (`calls`, `compiled_candidates`); `probes/closer-battery-2026-09-26/README.md`;
the compile probes of 2026-10-18 (scratch, recorded above); the four reviews under
`docs/plans/2026-10-16-principles-scope-currency/`.

**Risk** — the reviewer's candidates may fail at most places (PR 33285), so the step degenerates into the
battery with its volume; the free model may not follow an iteration contract (contracts moved it where prose
did not, but a six-try loop is more than a hand-back); the naming half needs a norm the record says is not
readable from the corpus alone; the control-PR bar of 2.0 will likely be exceeded by design, and the project has
no adjudication of unasked findings yet, so falsifier 2 is the first such reading and may be slow.
