# What maintainers say when they give a reason (2026-10-16, written before any ask is read)

R1 of `docs/plans/2026-10-16-principles-scope-currency.md` (amendment 1): the direct test of the user's
picture from the source. The picture: maintainers apply a short list of invariant principles,
instantiated by scope, drifting with automation and discussion; a decision is reasoning on evidence and
taste is a small residual. The rival: preference and authority. When a maintainer states a ground, which
kind is it?

## Already answered?

- `docs/questions.md`, "How does maintainer review work split by what it needs (older strata)?": 204
  round-1 comments coded by mechanizability (decidable 5%, computation 44%, convention 39%, preference
  12%). That coded the *ask*, not the *ground stated for it*.
- The premise review (`docs/plans/2026-10-16-principles-scope-currency/review-premise.md` §1.3) sized
  this by regex: 80% of census asks state no ground; 28% hedge; a consistency reference in 5%, an
  external source in 4%. No reader has coded the grounds.
- `docs/todo/conventions-nature.md`: studies 1-4 code principles behind asks (written by readers) and
  scope, conflict, maturity; none reads the maintainer's own stated reason.
- `docs/dead-ends.md`: no entry on stated grounds.
- `probes/enforcement-at-departures-2026-10-16`: for three conventions, the one-line sentence misstated
  the convention; stated grounds are where the maintainers' own statement of a line can be read.

## Selection (fixed now; `select.py`)

The census asks (reader A's 1,833 labelled val1000 asks), bodies rebuilt by
`results/pr_review_v5/adjudications/conventions-census-v1/provenance/materialise_bodies.py` into scratch
(bodies are never committed), code blocks stripped, selected if the text matches any of five marker
classes: a reason word (`because`, `since`, `so that`, `otherwise`, `to avoid`, `the reason is` …), a
consistency reference (`consistent`, `convention`, `as elsewhere`, `in Mathlib we`, `style guide` …), an
external source (a URL, Zulip, a PR number, a library note), a currency word (`deprecated`, `nowadays`,
`now that`, `modern`, `no longer` …), a preference word (`I prefer`, `personally`, `nicer`, `cleaner`,
`more readable` …). **318 asks.** The selection includes preference markers so that preference is not
selected out.

## Reading

Packets in scratch (the ask, the comment it replies to if any, the diff hunk's last lines, the PR's
title and path; no author, no codebook entry). **Two readers, independent, blind to the codebook.** Each
ask gets a primary ground and optionally a secondary, from:

- `principle`: a general value or invariant is named (readability, discoverability, generality,
  maintainability, automation, performance, correctness as a value) — record which;
- `scope_form`: a form is cited as what a scope does ("as elsewhere in this file", "Mathlib does X",
  "like the other lemmas") — record the scope (file, namespace, area, library);
- `currency`: a newer or deprecated form, a migration, new automation;
- `authority`: a decision elsewhere (Zulip, a maintainer's ruling, "we decided", a linked discussion);
- `preference`: aesthetics or worth in the first person ("I prefer", "nicer", "not worth it");
- `fact`: a technical fact (does not compile, `simp` cannot, a counterexample, a performance measurement);
- `other`; `none` (no ground is actually stated: a marker false positive).

Notes at most 25 words, quoting at most eight words of the ask.

## Reading rule, fixed now

Over asks with a stated ground (not `none`), primary grounds, each reader and both-agree:
- **The picture is contradicted** if `preference` + `authority` ≥ one third, or `principle` < one tenth
  (the premise review's falsifier).
- **The picture is supported** if `principle` + `scope_form` + `currency` + `fact` ≥ two thirds.
- Otherwise mixed. Reported beside it: the share of each kind; `scope_form` by scope level (the scope
  layer); `currency` (the drift layer); marginals by AI-authored PR and by the ask's census rank (head:
  the top 50 entries; tail). One reading of one model family; the 1,515 asks with no marker are not read,
  so this is the grounds *when stated*, not the reasons behind every ask.
