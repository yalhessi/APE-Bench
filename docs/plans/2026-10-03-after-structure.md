# After the structured designs: where the next recall is, and what to build for it (plan, 2026-10-03)

**Status** — plan, drafted at the user's request after D1 and D2's first dev reps. Nothing in it
has run. The user's reading (2026-10-03): D1 and D2 may be slightly better, within variance at one
rep; not a significant change in the reviewing; gpt stays stuck and Claude moves slightly. Where
does that point, and what would move issue recall?

## 0. What the record says the designs did, and did not do

Dev held-out 12, 23 obligations, judge v9, one rep per design (`review-designs`, the probe README
there, and the spine `consistency.py --runs`):

| cell | obligations | control findings per PR | note |
|---|---|---|---|
| hygiene baseline, reps 1-3 | 9, 9, 7 (mean 8.3, union 11, stable 6) | 1.0, 0.5, 2.0 | frozen |
| D1 `structured/2`, `structured/3` | 10, 10 (union 12, stable 8) | 1.5, 1.5 | the two together reach the four-solo-pass union at a fifth of its control cost |
| D2 critic on `structured/3` | 11 | 2.0 | +1, the one-`simp` golf, from 28 overturns in 1,950 cells |
| D1, D2 on gpt_5.2 | 2, 2 | 0.0 | 98% of cells `no_issue` with reasons; the unit of decision does not bind |
| the Opus family, every cell since 2026-10-01 | union 14 | | nine obligations reached by nothing |

Read at the altitude one rep supports:

- **Structure bought consistency, not a frontier.** The stable core went from 6 to 8: the Parseval
  lemma (`61f68eed`) and the order-dual `ciInf'` (`7fef913e`), each a one-in-three draw for the
  solo reviewer, are hit by every D1 pass. Two D1 passes reach 12 at 1.5 control findings per PR
  where four solo passes reach 12 at 7.0. That is what the plan of 2026-10-02 §3 predicted and it
  is worth keeping. It is also where it stops: D1, D2 and every solo sample converge on the same
  12 to 14, and the judge's noise at 23 is one to two obligations, so a design's +1 or +2 on dev
  is not yet a result.
- **The nine nobody reaches are not reachable by more structure.** By hand, from the gold claims:
  dot notation in a name and in a `rw` (`7f098f6a`, `8e276803`); a lemma family that `@[to_fun]`
  generates (`57bcc9fd`); a primed name wanting a descriptive suffix (`6b02b611`); the sibling of a
  rename the reviewer did file (`ce7b5d2e`); three design asks, generalize to `ciSup'`, generalize a
  specialized lemma, factor a repeated argument (`8d887ce4`, `55f65304`, `38e72250`); and a module
  doc that wants an implementation section (`0bb42bd2`). Five are conventions a check can state;
  three are comparisons with something that exists; one is documentation structure. This matches
  Phase 1 on three sets: of 67 residual asks, 25 are convention or mechanism knowledge, 19 are
  one compile away, 6 are analogues never compared.
- **The decision is the model's, and gpt_5.2's decision is "nothing to ask".** Asked per
  declaration and concern, then asked to argue every "nothing to ask", gpt_5.2 says nothing to ask
  with reasons in 98% of cells. The effort it is sent is the effort OpenAI runs (`a50256ae`), and
  the local 397B reads at the same floor (`89435e84`). This is a model gap, not a harness gap, and
  the record has now tested it from every side the harness has.
- **The evidence it has, it does not always use.** On 33337 `naming_norm` told every Opus cell the
  maintainers' name (`emerging`, `toLinearMap_` 21 to `coe_` 7, the name as a candidate); one
  hygiene rep of three filed it, and neither D1 rep did. Evidence in the packet raises the reach a
  reviewer *can* have; it does not guarantee the filing. Any expectation below carries that discount.
- **Everything so far is dev.** Twelve PRs, 23 obligations, one reviewer wrote 30 of the dev set's
  52 round-1 comments, 33149 (AI-generated) is 4 obligations and 18-24 findings a pass, and the
  set sits inside the Opus models' training window. Deltas of one or two obligations on it are
  not evidence of anything until they confirm on validation and post-cutoff
  (`docs/research/pipeline-overfit-2026-09.md`).

So the next recall is in three places, in this order of certainty: facts the packet does not yet
carry (conventions as detectors, and the try-it compiles), comparisons the reviewer does not make
(analogues), and reading everything off dev.

## 1. Confirm off dev before iterating further (the gate)

