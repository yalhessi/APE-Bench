# The conventions ceiling probe: does a reviewer briefed on the conventions reach more asks?

**Status** — open, drafted 2026-10-04. **Picked up the same day, local model first** at the user's
direction ("testing the local model first before any paid API runs"): stage L, the self-hosted
Qwen3.5-397B under contract v2 with and without the exact section, is pre-registered in
`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md`. It tests the machinery and
one untried local-unlock design; it is not Claude's ceiling, and the Claude step below is unchanged.

**Done so far (2026-10-04).**
- **The first step is done: 39 of the 46 asks are in census (85%)**, 25 of 30 on validation and 14
  of 16 post-cutoff; the two readers chose the same entry on all 38 they both assigned. The exact
  briefs hold 28 distinct entries, 0 to 5 a PR (`briefs_exact.json` there). Census coverage does not
  bound the ceiling.
- **Stage L read +0.051 on both matchers** (LB 4/117, LE 10/117 on in-census asks, three reps a
  condition): the bottom edge of its "inconclusive" band, far from its +0.15. The section makes the
  local model's reach repeatable (36822's attribute asks go from 1 of 3 reps to 3 of 3) and opens
  one new ask of 39. Where it missed, its notes show the convention checked and the code passed, or
  never raised. Nothing follows for Claude.
