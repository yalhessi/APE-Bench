# The four briefs, as handed over (2026-10-08, 08:55 EDT)

Four `general-purpose` subagents of the orchestrating session (Opus 5.5, the primary subscription),
launched together in the background, read-only, each with its own lens. None saw another's brief or
report. `<SP>` stands for the session scratchpad,
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/592272bf-2a21-4fd7-84f0-c3c437872216/scratchpad`;
the fact sheet they read there is `factsheet.txt` in this folder, before its suggestion-block section
was appended (that section came after the briefs were sent).

---

## R1 — mechanism

You are one of four independent reviewers in an adversarial round on a research proposal in the APE-Bench repository (Mathlib PR review research). Your lens: **MECHANISM — is "understanding a convention" a real, separate bottleneck, or a relabelling of the decision to file?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job, GPU job or paid run. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/review_R1/.
- Token economy: aim to stay under ~150k tokens. Use grep, `sed -n` ranges and small Python counts; never print census label files or run directories whole.
- The other reviewers' reports are not available to you; do not look for them.

## The proposal
`/research/projects/proofedit/ya475/APE-Bench/docs/todo/conventions-dossiers-exams.md` — read it in full first. In short: build an evidence-based dossier per Mathlib convention (census asks with hunk and merged fix, unasked situations, conforming code, corpus prevalence, a decision procedure and check); examine model+dossier on held-out census cases (asked / conforming / unasked-departure groups); use exam results to calibrate how strictly each convention is applied in review; measure the consequences of strict adherence without gold; map conventions × representations.

The user's framing (2026-10-08): models "don't have a deep understanding of these conventions, so they can't adhere to them strictly... A small sentence gives a sense of the convention... but it isn't the full picture. The model should develop an understanding of each convention before it uses it." And on method: "the tests we come up with are too uninformative at the moment because we keep trying to take safe evidence-based steps, but we're still not exploring the unexplored and not learning about the overall picture of the search space." Weigh informativeness about the search space, not only safety.

## The record (paths; R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-ds41)
- Stage README: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md`. Lines 215-391 stage C (exact conventions briefed to Claude, +0.26/+0.28; E1's ten misses, read from notes), 392-542 stage F (25 conventions picked from the diff: +0.03), 543-732 stage G (rules pinpointed at the place with a check: +0.000, the reviewer verified and overrode), 733-873 stage H (deciding which flagged places maintainers raise: AUC 0.56-0.64), 874-1190 stage D (DeepSeek-V4.1-Flash; DE exact sentences +0.231 over DX; DP = exact sentences + up to two census examples each + a precedence paragraph, a further +0.15/+0.18; **rep 1 only, provisional**; lines 1166-1176 classify DP1's 16 misses).
- Session evidence you may sample (at most ~4 sessions; read only the relevant parts):
  - Claude E1 / G1 notes: `W/results/pr_review_v5/probes/{construction-demo-2026-09-29,model-gap-val-small12,postcutoff-2026-09-29}/pr<N>/{E1,G1}/notes.md` (find with `git -C W ls-files | grep notes.md`).
  - DeepSeek rep-1 runs: `W/results/pr_review_v5/runs/iter_ds41_conv_{val,post}_{base,exact,prec}_rep1/` (thinking is kept as `reasoning_content` in the trajectories; grep for the convention or declaration).
