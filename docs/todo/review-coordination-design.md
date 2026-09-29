# Coordination: a principled design for how the review reads a PR

**Status** — open, 2026-09-29, **for a fresh session**; design and labelling, no runs.
**Cost** — no spend until a design exists.

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
