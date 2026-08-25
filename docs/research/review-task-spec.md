# First-Round Review of Mathlib PRs — Task Specification

*Step 0 deliverable. v0.1 (2026-06-12). This document freezes the operational definitions that the
dataset plumbing (Step 1), the hand audit (Step 2), and the stratum rubric (Step 3) all depend on.
Supersedes the framing in `pr-review-research-design.md` for this line of work.*

---

## 1. Purpose and scope

We define **first-round review** as a benchmark task: given a Mathlib PR exactly as it stood when a
maintainer first looked at it, produce the feedback that makes it more merge-ready. The gold signal
is what the maintainer actually said in that first round and what the author actually changed in
response.

In scope:
- **First review round only.** No conversation history exists at this point, which removes the
  hardest plumbing (round segmentation for context) and removes verdict/feedback leakage by
  construction.
- **Merged PRs as the primary population**, because only merged PRs have a defined endpoint
  ("what acceptable looked like"). Closed-unmerged PRs are kept as a tagged secondary slice.
- Two downstream consumers: (a) the **verifiability-stratum rubric** built from the gold comments
  (Project A), and (b) the eventual **review-lens audit of APE-Bench proof-engineering outputs**,
  which reuses this task's I/O contract with model-generated diffs in place of human PRs.

Out of scope (deliberately): follow-up rounds, the PR-split task, the legacy
`review_quality_score`, reviewer-in-the-loop generation, unmerged-PR outcome prediction.

---

## 2. Conceptual model

A PR is a tuple `(d, b, h₀)`:

- `d` — the PR title + description (as authored; see §6 for edit caveats),
- `b` — the merge-base commit on `master` for `h₀` (pins the workspace),
- `h₀` — the PR head as of the first maintainer review event, giving the diff `δ₀ = diff(b, h₀)`.

A **first review round** is the maintainers' response to `(d, δ₀)` and the author's reaction:

```
h₀  --[t₁: first maintainer event]-->  F₁ = {c₁ … cₙ}  --[author pushes]-->  h₁  …  h_merged
```

- `F₁` — all substantive maintainer feedback between `t₁` and the author's first subsequent push.
- `h₁` — the PR head at the *next* maintainer event after the author responds (or `h_merged` if
  there is none).
- `Δ₁ = diff(h₀, h₁)` and `Δ* = diff(h₀, h_merged)` — what changed in response to review, near and
  total (computed at patch level, §3.6, to exclude upstream churn).

**The gold object** for one PR is:

```
G = { verdict v₁,                       # APPROVED / CHANGES_REQUESTED / COMMENT_ONLY
      pairs  {(cᵢ, eᵢ)}ᵢ,               # comment cᵢ with its resolving edit eᵢ (eᵢ may be absent)
      deltas Δ₁, Δ*,                    # change-sets, hunk-level
      outcome (merged?, #rounds, time-to-merge) }
```

The central representational claim: *NL feedback and the induced diff are two views of the same
object*, linked by which edits resolved which comments. Every task definition below is a projection
of `G`.

---

## 3. Operational definitions

These are the decisions everything inherits. Each gives the primary rule, the data source, and the
known failure mode the Step-2 audit must check.

### 3.1 Reviewer ("maintainer")

A user `u` counts as a reviewer on PR `p` iff:
1. `u` is not a bot (`*[bot]`, `*-bot`, `bors` — existing `_is_bot_login`, extended with an explicit
   denylist: `leanprover-community-bot`, `leanprover-community-mathlib4-bot`, `github-actions`), and
2. `u` is not the PR author, and
3. `u` is in the **curated roster** (the public Mathlib maintainer + reviewer team lists, snapshotted
   into a versioned file) — primary rule — or, fallback when roster coverage is uncertain for older
   PRs, `author_association ∈ {MEMBER, OWNER, COLLABORATOR}` (existing `_is_maintainer_author`).

Roster membership is time-varying; we snapshot the current lists and accept the noise on old PRs
(report roster-vs-association disagreement in the audit). Comments by non-roster contributors are
recorded but excluded from `F₁`.

### 3.2 First maintainer event `t₁`

`t₁` = timestamp of the earliest **substantive** reviewer event on the PR, where an event is:
- a PR review with state in {APPROVED, CHANGES_REQUESTED, COMMENTED}, or
- an inline review comment, or an issue comment on the PR,

