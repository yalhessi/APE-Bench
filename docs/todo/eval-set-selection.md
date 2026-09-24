# Choosing the one evaluation set the next big run is spent on

**Status** — open, 2026-09-24; **surveyed read-only the same day, rulings pending** (branch
`eval-set-selection`; the survey and the seven rulings the draw needs are at the end). A thread of its own:
selection design, then a build that parallelizes in a few hours once the set is settled
**Cost** — the selection design is free; the build is free apart from gold-stage model calls; the run it
exists for is the one big run the budget allows, on roughly 50 PRs
**Motivating example** — every design since August was tuned on the dev set (the 16 medium PRs: the
held-out 12 plus smoke4), so any result there is in-sample, and the unified contract's 3 / 10 on four of them
cannot be told from judge noise (one obligation is 10 pp). The obvious fresh pool, the 46 large-tier PRs no v5
run touched (`eval-unseen-window.md`), is biased too, only differently: it is the residual of the gold-driven
selection that produced the medium tier -- style-heavy (25 of 58 obligations), mostly single-file (median
3.5k-char diff against the held-out 12's 10.4k over 6.5 files), and scored by 19 v2 runs. The user,
2026-09-24: only one ~50-PR run is affordable, so the set must not share the dev set's bias and must not swap
it for another.

## What the selection has to settle

1. **A sampling frame fixed without looking at gold.** The dev set was chosen from the 57 on gold concern
   statistics; any pool chosen by gold, or by where the system does well, inherits a bias. Draw with a seed
   from a defined frame (for example every included first-round episode in one window), stratified only on
   gold-free features: diff size, file count, Mathlib area, author.
2. **The window.** The PR store holds tier-2 data for January 2026 -- 1,046 PRs, 712 included first-round
   episodes over 318 base commits (measured 2026-09-23, read-only funnel run) -- later than anything the
   designs were tuned on, and clean with respect to `work-enumeration` Phase 1's corpus pool (reviewer
   comments before 2025-12-18 on unscored PRs). A December 2025 window is not clean against that pool; the
   v2 window (2025-09 to 2025-12) is exposed.
3. **Clean versus gold-bearing mix.** In the original 138 reviewed PRs, 72 carried an actionable finding and
   66 were clean (`docs/PROJECT-STATUS.md` §2). The natural rate keeps precision measurable through control-PR
   emission; enriching for gold-bearing PRs buys recall power. Decide which, explicitly, with the trade stated.
   *(Survey: that rate does not carry over -- the 138 are fast closers, and January is 17.6% clean on the one
   pre-gold definition, against 36% for the 138.)*
4. **Size.** Cap or stratify by work-unit count so no single PR dominates: on the held-out 12, PR 33149 was
   ~70% of findings and 48% of billed cost. *(Survey: cap on change targets, not units -- findings track
   targets, and a unit count moves with the renderer and the episode id.)*
5. **Gold, the long pole.** No gold pipeline reads the PR store today (the dev gold chain is v2 derive ->
   stratum and actionability labels -> v3 interventions -> the legacy scope and migration stages ->
   codex-assisted decomposition; `eval-unseen-window.md` and the 2026-09-23 survey trace it). The dev gold
   itself is LLM-built (`migration_proposal`, no human sitting). Whatever builds the new gold must not reuse
   labels produced by the systems under test (`.claude/rules/mathlib-review.md`, "A label is not gold").
6. **Buildability must not select.** 26 of the 318 January base commits have built snapshots (a 27th is a stale
   `building` state from 2026-06-03), and 22 of the 26 are APE-Bench merge commits from Jan 6-12, the most
   exposed week of the window; choosing PRs on built bases would bias toward busy and exposed commits. Draw
   first, then build what was drawn (`prebuild --reviewed`, ~2.9 GB and 2.4-16.6 min per episode, only while
   no paid run is live).
