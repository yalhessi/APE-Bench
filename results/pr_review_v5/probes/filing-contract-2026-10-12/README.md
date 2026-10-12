# The filing contract, tested: pre-registration (2026-10-12, written before any session runs)

The experiment of `docs/research/filing-decision-design-2026-10-12.md` §11, approved by the user on
2026-10-12 ("we can run the experiment and test this design"). Everything below is fixed before the
first session; an amendment is dated, says why, and is written before the reading it affects.

## The question

The per-ask reading found that the free reviewer, at most of its misses, names the maintainer's concern
and clears it, on grounds a contract can refuse (worth, a plurality, the file's siblings, a check not
run, nothing stated). The design that survived the adversarial round is **a submission contract the
harness enforces**: a cell may be closed as conforming only with evidence the harness can verify;
everything else at a cell is filed, as a change or as a question to the author; nothing is withheld.
Two readings decide it: **does a reviewer that may not withhold still name the asks** (bar 1), and **at
what volume** (bar 2).

## Condition G: the design `filing_contract`

A review design (`src/ape/tasks/lean_tasks/formal_math/review/filing_contract.py`), a subclass of D1
`structured`, added by the rule's three edits. Everything a DeepSeek DX/AP session had is kept: the model
(DeepSeek-V4.1-Flash on `first`, reasoning high, thinking kept), brief G2, user prompt v2, the PR model,
the tools, and the AP sessions' conventions section with its precedence paragraph (`context_<set>_apt.jsonl`,
the registered bytes of `conventions-ceiling-2026-10-04/context_apt.sha256`). What changes is the contract
appended to the user prompt:

- **Subjects and questions.** D1's: every declaration the PR leaves in place × six concerns, every changed
  file × three file concerns; plus **one PR subject** × two concerns (`description`: does the description
  say what and why, and the plan; `scope`: is the PR one thing, and does it finish the job at the
  analogous places). The declaration concerns carry the questions the reading found the audit never asks:
  under `proof`, whether a tactic, attribute or generator makes the proof or the declaration unnecessary;
  under `statement`, the shape a caller would want and what the proof uses of each hypothesis and
  constant; under `library`, the library's current form for this (its newest declarations and
  deprecations, not only this file's) and what already exists; under `placement`, what a new import costs.
- **Three dispositions per cell.** `conforms`, `candidate` (a change the author should make), `ask_author`
  (a question to the author: a check that could not be run, or that failed for want of something the
  author could supply).
- **`conforms` is refusable.** It is recorded only with at least one evidence item the task verifies:
  a `quote` (a verbatim line of that subject's own reviewed code, at least 12 non-space characters,
  whitespace-normalised; a sibling's line is not the subject's code) or a `check` (an edit compiled with
  `lean_verify_edit` in this session, named by its declaration and new text or line span and found in the
  task's compile cache; or a declaration name whose lookup the task re-runs and finds). A `conforms`
  without one is refused, all-or-nothing per call, as D1 refuses an empty reason.
- **Every `candidate` and `ask_author` cell is filed** as a finding (form `change` or `question`), with
  typed evidence (`check`, `quote`, `convention`, `form`, `construction`, `analogue`, `own`) and
  `would_clear_on`: the ground on which the reviewer would have left it out, as one of `nothing`, `worth`,
  `maintainers_might_not_ask`, `file_or_siblings`, `corpus_or_tool_count`, `brief_or_budget`,
  `change_may_be_wrong`, `other`, with its own words.
- **A change the tools contradict** (an edit that does not compile, a duplicate that does not exist, a
  rename onto an existing name) is handed back up to three times, as in D1; after that it is **filed as
  an `ask_author` question carrying the tool's answer**, not dropped.
- **No withholding:** no finding budget, and the contract states that it replaces the brief's
  instructions to predict only requests, to emit only changes the reviewer would actually request, and
  not to report questions or what was checked.

The published findings of a G session are its candidates and questions: **All(G)**.

**A(G)**, the authority order as an offline policy over a session's stored ledger, fixed now: keep every
finding, except withhold a `candidate` whose `would_clear_on` is `change_may_be_wrong` *and* which carries a
verified `check` evidence item; a contradicted change stays as the question it was filed as. This is the
draft's order applied mechanically: every other ground is inadmissible, so it never withholds. The record
review and the generality review predicted that this policy discards little. If A(G) withholds fewer than
10% of All(G)'s findings, it is read through All(G)'s matches (an ask whose matched finding A(G) keeps); at
10% or more, A(G) is matched as its own sessions in a second seal before it is read.

## Where and how many

- PRs: the dev release's 15 (twelve with asks, three controls: 33304, 33315, 33438) and P14's 14 (validation
  small12's eight with asks, post-cutoff's six). 29 PRs.
- Three reps a set, run names `filing_g_<dev|val|post>_rep<n>`, configs
  `configs/designs/filing_contract_<set>_local.yaml` (each extends that set's DeepSeek contract-v2 config and
  states the design alone), context file set at invocation as the DX/AP runs set it.
- A smoke session first, on one PR per set (33145, 30641, 42814), run names `filing_g_smoke_<set>`: does the
  contract bind (cells recorded, a bare `conforms` refused, findings filed), and at what volume. Not read for
  the bars.
- Unattended as a Slurm job on `first`, once the GPUs are free, with the DeepSeek server of
  `serve_ds41.sbatch` and its two probes, as the table's DeepSeek cells ran.

## Matching

One seal per set (P14_val, P14_post, D12): per PR, G1, G2, G3 and two anchors, DX1 and AP1, re-matched
blind among them, five sessions a PR, harness-blind, two matchers a batch (`run_matching.sh`). The matcher
rubric gains one paragraph, the question form (a new file beside the old, chosen by a flag, so every
earlier seal stays reproducible):

> A finding may be a question to the author. Judge it like any other finding: it `reached` the ask when
> the change it asks about is the maintainer's change (the author answering yes and making it would
> satisfy the maintainer), or when the maintainer's ask is itself that question; it is `partial` when it
> asks about the same thing and the same kind of issue without naming the maintainer's change.