and **substantive** means it survives the trivial-token filter (existing
`_strip_trivial_feedback_tokens`; strips bare "LGTM", emoji, `bors r+`/`bors d+`/`maintainer merge`
command-only messages — a command-only approval still sets the *verdict* but contributes no
finding).

Draft PRs: events before `ready_for_review` are ignored; `t₁` must follow it.

### 3.3 The reviewed head `h₀`

`h₀` = the PR head commit that `F₁`'s author saw. Resolution order (extends
`_select_snapshot_head_sha`):
1. `commit_id` of the first review event, if it is a known PR commit;
2. else the latest PR commit **pushed** before `t₁`.

Known failure mode: the REST commits list gives `committed_at` (author/committer dates), not push
time — rebases and force-pushes can carry old dates or rewrite history so the commit the reviewer
saw no longer exists. Hardening (Step 1): use the GraphQL timeline (`PullRequestCommit`,
`HeadRefForcePushedEvent`) to recover push-ordering; PRs whose `h₀` is unfetchable are dropped and
counted in the funnel. The Step-2 audit hand-verifies `h₀` on 30 PRs; if the audit fails it for
>10% of PRs, restrict to PRs with `commit_id`-anchored reviews.

### 3.4 Round-1 window and `F₁`

`F₁` = all substantive reviewer events in `[t₁, t_push)`, where `t_push` is the author's first push
after `t₁` (if the author never pushes again, the window extends to merge/close). Multiple
reviewers within the window all contribute to `F₁` (multi-reviewer PRs are tagged — they are the
natural-experiment material for the later noise-ceiling work).

Each comment `cᵢ` keeps: author, timestamp, kind (review body / inline / issue comment), anchor
(`path`, `line`/`original_line`, hunk) when inline, thread id, and resolution status.

### 3.5 Verdict `v₁`

- `APPROVED` if the first review event (or any event in the round-1 window by a roster reviewer)
  is an approval or a bors/`maintainer merge` delegation signal with no accompanying
  CHANGES_REQUESTED;
- `CHANGES_REQUESTED` if any round-1 event has that state;
- else `COMMENT_ONLY`.

Mathlib process signals (`awaiting-author`/`awaiting-review` label transitions, `bors r+`, `bors
d+`, `maintainer merge`) are recorded on every record as a **validation timeline**, not as the
primary definition — label usage is inconsistent across eras. The audit cross-checks `v₁` against
the label timeline.

### 3.6 Change-sets `Δ₁`, `Δ*`

Naive `git diff h₀ h₁` conflates review-induced changes with upstream `master` churn merged into
the branch. Definition used instead — **patch-level comparison**:

```
P₀ = diff(merge_base(master, h₀), h₀)        # the PR's effective change at review time
P₁ = diff(merge_base(master, h₁), h₁)
Δ₁ = hunk-level difference between P₀ and P₁, aligned per file
Δ* = same with h_merged
```

Pure-rebase rounds (P unchanged) yield `Δ = ∅`. Exact hunk-alignment algorithm is an
implementation detail to be validated in the Step-2 audit; the spec-level commitment is that Δ is
computed between *patches*, not between *trees*.

### 3.7 Comment→edit linkage `(cᵢ, eᵢ)`

`eᵢ` = the hunks of `Δ₁` attributable to `cᵢ`. Heuristic (in confidence order):
1. GitHub *resolved thread* whose last activity precedes the resolving push, matched to hunks
   overlapping the thread's `path:line` span (±5 lines after offset adjustment);
2. file+line overlap between an inline comment's anchor and a `Δ₁` hunk;
3. unlinked (`eᵢ = ∅`) — comment was discussed away, out of scope, or PR-level (issue comments
   usually land here).

Linkage carries a confidence tag (`resolved_thread` / `line_overlap` / `none`). Metrics that
consume linkage (D3 per-pair form) are reported on the high-confidence subset; the Δ-level metrics
(D3 aggregate) need no linkage at all.

### 3.8 Eligibility funnel

Applied in order, with per-stage counts reported (the funnel is part of the dataset's
documentation):

1. PR in `leanprover-community/mathlib4`, within the configured date window.
2. Not a bot-authored PR; not a revert (`title ~ /^revert/i`); not a dependency/toolchain bump
   (`lean-toolchain`/`lakefile` only); not a mass-automated change (tagged, e.g. deprecation
   sweeps — kept but sliced out of the headline).
3. Touches ≥1 `.lean` file under `Mathlib/`; within size bounds (defaults: ≤30 files, 10–800
   changed lines — existing config).