- The disposition paragraph and stage W (gpt-5.5, +0.189 out of sample): `git -C R show generation-suppression:docs/plans/2026-10-06-generation-without-suppression.md`.
- `R/docs/plans/2026-10-06-convention-decision-designs.md` (stage H's design space).
- `R/docs/dead-ends.md` (entries: "Convention detectors as a recall lever", "Selection from artifact-only signals", "Precedent priming, Mode A", "Community-guidelines injection, statute").
- `R/docs/todo/reviewer-model-gap.md` (gpt models' filing bar "would require" vs "would request"; GE1's misses mostly never considered).
- Census: `R/results/pr_review_v5/adjudications/conventions-census-v1/results.md`, `reader_A/codebook.json`.
- A fact sheet I computed (verify what you rely on): `<SP>/factsheet_probe_asks.txt` — the 39 in-census probe asks on stage L/D's two sets with reader A's entry, its rank and ask count over val1000, and reach per session (Claude X1, X2; DeepSeek DX1, DE1, DP1; matcher 1).

## Your task
Decompose where reviewers fail on convention asks, across the record: retrieval (which convention), localisation (where), **understanding** (what the convention requires, its scope, its comparison class, what the fix looks like), decision (whether to file, given it understood), execution (a check failed or was run on the wrong variant). Then:
- Is "understanding" a separate failure mode that a better representation could fix, or is it the decision to file under another name? What evidence distinguishes them? (E.g. "`_left`/`_right` matches local siblings" is that a misunderstood comparison class or a filing decision?)
- DP already gives two maintainer examples per convention plus precedence and moved DeepSeek. What does a dossier add over DP? Which of DP1's 16 misses (and stage C E1's 10, stage G's overrides) would a dossier plausibly fix, which would it not, and why?
- In a realistic, ask-free review the reviewer must choose among ~400 conventions (stage F) and decide which situations maintainers raise (stage H: ≤5%). Where does understanding sit in that chain, and how much of the recall loss is downstream or upstream of it?

## Deliver, as your final message (≤ 1,200 words; it goes to me, not the user)
1. Verdict in your lens: proceed / narrow / drop, one paragraph.
2. The strongest objections, ranked; each with evidence (file:line or figure) and what would refute it.
3. Answers to: (a) Is understanding separable from the decision to file? (b) Does the exam predict review recall, or only itself? (c) Is the tail cap fatal? (d) What is the cheapest experiment that could falsify the idea? — one short paragraph each, in your lens.
4. Proposals you would reject outright, with the evidence (they will be kept in the record).
5. The one experiment you would run first, with a pre-stated threshold and its cost.
Report at the altitude the evidence supports; separate "the designs tried did not work" from "cannot work"; mark what you read versus inferred. The project's goal is issue recall (share of maintainers' round-1 asks reached); gold is a lower bound, so precision claims are unsupported.

---

## R2 — measurement

You are one of four independent reviewers in an adversarial round on a research proposal in the APE-Bench repository (Mathlib PR review research). Your lens: **MEASUREMENT — does the proposed exam measure anything that matters for review, and can it be read at the sizes available?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job, GPU job or paid run. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/review_R2/.
- Token economy: aim to stay under ~150k tokens. Use grep, `sed -n` ranges and small Python counts; never print census label files whole.
- The other reviewers' reports are not available to you; do not look for them.

## The proposal
`/research/projects/proofedit/ya475/APE-Bench/docs/todo/conventions-dossiers-exams.md` — read it in full first. In short: build an evidence-based dossier per Mathlib convention; **examine model+dossier on held-out census cases in three groups scored separately** (asked: flag the place and propose the merged fix; conforming: stay silent; unasked departures: read as volume, not error); use exam results to calibrate how strictly each convention is applied in review; measure consequences of strict adherence without gold (volume, validity, and "revealed preference": did Mathlib later change flagged code to conform); and a map of conventions (top 50 + a tail sample) × representations (sentence; sentence+examples; dossier; dossier+check) scored by exam on the free local DeepSeek model.

The user's framing (2026-10-08): models lack deep understanding of conventions; "the tests we come up with are too uninformative at the moment because we keep trying to take safe evidence-based steps, but we're still not exploring the unexplored and not learning about the overall picture of the search space." So an exam that is informative about the search space is wanted; do not just recommend another narrow probe, but do not accept an exam that measures only itself.

