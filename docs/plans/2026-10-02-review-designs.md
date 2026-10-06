# Review designs beside a frozen solo baseline: the structured reviewer, and the organization that lets designs coexist (plan, 2026-10-02)

**Status** — plan, written on `hygiene-layer` for a spawned build session (`review-designs`).
Nothing in it has run. The user's direction (2026-10-02): the solo baseline is frozen, "review
this as a maintainer"; what comes next are other designs, judged by whether they reach the
obligations the solo cannot and reach the ones it can more consistently; and since several
designs will be built, they must be organized so that many reviewers exist and run easily on the
same PRs.

## 1. What is frozen, and what every design is read against

The solo baseline is one task (`lean_pr_review_v5_solo`) under one contract (v2: brief G2, the
PR model before the diff, the request filing bar, a per-declaration ledger in the submission) on
the hygiene layer's tools, run through Claude Code on the subscription:

| config | what it is | dev held-out 12 (23 obligations, judge v9) |
|---|---|---|
| `configs/pr_review_v5_dev_medium_opus55_contract2_claude_sub.yaml` | H-claude, the tools before the hygiene layer | 7, 7 (union 8, stable 6) |
| `configs/pr_review_v5_dev_medium_opus55_contract2_hygiene_claude_sub.yaml` | the same on the cleaned tools, `Write`/`Edit` under `scratch/`, budget 40 | 9 (reps 2 and 3 pending) |

Neither config, nor `solo.py`'s prompts, is edited again. A design is a new task and a new
config. Every design is read on the same PR set, the same reviewed workspaces, the same judge
config and the same probe harness, against the hygiene baseline's mean / union / stable, with
the four-pass union (`docs/todo/ensemble-union-reading.md`) as the second yardstick: a design
that reaches alone what four solo samples reach together has closed the consistency gap.

What the record says the designs must act on (`docs/plans/2026-10-01-beyond-the-solo-baseline.md`
§2): aim is flat at about 0.1 obligations per finding for every reviewer; two reps of one
configuration share 65% of their targets and ask different things at them; location recall
(0.65-0.74) is twice issue recall; the reviewer files one ask per attended object; forcing the
arms to speak was the largest effect ever measured here (0.20 to 0.50); and the never-reached
ten are judgement on attended objects, moved so far only by facts about the PR delivered as
evidence, never by rules or precedents in the prompt.

## 2. The organization: a design is a per-PR task that ends in the solo submission contract

The seam that already exists: the runner's solo path builds one task per episode
(`runner.py::_solo_task_data`), reads each result through `solo_responses`, anchors findings by
path and line, and finalizes them into `findings.jsonl`, which the judge and the probe harness
read. Everything downstream of the submission is design-agnostic. So:

- **A design is a task type** under `src/ape/tasks/lean_tasks/formal_math/review/`, registered
  as the others are, whose result is the solo submission (findings with `path`, `line_start`,
  `claim`, `suggested_fix`, `severity`, and `notes`) plus whatever the design records for itself.
  The runner selects it by a new `dataset.design` key, default `solo`, looked up in a registry
  beside the task registry (`review/__init__.py`), so every existing config renders byte for
  byte and a new design is one task module and one registry line, not twenty `routing_mode`
  branches. `routing_mode: solo` stays the family name for per-PR reviewers; `lead`, `fanout`
  and `rules` are untouched.
- **A multi-stage design nests its stages inside its per-PR task** through
  `run_subtasks` (`orchestration/subtasks.py`, the path `delegation.py` already uses), so one
  run, one run plan and one cap (`solo_token_cap`) cover a PR's whole review, and the standard
  layout holds its stages as children. If the Claude Code scaffold on the subscription cannot
  nest a session (untested), the fallback is a chained stage run that reads the first stage's
  per-PR outputs through `StageInput` (`cli run --of <stage A run>`), which the stage-provenance
  work built for exactly this. The build session decides after one smoke on one PR.
- **Configs**: `configs/designs/<design>_<set>_<route>.yaml`, each extending the frozen hygiene
  baseline config and stating only `dataset.design` and the design's own block, with a test that
  a design config differs from its baseline in nothing else (the pattern of
  `test_the_two_solo_conditions_differ_only_in_their_scaffold`). Run names carry the design and
  the rep.
- **Comparison**: `report conditions --condition` for side-by-side runs; the per-obligation
  spine (`results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py`) generalized to
  take `--runs`, so a design's reps join the table beside the baseline's; `report union` from
  the ensemble session for unions across designs.

