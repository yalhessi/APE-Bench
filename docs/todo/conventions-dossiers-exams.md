# Convention dossiers and exams: does a model understand a convention before it applies one?

**Status** — open, **narrowed by the adversarial round (2026-10-08, branch `conventions-dossiers`;
`docs/research/conventions-dossiers-review-2026-10.md`)**. Nothing built, nothing run but counting.
All four reviewers say narrow. The question to answer first is not whether a dossier teaches better
than a sentence. It is whether anything carries DP's gain once the asks are no longer given. The
remaining order is "After the round" below. The original first slice (head conventions, sentence
against dossier) is rejected with its evidence.

The user asked for the round (2026-10-08): *"We should still run the adversarial review and try to
steelman the idea as much as possible before we commit to a lot of running and replicating with
various models."*

**The user (2026-10-08).** *"A question that needs answering in this project, now that conventions play
such a fundamental role, is 1) how do we get models to strictly adhere to conventions, 2) what are the
consequences of this. The models still don't have a deep understanding of these conventions, so they
can't adhere to them strictly. This is partially a limitation of using a text representation of these
conventions. A small sentence gives a sense of the convention, just like the description of an MCP tool
or skill is helpful, but it isn't the full picture. The model should develop an understanding of each
convention before it uses it, because otherwise it risks using it incorrectly."* On method: *"the tests
we come up with are too uninformative at the moment because we keep trying to take safe evidence-based
steps, but we're still not exploring the unexplored and not learning about the overall picture of the
search space."*

**Motivating measurements.**
- **A convention reaches the reviewer as one sentence.** A census entry is a `principle` with
  `rationale` tags and a `form` (`results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json`,
  438 entries). For example, P003: "A lemma whose left-hand side applies a definition to a canonical
  argument and whose right-hand side is simpler is tagged `@[simp]`."
- **Knowing the right convention at the right place was not enough** (stage G,
  `conventions-ceiling-probe.md`).
  - A candidate carried the right entry at the ask's place for 21 asks. The reviewer reached 9 of
    them, as unbriefed Claude does; the exact brief reached 17.
  - Its notes show it verified and overrode: "`gcongr` failed so dropped"; "Mathlib does not
    require these"; a primed private helper "acceptable".
- **Only the exact conventions move a reviewer.** In-census reach:
  - Claude +0.26 / +0.28, gpt-5.5 +0.22, Qwen3.5 +0.05;
  - 25 conventions picked from the diff by a blind selector: +0.03 (stage F).
- **Strict application files far more than maintainers ask.**
  - Maintainers raise a convention at 5% or less of the places its situation occurs (stage H; five
    decision designs, AUC 0.56-0.64).
  - Detector facts are asked for at 4-9% of the places flagged.
  - Under the disposition paragraph gpt-5.5 filed 13 of 14 unasked facts (`docs/dead-ends.md`,
    "Convention detectors as a recall lever").
- **The tail.** The census's 1,833 asks fall into 399 conventions: the top 10 hold 20%, the top 50
  half, and 286 have three asks or fewer (`docs/dead-ends.md`).
- **Stage D is running** (branch `conventions-ds41`; README Stage D). DP gives each exact convention two
  maintainer asks from other PRs and states that they outrank the reviewer's judgement. If DP moves the
  reviewer, the decision to file is the lever. If it does not, understanding is a candidate. **Read it
  before designing.**

**The idea** (sketched 2026-10-08; to be attacked, not built).
1. **Study.** Build one dossier per convention, offline and once, by an agent working from evidence
   rather than the sentence. The dossier holds:
   - every census ask under the convention: comment, hunk, and what was merged;
   - situations where the convention applied and nobody asked;
   - conforming code;
   - prevalence in the Mathlib corpus at base;
   - a decision procedure: when it applies, the fix, and how to check it (compile where possible).
2. **Exam.** Before a dossier is used, test model plus dossier on held-out census cases for that
   convention, in three groups scored separately:
   - asked: flag the place and propose the merged fix;
   - conforming: stay silent;
   - unasked departures: these are ambiguous, and are read as volume, not as error.

   Understanding becomes a measured property of each convention. A failed exam says what was
   misunderstood.
