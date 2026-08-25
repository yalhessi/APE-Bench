# Step 2 Audit: `pr_review_v2` Generated Data

Audit date: 2026-06-12

Primary artifact audited:
`inputs/pr_review_v2/mathlib_pr_review_v2_2025-09-01_to_2025-12-31_20260612071625.jsonl`

This is the Step 2 gate from `docs/research/step-by-step.md`: inspect whether the
round-1 extraction is trustworthy enough to support the rubric/matcher work.

> **UPDATE (same day):** a re-scan after the title/description fixes and an `h₀`
> bug fix supersedes parts of this gate — see **“Re-scan after fixes”** at the
> end of this document for the revised decision. The scan is now automated:
> `python -m src.datasets.pr_review_v2.audit_scan <records.jsonl> --bundles data/pr_review_v2/cache/bundles`.

## Gate Decision (original extract)

**Do not proceed to benchmark/rubric work on this extract as-is.**

The data is close enough to be useful for debugging the pipeline, but it has
several systematic issues that would leak outcome information into inputs and
make D3/linkage scores hard to interpret. The biggest problems are:

1. `CHANGES_REQUESTED` is never used in this slice, so GitHub review state does
   not distinguish blocking from non-blocking feedback.
2. PR titles in `input.title` are post-review Bors-rewritten titles.
3. PR descriptions are current bodies, not rolled back text.
4. `h0` and `h1` still depend on REST commit dates rather than push order.
5. Process commands are still present as gold comments.
6. Delta/linkage currently treats rewritten hunks as separate added/removed
   objects, which is too noisy for per-pair D3.

Recommended path: fix the input leakage and process-comment filtering first,
then rerun Step 2 on a fresh extract. Until GraphQL push-ordering is implemented,
report results separately for the `review_commit_id` subset. Also separate
process verdict from blockingness: Mathlib uses comments, labels, Bors
delegation, and follow-up pushes rather than GitHub's `CHANGES_REQUESTED` state.

## Aggregate Sanity Checks

Rows: 137 PRs from PR #33047 to #33440.

Funnel summary:

- Kept: 137
- Skipped: 63
- Largest skip reason: `size:diff_lines` = 39
- Other notable skips: `review_signal:no_reviewer_events` = 9,
  `h0:no_commit_before_t1` = 3

Population:

- Verdicts: 99 `APPROVED`, 38 `COMMENT_ONLY`, 0 `CHANGES_REQUESTED`
- Raw cached GitHub review states: 280 `COMMENTED`, 58 `APPROVED`,
  0 `CHANGES_REQUESTED`
- Merged slice: 131 merged, 6 closed-unmerged
- Author-is-maintainer: 101 true, 36 false
- Multi-reviewer: 12 true, 125 false
- `h0_resolution`: 99 `review_commit_id`, 38 `pushed_before_t1`

Gold comments and linkage:

- Total comments: 203
- Comment kinds: 129 inline, 49 issue comments, 25 review bodies
- Link confidence: 87 `resolved_thread`, 6 `line_overlap`, 110 `none`
- Delta records: 57 PRs have nonempty `delta_near`; 214 near hunks total
- Delta ops in `delta_near`: 117 `added_in_revision`, 97 `removed_in_revision`

Input hygiene red flags:

- 131/137 input titles start with `[Merged by Bors]`
- 131/131 merged-slice rows have `gold.outcome.merged_at = null`
- 126/137 descriptions contain the PR-template HTML comment
- 132/137 descriptions contain the Gitpod badge
- 11 rows are tagged `description_maybe_post_edited = true`

Process/comment red flags:

- 31 comments contain process-command patterns such as `bors`,
  `maintainer merge`, `maintainer delegate`, or `!bench`
- 9 comments contain `maintainer delegate`
- 2 comments are bare `!bench`
- 22 PRs are `APPROVED` with gold comments but empty `delta_near`

Push-order risk:

- 38 rows use `pushed_before_t1`
- 16 rows have `force_push_before_t1 = true`
- 5 rows combine `pushed_before_t1` with `force_push_before_t1`

## Main Issues

### 1. No Blockingness Signal: `CHANGES_REQUESTED` Is Unused