## 3. Design D1, `structured`: decide per object and concern, verify before filing

The solo decides once per PR; D1 decides once per (attended declaration, concern):
1. The packet is the baseline's (PR, PR model, diff, tools).
2. The contract: for every declaration in the PR model, a verdict per concern family (proof,
   statement and generality, library duplicate, name, docstring, attributes and placement),
   `no_issue` with its reason or `would_change` with the change; silence is not a legal verdict
   (the arms' `target_verdicts` contract, `candidates.py`, generalized to the whole-PR reviewer;
   it was built for arms, refused for solo at `runner.py:906`, and never run on a model that
   reaches anything).
3. Every `would_change` with an edit is compiled (`lean_verify_edit`, linters on) and every
   claimed duplicate or name is looked up (`declaration_search`, `naming_norm`) before it is
   filed, by the task, not by the reviewer's discretion (the `verify_edits_if_present` policy
   for the solo). A change the tools contradict is recorded as refuted, not filed; a change the
   tools cannot check is filed as advisory and marked unverified. Filing is the request bar.
4. The verdict ledger is a structured field of the submission (declaration, concern, verdict,
   reason, evidence), not prose, so D2 and the reading can consume it.

Why it should move the inconsistency class: the flipping obligations are second and third asks
at an object the reviewer already attended; the unit change makes each one its own decision.
Why it should not cost precision: the controls measure it, and the verification is refutation
by tools, never a value judgement (the selection ruling of 2026-09-22 stands; nothing ranks or
withholds a verified ask).

## 4. Design D2, `structured_critic`: structured disagreement on the "nothing to ask" verdicts

D1's ledger, per PR, goes to a second session with the same packet and tools, told to take each
`no_issue` verdict and argue the opposite with evidence (a compile, a lookup, a sibling in the
file, the area's census) or concede it explicitly; and to take each `would_change` and try to
refute it the same way. Its `would_change` candidates go through the same verification as
D1's, and the union of the two stages by evidence key is the design's output, each finding
labelled with the stage that raised it and whether the other stage agreed. Why: 60% of the
residual misses are `attempted_concluded_fine` (`phase1-residual-mechanisms-2026-09-30`), and
Adversarial Review's measured result is that a critic adds only when disagreement is prompted
explicitly, since the naive version converges on false consensus. The critic never removes a
finding; the tools do.

## 5. Rules, stated before any run

On the dev held-out 12, one run first, then reps, always beside hits per finding and the
control PRs' emission:

| comparison | a lever | not, as built |
|---|---|---|
| D1 against the hygiene baseline | ≥ 10 of 23 with control emission ≤ 2.0 per control PR | ≤ 8, or control emission > 2.0 |
| D1 against the four-pass union | D1 alone within 1 of the union's judged count: the consistency gap is closed by structure | |
| D2 against D1 | +2 obligations at control emission ≤ 2.0 | fewer, or the critic's additions are refuted at the controls |

Confirmation on validation small12 and post-cutoff through the blind matchers (plan of
2026-10-01, §5), reach ≥ the baseline's + 0.10 on both. A design that passes on dev and fails
there is read as in-window memory, not review.

## 6. Order, cost and quota

1. The build, in a spawned session on `review-designs` off `hygiene-layer`: §2's organization
   with tests, D1, D2, a one-PR smoke of each under `cli plan` and a no-spend dry run, no
   `--execute`. Nothing billed; the session's own tokens only.
2. Quota (subscription windows): hygiene reps 2 and 3 first (the 10:00 and 15:20 windows of
   2026-10-02), so the baseline has its three reps; D1 rep 1 in the window after; D2 rep 1 after
   D1 is read. Each dev run is about one five-hour window; each judge about $0.20.
3. Reps of whichever design passes its rule, then the confirmation sets.

## 7. What this plan does not do

- No lead, arms or routing: the whole-PR reader is kept because it is what reached design and
  sibling asks; structure is added around its decisions, not by dividing its view.
- No selection: verification refutes, it does not rank; agreement is a label.
- No prompt-wording thread, no bigger caps, no more retrieval breadth.
- Layer 1's evidence packets (`docs/todo/static-analysis-pass.md`, the try-it battery, the area
  census) are the complement for the never-reached ten and join D1's packet when they are
  measured, as sections, not as a design of their own.