4. Has a resolvable `h₀` (§3.3) and at least one substantive reviewer event (§3.2).
5. Primary slice: merged. Secondary slice: closed-unmerged, tagged.

**Important inclusion:** PRs whose first round is an *approval with no findings* are **kept**.
They are the merge-ready-at-`h₀` control class — both the negative class for D1 and the
false-positive control for D2/D3. Maintainer-authored PRs are kept and tagged
(`author_is_maintainer`), since author identity is a known confound to measure, not hide.

---

## 4. Task definitions

All three share the same input contract.

**Input** (what the system under evaluation sees — and *nothing else*, §6):
- `d` — PR title + description,
- `δ₀` — the unified diff `diff(b, h₀)`,
- the **pinned workspace**: Mathlib checked out at `b` with the matching toolchain, with `δ₀`
  applied (the existing snapshot machinery), and whatever read-only tooling the harness variant
  allows (compile, `#lint`, `exact?`, Loogle, file reading). Tool access is a *harness variable*,
  not part of the task definition.

### D1 — Verdict prediction (reported, never headlined)

- **Output:** `v̂ ∈ {APPROVED, CHANGES_REQUESTED|COMMENT_ONLY}` + probability.
- **Gold:** `v₁` (§3.5), with COMMENT_ONLY collapsed into "not approved" for the binary form.
- **Evaluation:** accuracy / Brier / calibration, always reported alongside the metadata-only
  baseline (author track record, size, files touched — Gousios-style) and with the explicit caveat
  that `v₁` is one draw from a reviewer-dependent process. D1 exists because it is cheap and
  comparable, not because it is the construct.

### D2 — Findings (primary definition)

- **Output:** a set of findings, each:
  ```
  { anchor:   {path, line_span} | PR_LEVEL,
    severity: blocking | advisory,
    stratum:  V1 | V2 | V3 | V4        # rubric tag, once the rubric exists
    claim:    short NL statement of the issue (and, optionally, the suggested resolution) }
  ```
  with a hard **budget** (default: ≤10 findings) — precision-at-budget is the deployment-relevant
  number; unlimited finding lists are not a valid submission.
- **Gold:** the comments of `F₁` (each gold comment likewise rubric-tagged in Step 3).
- **Evaluation:** predicted findings are matched to gold comments by a validated matcher
  (anchor-overlap gate + claim-equivalence judgment; hand-validated once on ~50 pairs, then
  frozen — the only place an LLM appears in evaluation, confined to recall/matching, never to
  precision of verified claims). Metrics: precision@budget, recall, blocking-recall (fraction of
  PRs where the blocking concern was caught), all reported **per stratum**.
- **FP control:** finding rate on the approval-control PRs (§3.8) — a reviewer that flags
  merge-ready code is measurably wrong, no matching needed.

### D3 — Revision specification (secondary, most objective)

- **Output:** the set of locations (file + hunk span) the PR must change before merge, optionally
  with proposed edits.
- **Gold:** `Δ₁` hunks (near form) and `Δ*` hunks (total form); per-pair scoring against
  high-confidence `(cᵢ, eᵢ)` links where available.
- **Evaluation:** hunk-localization precision/recall (overlap-based); FP control = hunks of `δ₀`
  that survive to `h_merged` untouched. No text matching, no LLM anywhere — this is the
  judge-free anchor of the suite.

D2 and D3 are projections of the same gold `G`; systems may emit both from one pass (a finding
with a suggested resolution *is* a D3 entry). D2 is primary because the rubric work (Project A)
operates on comments; D3 is the objectivity check that D2's matcher isn't doing the work.

---

## 5. Gold record schema (one JSONL row per PR)

```jsonc
{
  "pr_number": 12345,
  "slices": {"merged": true, "author_is_maintainer": false, "ai_authored": false,
              "multi_reviewer": false, "automated_sweep": false},
  "input": {
    "description": "...",                      // d (title + body as of t₁ when recoverable)
    "base_sha": "...", "head_sha": "...",      // b, h₀ (+ toolchain pin via existing machinery)
    "diff": "...",                             // δ₀
    "h0_resolution": "review_commit_id | pushed_before_t1"   // provenance of h₀
  },
  "gold": {
    "verdict": "APPROVED | CHANGES_REQUESTED | COMMENT_ONLY",
    "comments": [ {"id": "...", "author": "...", "kind": "inline|review_body|issue_comment",
                    "anchor": {"path": "...", "line": 0} , "body": "...",
                    "linked_hunks": ["..."], "link_confidence": "resolved_thread|line_overlap|none",
                    "stratum": null, "severity": null } ],   // filled by Step-3 rubric pass
    "delta_near": [ /* Δ₁ hunks */ ], "delta_total": [ /* Δ* hunks */ ],
    "outcome": {"merged": true, "rounds": 3, "merged_at": "...", "merge_signal": "bors r+ | ..."}
  },
  "validation": {"label_timeline": [...], "process_signals": [...]}   // §3.5 cross-checks
}
```