This is the largest task-definition problem in the current extract. The dataset
has no `CHANGES_REQUESTED` records because Mathlib reviewers in this slice do
not use GitHub's formal changes-requested state. They usually leave ordinary
comments, sometimes approve/delegate in the same first round, and expect the
author to apply changes before merging.

Observed evidence:

- Emitted verdicts: 99 `APPROVED`, 38 `COMMENT_ONLY`, 0 `CHANGES_REQUESTED`.
- Raw cached review states: 280 `COMMENTED`, 58 `APPROVED`,
  0 `CHANGES_REQUESTED`.
- Many apparently blocking comments appear under `APPROVED`, for example
  `bors d+`/delegation comments that still ask the author to fix CI, add a
  docstring, revert a change, or adjust code before merging.
- Many `COMMENT_ONLY` rows have nonempty `delta_near`, so they do represent
  author revisions even though there was no formal changes-requested state.

Consequence:

- D1 as currently written is not measuring "approve vs request changes"; it is
  mostly measuring "did someone issue an approval/delegation signal in the first
  window?"
- D2 and D3 need a separate blocking/non-blocking annotation independent of
  GitHub review state.

Fix:

- Rename or reinterpret `gold.verdict` as a process verdict:
  `APPROVED | COMMENT_ONLY | CHANGES_REQUESTED`, with the caveat that
  `CHANGES_REQUESTED` may be empty for Mathlib.
- Add a separate PR-level field such as `gold.requires_revision` or
  `gold.round1_blockingness` with values like
  `merge_ready | revision_required | discussion_only | unknown`.
- Add comment-level `severity` earlier than Step 3, at least as a hand-audited
  field for the 30-record gate sample. The existing nullable `severity` slot is
  the right place for this.
- Use multiple signals for a preliminary blocking heuristic:
  author push after `t1`, nonempty `delta_near`, `awaiting-author` label,
  `bors r-`, CI-failure text, imperative reviewer wording, and whether the PR
  later receives an approval/delegation signal only after edits.
- Do not headline any metric that relies on formal `CHANGES_REQUESTED` for this
  dataset.

### 2. Outcome Leakage Through Titles

Every merged PR in the extract has a current Bors-rewritten title such as
`[Merged by Bors] - feat(...)`. This leaks that the PR eventually merged, and
often leaks the process status into the model-visible input.

The cause is that the collector searches closed PRs because Mathlib's Bors flow
does not populate GitHub's ordinary merged signal, then `derive.py` uses the
current REST PR title both to infer merged status and to populate `input.title`.
See `src/datasets/pr_review_v2/fetch.py` lines 75-78 and
`src/datasets/pr_review_v2/derive.py` lines 247 and 395-397.

Fix:

- Strip `[Merged by Bors] - ` from `input.title` at minimum.
- Prefer the original PR title before the Bors rewrite if timeline/event data can
  recover it.
- Keep Bors-derived merged status only in `gold.outcome` / `validation`, not in
  input.

### 3. Description Rollback Is Not Implemented

The spec says the description should be rolled back to the last pre-`t1`
revision when recoverable. The implementation only fetches edit timestamps, not
the edited content, and then writes the current PR body to `input.description`.

This affects at least the 11 rows tagged `description_maybe_post_edited = true`:
PRs 33367, 33333, 33310, 33287, 33207, 33203, 33183, 33151, 33111, 33067, and
33047.

The implementation site is `src/datasets/pr_review_v2/fetch.py` lines 119-123
and `src/datasets/pr_review_v2/derive.py` lines 371-378 and 395-398.

Fix:

- Fetch edit content if GraphQL exposes it for PR bodies, or keep current bodies
  but exclude/tag post-edited rows from input-based benchmark runs.
- Also remove the visible PR template boilerplate from the task input; it appears
  in 126/137 records and is not useful review context.

### 4. `h0`/`h1` Still Have Push-Ordering Risk

For `pushed_before_t1`, `h0` is selected from REST commit committer dates. The
spec calls this out as a known failure mode because rebases/force-pushes can
carry old commit dates. The code still uses this fallback for 38 records and
also derives `t_push`, `h1`, and `final_head` from the same sorted commit-date
list.