7. **The config, chosen with the set.** At the rates measured on 2026-09-23 a 50-PR run bills roughly: lean-
   roster fanout ~$35 (five arms, `configs/pr_review_v5_contract_fanout4_lean.yaml` scaled), lead ~$58, full
   fanout ~$70; judge extra (~$0.006 a pair). The set's size, mix and config trade against each other and
   should be fixed together. *(Survey: these scale small dev means; re-priced on the frame's own sizes below.)*
8. **Pre-registration.** Frame, strata, seed, exclusions (PRs used for development; a reviewed state that
   does not compile -- 33057 round 1 is the example; AI-generated PRs are labelled, not excluded, per the
   2026-09-24 ruling), controls, and the reading rule, frozen with a digest before anyone reads the new gold.

## Start here

- **read:** `docs/todo/eval-unseen-window.md` (one candidate pool and the defects every pool inherits: the
  tool-schema gold leak in `review/base.py`'s `lean_verify_edit` example, the inventory builder's refusal on
  whitespace-only targets, the missing hittability audit); `inputs/pr_review_v4/benchmarks/tiers-v1.json` and
  `docs/research/pr-review-v4-benchmark-tiers.md` (how the tiers were cut); `docs/plans/2026-09-11-pull-request-store.md`
  and `docs/todo/operational-floor.md` §3 (the store, its acceptance report and the one explained mismatch --
  the store floor should be closed before it backs a set); `src/datasets/pull_requests/projections/episodes.py`
  (the funnel); `src/mathlib_review/legacy_pipeline/pilot.py` (`CASE_REGISTRIES`, `CONTROL_SEMANTICS`).
- **run (free):** the funnel in memory over a January 2026 frame, to count included episodes by stratum
  before any rule is fixed -- `ape/bin/python -c "from src.datasets.pull_requests.store import
  PullRequestStore as S; from src.datasets.pull_requests.definitions import load_roster; from
  src.datasets.pull_requests.projections.episodes import project_episodes, eligible_numbers; s=S();
  t2=eligible_numbers(s); jan=[n for n in t2 if str((s.read(n,'pr') or {}).get('created_at',''))[:7]=='2026-01'];
  p=project_episodes(s, roster=load_roster('inputs/pull_requests/rosters/mathlib_roster_2026-09-11.txt'), prs=jan);
  print(len(jan), len(p.episodes), len({e.base_sha for e in p.episodes}), s.content_digest()[:12])"` prints
  `1046 712 318 f2d2beb6af2b` in ~35 s; `ape/bin/python -m src.mathlib_review.review.cli plan --config <new config>
  --run-name <name>` once a release exists (prices it, spends nothing).
- **bounded by:** selection of *findings* stays parked (this is selection of *PRs to evaluate on*, which is
  measurement); `docs/dead-ends.md` "Specialists as the coverage floor" and the no-pruning ruling (no broad
  coverage runs); three reps is the project's floor for a rate, so a single ~50-PR run is read as a level with
  its denominator stated, not as a rate.

## Risk

Any window the store can serve today is Mathlib-in-early-2026: one community at one moment, with its
conventions in flux (`grind`, `toLinearMap_`). A clean draw removes the selection bias, not that one.

## Survey, 2026-09-24 (read-only, nothing spent)

Six readers, an adversarial verifier on each, and a completeness critic. No gold was read for any January
PR: counts only, never comment text. The scripts stayed in that session's scratch; the build step turns
the ones it needs into committed tooling. The corrections above are marked *(Survey: ...)*.

**The frame reproduces.** Store content `f2d2beb6`, roster `mathlib_roster_2026-09-11` (`d7e9ea12`):
1,212 January-created PRs -> pre-gate 1,046 -> **712 included first-round episodes over 318 bases**. The
frozen v2 roster gives 711 / 317, and it moves the reviewed head on 16 more PRs, so 17 episodes differ.
The dev releases used the v2 roster. Nothing created after January has tier 2: February to August hold
8,545 PRs at tier 1 only. February's pre-gate passes 1,001, so collecting it would take about 8k requests.

**January is clean of v2 to v5, not of v1.** Every PR a v2-v5 run touched was created 2025-11-07 to
12-31. All 138 are 2025 PRs: PROJECT-STATUS §2's "2026-01-01 to 2026-03-31" is the name of a v1 file,
and is corrected there. But 34 included January episodes are exposed at gold level through the June-era
v1 sets and the APE-Bench drop (`inputs/ape_bench`, the Jan 6-12 commits). Those pilots' prompts carried
the maintainer diff, and their feedback scans kept reviewer previews. Another 10-12 episodes are
adjacent (depends-on and cross-reference links), and which ones depends on the rule, so the rule must be
mechanical. The model snapshots are dated, `gpt-5.2-2025-12-11` and `gpt-5-mini-2025-08-07`
(`src/ape/llm_clients/config.py:97,113`). Both are before January, but also before dev, so the window
buys no cleanliness against the generator. `elm_gpt_5.2` and `gpt_5.4` are bare aliases.

**A dev-pool bias not recorded before.** v2 fetched `is:closed` PRs sorted by creation, newest first,
and kept 200 (`src/datasets/pr_review_v2/fetch.py:55`). The dev pool is therefore fast closers: median
0.9 d open, maximum 14.2 d. The January frame has median 6.5 d and p90 58.5 d, and 229 of its 712 are
open longer than 14.2 d. Only one control definition exists before gold: no round-1 feedback event and
no later head. On it January is 125 / 712 (17.6%) clean, against 50 / 138 (36%) for the 138.

**Exclusions, as counted.**
- AI-authored: 14 are detectable at fetch time (label 2, commit trailers 6, description disclosures 11,
  14 in the union). Only 9 rest on evidence present at the reviewed head, because the label was applied
  by third parties in March-April 2026.
- Closed without a bors merge: 48. Gold-free data cannot separate these from rejected or superseded
  PRs, and the same predicate would have removed held-out 33149.
- A reviewed state that does not compile cannot be decided before the draw: the store has no CI
  endpoint.
- 712 minus the gold-level exposure minus the 14 AI PRs is **667**; minus the adjacency list, about 656.

**Size: targets, not units.** On the held-out 12, per-PR findings track change targets (Spearman 0.82
at 0.5.0, 0.68 at 0.3.0) and not work units (0.14 and 0.19). This is n = 12, so provisional. Targets do
not depend on the renderer or the episode id; unit counts do, moving by ±1 on 5.5% of PRs when the id
changes. Gold-free targets and units for all 712 come from the local mathlib4 clone in about 2.5 min.
The same method reproduces dev-medium-0.3.0's 225 units, PR for PR.

In the 667, targets are p50 12, p95 80, max 302. The p99 share of the largest PR in a 50-PR draw is:

| Target cap | PRs dropped | p99 largest-PR share |
|---|---|---|
| none | 0 | 24% |
| ≤150 | 8 | 16% |
| ≤100 | 23 | 12% |

**Against dev.** The frame's median diff is 4.9k chars over 2 files, and 38% of its PRs touch one file;
the held-out 12 have 10.4k over 6.5. There are 121 authors: the top one holds 6.2%, the top five 23.7%.
There are 32 primary areas, and four of them hold 48%. A simple random 50 puts ≥4 PRs from one author in
86% of draws. An author cap of 3 binds in 87% of draws and displaces 2.4 PRs on average.

**Yield of a 50-PR draw.**
- Natural rate: median 9 structural controls (5-95%: 5-14). Zero emissions on 9 controls bounds the rate
  only at about 30%. Expect about 40-60 eligible obligations, on v2's conversion rates, so low
  confidence.
- Enriched to gold-bearing: about 70-90 obligations.

**Cost, re-priced on the frame's own sizes** (the figures in item 7 scale small dev means):

| Shape | 50-PR cost | Wall clock |
|---|---|---|
| Lead | ~$26 at renderer /14, ~$35 at /12 | 1.2-2.4 h |
| Lean fanout | ~$38-50 | -- |
| Full fanout | ~$70 at /14, ~$90 at /12 | 4-14 h |

The lean roster's own config disowns use off the four PRs it was chosen on
(`configs/pr_review_v5_contract_fanout4_lean.yaml:6-12`). The judge adds about $1-2.5. No paid run is
live: the untracked `pr5_F_fanout_heldout12_v2_rep1` stalled on 2026-09-14 at 106 of 1,409.

**Build, measured.** A draw needs about 44 unbuilt bases. Their recorded build time is a mean of
1,534 s and a median of 1,005 s, and `build.py --num_processes` runs them in parallel. Then about 50
reviewed overlays at a median of 232 s, run one after another. 3.2 TB is free. Six January bases are
absent from the local clone.

**Blockers not in the items above.**
- Release:
  - No CLI wraps `write_episode_release`.
  - `validate_release` refuses store sources (`src/mathlib_review/release/validate.py:88-93`).
  - `verify_frozen` hashes `data/pull_requests/manifest.json`, while a store release records the store
    content digest.
  - `hydrate_change_sources` defaults into a cache that five frozen manifests hash.
  - Base-mode `prebuild` rejects v5 configs.
  - The whitespace-only inventory refusal hits 6 of the 712.
  - `graph_id` depends on whether the base text came from a workspace or the blob cache, so the graphs
    must be frozen once.
- Gold:
  - Every stage after episodes reads the v2 bundle shape.
  - The stratum pass was one Claude session and has no code.
  - The dev gold used the systems under test: i5 ran on `gpt_5.2` (the generator), actionability on
    `gpt_5_mini` (the judge).
  - 0 judgments are human-confirmed.
  - Hittability is one global dev file, and an obligation absent from it counts as hittable.
  - 275 of 475 next-head compares are missing.
  - Estimate: 16-24 h of code, a 3-7 h human sitting, under $20 of model spend.
- Tests:
  - `tests/datasets/test_pull_requests_definitions.py:223` pins `scored_pr_numbers() == 138`.
  - `tests/datasets/test_pull_requests_cutoffs.py` sweeps every release against a legacy-seeded store.
  - `tests/datasets/test_prompt_contamination.py` sweeps every release's gold and **prints** what it
    matches, so every suite run would read unread gold until the test has a blind mode.
- Model inputs:
  - 68 of the 712 titles were renamed after review started, and the new title reaches the model as
    `pr_title`. The review-time title can be rebuilt from timeline `renamed` events.
  - The precedent corpus ends 2025-12-31, while January retrieval cutoffs fall a median of 18.8 d later
    (126 more than 28 d later). That handicaps the arms granted `precedent_search` in a way dev never
    was.

**Hygiene while the set is open.** None of the following may be read about frame PRs by a design
session:
- `data/pull_requests/projections/corpus/reviewer_view.jsonl` holds 3,475 reviewer rows on 481 of the
  712, and nothing excludes them until a release lists those PRs.
- The Zulip store references 174 of the 712.
- `naming-from-statement`'s planned rename testbed (the 2026-05 tree) contains renames that January PRs
  made.

### The rulings the draw needs (user)

1. **Mix.** Natural rate (fully gold-free; about 9 controls and 40-60 obligations), or oversampling on a
   gold correlate with known weights. The correlates are the round-1 feedback count and post-review
   commits, which separate 87% from 7% gold-bearing on v2.
2. **Closed-unmerged.** Keep them with a disclosed sub-count, or exclude them and accept that the rule
   would have removed 33149.
3. **AI-authored.** Judge on evidence available at fetch time (14 PRs) or at review time (9).
4. **Size and concentration.** A target cap (≤150, ≤100 or none), and author and base caps.
5. **Roster.** Dated (correct as of collection) or v2 (comparable with dev).
6. **Frame.** January alone, or collect February's tier 2 first.
7. **Gold.** Who sits the human confirmation; which model builds the gold (not `gpt_5.2` or
   `gpt_5_mini`); and whether it is built before the run.

### The user's rulings, 2026-09-24

- **Accepted:** 1 (natural rate), 2 (keep closed-unmerged, with a disclosed count), 4 (a target cap plus
  author and base caps -- the cap is now to be re-checked against AI PRs, which run larger), 5 (dated roster).
- **3, overruled: AI-generated PRs are kept, labelled, and filterable, never excluded.** The system is
  ultimately for reviewing AI-generated PRs. They are the maintainers' pain point: frequent, and at times
  much larger. Handling them may later need new features, such as splitting a big PR.
- **6, overruled: a long span of dates, December 2025 included.** *"You are interpreting leakage too
  strongly. We will construct a proper test set that we have not used for development, but since we are
  not training a model, worrying about leakage too much isn't productive at this stage."* The only
  exclusion is PR-level: PRs used for development, by a mechanical rule. Window-level gates are
  withdrawn: the Phase 1 corpus pool, the v1-era adjacency list, the precedent-corpus lag and model
  snapshot dates. A breadth argument backs this too: *"the signal is inherently sparse and looking at a
  very long span of dates is much more helpful for the development of our system than sticking too
  closely to looking at a limited set of PRs."*
- **7: not yet ruled.**

What still binds: the test set is sealed from development once drawn, so the hygiene list above now
applies to the drawn PRs, not to whole windows. Biases that are not leakage stay disclosed: outcome
censoring (closed by the listing walk), the funnel's final-state size gates, and the fast-closer shape
of the dev pool.

## Long-span measurements, 2026-09-24 (read-only, nothing spent)

Four measurers, after the rulings. The scripts are in that session's scratch.

**The span, month by month.**
- The listing walk is complete from 2024-03, and PRs still open at the walk exceed 10% only from 2026-04
  (12.0%, then 18.9%, 19.2%, 36.2%, 40.2%). So a span ending at **2026-03** keeps censoring at about
  8%, the Dec-Feb level.
- The funnel includes 70.8% of pre-gate passes in Dec and 68.1% in Jan. Estimated fresh included
  episodes: about 15,400 over 2024-03..2026-03, and about 6,800 over 2025-06..2026-03.
- The roster covers early 2024: roster members make 95.8% of 2024-H1 decisions.
- **Defect:** `leanprover-community-bot-assistant` passes `is_bot` (`definitions.py:49-62`). It is the
  only decider on 163 pre-gate passes in 2024-03..2025-07, up to 44 a month in 2025-02..06. It also
  authored dev bundle PR 33350, so a fix may move a frozen dev-raw funnel file; check with `verify_frozen`.

**Dev-used, as a union: 427 PRs** (per source in the survey scratch's `dev_used.json`).
- **232** were run on, or sit in a frozen release, tier or the v2 bundle cache.
- **195** were only collected: 142 in the June v1 AI dataset (`data/mathlib_pr_review_all_ai*`; 2 of
  its PRs were run on and are in the 232), and 53 in the upstream APE-Bench drop outside the
  proof_pr_review sets.
- The 142 are 137 of the 362 AI-flagged pre-gate passes in 2026-02..04.

**AI-generated PRs.**
- The label `LLM-generated` is on 809 PRs, the earliest created 2025-06-15. It is applied later by
  third parties (all 11 in Dec-Jan on or after 2026-03-16), and is the only authorship label in the
  85-label vocabulary.
- A frozen disclosure regex over title and description (strict form: 2.5-5% false positives on n = 40)
  unions with the label to give AI shares of about 5% in Dec-Jan, 9% in Feb-Mar, 15% in April, and
  11-22% after.
- Copilot `Co-authored-by` trailers from accepted review suggestions are AI in review, not authorship
  (10 PRs in Dec-Jan).
- On all 2,059 Dec-Jan tier-2 PRs, 113 are AI-detected, and 59 of those are one author.
- The funnel's upper size gates remove **38%** of the AI PRs that pass the rest of the funnel, against
  5% of other PRs.
- 22 of the 26 over-gate AI PRs are mechanical sweeps; 15 are one `@[expose]`-removal series. The
  large AI *feature* PRs number about four, all unmerged, and three have unusable size data.
- Inside the gates AI PRs are not larger, so a <=100-target cap drops **0** included AI PRs.
- At the natural rate a 50-PR draw holds about 1.5 AI PRs (Dec-Jan) and about 3 (2025-06..2026-03).
  No gate setting gives an AI reading; only a separately weighted stratum does.

**Draw, then collect.**
- The funnel decides per PR: a random 300-PR subset reproduces the full Dec-Jan run exactly.
- Tier 2 costs about 8.2 requests and 3 s a PR, so 100 candidates take about 5 minutes. The whole
  span would take about 163k requests, or 33 h.
- `collect.py` has no explicit-PR-list option. A `--prs FILE` flag (a `select_prs` beside
  `slice_prs`) is about ten lines plus a test.
- Size is not known before tier 2, so size caps are skip rules applied in seed order, with
  replacement. Month, author, `t-*` area labels (79% coverage) and the AI label are available before
  tier 2.

**Tooling on old bases.**
- Every workspace ever built sits on a base from 2025-11-21 or later, after Mathlib moved to the
  module system (2025-11-19, `6a54a80825`). About 64% of the frame's PRs predate that.
- Known breakages before it:
  - `canonical_api.py:322` passes `-Dexperimental.module=true` unconditionally, which a toolchain
    without the option rejects. Every proposal would silently read "did not compile".
  - `#align` lines (until 2024-07-19) each become a change-graph entity, which inflates targets.
  - Before v4.20 the `.ilean` key format may make exposure reach read 0 silently.
  - The cache backend was Azure until 2025-08-15, then a hardcoded Cloudflare window until
    2025-09-08, which no build here has used.
  - `build.py` parses `--build_timeout` and never applies it, so a cache miss becomes an unbounded full
    compile.
  - A 50-PR draw over the full span needs about 27 toolchains, about 19 of them not installed.
- Pilot bases: `2a0739561acd` (2024-03-01, v4.6.0; the worst case) and `6ea68a87c1a3` (2025-06-01,
  v4.20.0-rc5; its toolchain is installed).

**Deferred, not pursued here: large AI PRs as their own case set.** The user expects large AI PRs to
need new features, such as splitting a big PR. The motivating numbers are above: 38% of AI PRs over
the gate against 5% of others, and about four large feature PRs, all unmerged. Before any of them can
be an episode, they need a reviewed-head compare fetch, full file contents where GitHub omitted the
patch (34481), and a check of 32976's 1,287-file diff.