- **The Claude exact step read +0.256 and +0.282: a good direction, by the rule below.** Run at the
  user's direction as one briefed session on the ten PRs where unbriefed Claude missed an in-census
  ask (stage C in the same README, pre-registered before its sessions; about one window, not the
  todo's 28 sessions). Per-session reach on the 39 in-census asks: 0.49 / 0.46 unbriefed, 0.74
  briefed; on all asks 0.48 against 0.70 / 0.73. Nothing an unbriefed session reached was lost,
  out-of-census asks did not move, and an unbriefed control through the briefed sessions' route
  read exactly as X (0.29 against 0.29 on two PRs). Ten in-census asks stay missed: six are design or judgement calls
  the convention does not carry (three of them PR-level asks for motivation), two the right
  convention at a neighbouring place.
- **The ceiling holds for gpt-5.5 (2026-10-05, stage M, `cross_model.md` there).** One briefed run a set at
  high effort through ELM, against the unbriefed gpt-5.5 runs on disk: in-census reach 0.19 to 0.41,
  +0.222 on both matchers; nine asks gained and none lost. With Claude (+0.26 / +0.28) and the local
  397B (+0.05), the gain holds for both strong reviewers and not for the floor model.
- **The floor (the ladder's "applicable" level) read +0.026: the gain needed the asks' pinpointing.**
  A blind selector picked 25 census entries a PR from the diff alone (stage F, same README); they
  hold the entry behind 22 of the 33 in-census asks. The same reviewer briefed with them reaches
  0.49 / 0.46 of in-census asks against 0.46 / 0.44 unbriefed and 0.74 / 0.72 with the exact brief,
  all under one seal. With the right sentence in the brief it reaches 12 of 22 asks where the exact
  brief reaches 18 and no brief 10.5; it files 82 findings against 52.5 and aims worse. "Common" was
  not run (the top 50 hold the entry of 16 of 33); "all" was not run.
- **So: only exact moves.** By this todo's own reading, the work is in pinpointing which convention
  the code departs from at the reviewing point, not in supplying the conventions. Untried: a
  pinpointing pass with tools that outputs candidate departures at named places for the reviewer to
  vet; the selector's `where` delivered; exemplars; a second session a PR.
- **Stage G, pre-registered 2026-10-05 at the user's direction: conventions as guarded rules,
  pinpointed.** Each of 52 entries (the 26 behind the ten PRs' asks, pooled, and 26 decoys from stage
  F's blind selections) is written as a rule with a trigger and a check, from census asks only; a
  blind pass a PR lists where each trigger holds; the reviewer gets the place, the convention and the
  check. Its leak is the pooled rule set, so it is a best case for the delivery, not a floor. Rule:
  G − X within 0.05 of E − X recovers the ceiling; `≤ +0.05` does not carry it. Same README.
- **Stage G read +0.000 on both matchers (2026-10-06): pinpointed rules move nothing.** A candidate
  carried the right entry for 28 of 33 asks, at the ask's place for 21; the reviewer reaches 9 of
  those 21, as unbriefed Claude does, where the exact brief reaches 17. Its notes show it verified
  and overrode (`gcongr` failed so dropped; repeated `{D : ℤ}`: "Mathlib does not require
  these"; a primed private helper: "acceptable"). So the gap is the decision to file, not
  knowledge or location: the exact brief's short list asserts that maintainers ask for these.
  Untried: the exact entries under G's verify-and-drop lead (isolates the lead); an asserting lead
  that files a question where a check fails. README, Result 5.
- **Stage H (2026-10-06): no decision design picks the places maintainers raise.** Five designs over one
  record (rule, census asks, negatives mined on 16 census PRs, rate), on stage G's 149 places for ten
  rules (12 at an ask): every model design raised 2-5, none at an ask; the rate design 2 of 12; the
  pass's own order 7 of 12. Ranked by probability, AUC 0.56-0.64, the record's old artifact-only
  level. Maintainers raise at most 5% of the places a rule's situation is flagged. Untried: whether
  the unasked departures would be welcome (adjudication), and reviewer, PR-theme and file-local
  signals. README, Result 6; designs in `docs/plans/2026-10-06-convention-decision-designs.md`.
- **Picked up on DeepSeek-V4.1-Flash, 2026-10-08, at the user's direction** ("a good opportunity
  to replicate those results and try one alternate design of how conventions get used: models still
  don't seem to understand how we want them to use conventions, and that the examples of conventions
  should count as stronger evidence than their internal judgement"). The self-hosted DeepSeek reaches
  8, 6, 9 of 23 on the dev held-out 12 with its thinking kept (Opus 5.5: 7, 7), free on `first`
  (CLAUDE.md; `results/pr_review_v5/probes/local-ds41-2026-10-06/`). Two steps, both pre-registered
  before any session runs:
  1. **Replicate stage L on DeepSeek:** X against the exact brief, on both sets, three reps a
     condition, matched as stage L was. Read against Qwen +0.05, gpt-5.5 +0.22 and Claude
     +0.26 / +0.28: does a strong local model carry the ceiling?
  2. **One alternate design of how the conventions are used,** where the listed conventions and their
     examples outrank the reviewer's own judgement of the code. Stage G's notes show the reviewer
     verifying and then overriding; stage W's disposition paragraph (branch `generation-suppression`,
     unmerged; `docs/plans/2026-10-06-generation-without-suppression.md` there) removed the guess about
     maintainers and moved gpt-5.5 by +0.189 out of sample. Build on it: either the disposition
     paragraph itself on DeepSeek, or a variant that states precedence outright. Say which, and
     why, against that record before running.
  - **Generation is free; matching is not run as a paid call.** The server and the `cli run` reps
    are GPU time on `first`. Run them as one unattended Slurm gate (server, the probes, every rep,
    release the node; `run_ds41_keepthink.sh` is the pattern), never a session waiting for hours.
    The two blind matchers run as the probe harness runs them.
  - **The node may be busy.** On 2026-10-08 gg676's jobs held 5 of `first`'s 8 GPUs for 7.5-12 h,
    and the server needs all 8. Queue the gate and prepare while it waits.
- **Stage D, pre-registered 2026-10-08 before any session** (README, "Stage D"): DX, DE and DP on both
  sets, three reps each, 18 runs on `local_deepseek_v4.1_flash` (reasoning high, thinking kept), `cli
  plan` passing for every one. **The alternate design is P, not the disposition paragraph as it
  stands:** the exact section with up to two census asks beneath each convention (stage G's writers'
  first two, chosen by seed) and a closing paragraph saying the conventions and examples outrank the
  reviewer's judgement of the code, with taste, local practice and imperfect fit ruled out as grounds
  beside the disposition paragraph's uptake grounds, and a question where the change cannot be made.
  Why: the exact brief's misses on record are mostly the reviewer's judgement of the code or of fit,
  which the disposition paragraph leaves alone, and examples are the record's untried delivery.
  Rules: DE − DX at the todo's +0.15 / +0.05; DP − DE `≥ +0.10` moves, `≤ +0.03` does not, with
  stage W's +3.0 findings-a-PR volume guard. One Slurm gate runs it (`run_stage_d_gate.sh`).
**Cost** — the exact-conventions step is about 1.5 subscription windows; the full ladder about 6
more; two small reader runs to label the asks; optionally about $15 of `gpt_5.2`.

**The user (2026-10-04).** *"If conventions are a good direction to explore, we would expect that
being briefed on the conventions (exact conventions at a given reviewing point, applicable
conventions, common conventions, all conventions) should have a positive effect on the models
judgements. We have many baselines without conventions and without sufficiently specific
conventions. At this point, we need to assess a ceiling/best case scenario of the conventions work
now that we have a solid summaries of Mathlib conventions."*

**Motivating measurements.**
- **The census is built** (`results/pr_review_v5/adjudications/conventions-census-v1/results.md`).
  Reader A's codebook holds 438 principles, written from 2,102 asks on PRs disjoint from every
  evaluation set. The top 50 cover 55% of principled asks.
- **The residual wall is largely convention knowledge.** 25 of the 67 asks no reviewer reaches on
  three sets are convention or mechanism knowledge (`develop`, `docs/plans/2026-10-03-after-structure.md`).
- **The record's briefs never held specific conventions.** The "statute" injection (null at N=115)
  and precedent priming (13 against 11) delivered written guidance or past comments, never the
  conventions that apply to the PR under review (`docs/dead-ends.md`). None of them is a ceiling.

**The question.** At best, how much does knowing the conventions move a reviewer toward the
maintainers? The probe briefs the strongest reviewer with conventions at four levels of
specificity and compares it with the unbriefed sessions already on disk. If even the exact
conventions move nothing, briefing has a low ceiling and the conventions work should be pointed
elsewhere. If they move reach, the ladder says how specific a delivery must be.

## Sets and baseline (no new baseline sessions)

| set | asks | PRs with asks | controls | Claude's window |
|---|---|---|---|---|
| validation small12 (`configs/probe_sets/val_small12.yaml`) | 30 | 8 | 3 | inside |
| post-cutoff (`configs/probe_sets/postcutoff_2026_07_08_v1.yaml`) | 16 | 6 | 4 | after |

Both are PR-disjoint from every PR the census read (checked 2026-10-04). The baseline is each
set's Claude X1 and X2: `claude-opus-5-5`, the X brief, the pass-0 model and the arms' tools, at
per-session reach 0.48 / 0.50 (validation) and 0.47 (post-cutoff). Where a carried `gpt_5.2` run
(Grc) exists on a set, it is the second family's baseline.

## The four briefs

Each is the X brief plus one section, "Conventions the maintainers hold". Nothing else in the
packet changes. Every section is drawn from reader A's codebook (`reader_A/codebook.json`, 438
entries at `2bb3063a`), as sentences only, with no location.

| brief | the section holds | who builds it |
|---|---|---|
| **exact** (the ceiling) | the entries behind this PR's maintainer asks | two readers label the 46 asks against the codebook, assign-only (an ask with no entry is marked out of census); the brief is the union of their entries |
| **applicable** | entries that apply to this PR's changed code, at most 25 | a Claude selector reading the diff, `pr.md` and the codebook, never the asks |
| **common** | the 50 most-used entries | fixed, the same for every PR |
| **all** | all 438 entries (about 16k tokens) | fixed |

The exact brief is built from the asks. It deliberately breaks the harness rule that nothing a
reviewer reads is written by a step that has seen feedback, and that is what makes it a ceiling.
Two leaks come with it, and both are stated as limits rather than fixed: the number of entries
hints at the number of asks, and controls get no exact brief, so exact runs on the 14 ask PRs only.
The other three briefs keep the rule.

## Running it

- **Reviewers:** Claude Opus 5.5 subagents through the probe harness (`cli probe packets` with the
  brief variant; `cli probe prompts`), two sessions per PR per brief, under the harness's packet,
  scratch and audit rules. Optionally `gpt_5.2` carried on the exact brief, one rep per set, where
  a Grc baseline exists.
- **Order:** exact first, on both sets. It is the ceiling: the other briefs hold the exact entries
  diluted among others, or not at all. So the ladder runs only if exact clears the bar below, on the
  ask PRs, in one batch.
- **Matching:** one seal per step and set, holding the new sessions together with X1 and X2. Two
  blind matchers use the set's existing rubric (`construction-demo-2026-09-29/matcher_rubric.md`,
  generalised), with labels shuffled and condition cues redacted, followed by the usual audit.

## Reading rule, fixed before any session runs

The measure is per-session reach on the **in-census asks** (asks with at least one codebook entry),
on each matcher, pooled over the two sets and reported per set. Asks reached per finding must be no
lower than X's, so that filing more is not read as reaching more.

| exact − X, on both matchers, pooled | reading |
|---|---|
| **≥ +0.15** | **conventions are a good direction**: knowing the right ones moves the reviewer. Run the ladder. |
| **≤ +0.05** | **low ceiling**: even the exact conventions do not change what the reviewer asks. Briefing is not where the conventions work pays off; record it in `docs/dead-ends.md` with the untried deliveries (facts about the PR, detectors, exemplars of each principle's asks). |
| between | inconclusive at this size: read the per-ask transcripts before deciding |

**The ladder, if run.** Applicable within 0.05 of exact means retrieval from the diff is enough.
Only exact moving means the work is in pinpointing which conventions apply at the reviewing point
(point (a) of the census's purpose). Common or all moving as much as exact means the conventions
were simply missing from the brief.

**Also read, not in the rule:**
- out-of-census asks, the within-session control (they should not move);
- for every in-census ask still missed under exact, whether the session's `notes.md` shows it
  considered the convention: known but not filed (the 33337 filing discount), or never connected;
- the applicable selector's recall of the exact entries, a free measurement of retrieval.

## What would close it

The exact step's reading on both sets. Then either the ladder's table, or a dead-ends entry. The
result is recorded here and in the census's `results.md` §7.

## Start here

- **Read:** `results/pr_review_v5/probes/model-gap-val-small12/README.md` and
  `postcutoff-2026-09-29/README.md` (the baselines, packets and matcher setup); `asks.json` and
  `feedback.json` in each (the asks to label); the census `reader_rubric_census_v1.md` (what an entry
  is) and `reader_A/codebook.json`; `src/mathlib_review/analysis/probes.py` on `develop` (the harness).
- **First step (no model spend):** label the 46 asks against the codebook, two readers, assign-only,
  and print each PR's exact brief. If most asks come out of census, the ceiling is bounded before any
  session runs, and that is itself a reading.