The relevant implementation is `src/datasets/pr_review_v2/derive.py` lines
274-346.

Observed risk:

- 38/137 rows use `pushed_before_t1`.
- 16/137 rows have a force-push before `t1`.
- 5 rows have both fallback `h0` and a force-push before `t1`.

Fix:

- Implement GraphQL timeline push ordering for `PullRequestCommit` and
  `HeadRefForcePushedEvent`.
- Until then, either restrict headline audits to the 99 `review_commit_id` rows
  or slice fallback rows separately.

### 5. Process Commands Are Still Gold Comments

The spec says command-only approvals/delegations should set verdict/process
signals but contribute no finding. The current substantive filter removes some
Bors/merge tokens, but not `maintainer delegate` or `!bench`, and when a body
contains both feedback and a process command the raw command remains inside the
gold comment text.

Examples:

- PR 33421: `Thanks! maintainer delegate`
- PR 33266: bare `!bench`
- PR 33135: bare `!bench`
- PR 33305: `bors r- bors d+` plus a CI failure note

The relevant implementation is `src/datasets/pr_review_v2/derive.py` lines
263-268, 304-315, and 317-336.

Fix:

- Extend trivial/process stripping to `maintainer delegate`, `maintainer merge?`,
  `bors r-`, and `!bench`.
- Store process commands in `validation.process_signals`.
- Store cleaned human feedback in `gold.comments.body`, or add both `raw_body`
  and `body`.
- Drop pure process comments from `F1`.

### 6. Delta/Linkage Is Too Coarse For Per-Pair D3

The delta extractor identifies hunks by hashing changed `+`/`-` lines and then
compares hunk sets. For a rewrite, this often emits both an `added_in_revision`
hunk and a `removed_in_revision` hunk for one logical edit. Linked comments can
therefore point to both the before and after hunk IDs.

The relevant implementation is `src/datasets/pr_review_v2/delta.py` lines
37-45 and 101-113. Linkage then uses line overlap against these delta hunks at
lines 149-163.

This is acceptable as a rough PR-level "patch changed here" signal, but it is
not reliable enough yet for D3 per-pair scoring.

Examples:

- PR 33419 has one naming comment but two linked hunks: one added and one
  removed version of the same logical rename.
- PR 33421 has several comments linked to added/removed pairs.
- Overall, only 93/203 comments link to any hunk, and 110/203 are unlinked.

Fix:

- Treat replacement as one logical `modified_in_revision` hunk when old/new
  spans overlap.
- Keep `added`/`removed` as internal detail but score D3 at file/span level.
- For Step 3, use high-confidence resolved-thread links only as qualitative
  examples, not as a frozen per-pair metric.

### 7. Near/Total Delta Anomalies Need Manual Review

Two records are especially suspicious:

- PR 33048: `delta_near = 9`, `delta_total = 0`; `final_head_sha` equals `h0`
  even though there was an intervening `h1`.
- PR 33111: `delta_near = 0`, `delta_total = 10`; the first author push appears
  not to change the patch, but later changes do.

The second case may be a legitimate "late total-only change"; the first is a
strong sign that date-sorted commit history or force-push handling can produce
non-monotone head sequences.

Fix:

- Add an audit assertion for `h0 -> h1 -> final_head` ordering from timeline
  events rather than commit dates.
- Surface `delta_near_nonempty_total_empty` and
  `delta_near_empty_total_nonempty` counts in the funnel/report.

### 8. Outcome Fields Are Confusing For Bors-Merged PRs

All 131 merged-slice rows have `gold.outcome.merged_at = null` and use
`closed_at` as the only endpoint timestamp. This is probably expected for
Mathlib's Bors flow, but the schema name `merged_at` is misleading if left null
for every primary-slice record.

Fix:

- Add `effective_merged_at`, populated from Bors close/merge signal time.
- Keep GitHub `merged_at` separately as `github_merged_at`.
- Add `merge_mechanism: bors | github_merge | unknown`.

## 30-Record Audit Sample

The sample intentionally includes all six closed-unmerged rows, several
`pushed_before_t1` rows, the largest delta rows, approval-with-comment/no-delta
rows, and representative clean approvals.