## The record (R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-ds41)
- Stage README: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` — stage C 215-391, F 392-542, G 543-732, H 733-873 (stage H mined negatives with a blind pinpointer on 16 census PRs: 205 flagged places, 6 at an ask; deciders' AUC 0.56-0.64; `stage_h.py`, `census_sample.json`, `census_pinpoints/` beside the README), stage D 874-1190 (DeepSeek-V4.1-Flash; DP = exact sentences + up to two census examples + precedence: +0.15/+0.18 over DE; rep 1 only, provisional; one ask = 0.026; DeepSeek moved 6-9 of 23 rep to rep on dev).
- Census: `R/results/pr_review_v5/adjudications/conventions-census-v1/` — `results.md`, `reader_rubric_census_v1.md`, `reader_A/codebook.json` (438 entries: principle, rationale, form rule/standard), `reader_A/labels_b*.jsonl` (val1000, 1,833 asks; per-ask principle_id), `labels_y*.jsonl` (other years), `crossmap.json` (reader agreement 0.809 at ask level). Bodies (comments, hunks) are not committed; `provenance/materialise_bodies.py` rebuilds them from the PR store (do not run it unless you need one example; it is local, no network).
- `R/CLAUDE.md` §"Reporting results": three reps minimum; semantic judge self-agreement ~90%, so one obligation at n≈8 is ±12pp; `location_recall` is not a quality signal; gold is a lower bound, precision unsupported.
- `R/docs/dead-ends.md`: "Δ revealed-preference framing" (scoring against first-push→merged diff; dropped, reopens "never as ground truth"), "Selection from artifact-only signals", "Precedent priming, Mode A", "Convention detectors as a recall lever", "Linter-as-convention-oracle". `R/docs/todo/README.md` lines ~160-195 ("was it acted on" to order adjudication, never to score). `R/docs/todo/adjudication-rubric.md`.
- Leakage: `R/MEMORY` is not yours; the rule is in the proposal ("Leakage") and `R/docs/todo/eval-set-selection.md` if needed. DeepSeek-V4.1 was released 2026-09-10, training cutoff unknown; census PRs are val1000 (2025-06..2026-03) and outside_years.
- A fact sheet I computed (verify what you rely on): `<SP>/factsheet_probe_asks.txt` — the 39 in-census probe asks with reader A's entry, its rank and val1000 ask count, and per-session reach (Claude X1/X2; DeepSeek DX1/DE1/DP1).

## Your task
Attack the exam's construct validity and power:
- Ceiling and floor effects when the convention and the hunk are handed over (stage C/G: the hard part of review is knowing which convention is in play, and where); base rates of each group; what each group's score means.
- How would "conforming" and "unasked departure" cases be mined, from what, and how noisy are they (stage H's pinpointer flagged 12.8 places a PR for ten rules; maintainers raise ≤5%)? Is there a cleaner construction (e.g. minimal pairs)?
- Can exam scores ever be validated against review recall at the sizes available? Count, from the fact sheet and census, how many probe/eval asks fall under each head convention; what correlation could be detected.
- Leakage and memorisation of merged fixes; judge noise for "proposes the merged fix"; the third group's interpretability.
- The "revealed preference" measure (Mathlib later conforming) against the Δ dead end: is it a different measurement, and what would it need?
- The map: cells = conventions × representations; at what number of cases per cell is a difference readable?
- Propose the most informative exam design you can, if any.

## Deliver, as your final message (≤ 1,200 words; it goes to me, not the user)
1. Verdict in your lens: proceed / narrow / drop, one paragraph.
2. The strongest objections, ranked; each with evidence (file:line or figure) and what would refute it.
3. Answers to: (a) Is understanding separable from the decision to file? (b) Does the exam predict review recall, or only itself? (c) Is the tail cap fatal? (d) What is the cheapest experiment that could falsify the idea? — one short paragraph each, in your lens.
4. Proposals you would reject outright, with the evidence (they will be kept in the record).
5. The one experiment you would run first, with a pre-stated threshold and its cost.
Report at the altitude the evidence supports; separate "the designs tried did not work" from "cannot work"; mark what you read versus inferred.

---

## R3 — ceiling, cost and the record

You are one of four independent reviewers in an adversarial round on a research proposal in the APE-Bench repository (Mathlib PR review research). Your lens: **CEILING, COST AND THE RECORD — what is the most issue recall this could add, what does it cost, and which parts are re-runs of recorded dead ends under another name?**

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job, GPU job or paid run. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/review_R3/.
- Token economy: aim to stay under ~150k tokens. Use grep, `sed -n` ranges and small Python counts; never print census label files whole.
- The other reviewers' reports are not available to you; do not look for them.

## The proposal
`/research/projects/proofedit/ya475/APE-Bench/docs/todo/conventions-dossiers-exams.md` — read it in full first. In short: build an evidence-based dossier per Mathlib convention (asks with hunk and merged fix, unasked situations, conforming code, corpus prevalence, a decision procedure and check); examine model+dossier on held-out census cases; use exam results to calibrate strictness in review (reviewer sees a one-line index and opens dossiers like skills); measure consequences of strict adherence; map conventions × representations on the free local model.

The user's framing (2026-10-08) is in the proposal. Note the user also said "the tests we come up with are too uninformative at the moment because we keep trying to take safe evidence-based steps, but we're still not exploring the unexplored and not learning about the overall picture of the search space." And the user's standing rule (2026-10-07): the sole current goal is issue recall; before proposing spend, state the most recall it could add; "there aren't a small number of detectors to capture most findings" closed the detector line.

## The record (R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-ds41)
- Stage README: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` — stage C 215-391 (Claude + exact conventions 0.74 vs 0.46-0.49), F 392-542 (top-50 list bounded low: lines ~400-405; selector of 25 holds right entry for 22 of 33; reach +0.03), G 543-732 (+0.000), H 733-873 (deciders AUC 0.56-0.64; maintainers raise ≤5% of flagged places), D 874-1190 (DeepSeek: DX 0.21, DE 0.44, DP 0.62/0.59 on 39 in-census asks, rep 1, provisional; DP = exact sentences + up to two census examples + precedence).
- Census: `R/results/pr_review_v5/adjudications/conventions-census-v1/results.md` (1,833 asks, ~400 principles, top 50 ≈ 55% of principled asks, 85% of probe asks in census, not saturated: one new principle per ten asks); `reader_A/codebook.json`; `reader_A/labels_b*.jsonl` (per-ask principle_id; val1000).
- `R/docs/dead-ends.md` — check the idea against at least: "Community-guidelines injection, statute", "Selection from artifact-only signals", "Precedent priming, Mode A" and "Flag-rate priors, Mode B", "Convention detectors as a recall lever", "Δ revealed-preference framing", "Linter-as-convention-oracle", "Surface proxies for convention discovery", and the local-model steering screen ("examples", "conventions as directive": no effect on Qwen).
- `R/docs/research/pr-review-v5-principled-design.md` §D2 (norm store with maturity, never built), `R/docs/plans/2026-10-03-after-structure.md`, `R/docs/plans/2026-10-06-convention-decision-designs.md`, `R/docs/todo/README.md` (the index; rows on residual mechanisms: "the 67 residual asks... convention knowledge (25 asks) and untried automation (19)"), `R/docs/todo/conventions-ceiling-probe.md`, `R/docs/PROJECT-STATUS.md` §6 (precedent retrieval: a dense index, hit@5 49%, never measured on reviewer output).
- Costs: `R/CLAUDE.md` (DeepSeek on `first`: free, a 15-session rep ~35 min, 8 GPUs, ~12 min to serve, shared with another user gg676's jobs; the primary Claude subscription's week stood at 93% on 2026-10-08, resets Friday 10:00; census reader runs ~200k subagent tokens per 125 asks).
- A fact sheet I computed (verify what you rely on): `<SP>/factsheet_probe_asks.txt` — the 39 in-census probe asks with reader A's entry, its rank and val1000 ask count, and per-session reach (Claude X1/X2; DeepSeek DX1/DE1/DP1), plus head coverage (top 10/25/50/100/200 = 0.22/0.39/0.55/0.70/0.86 of principled asks).

