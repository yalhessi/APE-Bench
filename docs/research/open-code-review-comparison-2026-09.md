# open-code-review: what transfers to Mathlib PR review

*2026-09-15. Read at `alibaba/open-code-review@5589990` (Go, ~24k non-test lines in `internal/`),
plus the AACR-Bench evaluation README. Nothing was run; every OCR claim below is either read from
their source (file cited) or labelled as their own report.*

## What it is

A CLI that reviews a git diff. Alibaba's internal reviewer for two years before release; their
stated thesis is *deterministic engineering for the steps that must not go wrong, the agent only
for dynamic context retrieval and judgment*. The pipeline (`internal/agent/agent.go::Run`):

1. **Select** files with one pure function (`agent/selection.go::selectFiles`) that `--preview`
   and the real run both call, so the two cannot drift (their issue #782).
2. **Group** files with one LLM call over metadata only (path, status, +/-), answering with integer
   indices rather than paths to save output tokens; deterministic fallback to per-file groups;
   max 10 files, token-budget split (`agent/grouping.go`).
3. **Per group, in parallel:** an optional tool-less plan call (only above a churn threshold), then
   a tool-use loop whose only output channel is a `code_comment` tool; up to `--effort` rounds,
   rounds 2+ get the confirmed findings and *no plan* ("a plan acts as a coverage ceiling"),
   stopping early when a round adds nothing (`executeGroupSubtask`).
4. **Anchor** each comment deterministically from a verbatim `existing_code` quote: sliding-window
   match in its own file's hunks → unique match in another reviewed file re-files it (ambiguous
   declines) → only then an LLM re-location call (`diff/resolver.go`, `llmloop/loop.go:667`).
5. **Filter** with a separate LLM call that may remove only comments a diff line *provably*
   contradicts; never on value; protected subjects are vetoed (`prompts/review_filter_task_user.md`).

Rules are markdown checklists selected per path glob, first match wins, four override layers
(`config/rules/`). Every run writes a sealed coverage manifest with per-item failure classes and a
resume identity that refuses a resume whose input or rules changed (`session/manifest.go`,
`session/resume_identity.go`).

Their own benchmark claim: higher precision and F1 than Claude Code with the same model at ~1/9 the
tokens, **lower recall**, a trade-off they state as deliberate.

## Stages, side by side

`D` = deterministic code, `L` = model call.

