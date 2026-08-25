# Review overlay — the PR diff, with what the reviewer did to it

## Why this exists

Seeing what the v4 reviewer did to one PR meant hand-joining eight JSONL files by ID. The
pipeline is wide — the 16 medium PRs decompose into 508 change targets, 508 modifications,
2,253 scheduled investigations and 2,253 capability assessments, which yield 42
opportunities and 39 findings — and a table of those totals hides the only interesting
thing about them: *where* the attrition sits relative to the diff. The system is scheduled
at nearly every gold site and says the wrong thing there. That is a spatial claim, so it
wants a spatial picture.

The design follows `../overtone/overtone/agent/blueprint.py`, which solved the same problem
for proof search: one Python module emitting one self-contained HTML file per run, no React,
no CDN, no server, no build step. Overtone's spine is a proof DAG scrubbed over draft
iterations. Ours is the PR's diff scrubbed over pipeline depth — every medium episode is
`round1`, so there is no time axis to scrub, and depth of processing is the axis that
carries the information.

## Building one

```
./ape/bin/python -m src.datasets.pr_review_v4.review_overlay \
  --release   inputs/pr_review_v4/releases/dev-medium-0.3.0 \
  --treatment inputs/pr_review_v4/treatments/systematic-opportunities-v3-medium \
  --executor  results/pr_review_v4/audits/phase10-medium-executor-v5 \
  --run       results/pr_review_v4/runs/dev-medium-smoke4-rep1 \
  --condition results/pr_review_v4/conditions/medium-checker-only-v2 \
  --out       results/overlays/pr_review_v4/medium-v1
```

Those are the defaults for `--release`, `--treatment` and `--executor`, so a bare invocation
gives the deterministic arm over all 16 medium PRs. `--run` and `--condition` are repeatable.
Add `--pr 33098` to restrict, `--judge <dir>` to fold in `matches.jsonl`, `--no-gold` to omit
gold entirely. Output is `pr-<n>.html` per PR, `index.html`, and `bundle.json` (the joined
data, useful on its own).

**Output must live outside `results/pr_review_v4/`.** `verify_frozen` hashes every file under
`inputs/pr_review_v4` and `results/pr_review_v4` and fails on any it has not sealed, so
rendered pages there turn each render into an integrity-gate failure. The default is
`results/overlays/pr_review_v4/latest` and `--out` refuses a frozen root outright.

**Use the v3 treatment, not v2.** The medium executor ledger keys on v3's investigation IDs
(2,253/2,253 overlap); against v2's schedule the join is empty, which renders every checker
cell as unscheduled and looks exactly like the arm never ran.

## Reading the page

The page opens on **the diff**. That is the anchor: which files changed, how big they are,
where in each file the edits landed, and what the harness scheduled at each one. The matrix
is a sibling view behind the `matrix view` toggle, better for scanning 119 sites at once.

### The rail — which files, and where

One strip per changed file, scaled to the **true reviewed line count**, with hunk positions
marked above and change-target spans below. PR 33421 reads at a glance: fifteen files,
eleven of them a single tick at the very top (an import bump) and one, `Round.lean`, carrying
ten targets through the middle.

The true line count is why the builder reconstructs sources at all. It reads the base file
from `data/code_execute/repos/mathlib4/workspaces/<base_sha>/` (falling back to
`data/pr_review_v4/cache/base_files/`) and replays the patch with
`change_graph.apply_file_patch` — 85/85 medium files reconstruct byte-exact against
`ChangeFileCoverage.reviewed_source_sha256`. Guessing extent from hunk or entity spans
instead runs a median 0.41 and 0.56 of true length, and 0.01 on an import-only edit, so
every import bump would be drawn in the middle of a file it actually sits at the top of.
When no source resolves the file is marked `context: unavailable` and its targets render
without file context — the build never fails on a missing workspace.

### The diff — windowed, and honest about it

Each file shows its hunks with 12 lines of real context, plus every target's full entity
span, and counts what it skips: `⋮ 173 unchanged lines`. Shown plus elided always equals the
file's line count, which a test asserts. Only genuinely added lines are tinted — marking a
hunk's *extent* instead of its body painted 23 unchanged lines of PR 33098's module doc as
additions.