**Motivation.** Every design number is dev-only, one rep, inside a two-obligation noise band, on a
set the model has seen. The plan of 2026-10-01 §5 and the plan of 2026-10-02 §5 both require
validation small12 (30 asks) and post-cutoff (16 asks) by the blind matchers before anything is
believed; neither has been run for any design.

**Design.** Run the hygiene baseline (two reps), D1 `structured/3` and D2 on validation small12 and
on post-cutoff through the probe harness, one seal per set with the existing X1/X2 sessions and the
gpt reference, two blind matchers, audited. Reviewed workspaces exist for both sets.

**Expectation.** If D1's +1.7 mean on dev is real, it reads as reach +0.05 to +0.10 on each set
against the hygiene baseline, with asks reached per finding no lower. If it vanishes, the dev gain
was in-window memory or a draw, and D1 is kept for what it does prove, the lower control cost of
a union. Either way this is the gate for steps 2 to 4, whose readings are on these sets.

**Cost.** About six subscription windows of runs plus matcher sessions; no API spend beyond the
usual.

## 2. Conventions as detectors in the packet (the largest never-reached slice)

**Motivation.** Five of dev's nine never-reached obligations are conventions a deterministic check
can state about this PR, and 25 of 67 residual asks across three sets are convention or mechanism
knowledge. The record's lesson on how such knowledge reaches a model is settled: rules in the prompt
did nothing twice (guideline injection, precedent priming), facts about the PR moved the naming
arm (the counted rename) and every Opus cell (the long line, once the compile reported it). The
static pass showed the standard linter set is nearly silent on human PRs, so the facts have to come
from checks Mathlib does not ship.

**Design.** A `conventions` evidence stage, deterministic, over the diff and the reviewed file, each
detector emitting fact lines keyed to a declaration, delivered as a packet section restricted to the
diff and, for D1, into the matching ledger cell as that cell's evidence:
1. **Dot notation.** A new theorem whose first explicit hypothesis has head `N.P` and whose name is
   `foo_of_P`-shaped: "the dot-notation form `N.P.foo` is how k of n siblings in this file are
   named". A `rw [N.lemma h …]` where `h : N …`: "`h.lemma` is available". Two dev obligations.
2. **Generated families.** A hand-written family that an attribute generates (`fun_*` twins for
   `@[to_fun]`, additive twins for `@[to_additive]`, `simps` projections, `mk_iff`): the attribute's
   own docstring as the fact, with the family listed. One dev obligation; `to_fun` is Phase 1's
   lead example.
3. **Primed names.** A new declaration ending in `'` whose unprimed name exists: the naming page's
   sentence on primes, with the siblings that use a descriptive suffix. One dev obligation.
4. **Sibling propagation of a filed rename.** When a rename is filed at one declaration, every
   sibling in the file sharing the renamed token is listed beside it. One dev obligation; this is
   a post-pass on the ledger, not a detector.
