# Which departures would a maintainer raise? Decision designs over one convention record (plan, 2026-10-06)

**Status** — plan, written on `conventions-nature` after stage G of the ceiling probe. Its first
test is stage H (`results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md`).

## Why

The ceiling probe's three stages (README, Results 3-5) say the reviewer has the conventions and
lacks the maintainers' choice among them. With the exact conventions it reaches 0.74 of in-census
asks; with 25 picked from the diff, 0.49; with rules pinpointed at their place and a check, 0.46,
the same as no brief. On the ten probe PRs the blind pinpointer flagged 78 places where reading
alone shows a departure, and maintainers asked at 9. So a convention needs a demand side: where it
is broken, how often a maintainer asks.

The user (2026-10-06): *"It seems like knowing negatives is helpful. It seems like recording examples
of conventions and nudging the agent to retrieve examples of how a convention is applied is also
useful so we minimize model-specific judgement and thresholds. We should first consider multiple
designs, maintain them in parallel and test them on a small number of rules/PRs."*

## One record, several decisions

Every design reads the same convention record and differs only in how it decides. Kept in parallel
so that a result says which ingredient carries the decision, not which bundle won.

**The record, per convention** (all from census PRs, which are disjoint from every evaluation set):
- **the rule**: trigger, preferred form, check and its kind, exception (stage G's `rules.json`);
- **positives**: census asks filed under it, the maintainer's comment and the code;
- **negatives**: places a blind pinpointer flags under it on census PRs where no maintainer asked
  in round 1, with their code;
- **a rate**: census asks over places flagged, an index of how often maintainers raise it when its
  situation occurs. Scope (area, era) is a later field, once the counts allow it.

**The decisions** (stage H runs each on the same candidates):

| design | what decides | model judgement |
|---|---|---|
| `judge` | a model, from the rule and the candidate's code alone | all of it; the control for the others |
| `examples` | a model, shown four asked and four not-asked examples a rule | anchored to examples |
| `examples_rate` | as `examples`, with the rule's measured rate as the prior | anchored to examples and a count |
| `retrieve` | a model that must look up the most similar asked and not-asked examples for each candidate and cite them | anchored to the examples it retrieves |
| `rate` | no model: per PR, the three candidates whose rule has the highest rate | none |

The contrasts: `judge` against `examples` (do examples with negatives help); `examples` against
`retrieve` (fixed examples against retrieved nearest ones); `examples` against `examples_rate`
(does a count add to examples); `rate` against the rest (how far a model-free decision gets).

## How it is tested, in steps

1. **Stage H, selection only (no reviewer session).** The ten rules of `stage_h_rules.json`, the
   stage G candidates on the ten probe PRs (149, 12 at an ask), negatives mined by the same
   pinpointer on 16 census PRs. Each design decides which candidates to raise; scored against the
   maintainers' asks at the place. Cheap: 16 pinpointers and eight decider runs.
2. **Reviewer sessions, only for designs over stage H's bar.** The raised candidates delivered as
   few, asserted items ("maintainers ask for this here"), one session a PR on the ten PRs, against
   X and E under one seal, as stages C, F and G.
3. **Scale the record**, only if step 2 moves reach: more rules, more census PRs, scope by area and
   era, and the retrieval tool inside the reviewer's session.

## What would retire a design

Below stage H's bar in two independent runs, or no better than `judge` by two asks or more. A
design that needs model judgement and does not beat `rate` is not worth its cost.