## Your task
- **The ceiling, in numbers.** The most issue recall the idea could add if everything went right: (i) in the exact-brief regime (dossier vs DP), and (ii) in a realistic ask-free review (dossier index the reviewer browses), using census coverage, head share, what unbriefed and briefed reviewers already reach under head conventions (fact sheet), retrieval losses (stage F) and selection (stage H). Compare with the detector line's 2.9% that closed it. Is the tail cap fatal? Would a coarser grain (dossiers per mechanism/family) change the cap, and at what cost to specificity?
- **Novelty against the record.** Which parts are re-runs under another name (statute, priming, exemplars, stage G's rule writer from four census asks, the norm store), and which are genuinely untried? Where the record's negative was on a weaker model (gpt-5.2 without reasoning, Qwen), say whether it transfers.
- **Cost.** Offline dossier building (per convention, which model/route, how many tokens), the exam on DeepSeek (GPU-hours on a shared node), any Claude subscription use.
- **A cheaper first step.** Is there an experiment on data already on disk (stage D reps 2-3 are running now; DP1's 16 misses; stage C/G notes; census) that answers the key question before any dossier is built?

## Deliver, as your final message (≤ 1,200 words; it goes to me, not the user)
1. Verdict in your lens: proceed / narrow / drop, one paragraph.
2. The strongest objections, ranked; each with evidence (file:line or figure) and what would refute it.
3. Answers to: (a) Is understanding separable from the decision to file? (b) Does the exam predict review recall, or only itself? (c) Is the tail cap fatal? (d) What is the cheapest experiment that could falsify the idea? — one short paragraph each, in your lens.
4. Proposals you would reject outright, with the evidence (they will be kept in the record).
5. The one experiment you would run first, with a pre-stated threshold and its cost.
Report at the altitude the evidence supports; separate "the designs tried did not work" from "cannot work"; mark what you read versus inferred.

---

## S — steelman

You are the STEELMAN in an adversarial round of four on a research proposal in the APE-Bench repository (Mathlib PR review research). Three other reviewers attack the idea independently; your job is to make it as strong as it can honestly be, then say where even the strongest version fails.

## Rules
- Read-only. Do not edit, write or commit anything in the repository. Do not start any LLM call, `claude` process, Slurm job, GPU job or paid run. Python/grep/sed for reading and counting is fine; scratch files only under <SP>/review_S/.
- Token economy: aim to stay under ~150k tokens. Use grep, `sed -n` ranges and small Python counts; never print census label files whole.
- The other reviewers' reports are not available to you; do not look for them.

## The proposal
`/research/projects/proofedit/ya475/APE-Bench/docs/todo/conventions-dossiers-exams.md` — read it in full first. In short: an evidence-built dossier per Mathlib convention; an exam on held-out census cases that makes understanding a measured property; exam-calibrated authority in review (index + open dossiers like skills); consequences of strict adherence measured without gold; a map of conventions × representations on the free local model.

The user's framing (2026-10-08): models "don't have a deep understanding of these conventions, so they can't adhere to them strictly. This is partially a limitation of using a text representation of these conventions. A small sentence gives a sense of the convention, just like the description of an MCP tool or skill is helpful, but it isn't the full picture. The model should develop an understanding of each convention before it uses it." On method: "the tests we come up with are too uninformative at the moment because we keep trying to take safe evidence-based steps, but we're still not exploring the unexplored and not learning about the overall picture of the search space." The project's single current goal is issue recall (share of maintainers' round-1 asks a reviewer reaches).

## The record (R = /research/projects/proofedit/ya475/APE-Bench, W = R/.claude/worktrees/conventions-ds41)
- Stage README: `W/results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md` — stage C 215-391 (exact conventions: Claude 0.74 vs 0.46-0.49), F 392-542 (25 picked from the diff: +0.03; untried list ~455-458, 523-530), G 543-732 (pinpointed rules with checks: +0.000, verified and overridden; untried 719-723), H 733-873 (which flagged places maintainers raise: AUC 0.56-0.64; untried 863-872), D 874-1190 (DeepSeek-V4.1-Flash: DX 0.21 → DE 0.44 → DP 0.62/0.59; DP = exact sentences + two census examples + precedence; rep 1, provisional; DP1's misses classified 1166-1176).
- Census: `R/results/pr_review_v5/adjudications/conventions-census-v1/results.md`; `reader_A/codebook.json` (438 entries); `reader_A/labels_*.jsonl`.
- `R/docs/dead-ends.md` (statute; selection from artifact-only signals; precedent priming Mode A — "reopens if ... a different use of the precedent (recognition mode, ranking), not as prompt priming"; convention detectors; Δ revealed preference).
- `R/docs/PROJECT-STATUS.md` §6: a dense precedent index (34,640 hunks × 384, hit@5 49%), never measured on reviewer output. `R/src/mathlib_review/` and `R/src/ape/toolkits/retrieve/` for what retrieval exists.
- `git -C R show generation-suppression:docs/plans/2026-10-06-generation-without-suppression.md` (the disposition paragraph; stage W: +0.189 on gpt-5.5 out of sample).
- `R/docs/todo/conventions-nature.md` (studies 2-4: scope, conflict, maturity; the 30458 and 32875 worked cases), `R/docs/research/pr-review-v5-principled-design.md` §D2 (norm store, never built), `R/docs/todo/static-analysis-pass.md`, `R/docs/plans/2026-10-03-after-structure.md` (try-it battery, persistent checker).
- External context you may use from memory (do not browse): skills/tool descriptions as progressive disclosure; in-context learning from many examples; legal reasoning from precedent; NATURALIZE-style convention learning from corpora.
- A fact sheet I computed (verify what you rely on): `<SP>/factsheet_probe_asks.txt` — the 39 in-census probe asks with reader A's entry, its rank and val1000 ask count, and per-session reach (Claude X1/X2; DeepSeek DX1/DE1/DP1), plus head coverage.

## Your task
Construct the 3-5 strongest variants of the idea. Include, and go beyond: (i) a dossier the model writes itself by studying census cases, and is then examined on; (ii) retrieval of the nearest census examples (code, ask, merged fix) at review time, which covers the tail without per-convention dossiers; (iii) executable checks; (iv) dossiers at a coarser grain than census entries, to beat the tail cap; (v) the exam used not only as a measurement but as a selection or calibration tool. For each variant:
- the mechanism by which it would raise issue recall, step by step;
- the record's evidence for it (cite), the record's evidence against it, and why that evidence may not transfer (model strength, delivery, regime);
- its recall ceiling, with numbers where the record allows;
- the cheapest test that could falsify it, with a threshold.
Then answer the four questions from the idea's strongest position, and say plainly where the steelman fails.

## Deliver, as your final message (≤ 1,400 words; it goes to me, not the user)
1. The strongest variant and why, one paragraph.
2. The variants, as above.
3. Answers to: (a) Is understanding separable from the decision to file? (b) Does the exam predict review recall, or only itself? (c) Is the tail cap fatal? (d) What is the cheapest experiment that could falsify the idea?
4. What you would drop from the idea as stated, with the evidence.
5. The one experiment you would run first, with a pre-stated threshold and its cost.
Report at the altitude the evidence supports; mark what you read versus inferred.