5. **The area census**, already built (`naming_norm`'s directory scope, `7d39d0d7`), promoted
   from a tool the reviewer may call to a section it always sees for every new name.

Measured alone first, under the static pass's protocol (`results/pr_review_v5/probes/static-pass-2026-10-01/README.md`):
hits at gold sites by hand, emission on the control PRs, before any reviewer reads it. Decisive
detectors (a primed name with its base present, a hand-written generated family) may also file
directly, as the v4 deterministic arm did, which is the one reproducible-in-three-reps result in
this project's history; the others stay evidence.

**Expectation.** On dev, the four convention obligations become reachable; with the 33337 discount
(evidence filed one time in three) the expected gain is +2 of 23 per pass and +3 to +4 in the
union, taking a single D1 pass from 10 to about 12 and the family's never-reached set from nine to
five. On validation, convention asks are the largest residual class; detectors of this kind cover
perhaps a third of them, so +3 to +5 of 30 reachable asks. Control emission is the risk: a
dot-notation detector fires on existing code too, which is why it is restricted to the diff and
measured alone first.

## 3. The try-it battery on a persistent checker

**Motivation.** Nineteen of 67 residual asks are decidable by one compile nobody ran, and the closer
battery produced eight of fifteen such asks outright. Compile is 20 to 51% of session wall on the
Opus runs; a persistent Lean server takes a recorded edit from 9.6 s to 0.7 s
(`docs/todo/lean-persistent-checker.md`, corrected for the client race). At the cold cost the battery
over every changed proof is an hour a PR; at the server's it is minutes, which is what makes it a
packet section rather than a probe.

**Design.** Build item 1 of the persistent-checker todo (one server per attempt and reviewed
workspace, `waitForDiagnostics` on the exact version, the lakefile's options applied). Then the
battery as a deterministic pre-stage: for every changed proof, the standard finishers (`simp`,
`simpa`, `positivity`, `gcongr`, `grind`, `omega`, `norm_num`, `exact?` and `apply?` in the file),
the pre-PR proof under the new statement, each `noncomputable` dropped, and the `αᵒᵈ` dual for
sup/inf pairs; outcomes as evidence lines ("`simpa using h` closes this goal"), with the compile
tools and D1's edit gate running on the same server.

**Expectation.** On dev, little: its never-reached set is not the try-it class, and the one golf
obligation is now reached by D1 and D2. On validation, the try-it class is the second largest
residual (12 of the 30 Claude-only asks were try-it for gpt_5.2; 5 of 37 for Claude), so +3 to +5
of 30 reachable asks, concentrated on proof asks, with the same filing discount. Beside recall, every
session gets shorter and D1's large-PR ledgers cheaper, which is what makes reps affordable.

## 4. The design asks: compare against the area's analogue

**Motivation.** Three of dev's nine never-reached obligations and 95 of 506 validation asks (F6) are
comparisons against something that exists, in the library or in the PR. Two blind readers named the
same analogue for 43 of 43 such asks, and the comparison was reachable by API shape in 17 to 23 of
them; name retrieval found the analogue in the top ten for 0 of 43, and Loogle shape search ranked
it first in 1 of 15 (`docs/todo/review-design-comparison.md`). The wrong-sibling risk the user named
lives in retrieval, not in judgement.

**Design, measurement first.** An analogue stage in two parts: a role statement per new declaration
(what kind of object or API it is, from its signature and namespace, produced by a cheap model
call or by the reviewer in a pre-pass), then retrieval by role rather than name: same declaration
kind, same position in the class hierarchy, same type head, in the same area first. Measured on the
43 labelled asks (analogue recall at k, wrong-analogue rate) before any reviewer sees it; delivered
as a packet section that names the analogue, so a wrong one is a visible, refutable claim.

**Expectation.** Unknown until the retrieval is measured; that measurement is the step. If
retrieval reaches half the labelled analogues, the design class on validation (the largest family
everywhere, 23%) opens by a few asks per set, and up to three dev obligations. This is the
highest-ceiling item and the least certain.

## 5. Reps and the new baseline (background, no design)

D1 `structured/3` and D2 reps 2 and 3 on dev, so that mean, union and stable exist for the design
the next steps are read against, and the K=2 D1 union is read as the cheap ensemble (12 at 1.5
control findings per PR). Two windows a rep, judged at about $0.40.

## 6. gpt: one check, then park

One gpt-5.5 run at `xhigh`, the one effort level never run (`a50256ae`), under the hygiene contract.
Otherwise no further design iteration on gpt: the forced unit of decision and the critic both leave
it at 2 of 23, with reasons, and the self-hosted tier reads at the same floor. Its measured
strength, compiling and verifying more edits than Claude, is a verifier's, and the critic todo
records "a critic on another model" as the one untried use. Expected gain from the `xhigh` run: at
most one or two obligations; the point is to close the question.

## 7. Order, and the expectation in one table

| step | what moves | dev, per pass (now 10-11) | validation small12 (now about 0.5 reach) | cost |
|---|---|---|---|---|
| 1 confirm off dev | nothing; it is the gate | | tells whether D1's +1.7 is real | 6 windows + matchers |
| 2 convention detectors | the never-reached set | +2, union +3 to +4 | +3 to +5 asks of 30 | detectors are code; one rep per set |
| 3 try-it battery on a persistent checker | validation's proof asks; session cost | 0 to +1 | +3 to +5 asks | the checker is the build; runs then cheaper |
| 4 analogue retrieval | the design class | up to +3 | the largest family, unmeasured | the 43-ask measurement first |
| 5 D1/D2 reps | the yardstick | | | 4 windows |
| 6 gpt-5.5 xhigh | closes a question | | | $20-30 |

If steps 2 and 4 land as expected, a single D1 pass on dev goes from 10 to about 13 of 23 and the
family's never-reached set from nine to about four, which are then the design asks and the
documentation structure; validation reach from about 0.5 to 0.6-0.65. Every number here is an
expectation under the filing discount measured on 33337, and none is a result until step 1's sets
say so.