| PR | Verdict | Comments | Delta near/total | h0 source | Merged | Notes |
|---:|---|---:|---:|---|---|---|
| 33296 | COMMENT_ONLY | 2 | 0/0 | pushed_before_t1 | False |  |
| 33200 | COMMENT_ONLY | 5 | 0/0 | pushed_before_t1 | False |  |
| 33149 | COMMENT_ONLY | 5 | 0/0 | review_commit_id | False |  |
| 33107 | COMMENT_ONLY | 2 | 0/0 | pushed_before_t1 | False |  |
| 33104 | COMMENT_ONLY | 2 | 0/0 | review_commit_id | False |  |
| 33056 | COMMENT_ONLY | 1 | 0/0 | pushed_before_t1 | False |  |
| 33432 | APPROVED | 0 | 0/0 | pushed_before_t1 | True | Bors title |
| 33413 | APPROVED | 2 | 0/0 | pushed_before_t1 | True | Bors title |
| 33385 | APPROVED | 0 | 0/0 | pushed_before_t1 | True | Bors title |
| 33370 | APPROVED | 0 | 0/0 | pushed_before_t1 | True | force-push before t1, Bors title |
| 33421 | APPROVED | 4 | 10/10 | review_commit_id | True | Bors title, process in gold |
| 33207 | COMMENT_ONLY | 1 | 10/10 | review_commit_id | True | Bors title, post-edited desc |
| 33316 | COMMENT_ONLY | 1 | 9/11 | review_commit_id | True | Bors title |
| 33048 | COMMENT_ONLY | 5 | 9/0 | review_commit_id | True | Bors title, near/total anomaly |
| 33302 | COMMENT_ONLY | 1 | 8/9 | pushed_before_t1 | True | Bors title |
| 33079 | APPROVED | 2 | 8/8 | review_commit_id | True | Bors title |
| 33057 | APPROVED | 1 | 8/8 | pushed_before_t1 | True | Bors title |
| 33047 | COMMENT_ONLY | 1 | 7/53 | pushed_before_t1 | True | Bors title, post-edited desc |
| 33362 | COMMENT_ONLY | 1 | 6/6 | review_commit_id | True | Bors title |
| 33337 | APPROVED | 2 | 6/6 | review_commit_id | True | Bors title |
| 33418 | APPROVED | 1 | 0/0 | review_commit_id | True | Bors title |
| 33400 | APPROVED | 3 | 0/0 | review_commit_id | True | Bors title |
| 33376 | APPROVED | 2 | 0/0 | review_commit_id | True | Bors title |
| 33357 | APPROVED | 1 | 0/0 | pushed_before_t1 | True | Bors title |
| 33340 | APPROVED | 1 | 0/0 | pushed_before_t1 | True | Bors title |
| 33440 | APPROVED | 0 | 0/0 | review_commit_id | True | Bors title |
| 33395 | APPROVED | 1 | 2/2 | review_commit_id | True | Bors title |
| 33345 | APPROVED | 2 | 2/2 | review_commit_id | True | Bors title, process in gold |
| 33283 | COMMENT_ONLY | 3 | 2/2 | review_commit_id | True | Bors title, process in gold |
| 33245 | APPROVED | 1 | 0/0 | pushed_before_t1 | True | Bors title |

## What Is Still Usable

- The rough first-round comment collection is useful for developing the Step 3
  rubric, especially inline comments with `resolved_thread` linkage.
- The approval-control slice exists and is valuable, but its model-visible title
  must be cleaned first.
- PR-level `delta_near`/`delta_total` is useful for exploratory analysis after
  suspicious ordering cases are filtered.

## Recommended Next Extraction Pass

1. Clean `input.title` and `input.description`.
2. Add process-command cleaning/drop rules before gold comment emission.
3. Implement timeline-based push ordering or slice to `review_commit_id`.
4. Add anomaly counters to the funnel:
   `bors_title_in_input`, `post_edited_description`, `process_comment_in_gold`,
   `force_push_before_t1`, `near_nonempty_total_empty`,
   `near_empty_total_nonempty`.
5. Re-emit the same date window with a larger `max_prs` if the target remains
   150-300 kept records; this run kept only 137.
6. Redo Step 2 on the fixed extract before freezing any matcher or rubric stats.

