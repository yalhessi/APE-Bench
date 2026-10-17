# Is a rule the maintainers' own practice, and do they enforce it where they look? (2026-10-17, before any outcome)

The user's question (2026-10-16): forcing a reviewer to apply the right convention gives the best results, yet
conventions seemed raised at about 5% of the places they apply; a project as mature as Mathlib cannot run on rules
applied one time in twenty, so the 5% may measure our rule texts and our idea of "applies". Stage H's step 4 and
its review (`probes/stage-h-departures-2026-10-16/RESULTS.md`, corrections after review 3) left three rival
explanations standing for the low rate, and the direction review ranked the deterministic tests that separate them
first (`docs/plans/2026-10-16-principles-scope-currency/review3-direction.md`, §4, ranks 1-3):
- **the rule as written is not the maintainers' practice** (the paraphrase is broader than what they do);
- **attention and budget**: maintainers fix a departure where they look, and most places nobody looked at;
- **a decision at the place**: maintainers see the departure and leave it, on evidence at the place (the user's
  picture's negative half), such as the file's own practice or the code being old.

This probe tests the three, rule by rule, on six rules a script can check exactly, over the 973 val1000 PRs, with
an outcome that needs no gold: whether the departure is gone at the merge commit.

## Already answered?

- `docs/questions.md`, "For the ten rules behind the 5%…" (stage H, step 4 and review 3): on 59 places, departures
  persist to merge (23 of 27) and survive mostly where no maintainer commented (17 of 20 against 3 of 7); the census
  caught 6 of 12 round-1 asks. That reading had 27 departures on 11 PRs and no way to tell the three rivals apart.
- `docs/questions.md`, "Of the departures a detector finds at the reviewed head, how many are fixed by merge"
  (enforcement probe): for dot notation and primed names the only route to a fix is an ask; where the file has a
  practice the PR writes it (29 of 34). This probe measures the same outcome for six other rules at scale, and adds
  the two things it lacked: attention at the place, and the maintainers' own code.
- `docs/questions.md`, "Does supplying Mathlib's written guidelines, or its own linters…": the 23 binding
  conventions are enforced by CI. The long-line linter is used here as the control for that reason.
- `review3-direction.md` §4 ran the first cut for line joins: 369 joinable two-line signatures, 3 asked; 2 of 31
  asked where another ask sat at the signature; maintainers' own suggestion blocks leave 28% joinable. This probe
  extends it to six rules, adds the merge outcome and the place predicates, and pre-registers the reading.
- `docs/todo/conventions-nature.md` (studies 2-4: scope, conflict, maturity) is the open hypothesis this serves; the
  file-practice predicate below is its scope question asked of fixes, not of asks.
- `docs/dead-ends.md`: the filing contract (design G) and selection are closed; nothing here proposes a filter on
  what a reviewer files. The result is about what the maintainers' rate measures.
- Found before writing this (detector counts only; no merge commit read, no census ask joined), from `places.py`:
  3,628 departures on 571 PRs, 3,040 on the 500 PRs with a merge commit in the clone; 30 authors are active
  reviewers (20 or more round-1 review comments on other val1000 PRs). Departures with a round-1 comment within
  3 lines: P084J 73, P097 114, P341 384, P012 52, P240 38, P392 16, LONG 7. Reading random samples moved four
  detector choices before this was written: `MathlibTest/` excluded (its own conventions); a `:=` inside a named
  argument no longer ends a signature; P392 counts only unqualified heads that are unambiguous classes (plus
  `Nonempty`, `Finite`, `Countable`, `Subsingleton`), after `Function.Surjective` and `Endofunctor.Algebra` were
  matched; P097's practice rate is per touched proof, not per line.

## The rules (detectors in `detect.py`; texts in `conventions-ceiling-2026-10-04/rules.json`)

| id | stage G rule | departure, exactly |
|---|---|---|
| P084J | P084 line breaks | a new two-line signature (header, one continuation ending `:=` or `:= by`) whose join fits in 100 characters |
| P097 | P097 one tactic per line | tactics joined by `;` at bracket depth 0, not `<;>`, on an added line of a theorem or lemma body |
| P341 | P341 a `theorem` has a docstring | a new `theorem` with no `/-- … -/` docstring above it and its attributes |
| P012 | P012 blank lines around commands | an added `namespace`, `section`, `end` or `variable` command with a non-blank line directly above or below |
| P240 | P240 term proof on its own line | a new theorem or lemma whose statement spans several lines and whose term proof follows `:=` on the last |
| P392 | P392 class hypotheses as `[C x]` | a named binder whose whole type is an unambiguous class applied to arguments |
| LONG | the long-line linter (control) | an added line over 100 characters with no URL |

Opportunities (the denominator of a practice rate): new two-line signatures (P084J); touched theorem and lemma
proofs (P097); new `theorem`s (P341); added commands (P012); new multi-line theorems or lemmas with a term proof
(P240); class-typed binders, named or instance (P392). Only `Mathlib/` files.

## Covariates (`places.py`, done)

- **attention**: `near` if a round-1 inline review comment by someone other than the author (no bots) sits within
  3 lines of the departure's declaration span (or of the command); `pr_reviewed` if the PR has such a comment but
  not near; `pr_unreviewed` if it has none in round 1 (later rounds are not counted).
- **group**: `reviewer` (an active reviewer wrote the PR), `other` (another human), `ai` (AI-flagged in the draw).
- **moved**: every departing line also appears among the PR's removed lines.
- **edited**: the declaration's written name is already a header in the base version of the file.
- **file practice**: the same detector over every line of the base file; its departures over its opportunities.

## Step 2: own practice (Q1; `practice.py`)

Per rule, the departure rate per opportunity in four kinds of code: round-1 code of PRs by active reviewers;
round-1 code of other human authors; suggestion blocks written in review by anyone but the PR's author, any round
(where they hold 20 or more opportunities); the base version of every file the PRs touch (each path once).

**Reading, per rule** (`r` is the active reviewers' rate, `o` the other humans'):
- **not their practice** if `r` ≥ 20% and `r` ≥ ⅔·`o`;
- **their practice** if `r` ≤ 5% or `r` ≤ ⅓·`o`;
- **mixed** otherwise. Where suggestion blocks hold 20 or more opportunities and fall on the other side of the 5% or
  20% line from `r`, the rule reads **contested**.

## Step 3: enforced where they look? (Q2, Q3, control; `outcome.py`)

**Outcome, per departure on a PR with a merge commit in the clone** (`git log --grep='(#N)'`): find the same
construct in the file at the merge commit (by the declaration's written name; a command by its text, a long line by
its text) and run the same detector on it.
- `fixed`: the construct is there and the departure is not; `persists`: it is still there; `gone`: the declaration
  or command is absent (renamed, moved or deleted); `ambiguous`: the name or command text occurs more than once in
  either version; `no_merge`, `file_gone`.
- **targeted**: a `fixed` whose declaration is otherwise unchanged: equal after removing all whitespace and `;`
  (P084J, P097, P240, P012 by the command's neighbourhood), or after also reading `theorem` as `lemma` (P341). P392
  has no targeted form and reports `fixed` only.
- The fix rate is targeted fixes over `fixed` + `persists` (P392: `fixed` over the same); `gone`, `ambiguous` and
  the rest are reported, never counted. Moved departures are reported apart and left out of Q2 and Q3.
- Secondary, reported only: a census ask (reader A's primary or second label is the rule's stage G id) within one
  line of the departure.

**Control, read first.** LONG departures on merged PRs: `fixed` (any) at 90% or more. Below that the outcome or the
matching is broken: nothing else is read and the defect is reported.

**Q2, per rule, needs 20 or more `near` departures with an outcome:**
- **enforced where seen** if the `near` fix rate is 50% or more;
- **left where seen** if it is 15% or less;
- **mixed** between. The far rate (`pr_reviewed` and `pr_unreviewed` together) and the ratio are reported.

**Q3, place predicates, for rules step 2 does not read "not their practice" and Q2 reads "left where seen" or
"mixed", on `near` departures, each arm with 10 or more:**
- **new against edited**: fix rate on departures in new declarations over the rate in edited ones;
- **file conforms against file departs**: base file practice ≤ 10% against ≥ 50% (each with 3 or more base
  opportunities).
- A predicate **separates** if its ratio is 2 or more. Read on all departures too (larger n), reported as secondary.

**The reading across rules.** Each rule lands in one cell: not their practice (the low rate measures our rule
text); their practice and enforced where seen (the low rate is attention); their practice, left where seen, a place
predicate separating (a scope-dependent decision the evidence at the place predicts: the user's picture); their
practice, left where seen, nothing separating (a decision on something these predicates do not see); or too few.
The answer to the user's question is the count of rules in each cell, not a pooled rate.

## Step 4: what maintainers say when they decline (`declines.py`, one reader)

The only written record of the negative half: comments in any round on the val1000 PRs, by anyone but the author
and not a bot, that carry a decline phrase (`review3-direction.md`'s list: "no need", "fine as is", "either is
fine", "up to you", "not worth", …): 77 comments. Ten census asks (seeded) are mixed in blind as calibration.

One reader (a Claude subagent; one model family, so one reader) codes each comment: `decline` yes or no (the
commenter says a change is unneeded or optional); the `object` declined (`convention` a style or library-form
change, `content`, `process` such as splitting or later PRs, `unclear`); the `ground` (`economy`: not worth a round
or the churn; `indifference`: up to you, either is fine; `place`: a fact about this code or library, such as the
file's practice, a downstream use, the code being moved or old, performance, consistency; `scope`: a later or
separate PR; `authority`: someone else decides; `none`), with a quote of at most eight words.

**Read only if** the reader marks at least 8 of the 10 calibration asks `decline: no`. **On the declines of a
convention:** `place` at a third or more, maintainers state evidence at the place when they decline; `economy` +
`indifference` at two thirds or more, the negative half in their words is economy and indifference; between,
mixed. Comment bodies stay in scratch and are never committed.

## Limits, stated now

The six rules are rules of form a script can check; the substantive rules (use the API, name like siblings, drop
a hypothesis) are not covered, and the reading says so. Attention is round 1 only. "Active reviewer" is a count
threshold, not the maintainer team. A targeted fix can still be an author's own clean-up. Departures in PRs merged
after the clone's HEAD (2026-05-14) or never merged are out.