Each change target gets a header row in the flow carrying its name, its lifecycle and
subject kind, how many methods fired, the work-unit band it belongs to, and **the same
thirteen cells as its matrix row** — same states, same tokens, same click target. A test
asserts the two views never disagree.

### What the harness scheduled, and why

Selecting a target explains its routing: *"This is added public theorem, changing name,
proof, statement_or_type. The scheduler matches that against each method's declared
applicability — four membership tests, no model — giving 7 of 7 methods here."* Every method
that did not fire names the predicate that rejected it.

This is recomputed from `investigations.method_applies` rather than read off a stored
verdict, and asserted equal to `investigation_tasks.jsonl` for all 508 targets. The shape it
exposes: methods-per-target is `{0:19, 1:43, 2:75, 3:90, 5:77, 6:23, 7:181}` over 45 distinct
routing profiles — and the 19 targets nothing looks at are exactly the `removed` ones, because
`removed` appears in no method's `lifecycles`.

**Related changes** are drawn as a fan from the selected target, dashed where the edge leaves
the target's work unit. These come from `pr_relations.jsonl` — 1,005 typed, evidence-cited
edges across the medium set, 794 of them cross-call. They are *use-of* edges, not
*because-of*: there is no rename-implication relation in this data and the page must not
imply one.

### What decomposition cost

The header panel states it plainly, because the intuitive claim is wrong. Across the medium
set the scheduled arm spends **4.80M characters over 225 calls** against **456k** for
whole-PR single calls — **10.5× more**, since each call repeats its file's diff and code. PR
33149 is 71.6× on its own: 108 calls for a PR whose entire content is 36.6k characters.

The bounding argument is also weak here: the largest scheduled call is 47.1k characters and
the largest single call would be 106.1k, and **every PR in this corpus fits in one call**. An
earlier framing claimed PR 33149 would be 2.03M characters as one call; that figure came from
concatenating its identical diff blob once per target, which is an artefact of the packer,
not something a single-call harness would send.

So what decomposition buys is **per-target attribution** — 508 targets each with their own
scheduled investigations and terminal state, which one call cannot produce. The page says
that, and claims no cost or context-window win.

### The matrix — every site against every component

Behind `matrix view`: one row per change target, one column per component. Better than the
diff for scanning a 119-site PR in one screen, and the source of the cell vocabulary the
diff pane reuses inline.

**Rows are change targets** — `change:<sha>`, one changed declaration with complete
`base_code` and `reviewed_code` — ordered by file, then by the target's own entity span.
Non-declaration targets (imports, module docs, namespaces, bare commands) are labelled
`‹module doc›` rather than by filename, because PR 33098 has nine of them in one file.

**Columns are components**, grouped by arm: the seven checker methods, the generalist, the
four focused specs, and the file-scoped reviewer. Columns for arms that were not run render
**present but empty**. That is deliberate: an omitted column is indistinguishable from an arm
that found nothing.

**Cell colour is how far that component got at that site**, on one ordered ladder. The
deepest state reached wins within a cell.

| state | meaning | source |
|---|---|---|
| not scheduled here | the method does not apply to this target | no `InvestigationTask` |
| scheduled, no implementation | enumerated, nothing could execute it | `terminal_stage=capability_assessed` |
| operator could not run | tried, unavailable | `terminal_stage=operator_unavailable` |
| **checked, found nothing** | ran and came back empty | `operator_completed` + `checked_no_opportunity`, with its `basis` |
| named by a claim anchored elsewhere | scope spillover from a multi-site claim | non-primary `change_id` of a candidate or finding |
| claimed, evidence refuted it | a claim whose evidence packet came back `contradicted` | `EvidencePacket.status` |
| transformation constructed | an opportunity | `terminal_stage=transformation_constructed` |
| claim emitted | a `CandidateClaim` | run's `candidates.jsonl` |
| published finding | survived merge and adjudication | condition's `findings.jsonl` |

Two of these earn their place by having been wrong once:

