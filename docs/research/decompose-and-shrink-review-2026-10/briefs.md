# The four briefs, as handed over (2026-10-09, about 05:45 EDT)

Four `general-purpose` subagents of the orchestrating session (Opus 5.5, the primary subscription),
launched together in the background, read-only, each with its own lens; none saw another's brief or
report. Each was pointed at `draft.md` (this folder; it was at
`<SP>/round2/draft.md`, where `<SP>` is the session scratchpad
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/592272bf-2a21-4fd7-84f0-c3c437872216/scratchpad`).
`R` is the main checkout `/research/projects/proofedit/ya475/APE-Bench`; `W` is the worktree
`R/.claude/worktrees/conventions-dossiers`. The text below is each prompt with those two
substitutions only.

---

## R1 — Q1, decomposition and coverage

You are one of four independent reviewers in an adversarial round on a research idea in the APE-Bench repository (Mathlib PR review research). Your lens: **Q1, DECOMPOSITION AND COVERAGE — how should a whole PR be divided into parts so that each part needs only a small subset of conventions, and can such a division cover all the review work in a PR?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round2/R1/.
- Token economy: stay under ~120k tokens. Use grep, `sed -n` ranges and small Python counts; never print large JSON or run directories whole.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
- The draft under review, with the user's words and the facts in hand: `<SP>/round2/draft.md`.

## The record (R = /research/projects/proofedit/ya475/APE-Bench)
- `R/docs/plans/2026-09-23-work-enumeration.md` (the question-per-target design; 91% located / 57% asked; the corrections and decisions at the end).
- `R/docs/todo/batching-work-units.md` (how work units are built from change targets; 3 of 42 obligations span units; coordinated emission), `R/docs/plans/2026-09-22-coordinated-emission.md`.
- `R/docs/research/review-work-structure-2026-09.md` (a structure for review work: §1-§3, §7.6 the division, §7.8 the relabel).
- `R/docs/todo/pipeline-overfit-review.md` and `R/docs/research/pipeline-overfit-2026-09*.md` if present (PR-grain asks 14% of validation; AI-generated PRs' PR-level asks 16%).
- Code, to see what a unit is today: `R/src/mathlib_review/` — grep for `build_work_units`, `change_id`, `change target`, `agenda` (read signatures and docstrings only).
- The census (`R/results/pr_review_v5/adjudications/conventions-census-v1/`): `results.md`; `reader_A/codebook.json` (438 entries with `family`? check the fields); `reader_A/labels_b*.jsonl` (per ask: cid, principle_id, family). Each census ask has a `path` and `line` (comment place) in `R/results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl` (join on cid); `kind` tells review_comment (on a line) vs issue_comment (on the PR).
- `R/docs/dead-ends.md` entries: "Facet-keyed review join" (reviewers ask about a pattern in the code, not the declaration's shape), "The family division of the specialist arms", "Specialists as the coverage floor", "Oracle-site instantiate pipeline".

## Your task
- What unit(s) of decomposition does the record support: hunk, declaration, declaration family, file, proof, docstring, imports, PR? For each, what share of maintainer asks falls wholly inside one unit, and which asks cannot be seen from inside any unit (PR-level, cross-file, sibling and analogue comparisons, "move this to another file", "split the PR", consistency with the library)? Use the census where you can: e.g. the share of asks that are issue comments (PR-level), the families that are inherently cross-unit (PR level F12, generality F7, naming against siblings), and any counts the record already has.
- Coverage: how would we know a decomposition covers *all* the work, without gold? (The record's `coverage_gaps` metric, gold-independence tests, the work-enumeration plan's own ideas.)
- What breaks when the review is split: context a part needs from elsewhere (the file, siblings, the library), coordinated asks across parts, double filing, and how the record handled each.
- Is decomposing by *convention group* (family, rationale) a different thing from decomposing by *code part*, and which does the shrink idea actually need?

## Deliver, as your final message (≤ 1,200 words; it goes to the orchestrating session, not the user)
1. Verdict in your lens: what decomposition the record supports, in one paragraph.
2. The strongest objections to the draft's step 1, ranked, each with evidence (file:line or figure) and what would refute it.
3. Your best answer to Q1: the decomposition you would propose, its expected coverage with numbers where the record allows, and what it leaves out.
4. What you would reject outright, with evidence.
5. The cheapest measurement that would settle Q1 before any review run, with a pre-stated threshold and cost (prefer measurements on data already on disk).
Report at the altitude the evidence supports; separate "tried and failed" from "cannot work"; mark read versus inferred. The project's goal is issue recall (share of maintainers' round-1 asks reached).

---

## R2 — Q2, subset selection from a partial PR

You are one of four independent reviewers in an adversarial round on a research idea in the APE-Bench repository (Mathlib PR review research). Your lens: **Q2, SUBSET SELECTION FROM A PARTIAL PR — given one part of a PR (a hunk, a declaration, a proof...), can we choose a small subset of the ~400 census conventions (5-10) that contains the convention a maintainer actually asked for there, soundly and cheaply?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round2/R2/.
- Token economy: stay under ~120k tokens. Use grep, `sed -n` ranges and small Python counts; never print large JSON whole.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
- The draft under review, with the user's words and the facts in hand: `<SP>/round2/draft.md`.

## The record (R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-dossiers)
- Stage README: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` — stage F 392-542 (the blind selector: `selector_rubric.md`, `selectors/`, `briefs_applicable.json`, retrieval 22/33 at 25, ranks of the right entry), stage G 543-732 (rule writers wrote `trigger`, `applies_to`, `not_when`, `check_kind` for 52 entries: `rules.json`, `rule_writer_rubric.md`; the pinpointer, `pinpoints/`), stage H 733-873 (maintainers raise 1 in 20 to 1 in 400 of flagged places).
- The census: `R/results/pr_review_v5/adjudications/conventions-census-v1/` — `results.md`, `reader_A/codebook.json` (fields: principle, rationale, form...), `reader_A/labels_*.jsonl`, `crossmap.json` (reader agreement 0.809), `reader_rubric_census_v1.md` (the grain rule).
- `R/docs/dead-ends.md`: "Convention detectors as a recall lever", "Selection from artifact-only signals", "Precedent priming, Mode A", "Facet-keyed review join", "Surface proxies for convention discovery", "Linter-as-convention-oracle".
- `R/docs/PROJECT-STATUS.md` §6 (a dense precedent index, hit@5 49% on its own bench), `R/src/mathlib_review/retrieval/precedent_index.py` (docstring), `R/src/datasets/pull_requests/projections/ledger.py` (A→B suggestion pairs).
- The ladder (one turn at the ask's place, DeepSeek): `W/results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md` and its running note at the end.
- `R/docs/todo/conventions-nature.md` (scope by area and era; the 30458 `variable` case where library scope won over file scope; the 32875 `grind` maturity case).

## Your task
- What can a part's syntax (what changed, the Lean constructs, the file area) determine about which conventions apply? Estimate how far syntax alone could shrink 400 → N with what loss: e.g. the families and forms in the census, stage G's triggers (how many triggers are syntactic?), the census's rule/standard split. Where you can compute an estimate from data on disk, do it (e.g., for the 39 probe asks or census asks, what part kind the commented hunk is, and how many census entries share that kind).
- Which conventions cannot be selected from a partial PR at all, because their situation depends on information outside the part: siblings and analogues in the library, the file's own regularities, the PR's purpose, earlier versions (old proof), migrations in progress, maintainer preference? How large a share of asks is that?
- Cheap semantic shrinking: a small model or retrieval over census examples. The record's selectors (stage F 22/33 at 25, 6/33 at 5; stage H AUC ~0.6; precedent priming) — what do they imply for 5-10 per part, and what would differ per part rather than per PR?
- "Soundly": what would it mean for a shrink to be sound (never drop the applicable convention)? Is a sound syntactic filter possible for `standard`-form conventions?
- How to measure a shrink step's recall without a review run, with power (census leave-PR-out, the A→B ledger, the 39 probe asks).

## Deliver, as your final message (≤ 1,200 words; it goes to the orchestrating session, not the user)
1. Verdict in your lens, one paragraph.
2. The strongest objections to the draft's step 2, ranked, each with evidence and what would refute it.
3. Your best answer to Q2: the shrink pipeline you would propose, with the recall@k you expect at each stage (numbers where the record allows), and what it cannot select.
4. What you would reject outright, with evidence.
5. The cheapest measurement that would settle Q2 before any review run, with a pre-stated threshold and cost.
Report at the altitude the evidence supports; separate "tried and failed" from "cannot work"; mark read versus inferred. The project's goal is issue recall.

---

## R3 — behaviour, cost and the decomposition record

You are one of four independent reviewers in an adversarial round on a research idea in the APE-Bench repository (Mathlib PR review research). Your lens: **BEHAVIOUR, COST AND THE DECOMPOSITION RECORD — if the PR is split into parts and each part is reviewed concurrently with 5-10 conventions delivered DP-style, how will the sub-reviewers behave, what does it cost, and which parts of this repeat recorded failures?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round2/R3/.
- Token economy: stay under ~120k tokens. Use grep, `sed -n` ranges and small Python counts.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
- The draft under review, with the user's words and the facts in hand: `<SP>/round2/draft.md`.

## The record (R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-dossiers)
- Stage README: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` — stage F (392-542: 25 sentences treated as a checklist; asks reached a finding fell), stage G (543-732: half decoys, verify-and-drop, overridden), stage H (733-873), stage D and Result 7 (874 onward: DP over three reps, volume +0.62 findings a PR).
- `R/docs/dead-ends.md`: "Convention detectors as a recall lever" (13 of 14 unasked facts filed under the disposition paragraph), "The family division of the specialist arms", "Specialists as the coverage floor", "Selection from artifact-only signals", and the local-model steering screen (over-file helps the floor model).
- `R/docs/plans/2026-09-23-work-enumeration.md` (forcing verdicts 0.20 → 0.50; the generalist held 64 of 71 hits; the decisions), `R/docs/plans/2026-09-22-coordinated-emission.md`, `R/docs/todo/routing-lead-iterative-queue.md`, `R/docs/todo/routing-remit-and-silence.md`, `R/docs/plans/2026-10-01-beyond-the-solo-baseline.md` (K decorrelated passes unioned; ensembles), `R/docs/plans/2026-10-03-after-structure.md` (D1/D2 designs bought consistency, not a frontier).
- `R/docs/research/harness*` or the user's memory note is not available to you; the project's framing (`R/CLAUDE.md`): model and harness changes moved the wall, pipeline additions did not.
- Cost references in `R/CLAUDE.md`: DeepSeek on `first` is free (a 15-session rep ~35 min; stage D's 147 sessions took about 4.5 hours of the node); Claude runs on a subscription whose week is nearly spent; the ELM key has £500.
- `R/docs/todo/adjudication-rubric.md` (the unadjudicated ~90% of findings).

## Your task
- **The decoy problem.** Every positive result had lists where every convention was right. In a part with 5-10 conventions, most will be wrong for that part. What does the record predict a DP-style sub-reviewer does with wrong conventions under the precedence paragraph ("they outrank your own judgement")? Use stage G (decoys, verify lead), stage F (25, checklist), the detectors under disposition (13 of 14), stage H (raise rates), and the ladder's 93 of 117 "departs" at asked places. Estimate the false filings per PR under the draft and what that does to the reach-per-finding the stages used as a guard.
- **The decomposition record.** Specialist arms, the family division, fanout, forced verdicts, work units, coordinated emission: which failures were model-specific (gpt-5.2 with reasoning off, defective tools) and so may not transfer to Opus or DeepSeek, and which were structural (aggregation, emission across parts, the generalist's whole-file judgement) and will transfer?
- **Scrutiny.** The draft defers precision to a later scrutiny step. What can be scrutinised (validity: the departure is real, the fix compiles) and what cannot yet (demand)? Does recall-first-then-filter work here, given gold is a lower bound?
- **Cost.** Sessions per PR, wall time on DeepSeek, and whether Opus is affordable at all for this shape.
- **Altitude.** Is the claim "decomposition hasn't been tested with Opus or DS" right, and what is the closest thing in the record that was?

## Deliver, as your final message (≤ 1,200 words; it goes to the orchestrating session, not the user)
1. Verdict in your lens, one paragraph.
2. The strongest objections to the draft's steps 3-4, ranked, each with evidence and what would refute it.
3. Your answers to the user's two questions (Q1 decomposition, Q2 subset from a partial PR), one paragraph each, in your lens.
4. What you would reject outright, with evidence.
5. The cheapest experiment that would most change the picture, with a pre-stated threshold and cost.
Report at the altitude the evidence supports; separate "tried and failed" from "cannot work"; mark read versus inferred. The project's goal is issue recall.

---

## S — steelman

You are the STEELMAN in an adversarial round of four on a research idea in the APE-Bench repository (Mathlib PR review research). Three other reviewers attack it independently; your job is to make it as strong as it can honestly be, then say where even the strongest version fails.

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job or GPU job. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/round2/S/.
- Token economy: stay under ~120k tokens. Use grep, `sed -n` ranges and small Python counts.
- The other reviewers' reports are not available to you; do not look for them.

## Read first
- The draft under review, with the user's words and the facts in hand: `<SP>/round2/draft.md`. The user's two questions: (1) how do we decompose the entire PR into parts such that we can focus on only a subset of conventions in each part; (2) can we choose a correct subset given a partial PR.

## The record (R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-dossiers)
- `R/docs/plans/2026-09-23-work-enumeration.md` (the closest prior design: questions from maintainer comments, asked at every place, a verdict per target; never built with a corpus-derived list or a strong model).
- `R/docs/research/review-work-structure-2026-09.md` (§1 three facts that generate review work; §7 kinds of similarity between review questions and the division they give).
- `R/docs/todo/batching-work-units.md`, `R/docs/plans/2026-09-22-coordinated-emission.md` (units from change targets; 3 of 42 obligations span units).
- Stage README `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` (stages F, G, H, D and Result 7) and the ladder `W/results/pr_review_v5/probes/conventions-ladder-2026-10-08/README.md` (with its running note: at the place, the bare sentence writes 6 of DP's 7 gains).
- The census `R/results/pr_review_v5/adjudications/conventions-census-v1/` (`results.md`, `reader_A/codebook.json`, labels), stage G's `rules.json` (triggers for 52 entries) in the stage directory.
- `R/docs/dead-ends.md` (detectors; family division; specialists as the coverage floor; facet-keyed join; selection from artifact-only signals).
- `R/docs/todo/conventions-nature.md` (scope, conflict, maturity), `R/docs/research/pr-review-v5-principled-design.md` §D1/§D2.
- External context you may use from memory (do not browse): static analysis and linters as scoped rule engines (a rule declares the AST nodes it visits); code review bots that run many narrow checkers; retrieval-augmented review; mixture-of-experts style routing; how human Mathlib reviewers divide work (by area, by kind of concern).

## Your task
Construct the 3-4 strongest designs that answer both questions together. Include, and go beyond:
- syntactic scoping keyed on Lean constructs, the way linters declare the nodes they visit;
- a convention-situation index (each census entry given a situation predicate: syntactic where possible, semantic otherwise);
- grouping by family or rationale, as sub-reviews;
- a cheap semantic or retrieval step to 5-10;
- the ladder's finding that, at the place, the bare sentence often suffices: a per-(part, convention) one-turn check as the engine, rather than agentic sub-reviews.

For each design:
- the mechanism, step by step;
- the evidence for it and against it (cite);
- its recall ceiling, with numbers where the record allows;
- the false-filing risk and how it would be contained;
- the cheapest falsifying measurement, with a threshold.

Then say how the census must be made robust for the best design, and where the steelman fails.

## Deliver, as your final message (≤ 1,400 words; it goes to the orchestrating session, not the user)
1. The strongest design and why, one paragraph.
2. The designs, as above.
3. Answers to Q1 and Q2 from the idea's strongest position.
4. What you would drop from the draft, with evidence.
5. The one measurement you would run first, with a pre-stated threshold and its cost (prefer data on disk, CPU or the free DeepSeek).
Report at the altitude the evidence supports; mark read versus inferred. The project's goal is issue recall.