| # | OCR | | Ours (v5) | |
|---|---|---|---|---|
| 0 | resolve refs, freeze commits; pure file selection shared with `--preview` | D | release: targets, entities, families, work units, sealed rendered prompts | D |
| 1 | per-path rule checklist | D | agenda: arm × unit proposals, eligibility, mandatory generalist floor | D |
| 2 | group files — skipped below 4 files; indices, not paths | L/D | lead routes specialists per PR (prune / add / budget) | L |
| 3 | plan — only above a churn threshold, no tools, plain text | L | — (the arm's concern prompt stands in) | |
| 4 | main loop per group: context tools, `code_comment` **incrementally**, `task_done` gated on a pass per file; grace round on budget stop | L | arm session: context tools + `lean_verify_edit`, one terminal `submit_candidates` validated and compile-checked **as a batch** | L+D |
| 5 | anchor each comment from its quote; cross-file re-file; LLM re-locate last | D→L | anchor declared by `change_ids`, refused if outside the unit | D |
| 6 | refutation-only filter, per round | L | lead synthesis (subtractive, currently off) → evidence gate → merge → digest | L/D |
| 7 | rounds 2+ with confirmed findings, no plan; stop when a round adds nothing | L | — (one pass per arm × unit) | |
| 8 | manifest, render | D | semantic judge v9, 3 samples, anchor pairing | L |

The shapes differ in one place that matters: OCR has no router and no specialists, but it has
two stages we lack — a separate filter with narrow authority, and a second pass over the same
code.

## Which stages paid off — only three have numbers

OCR's history (694 commits, read in full) carries a measurement for three components. Everything
else — grace round, plan skip, index-based grouping, cross-file re-filing, the round loop — ships
with a rationale and no number, and their headline benchmark is not decomposed by component.

1. **The filter was harmful, then fixed** (`c8b6a39`, #295). An A/B over 194 commit ranges with
   claude-opus-4-6: the filter removed 22 comments at 36% precision, 8 of them real defects. Two
   causes: `comment_ids` serialised before any reasoning field (replay showed the model writing
   "this is a protected subject" after the id it could not retract), and a prompt step inviting a
   value judgement. After the fix, replaying all 455 recorded filter calls: **precision 36% → 88%,
   real findings deleted 8 → 0**, +37% filter tokens. Their caveat: grounds derived from the same
   data, so a training-set result.
2. **Grouping cost recall, and they measured why** (`a662400`, #808). Grouping cut recall
   **20.0% → 12.7%** (F1 25.2 → 19.1). The 396 dropped comments hit gold at 27.8%, "only 14% better
   than a random cut of the same size" — indiscriminate thinning. Secondary group members starved:
   `.h` files lost 79% of their comments and went silent 68% of the time against ~30% for
   implementation files; tool calls per file fell 4.12 → 2.92. Four fixes, one of which gates
   `task_done` on a pass per file. No post-fix recall is recorded in the commit.
3. **Stringified tool arguments** (`41917e2`, #1153). 13 of 4,540 tool calls, 37 comments lost;
   the repair recovers 12 batches / 34 comments. Also: the parser's "invalid character" wording
   made the model regenerate 13/13, a schema-violation message only 4/13.

Item 2 is our batching result from the other side: consolidating units cut generalist candidates
per target 0.494 → 0.154 here, and their starved-member measurement is the same mechanism.

The method behind items 1 and 3 is the transferable part: **every LLM request is recorded with
its inputs, so one stage is re-evaluated by replaying its recorded inputs** rather than by a new
end-to-end run.

## Measured on our side before recommending

- **Batch refusal** (the case for incremental emission). On `v2_rep1-3`, 24/319, 28/314 and 27/322
  arm sessions (~8.6%) had a submission refused at least once (`is invalid` 31/37/36,
  verification 8/3/2). All later submitted legally; **5/3/2 sessions resubmitted fewer candidates,
  losing 7/8/5 candidates per rep**, two of them becoming abstentions. Real but small — not worth
  restructuring emission for.
- **Budget stops** (the case for a grace round). 0 of 1,574 arm jobs ended without a result.
- `rel050_rep1-3` could not be measured the same way: see the trajectory defect in
  `docs/todo/operational-floor.md` §5.

## AACR-Bench scores the way we do; the difference is its gold

File → diff side → line overlap within k=1 → LLM semantic judge. That is our "same place AND same
concern". The difference is gold: *GitHub human comments → LLM enhancement → three rounds of
cross-annotation by 80+ engineers*, which yields 1,505 comments labelled correct **and 640 labelled
incorrect**. Because model-found issues were adjudicated into gold, they count unmatched predictions
against precision. Caveat for reading their numbers: gold enhanced by an LLM plausibly favours
reviewers that resemble the enhancer.

## Already built here — do not re-adopt

| OCR mechanism | Ours |
|---|---|
| Resume refused when input/rules change (`ValidateResume`) | sealed `run_plan.json`, semantic-field refusal (`review/runner.py:864-903`) |
| Sealed coverage denominator, per-item failure class | `coverage_gaps`, `TaskOutcome`, `reconcile` |
| Aggregate token budget look-ahead | `ExecutionLimits`, caps on billed cost |
| Semantic file grouping | work-unit packing, 203 → 92 units (`batching-and-prompt-repair-2026-09.md`) |
| Comments confined to the reviewed group; context tools for background only | `change_ids ⊆ unit` in `submit_candidates` |
| Session JSONL + web viewer | `cli trajectory`, `report overlay` |

## What transfers, ranked

Each item names the OCR mechanism and **our** measurement that makes it worth doing; OCR's success
with it is not evidence it works here.

### 0. Replay a recorded decision turn instead of re-running the job

*OCR:* the filter fix and the argument-repair wording were both settled by replaying recorded
requests (455 filter calls; 13 failed batches), not by new end-to-end runs.
*Ours:* the decision, not the investigation, is where findings are withheld — arms that abstain
investigate as much as arms that file (median 6.0 vs 7.0 tool calls, n=95/23), and forcing the
decision took issue recall 0.20 → 0.50 on identical PRs. Yet every change to the decision stage
(abstention wording, field order, the bar) is tested with a full rep: $7.26 billed, ~38 minutes,
investigation variance included, read through a judge that disagrees with itself on ~11% of pairs.
*Change:* take recorded arm sessions up to their `submit_candidates` call, swap the tool schema or
the closing instruction, and resample only that turn N times. The cost is one cached-prefix turn
per session, and the investigation is held fixed, so the difference is the change alone. Items 3
and 5 below, and the abstention bar generally, become cheap to test this way. APE already saves
completed turns for resume (`scaffolds/ape_agent/conversation.py:433`) — start there.
*Risk:* a replayed decision sees the transcript of an investigation shaped by the old schema; it
tests the decision, not a changed investigation.

### 1. Adjudicate off-gold findings once, and keep the labels

*OCR/AACR:* human correct/incorrect labels on model-found comments, folded into gold; OCR's
`session/compare.go::findingKey` (path | category | whitespace-normalised quoted code) gives a
finding an identity that survives reruns. (OCR's viewer "mark fixed/ignored" is `localStorage`
only — that part is not worth copying.)
*Ours:* ~90% of findings are not maintainer obligations and nothing adjudicates them; the batching
comparison moved `gold_alignment_rate` 0.069–0.091 → 0.181–0.202 and could not say whether output
got better. Gold already has a `curator_confirmed` status.
*Change:* key findings by `(primary_change_id, issue_kind, canonical_action)`
(`review/merge.py:53` exists), pool across runs, label each key once (correct ask / wrong /
valid-but-not-an-ask), and carry labels to every run that reproduces the key. Cost amortises
across reps because most keys recur. This is not the deferred recruited-annotator study.

### 2. Per-target dispositions in the submission

*OCR:* the main prompt requires "every `<file>` in `<review_files>` its own pass … a file being
the smaller or secondary member is not a reason to skip it"; delegate mode makes coverage
mandatory: every file ends `reviewed` or `skipped` with a concrete reason. Added after grouping
starved secondary members (`.h` files silent 68% of the time; see "Which stages paid off" §2).
*Ours:* consolidating units cut generalist candidates per target 0.494 → 0.154; 33321's docstring
typo was caught with a dedicated job and missed as one of ten-plus targets.
*Change:* `submit_candidates` requires each `change_id` in the unit to be covered by a candidate or
a per-target abstention label, refused once like a mute abstention. Makes per-target attention
measurable without gold. A third untried design beside "cap targets per unit" and "tell the
generalist its target count".
*Risk:* must stay a label, not a demand for findings — `forbid_abstention` took control emission
1 → 36.

### 3. Reason fields before verdict fields in tool schemas

*OCR:* `agent.go:1550-1557` — the filter tool's `analysis` must serialise before `comment_ids`;
"with the order reversed it picks ids first and cannot retract them", found by replaying recorded
sessions.
*Ours:* `abstention_reason` precedes `abstention_detail`; `concern_family` and `severity` precede
`claim`; `model_confidence` is last and came back null on every forced finding. Under
`forbid_abstention`, `already_correct` labelled suppressed candidates that align with gold at the
same rate as kept ones (0.038 vs 0.041).
*Change:* reorder so detail/claim precede the label, one arm on `cli bench`, three reps.
*Risk:* reasoning models deliberate before the call, so order may not matter for gpt-5.x; the
change alters what a run does, so it goes in the run name.

### 4. Verbatim-quote anchoring with a deterministic re-filing cascade

*OCR:* `diff/resolver.go::RelocateAcrossFiles` — a comment filed against one file whose quoted
code lives in another is re-filed on a unique hit, declined on zero or several, before any LLM.
*Ours:* the judge has paired only at `anchor`, 705 of 705 pairs; a correct ask anchored one change
away is never shown to it (PR 33362's namespace move). 5 of 24 anchored obligations span units.
*Change:* optional `quoted_code` on a candidate, resolved at ingestion against every PR change
fragment, recording `resolved_change_id` when unique. Gold-free, and a narrower alternative to
widening the judge to `relation` pairing.
*Risk:* changes what the judge sees, not reviewer quality; it cannot be claimed to fix 33362
until tried.

### 5. A refutation-only filter, after item 1

*OCR:* the filter removes only what a visible line contradicts, never judges value, vetoes
high-cost subjects, and tells the model the costs are asymmetric.
*Ours:* the arms' own bar is a volume filter, not a quality filter (dead-ends, "Specialists as the
coverage floor"). This is not the dead selection line — that predicted *which valid change a
maintainer raises*; this predicts *falsity*, which in Lean is often tool-checkable (a lemma claimed
missing exists; a claimed compile failure does not reproduce).
*Blocked on 1:* without adjudicated off-gold findings only control-PR emission can score it.

### Conveniences

- **`plan` writes the dispatch pool to a scratch path.** OCR's preview and run consume one answer.
  Our `plan` builds the agenda and then writes nothing, so it cannot show which tools an arm will
  hold — the gap that cost the `naming_norm` run ($1.11, 33337 rep14; `.claude/rules/mathlib-review.md`).
- **A finding-level diff between runs:** new / persisting / resolved / not-reviewed, with
  not-reviewed taken from coverage so an unexamined finding is never counted as resolved
  (`session/compare.go`). `report conditions` diffs gold obligations only; this covers the other
  90% and reuses item 1's key.

## Checked and not worth adopting now

- **Grace round** (one submit-only turn when the tool budget is exhausted). All 1,574 arm and 72
  lead jobs across the six held-out runs (`v2_rep1-3`, `rel050_rep1-3`) completed with a result.
- **Incremental emission instead of one validated batch.** Refusal cost 7/8/5 candidates per rep
  on `v2_rep1-3` (see "Measured on our side").
- **More review rounds with confirmed findings.** `forbid_abstention` already bought volume at an
  unchanged alignment rate; revisit once item 1 can say whether the extra findings are useful.
- **Memory compression.** Arms run a median of 6–7 tool calls before submitting.
- **Deterministic repair of stringified tool arguments** (`tool/comment_args_repair.go`). No
  measurement of how often our submissions are refused for schema shape; count before building.
- **Per-language rule docs by path glob.** Our unit of instruction is the concern arm, and arm
  prompts are sealed into prompt hashes; adding an arm is already two edits.
- **Effort presets, OpenTelemetry, IDE/CI integrations.** `extends:` + `--set` cover the first;
  the rest serve a product, not an experiment.

## One process note

Their retrospective records an AI-written change to a search tool that passed unit tests and broke
users on launch; the rule they adopted is that any core-path change runs the full 200-PR eval
before release. Our analogue already exists as practice — a confirming rep before believing a
contract change — and the "closed vocabulary silently filters a correct registration" entry in
`.claude/rules/mathlib-review.md` (assert the capability reaches the task before paying for the run)
is the cheaper half of the same lesson.