The anchors measure the seal's drift against the table's own matches of DX1 and AP1; a drift of more than
four asks on either matcher is reported beside every number.

## The cores (fixed: `cores.json`)

- **The inadmissible-dropped core, 37 asks:** every ask with at least one session row the mechanics review
  hand-coded as cleared on an inadmissible ground (`ask-reading-2026-10-12/review-mechanics/k_grounds.jsonl`).
- **The never-reached core, 32 asks:** no ask-free session reached it (X, T, OP, GPT, DX, AP; Opus + AP
  excluded), matcher 1, on the table's seals `match_P14_val`, `match_P14_post`, `match_D12b`.

## Bars (each read on each matcher separately)

1. **Naming.** All(G), the union of three reps, reaches **≥ 24 of the 37** and **≥ 8 of the 32**. Below
   **16 of 37**, the contract suppresses naming on this model and the design goes to `dead-ends.md`, with
   "a stage 1 that names into a scratch ledger and submits only its candidates" as its untried form.
2. **Volume.** All(G)'s published findings: **≤ 2.0 a control PR** (mean over 33304, 33315, 33438 and three
   reps), and **asks reached per published finding no lower than DX1's** on the same seal. Failing either
   with bar 1 met is reported as what it is: the generator names, at the volume of a pass-through, and the
   filing decision has moved to selection.
3. **The policy.** A(G) keeps ≥ 80% of All(G)'s reach on the 37 while meeting bar 2.
4. **Reported, not bars:** G's per-session reach on all 93 asks, beside the table's DX and AP and the
   anchors; findings a PR by set; the share of `conforms` refused and resubmitted; `would_clear_on` by
   ground over every filed finding, ask PRs and controls; the condition R (the authority order stated
   in-line to a solo reviewer) runs only if bar 1 passes, under its own pre-registration.

Everything here is in-sample on the reading's sets, one seal, three reps, two matchers with the table's
agreement; it is provisional, and the fresh 40-PR set decides after.

## Cost

Generation: $0, the self-hosted DeepSeek tier, three reps of 29 PRs, as the table's cells ran (about 35
minutes a 15-PR rep; G's cells make sessions longer). Matching: the primary Claude token (the user's
account), five sessions a PR on 26 PRs; its token estimate is computed from the table's matcher logs and
G's actual volume and reported to the user before the seal is launched.

## Amendment 1 (2026-10-12, before any session runs)

**The smoke adds 33294.** The preflight counts 17 to 551 cells a PR (33294: 86 declarations, 551 cells;
33149: 341), and the main risk to the design on this model is that a session cannot finish a ledger
that size inside the run's limits (160 turns, 16,080,000 tokens a PR, as the DX/AP runs had). None of
33145, 30641, 42814 is large. Smoke PRs: dev 33145 and 33294, val 30641, post 42814.

**The smoke's health checks, fixed now; the job proceeds to the reps only if all hold** (they are about
the harness, not the bars, and nothing in them reads an ask):
- every smoke session ends with a submitted result;
- at most 10% of a session's cells are `unstated`;
- no session stops on its turn or token limit.
Otherwise the job stops, releases the node, and the smoke is read by hand before anything else runs.