---

## 6. Leakage hygiene

The input may contain **nothing dated after `t₁`**. Specifically:
- not the review thread, verdict, labels applied after `t₁`, or later commits;
- the PR **description** is fetched with edit history (GraphQL `userContentEdits`) where available
  and rolled back to its last pre-`t₁` revision; where history is unavailable, the record is
  tagged `description_maybe_post_edited` (authors sometimes paste reviewer suggestions into the
  body);
- CI status *as of `h₀`* is legitimately part of the input (the reviewer saw it) but is deferred —
  v0.1 inputs exclude CI rather than risk reconstructing it wrong;
- pretraining contamination is handled by slicing, not exclusion: every record carries its dates,
  and headline numbers are reported on a post-model-cutoff window.

---

## 7. Known threats (what Step 2 must check)

| # | Threat | Where it bites | Audit check / fallback |
|---|---|---|---|
| 1 | `h₀` wrong (force-push, rebase, date-vs-push ordering) | everything | hand-verify on 30 PRs; fallback = `commit_id`-anchored reviews only |
| 2 | Δ polluted by upstream churn | D3 | patch-level Δ (§3.6); verify hunk alignment on audit PRs |
| 3 | linkage misattributes edits | D3 per-pair | confidence tiers; per-pair metrics on high-confidence subset only |
| 4 | verdict noise (reviewer-dependent) | D1 | never headline D1; metadata baseline mandatory |
| 5 | description edited post-review | input | edit-history rollback + tag (§6) |
| 6 | trivial/process comments inflate gold | D2 recall | substantive filter (§3.2); rubric pass marks process-only comments non-gold |
| 7 | roster drift on old PRs | F₁ membership | report roster-vs-association disagreement rate |

---

## 8. Mapping to existing code (Step 1 work list)

Reuse as-is: GitHub client, maintainer/bot detection, substantive-feedback filters, snapshot/
workspace machinery, slice/manifest writers.

Extend:
1. `_select_snapshot_head_sha` → explicit `h₀` resolution with provenance + GraphQL push-ordering
   hardening (§3.3).
2. New: patch-level Δ extractor (§3.6) — needs local clones at `h₀`/`h₁`/`h_merged`, not just the
   API.
3. New: comment→hunk linkage with confidence tiers (§3.7), incl. resolved-thread fetch (GraphQL).
4. New: label/process-signal timeline collection (§3.5 validation block).
5. New: description edit-history rollback (§6).
6. Funnel instrumentation: per-stage drop counts in the run summary.
7. Emit the §5 schema as a new record type (`lean_pr_review_v2` or similar) — do not overload the
   legacy round-based records; the legacy `review_quality_score` path is not carried forward.

Step-1 target: ~150–300 merged PRs + closed-unmerged slice, newest-first, with the funnel report.

---

## 9. Open items (to resolve during Steps 1–3, not blockers)

- ~~Curated roster source + snapshot format (§3.1)~~ — resolved: built from the
  leanprover-community website `teams.yaml`/`people.yaml` (admin + maintainers + reviewers) by
  `src/datasets/pr_review_v2/roster.py`, snapshotted at
  `src/datasets/pr_review_v2/data/mathlib_roster.txt`. The roster is *required*, not optional:
  GitHub reports `author_association: CONTRIBUTOR` for maintainers with private org membership
  (observed on PR #31342, reviewer bryangingechen).
- Hunk-alignment algorithm for patch-level Δ (§3.6) — pick during implementation, validate in audit.
- Finding budget default (10) — revisit once gold comment-count distribution is known.
- Whether CI-at-`h₀` can be reconstructed reliably enough to include in input (deferred, §6).
- Stratum rubric (V1–V4 operational tests) — Step 3's deliverable; this spec only reserves the
  fields.