3. **Use.** The reviewer sees a one-line index and opens a dossier when it judges one relevant, as
   with skills. Authority is calibrated by the exam: a passed convention is applied strictly, a failed
   one is filed as a question or advisory.
4. **Consequences of strict adherence**, measured without gold:
   - volume per PR;
   - validity: is the departure real, and does the fix compile;
   - **revealed preference**: did Mathlib later change the flagged code to conform (git history
     after the merge)? Untried. It also bears on stage H's open question of whether unasked
     departures would be welcome.
5. **The map.** A matrix of conventions (the top 50 and a sample of the tail) against representations
   (sentence; sentence and examples; dossier; dossier and a check), scored by exam on the free local
   model. It shows which conventions a model learns from text, which need examples or execution, and
   which are judgement calls no representation fixes.

**What is new against the record.**
- Stage G wrote a rule with a trigger and a check from four census asks, and never examined it.
- DP gives two examples and a precedence paragraph.
- The norm store (`docs/research/pr-review-v5-principled-design.md` §D2) types maturity from
  prevalence, and was never built.
- Exemplars are on stage F's untried list.

None of these measured whether the model understands a convention before it uses it.

**Known limits, for the review to press.**
- **The tail caps recall.** At most the head's share of asks is reachable, about half for the top 50.
  The 286 thin conventions cannot be examined. The goal is issue recall
  (`docs/dead-ends.md`, detectors entry), so the review must state the most recall this could add.
- Understanding may not be the bottleneck: stage G's overrides look like the decision to file.
- Unasked is not wrong (stage H), so the exam's third group cannot be scored as precision.
- Leakage: dossiers draw only on census PRs (val1000, outside_years), disjoint from every probe and
  evaluation set. DeepSeek-V4.1's training window may cover all of them.
- Not training a model: dossiers and exams are inputs and measurements, not fine-tuning data.

## The adversarial round (2026-10-08): narrow

The record: `docs/research/conventions-dossiers-review-2026-10.md`, with the briefs, the four reports
and the fact sheet in `docs/research/conventions-dossiers-review-2026-10/`.
- **How it ran.** Three attackers (mechanism; measurement; ceiling, cost and record) and a steelman:
  Opus 5.5 subagents, read-only, 563k tokens in all. The primary token's week went from 93% to 94%.
- **What the four agree on.**
  - **As specified, the exam measures itself.**
    - It hands over the convention and the place, where stages F and G show review fails.
    - Its three groups, scored separately, read a push to file as understanding.
    - No exam score can be tied to recall across conventions: 14 probe asks on 7 head entries, power 0.36.
  - **The planned head slice is where examples did nothing.**
    - By entry rank, DX1 / DE1 / DP1 reach 1 / 3 / 3 of 8 on the top 10, 3 / 3 / 7 of 10 on ranks
      11-50, and 1 / 7 / 11 of 16 past rank 100.
    - The head misses are failed checks and search: try-it work for the closer battery.
  - **Understanding is real and separable, but small.**
    - The test that separates it is a claim that the code conforms, made where it does not.
    - It is a quarter to a half of DP1's 16 misses: at most about +0.08 to +0.15 of in-census asks,
      and that is with the asks given.
  - **The assertion carried the gain, not the wording.**
    - At the 10 asks only the exact brief reached, stage G's reviewer, holding the same sentence at
      the same place, filed a different change at 6 (matcher 2: 5).
    - Every delivery that did not assert the convention moved nothing.
  - **"Passed means strict" is the disposition paragraph,** a volume lever.
  - **The map cannot be read cell by cell.**
- **The steelman's strongest form.** Precedent retrieval chooses the conventions in play: the nearest
  census hunks, their conventions delivered with DP's examples and precedence. Dossiers come only for
  the judgement conventions, examined by before/after pairs. Its own limit: every positive result on
  record needed the asks.
