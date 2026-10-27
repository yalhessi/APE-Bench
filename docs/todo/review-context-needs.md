# What a reviewer needs to know, and how to collect it

**Status:** open, 2026-09-25, **for a fresh session**. It is its own thread: context and evidence
for the arms, not how the arms are divided.

**Draft follow-up, 2026-10-23:** [review knowledge transfer across the long tail](../plans/2026-10-23-review-knowledge-transfer.md)
proposes a shared method for using independently sourced conditional reasons to guide review
investigations across concerns. Its immediate work is four worked choices and one controlled Task
recipe, distinguishing the mechanism from earlier precedent/example treatments. A later first
pilot is staged at two PRs; this drafting work authorizes no model campaign or collector catalogue.

**Next experiment, 2026-10-24:** the
[reusable-review-knowledge plan](../plans/2026-10-24-reusable-review-knowledge.md) follows the
[historical synthesis](../research/knowledge-transfer-experiment-synthesis-2026-10-23.md) and the
completed pilot's null historical-recovery result. Revised after review, it compares ordinary
review with compact and full knowledge banks acquired from the same eligible earlier sources.
Either resource can earn a fresh test; the fuller version must justify its added context over
a qualifying compact version. The first deliverable is bounded source/target selection and a
costed Task recipe; source acquisition and the 54 final reviews remain user-run. This is the
active next plan; the October 23 draft above is historical.

**Results follow-up, 2026-10-27:** the
[updated synthesis and next question](../research/review-harness-next-question-2026-10-27.md)
reviews the completed bank comparison and the subsequent 72-session focused-application
probe on their topic branches. Neither bank reached a primary concern. Focus exposed
working alternatives in two concern families, followed by decisions to decline them;
the automation question tested registration rather than the requested proof change.
The recommended next investigation fixes a technically checked generalization and
tests the grounds for suggesting or retaining it against explicit, feasible contrary
cases. This supersedes the launch recommendation above; it does not register a new
experiment or complete the pending usefulness evaluation.

**Cost:** the next plan budgets source acquisition/checks and 54 final reviews, with a maximum
of 266M processed tokens including twelve source checks, bounded repairs, smokes and matching.
The provisional 45–95M ordinary-work estimate and human reading allowances must be replaced by
a target-specific estimate before launch. The original scoping work below is free to read from
existing transcripts and val1000's labelled asks.

**The user (2026-09-25):**

> *"Even if we can't show progress in reviewing, narrow down the information that could be
> included in the brief or context in order to achieve better reviewing, and how the information
> can be collected. The naming tool helped us a bit there but I suspect the information/context we
> need is deeper than simple counting."*

## Motivating examples, from the facet-brief probe

Source: `results/pr_review_v5/probes/facet-brief-2026-09-25/`, the reviewers' `notes.md`.

**Where a reviewer said information was missing:** 13 stated drops or hesitations across 10 runs.

| kind | cases | examples |
|---|---|---|
| execution | 6 | "I could not confirm a shorter proof without compiling"; imports it "could not show … unused without compiling"; defeq robustness it "could not verify" |
| structure of the repository | 2 | "I had no import graph tool"; "nothing else uses `𝔸ᶠ[K]`" took a grep |
| demand | 2 | "I could not show a user needs it", which dropped a generalisation and a unified `normalized_smul` |
| conventions deeper than a count | 2 | two naming patterns with "no clean count separating them"; minor doc points dropped for lack of a count |

**What the gains used.** The probe's largest gain, the central `ConvexSpace` design ask, came from
recognising a design precedent:
- the monad-algebra form `FiniteProbability R M → M`;
- the `PMF` API as the template for what a new notion owes;
- the `Kernel.comp` against `compProd` naming;
- `stdSimplex` documented as "the free convex space".

None of these is a count. They were reached by grep plus the model's own knowledge of Mathlib.
That is retrieval by *concept* and *design role*, which no current tool offers.

**What the losses cost.** The facet reviewer dropped the two proof-golf asks on the control PR, and
other proof ideas, because it could not compile.

**Relation to the record:**
- `naming_norm` answers one counting question (`naming-from-statement.md`: the leading token only).
- `evidence-tiers-and-traces.md`: no v5 path produces `repository_measurement`.
- The facet relabel (`review-work-structure-2026-09.md` §7.8): the warrant an ask needs is set by
  its reference and object together, at 85%. That gives each cell the *kind* of evidence it needs,
  not how to get it.

**Added from probe rounds 2-3 (2026-09-25,** `facet-brief-probe-2026-09.md`):
- **Two information kinds no tool supplies:**
  - **Other open PRs.** "This looks to be a duplicate of #36915", and "declare that this PR depends
    on that one". It is deterministic from the PR store: PRs open at the review time that touch the
    same files or declarations.
  - **The description's links.** "The links in your description don't support your point."
- **Compile, used as a probe,** verified design points: a `#check` exposed a universe restriction,
  a weaker typeclass was tried, unused imports were dropped. It did not raise reach.
- **Precedent search, Zulip and `naming_norm` rarely carried a finding's evidence:** 0-11% of
  findings.

## What to find out first

1. **The information each kind of ask rests on.**
   - For a sample of val1000 round-1 asks, stratified by (reference, object) cell, record what a
     maintainer had to know to make the ask:
     - an execution fact;
     - a repository structure fact (imports, instances, dependencies, where things live);
     - a usage or demand fact;
     - a convention conditioned on shape;
     - a design precedent (an analogous construction or API);
     - a stated preference or policy (review history, Zulip, style guide);
     - the PR's own context.
   - Two readers, pre-registered, as the relabel was.
2. **Which of those the current tools can supply.** The tools are `declaration_search`,
   `content_search`, `precedent_search`, `zulip_search`, `naming_norm` and `lean_verify_edit`. For
   each, and for each information kind, answer can / partly / cannot.
3. **For each gap, the cheapest collector,** in this order:
   - deterministic from the Lean environment: the import graph, the instance graph, declaration
     dependencies and uses, `#check`/elaboration probes, `exact?`/`apply?` at base;
   - from the corpus: past review comments on analogous code, library notes, Zulip;
   - model-built: a design-precedent index over structures and classes by role.

**What would close it:** a table of information kinds against cells, with counts from the sample,
and against tools (can / partly / cannot). Plus a ranked list of collectors, each with the cells and
the ask count it would serve. The top one or two should then be built and tried in a probe of the
`facet-brief-probe` shape, with its reading rule written first.

**Risk:** designing collectors for the information the probe's five PRs happened to need. The
sample in step 1 is the guard: it is drawn from 1,833 asks, not from five PRs.