- **"checked, found nothing" must never collapse into "not scheduled".** "We did not look"
  and "we looked and found nothing" are different results and only the second is evidence
  about the reviewer. For a model arm this is recovered from the run's own release: work unit
  IDs move between releases (`dev-medium-0.1.0` and `0.3.0` share none of their 225) while
  change IDs do not, so the builder resolves `run_plan.json → dataset_manifest_path` to get
  the work-unit-to-change-id map. When that fails, the run is listed under
  `unresolved_run_coverage` and its columns show claims only — never silence dressed up as
  absence.
- **"named by a claim anchored elsewhere" is not a claim.** Findings are multi-site: PR
  33057's build-failure finding names eight targets, PR 33294's five findings name 72 further
  targets between them. Colouring those as claims reported "claim emitted 72" on a PR with
  zero candidates.

**The funnel ribbon is the scrubber.** Clicking a stage dims every cell below that stage's
floor, so the picture collapses to "what survived this far". Arrow keys scrub. The counts
come straight from the ledger — for PR 33098: 26 sites → 129 scheduled → 31 ran → 8
opportunities → 13 candidates → 5 findings → 3 published issues.

**The legend filters.** Click a swatch to mute that state.

**The right panel** shows, for the selected site: the diff at that site (the two complete
regions, not the hunk fragments), the inventory chips from `ModificationRecord`
(`component_deltas`: name / statement_or_type / proof / attributes / …), and one block per
component that touched it, deepest first — including the silent ones, greyed, with their
`basis`.

**`explain mode`** fades the unscheduled and unsupported detail and hides the debug lines
(IDs, assessments, operator runs), leaving the shape of the result.

**`gold`** is off by default and adds a right-hand column plus, in the panel, each
maintainer ask with its `resolution_criteria` set directly against what the system said at
the same site. That juxtaposition is the acceptability-gap figure.

### Gold is a physical boundary, not a CSS one

`--no-gold` does not hide gold; the builder never opens `gold/`, `Overlay.gold` is `None`,
the page carries `const GOLD=null`, and the toggle button is not emitted. A test asserts no
path containing `/gold/` is read in that mode. A page also carries only its *own* PR's
obligations, so one page is never a side channel for another's.

Location matching reuses `evaluate._covered`'s semantics — set intersection of change IDs —
and is funnel-only. It says a prediction landed on the right target, never that it asked for
the right thing. `issue_match` from the semantic judge (`--judge`) is the real verdict.
Obligations whose targets are not in the change graph appear under "asks with no site in the
change graph" rather than silently leaving the denominator.

## Cross-checking a build

The join is the part that can be wrong. Every headline number on the page has a source of
truth to check it against:

| page | source of truth |
|---|---|
| 508 sites, 2,253 investigations | `treatments/…-v3-medium/derived/schedule_report.json` |
| stage counts, drop reasons | `audits/phase10-medium-executor-v5/report.json` — `{capability_assessed: 1720, operator_completed: 379, operator_unavailable: 112, transformation_constructed: 42}` |
| 39 findings, 37 published | `conditions/medium-checker-only-v2/condition_report.json` |
| 19 published issues | `digest_findings` over those findings (39 findings → 21 issues; one aggregates `per_pattern`) |
| 43 obligations / 40 included | `releases/dev-medium-0.3.0/gold/` |

A mismatch is a join bug, not a display bug.

## Where the code is

- `src/datasets/pr_review_v4/review_overlay.py` — the join. Pure data; produces `PRBundle`s and
  `bundle.json`. Reuses `io.load_jsonl`, `paths.py` roots, `schema.py` models,
  `digest.digest_findings`, and `evaluate._covered`'s semantics.
- `src/datasets/pr_review_v4/review_overlay_html.py` — the page. `PALETTE` is the single source of
  colour and every per-state rule is generated from it. The matrix is an HTML table, not SVG:
  no graphviz dependency, text stays selectable and ctrl-F works.
- `tests/datasets/test_pr_review_v4_overlay.py` — ladder monotonicity, multi-site
  attribution, the gold barrier, and degradation.

Page weight runs 62 KB (PR 33438, 2 sites) to 1.24 MB (PR 33149, 108 sites). A page that
fails to render is caught and reported in `failed`; it never takes the rest of the build with
it.