- **Found beside it.** 45% of census asks carry a ```` ```suggestion ```` block, an exact before and
  after.
  - Mechanical entries nearly always have one (P017 30/32).
  - The judgement entries where understanding misses sit rarely do (P004 2/43, P063 3/27, P100 2/24).

**What would close it.**
- **Drop the dossier line as a recall lever** (a `docs/dead-ends.md` entry, listing self-study and
  index browsing as untried) if either of these reads as stated in "Start here":
  - step 0: DP − DE ≤ +0.03 over three reps;
  - step 3: AP or RP − DX ≤ +0.05, or a gain that fails the volume guard.
- **Proceed to dossiers (V2), for the judgement conventions at ranks 11-50,** only if step 3 reads
  ≥ +0.10 on both matchers within the guard and step 2 finds ≥ 7 of 22 misses that a richer
  representation could fix.

**Cost.**
- Step 1: CPU only.
- Steps 2 and 3: DeepSeek on `first`, $0, about two to three hours of the 8-GPU node in all.
- Matchers: about 0.5-1M subscription tokens, after the week resets on Friday 2026-10-09 10:00.

## Start here (after the round)

**2026-10-09, the ladder matched blind** (`results/pr_review_v5/probes/conventions-ladder-2026-10-08/`,
Result).
- **The place alone does not carry the asks:** told only that a maintainer asked, the model passes at
  5-6 of 39.
- **With the convention's sentence it passes at 25-29.**
- **DP's gains were already within the bare sentence's reach at the place:** 5-6 of 7.
- **DP's examples lower the judged verdicts:** UX against U is +1 / -5 and +0 / -4.
- **DP's misses read as mixed:** u 4-6, s 3, f 3-5.
- **The understanding hypothesis, as a lever for DeepSeek, finds no support.** What is measured is
  the per-place question: at the place, the bare sentence passes 13 asks that DE's review missed.

**2026-10-09, why the ceiling is not 100%** (`docs/research/ceiling-residual-2026-10.md`). The census
holds the knowledge behind what is missed.
- **What nothing reaches:** 6 of 46 asks, the union of every ceiling session over three models. Five
  are in census, and of the 7 asks outside the census, 6 are reached.
- **Most of the per-session gap is instability and model differences.** A DP session reaches about 25
  of 39, its three-rep union 29, the union over all models 34.
- **The rest is reviewers at the right place asking something else** (golfing, judging on merits,
  applying the convention next door), where the convention's question asked alone gets the change.
- **The smaller causes:** failed checks read as conforming; information outside the packet (a PR's
  history, the library's orientation).

**2026-10-09, a second adversarial round on the user's decompose-and-shrink idea**
(`docs/research/decompose-and-shrink-review-2026-10.md`). The user's two questions were: how to
decompose a PR so that each part needs only a subset of conventions, and whether a correct subset can
be chosen from a partial PR.
- **Q1:** decompose into overlapping lenses, keeping the whole PR in view. These are the declaration,
  family, file and PR lenses `components.py` already builds. Context, emission and demand are the
  limits; places are not. Nothing shows that splitting the reviewer itself adds recall.
- **Q2:** an applicable subset can be chosen, a demanded one cannot, and "sound" with "5-10" cannot
  both hold.
  - Part kind cuts ~400 to 134-234 and leaks 19-25%.
  - Part kind with frequency gets the right entry into the top 10 for 0.36-0.46 of asks in era and
    0.22 out of it. Stage F's Opus selector reached 0.45.
- **What binds is behaviour.** Nobody knows the false-departure rate at unasked places, or whether
  DP's licence survives wrong conventions.
- **Four measurements, none decided:** M1, decomposition and syntactic shrink, CPU; M2, a model ranker
  per part, DeepSeek; M3, the bare sentence at unasked places, DeepSeek; M4, DP with decoys, DeepSeek
  plus matchers.

**2026-10-09: the priority is selection.** The user: DP without its examples is not pressing; *"choosing
conventions without the asks is the most important question to address at this point."*
- The oracle ladder ran (step 2, `results/pr_review_v5/probes/conventions-ladder-2026-10-08/`). It is
  unmatched, and its unblinded look is provisional.
- What that look says: at the place, the bare sentence already writes 6 of DP's 7 gains, and DP's
  examples sometimes narrowed the model's reading. So the gain was not understanding, and the open
  lever is choosing which conventions are in play.

The full table, with each step's cost, threshold and recall ceiling, is §6 of the review.

0. **Stage D's three-rep result: read 2026-10-08, continue** (`conventions-ds41`, Result 7, `18f7c3c1`).
   - DP − DE = +0.197 / +0.179 and DE − DX = +0.222 / +0.248 over three reps, findings a PR +0.62.
   - On the head 10, DP adds 2 of 24 cells, and five of its 10 stable misses are head asks.
   - The rule as written before the read:
   - If DP − DE ≤ +0.03 over three reps, examples and precedence do not move DeepSeek even with the
     asks given, and the line stops.
   - Sort DP's stable misses by the separating test in the review's §2.3.
1. **V1, retrieval as the selector, CPU only, now.**
   - For each probe PR, rank census entries by the nearest census hunks to the PR's own hunks. The
     embedding is MiniLM, the precedent index's model, which is on disk.
   - Score whether each in-census ask's entry is in its PR's top 5.
   - Two baselines: the census's global top 5, and stage F's selector's first five.
   - Pre-register it in a README beside its script before it runs.
2. **The oracle ladder at ask level** (DeepSeek, under an hour of server time).
   - Each of DE's and DP's misses gets three forms: "does it conform?", "a maintainer asked for this
     here", and the same with DP's examples; plus a hunk-only floor.
   - It diagnoses where misses come from. In-sample, so it is not a gain.
3. **The recall test without asks** (DeepSeek, about 1.5 hours of the 8-GPU node).
   - AP: stage F's blind selections, each entry with DP's two examples, under DP's precedence
     paragraph. Or RP: step 1's retrieved entries, if step 1 passes.
   - The ten stage C PRs, three reps, one seal with DX1-3 and Claude's X1/X2 as anchors.
   - **≥ +0.10 over DX on both matchers, with findings a PR at most DX + 3.0:** a lever exists without
     the asks.
   - **≤ +0.05:** drop.
   - Recall ceiling: +0.30 in theory on the top-50 asks; +0.09 optimistic; about +0.02 on the record.
4. **Dossiers, only if 3 moves.**
   - Self-written by DeepSeek from census asks on half the census PRs, examined by pair ordering on
     the other half.
   - For the judgement conventions at ranks 11-50, never the head 10.

## The original start (done or replaced 2026-10-08)

1. **Read** stage D's result (`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md`,
   Stage D, on branch `conventions-ds41` until it is merged), and stages C, F, G and H in the same README.
   Then read:
   - the census `results.md` and `reader_rubric_census_v1.md`;
   - `docs/dead-ends.md` (convention detectors; statute injection);
   - `docs/plans/2026-10-06-generation-without-suppression.md` (on `generation-suppression`);
   - `docs/todo/conventions-nature.md`.
2. **Adversarial review and steelman, before any run.** Three independent reviewers attack the idea,
   and one steelmans it into its strongest variants. The variants include:
   - a dossier the model writes itself, by studying census cases, and is then examined on;
   - retrieval of the nearest census examples at review time;
   - executable checks.

   The questions to put to the round:
   - Is understanding separable from the decision to file?
   - Does the exam predict review recall, or only itself?
   - Is the tail cap fatal?
   - What is the cheapest experiment that could falsify it?

   Keep the rejected proposals with their evidence.
3. **Only then, the first slice** (*replaced by the round: it is aimed at the head, where DP did
   nothing; see the review's §7*), pre-registered with its threshold:
   - 5-10 head conventions with the most census asks;
   - the sentence against a dossier;
   - exam scores on held-out census cases;
   - DeepSeek on `first`;
   - no review runs.