---

## Re-scan after fixes (2026-06-12, extract `20260612102315`)

Re-scanned artifact:
`inputs/pr_review_v2/mathlib_pr_review_v2_2025-09-01_to_2025-12-31_20260612102315.jsonl`
(138 rows — one more than the original because the cache-driven `derive` stage
also picks up smoke-test PR #31342, which the search-driven run's newest-200
cutoff excluded). Scanner: `src/datasets/pr_review_v2/audit_scan.py`, which
reproduces every counter in this document plus an h₀→h₁→final ordering
cross-check against cached commit history.

### Resolved since the original audit

- **Issue #2 (title leakage): fixed.** `bors_title_in_input` 131 → **0**
  (`clean_input_title` strips the Bors outcome prefix).
- **Issue #3 (description boilerplate): fixed.** Template HTML comments
  126 → **0**, Gitpod badges 132 → **0** (`clean_input_description`).
  New observation: **27/138 descriptions are now empty** — the author wrote
  nothing beyond the template. Legitimate input, but worth a
  `empty_description` slice tag when running benchmarks.
- **Issue #7 (near/total anomalies): both explained, one was a real bug.**
  - **PR 33048 was an `h₀`-resolution bug, now fixed.** GitHub *repositions*
    inline review comments as the PR evolves: the comment's `commit_id` is
    updated to its current attachment commit, while `original_commit_id`
    preserves the review-time commit. Event normalization preferred
    `commit_id`, so `h₀` resolved to the final head. Fix in `derive.py`
    (prefer `original_commit_id`), regression test added. After the fix,
    33048 reads h₀ `7b0e1268` → h₁ `ec90d0d4` → final `aa1d2958`,
    Δ-near/total 10/13, and all 5 of its comments link.
  - **PR 33111 is legitimate.** The first post-`t₁` push didn't change the
    effective patch (Δ₁=∅); the substantive changes came three days later in
    response to a round-2 comment, landing in Δ* by design. Keep
    `near_empty_total_nonempty` as an expected, slice-able category.
  - The fix also improved the rest of the extract: head-ordering violations
    1 → **0**, PRs with nonempty Δ-near 57 → **60**, near hunks 214 → 230,
    `resolved_thread` links 87 → **101**, unlinked comments 110 → **95**
    (other PRs' inline `commit_id`s had drifted too).

### Still open (unchanged by this pass)

- **Issue #1 (no blockingness signal)** — still 0 `CHANGES_REQUESTED` anywhere;
  verdicts 100 APPROVED / 38 COMMENT_ONLY. This remains the main
  task-definition fix: separate process verdict from `requires_revision`.
- **Issue #4 (push-ordering risk)** — 39 `pushed_before_t1` rows,
  16 force-push-before-t₁, 5 overlapping. Needs GraphQL timeline push
  ordering, or slice headline stats to the 99 `review_commit_id` rows.
- **Issue #5 (process commands in gold)** — still 31 comments across 31 PRs
  (`maintainer delegate`, `!bench`, `bors r-` etc. not yet stripped/dropped).
- **Issue #6 (delta coarseness)** — rewrites still emit added/removed pairs
  (125 added / 105 removed near ops); per-pair D3 stays deferred to the
  resolved-thread subset until merged into `modified_in_revision`.
- **Issue #8 (`merged_at` null for Bors merges)** — schema rename pending.

### Revised gate decision

**Proceed to Step 3 (rubric drafting) on this extract, with two scoping
rules.** The h₀/Δ/linkage machinery now passes the checks this audit was
gating on: input leakage is closed, head ordering is consistent, both delta
anomalies are accounted for, and half the comment population (101/204
resolved-thread links, plus 8 line-overlap) has outcome-validated linkage.

Scoping rules until the open issues above are fixed:
1. Rubric/matcher work should treat `gold.verdict` as a *process* signal only
   (issue #1) and use the 31 process-command comments as a stratum-rubric
   edge case (they are process, not findings — issue #5).
2. Any D3 or Δ-based statistic should be reported on the `review_commit_id`
   slice (99 rows) as primary, with the `pushed_before_t1` slice (39 rows)
   shown separately (issue #4).
