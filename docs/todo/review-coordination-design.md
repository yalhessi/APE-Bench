# Coordination: a principled design for how the review reads a PR

**Status** — **design written, 2026-09-29**:
[`docs/research/review-coordination-design-2026-09.md`](../research/review-coordination-design-2026-09.md),
checked against the labelled asks (see "The design" at the foot). Open: the by-hand demonstration
that a construction produces a miss (`remaining-misses-kind.md`), then the build decision. No run.
**Cost** — no spend so far; the demonstration is free (`cli tool`); the first paid measurement is
three reps on validation small12, priced by `cli plan` before anything runs.

**The user (2026-09-29).** *"Having overfocused work units isn't optimal, but the principled design
is to come up with a way to chain context together. A per-PR pass seemed useful but didn't move the
needle. It seems like coordination should be helpful, but we haven't reached a compelling design. We
keep coming up with messy designs that fit the datapoint we directly consider rather than a design
principled enough to be robust to other proof engineering datapoints and capture something the
maintainers do."*

**Motivating examples.** The largest comparison class in the wide reading is the PR's own siblings,
29 of 99 asks ("do the same for the one above", "record it on both sides", "these two proofs are
identical", "the dual is missing"), which a reviewer of one work unit cannot say. PR-level asks are
6% of the population, 16% on AI-authored PRs, and have no reader. The generalist held 64 of 71
held-out hits. A whole-PR pass was tried and did not move recall: it was another reader, not a
shared model the readers condition on. The change graph, families and units are built and then
discarded before review.

**Where to look.** Software inspection research: *perspective-based reading* (Basili and others)
found that reviewers who each construct an artifact from a perspective, the user writing how the
code is used, the tester writing tests, find more defects than checklist or ad hoc readers, because
defects appear as obstacles to the construction. That is the principled form of "generate
alternatives and compare": a reviewer who rewrites a declaration in the library's idiom meets the
duplicate and the convention while rewriting; one who writes the API's use meets the missing lemma.
Compiler design: passes over one intermediate representation, each pass enriching it, questions
asked of the model rather than of fragments. The reading order of skilled maintainers: intent, then
definitions, then statements and API, then proofs, then the file as a whole. Other proof libraries'
review practice (the Isabelle AFP, math-comp) as the robustness test.

**What to explore.**
1. **The PR model**: what it must contain for the sibling and PR-level asks to be askable at all:
   objects and their kinds, the relations among them (twins, families, uses), the intent, the area
   and its regularities (`conventions-nature.md`). Check against the labelled asks: which need which
   part of the model.
2. **Constructed artifacts by perspective**: which constructions expose which ask families. Usage
   for API-owed and missing-lemma asks; rewrite-in-idiom for duplication, convention and
   compactness; generalisation for hypothesis and typeclass asks. Label the 38 misses and the
   variant-class design asks by the artifact that would have exposed them
   (`remaining-misses-kind.md`).
3. **Chaining**: what each pass writes into the model for the next, in what order, so that the
   design is a reading protocol and not a routing table.

**What would close it.** A design document: the PR model's schema, the perspectives and their
artifacts, the pass order, and, for each ask family in the population, which pass is expected to
produce it, with the labelled asks as the check. Only then a run.

**Risk.** Designing again from the datapoints in front of us; the guard is that every element of
the design must be justified by the reading protocol or the inspection literature, not by a miss.

## The design (2026-09-29)

**One PR model, six perspectives that construct, six passes that enrich it.** The model holds what
the reference facet says a reviewer compares against (objects, families with their twin pattern,
relations, library candidates as a family along the decoy axes, the area's regularities, intent,
open-PR overlap), every entry tagged `fact`, `construction` or `hypothesis`; a later pass may rely on
the first two and may only *ask* the third. The perspectives are the consumers of a merged
declaration (user, automation, maintainer, next developer, finder, gatekeeper), each building the
artifact its consumer would (a usage, automation's view, the proof re-done in the idiom, the
generalised statement and the family closure, the name and docstring from the code, the PR's story);
asks are what the construction cannot do, which is perspective-based reading's mechanism. The passes
run in cost-of-change order (intent, definitions and the typeclass layer, statements and the family,
proofs, names/prose/layout/location, the change), every applicable object receives every pass and
returns a verdict, and the family, not a hash-packed unit, is the unit of passes 3 and 4. Findings
are never shared between passes; facts and constructions are. The lead becomes the model's owner and
the passes' sequencer, which is the `sibling_view = "blackboard"` value `CoordinationPolicy` names
and refuses today.

**The check** (`results/pr_review_v5/adjudications/coordination-design-check-2026-09-29/`, one
reader, planning labels): on the 516 agreed reference × object asks, passes 3 and 4 hold 48%, pass 5
37%, pass 6 6%, pass 2 7%. All 31 agreed sibling asks of the outside reading land in passes 2–4,
27 of them in pass 3's family closure (19 are a twin the pattern expects). The 38 misses land 25 in
passes 3–4 against 48% of the population; of the 14 with a battery result, 11 were produced by the
construction. The design names no PR; the check does.

**What would close the next step.** The demonstration in `remaining-misses-kind.md`: the model built
by hand for three validation small12 PRs holding pass-3/4 misses, passes 3 and 4 run by hand through
`cli tool`, two runs, two blind matchers; threshold ≥ 3 unreached asks produced in both runs with the
compiled artifact as evidence. Then the minimal native build (§9 of the design) and three reps on
small12 against `pr5_val_small12_minus30714_lead_rep1` under the §10 thresholds.
