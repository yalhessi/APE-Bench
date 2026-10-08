# Convention dossiers and exams: does a model understand a convention before it applies one?

**Status** — open, 2026-10-08, **for a fresh session**. Nothing built, nothing run. **The first step is
an adversarial review and a steelman, before any run** (the user, 2026-10-08: *"We should still run the
adversarial review and try to steelman the idea as much as possible before we commit to a lot of
running and replicating with various models."*).

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

**What would close it.**
- The adversarial round's verdict: proceed, narrow, or drop, with the rejected proposals kept.
- If it proceeds, the first slice's pre-registered reading: does a dossier raise exam scores over the
  sentence on the head conventions?
- Drop if it does not, or if the review shows the tail cap leaves too little recall to pursue.
  Either way the reading goes here and, if dropped, into `docs/dead-ends.md`.

**Cost.** The review costs subagent rounds on the primary subscription. Its seven-day window stood at
91% on 2026-10-08 and resets Friday 2026-10-09 10:00, so check it first. The first slice is GPU time on
`first` (CLAUDE.md, the self-hosted DeepSeek), and $0.

## Start here

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
3. **Only then, the first slice**, pre-registered with its threshold:
   - 5-10 head conventions with the most census asks;
   - the sentence against a dossier;
   - exam scores on held-out census cases;
   - DeepSeek on `first`;
   - no review runs.
