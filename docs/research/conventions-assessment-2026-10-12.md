# The conventions direction after the one reviewer table: an assessment (2026-10-12)

**The question** (the user, 2026-10-12): the one reviewer table was built to say how fruitful the
conventions direction is. Its results read weaker than the idea first looked. Is the idea still worth
pursuing, does it answer an academic question other review systems have not, how could it be
iterated, and should the work pivot to another component given the gaps the table's sets show?

**Sources.** The table and its inspection and dev pair
(`results/pr_review_v5/probes/one-reviewer-table-2026-10-10/README.md`), the ceiling probe's stages
C to AP (`conventions-ceiling-2026-10-04/README.md`), the ladder, the places test, the selector probe,
the three adversarial rounds (`conventions-dossiers-review-2026-10.md`,
`decompose-and-shrink-review-2026-10.md`, `deployable-reviewer-review-2026-10.md`), the ceiling
residual (`ceiling-residual-2026-10.md`) and the systems survey
(`code-review-systems-survey-2026-09.md`). Three counts below were computed for this note from the
table's unblinded seals and are marked *(computed here)*; nothing was run.

## 1. The answer in one paragraph

The conventions idea has three layers, and the table sorts them. **The knowledge layer stands:** the
census holds the convention behind 85% of the asks on three sets, and a reviewer told which of them
apply to the PR under review reaches 0.22 to 0.42 more of the in-census asks, on three strong models,
three reps on DeepSeek. **The delivery layer does not transfer:** every way of choosing the conventions
without the asks (25 picks as sentences, pinpointed rules, picks with examples and precedence on
DeepSeek, the same on Opus) reads null off the PRs it was developed on, and the table's two
positive cells are the discovery sample re-scored. **The understanding layer (dossiers, exams) has no
support:** at the place, the bare sentence already produces the maintainer's change for most asks,
and examples made the model more conservative, not more accurate. The thread's own pre-registered
closing rule for the dossier line (an ask-free delivery at or under +0.05 off-sample, or one that
fails the volume guard) has now been met: on the ten PRs by the yield guard, and on both fresh cells
(P14's other four PRs −0.04, dev −0.01) by the bar. The lesson is a mechanism, not a wall:
the exact brief works because it *asserts which conventions are in play here*, which is the ask's
pinpointing in disguise, and nothing on record predicts that from the PR alone. That is an academic
result about review alignment that other systems have not published, and it also says the next
recall is not in another delivery variant.

## 2. What the table says, in five lines

Per-session reach on all asks, matcher 1 (`table.txt`, `table_D12b.txt`); P14 is 46 asks on 14 PRs,
D12 47 asks on 12.

| reviewer | P14 | D12 | reading by the plan's rule |
|---|---|---|---|
| gpt-5.5, contract v2 [3] | 0.24 | 0.28 | level with DeepSeek on P14, below it on D12 |
| DeepSeek-V4.1-Flash, contract v2 [3] | 0.28 | 0.40 | the free tier |
| DeepSeek + AP [3] | 0.41 | 0.39 | +0.20 on validation small12, 0.00 post-cutoff, −0.01 dev |
| Opus 5.5, X route [2] | 0.47 | 0.55-0.62 | ahead of DeepSeek on both, ordered |
| Opus 5.5 + AP, same day [1] | 0.67 | 0.60 (solo same day 0.53) | +0.20 on P14; +0.02 to +0.09 on dev, intervals spanning 0 |

- **Claude is the best solo reviewer on both benchmarks, by a margin larger than any convention
  effect measured off-sample.** The Opus harness gap (X route against the project harness, +0.10 on the
  matcher and +4 obligations on the judge) is as large as DeepSeek against gpt.
- **AP on DeepSeek moved only the eight validation PRs it was read on.** Every AP cell collected fresh
  (P14's other four PRs, the dev 15) is null against solo; nine of AP's net +18 cells on P14 are one
  suggestion repeated on three theorems of 34091.
- **Opus + AP's +0.20 is confined to the ten PRs chosen for solo Claude's misses.** On dev it files
  1.7 times as much for a gain inside the noise.
- **D12 is not "easier"; it is weighted by one reviewer's repeated asks** (29 of 47). Group-weighted,
  only Claude does better on D12.

## 3. Why the ask-free gain did not transfer

The inspection's fifth point carries the explanation, and it is worth stating because it says the
delivery is not broken, it is bounded.

- **AP's behaviour on a picked ask is the same everywhere.** On asks whose census entry the selector
  picked, AP reaches about 0.5 on the ten PRs, on P14's other four, and on dev (0.50, 0.52, 0.56).
- **What differs is solo's reach on those same asks:** 0.20 on the ten PRs, 0.49 on dev. The ten PRs
  were chosen where Claude missed, and they are where DeepSeek is weakest too. AP's gain is
  (share picked) × (0.5 − solo's reach on the picked), and on dev the second factor is near zero.
- **Where room did exist on dev, AP converted less:** 5 of 42 cells on the 14 picked asks solo never
  reaches, against 18 of 48 on the ten.
- **The form of the convention does not sort it** *(computed here, post hoc)*. Splitting AP − DX by
  the census entry's `form`: on validation AP gains on rule-form asks (+0.30, 9 asks) and on
  standard-form ones (+0.19, 16); on dev it gains on neither (+0.07 on 18 rule-form, 0.00 on 22
  standard-form, with room: DX 0.27). The gain tracks the set, not the kind of convention.
- **Behind that sits the mechanism the adversarial round found.** At the ten asks only the exact brief
  reached, stage G's reviewer, holding the same sentence at the same place, filed a different change at
  six. The exact brief said *these apply here*; G asked the reviewer to verify. Every delivery that did
  not assert applicability moved nothing (F +0.03, G +0.000), and an ask-free list of 25 holds about
  2.8 true asks, so it cannot assert without asserting 22 wrong ones. Under precedence the reviewer
  files them (13 of 14 unasked detector facts); under verification it overrides the right ones.
- **And demand is not predictable from the PR.** Maintainers raise a convention at 5% or less of the
  places its situation occurs (stage H); the best per-place discriminator on record is AUC 0.68-0.78
  at about 7% precision (the places test). Deployed systems that get precision from rule taxonomies
  do it with checkers and filters trained on outcome data at scale (AutoCommenter on ~800k
  norm-citing comments, RovoDev's gate on 50k resolutions). Mathlib has 1,833 census asks, and 0.68%
  of its reviewer comments cite a norm.

So "stick to the conventions" has a sound first half (the model acts on a convention it is told
applies) and an unsolved second half (which of the hundreds that apply would a maintainer raise
here). Every ask-free design so far has tried to solve the second half with the PR alone.

## 4. The three layers, and where each stands

| layer | claim | status | evidence |
|---|---|---|---|
| knowledge | the census holds what maintainers ask for, and a reviewer acts on it when told it applies | **supported, replicated** | 39 of 46 and 40 of 47 asks in census; exact brief +0.26/+0.28 Claude, +0.22 gpt-5.5, +0.22 DE and +0.42 DP DeepSeek over three reps; 5 of the 6 asks nothing reaches are in census |
| delivery without the asks | the applicable conventions can be chosen from the PR and delivered to get that gain | **not supported off-sample** | F +0.03, G +0.000, AP null on every fresh PR (P14's other four, dev's 15), Opus + AP null on dev; retrieval as selector 0.16-0.26 at 10 (a reviewer's exploratory count), DeepSeek's own selector 0.43 at 25 against Opus's 0.67 |
| understanding (dossiers, exams) | the model misapplies conventions it does not understand; a richer representation fixes it | **not supported; its drop rule is met** | the ladder: the bare sentence at the place passes 25-29 of 39, DP's examples −4 to −5; understanding is a quarter to half of DP1's misses with the asks given (at most +0.08 to +0.15 there); the todo's step-3 rule (≤ +0.05 off-sample, or a failed guard) met by the guard on the ten PRs and by the bar on both fresh cells |

**On the dossier line specifically.** It was never built, by design: the adversarial round narrowed
it to "does anything carry DP's gain once the asks are gone", and the table answers no for every
delivery tried. The honest disposition is a `docs/dead-ends.md` entry that keeps what is untried:
self-written dossiers examined by PR split, an index the reviewer browses, fewer picks (top 10), the
selector's `where` delivered, examples from the PR's own family, a delivery without the licence
wording, and AP as a second pass unioned with solo. None of these has a stated ceiling above the
table's noise on these sets, which is why they are untried rather than next.

## 5. Is there an academic question here, and is it answered?

Yes, and much of it is answered, as a result about the task rather than a system. Against the record
of other review systems (`code-review-systems-survey-2026-09.md`), four things are new:

1. **A convention census of a formal-math community with its saturation curve.** 409 and 407
   principles from 1,833 maintainer asks by two blind readers, not saturated (about one ask in ten
   brings a new one), the top 50 covering 55%, 370 in the tail, rules and standards split evenly.
   BitsAI's 219-rule taxonomy and AutoCommenter's URL set are hand-built or distilled; nobody has
   measured how many conventions a community's review traffic actually invokes, or shown the tail.
2. **A ceiling design that separates knowledge, selection and the decision to file.** Exact,
   applicable, pinpointed and precedence conditions, under one matcher protocol, on three models.
   The finding: the knowledge is present (in the census and in the model, since the bare sentence at
   the place suffices); the gap is selection and filing. MathlibPR says models cannot separate
   merge-ready from build-passing PRs; ProofJudge recovers reviewer preference between a declaration
   and its accepted revision. Neither asks where the gap sits.
3. **Demand is a small, unpredictable subset of applicability.** Maintainers raise a convention at
   5% or fewer of the places it applies; five decision designs read AUC 0.56-0.64 and a per-place
   verdict 0.68-0.78 at 7% precision. "Apply the conventions strictly" is therefore a volume lever,
   and an unasked departure is not wrong. This is Tricorder's "a false positive is anything the user
   did not want to see", measured for a convention taxonomy, and it bounds every guideline-injection
   result (RovoDev's +5% included) from below.
4. **The assertion, not the content, carries guideline gains.** The same sentence at the same place
   moves the reviewer when stated as applicable and not when offered for verification. No published
   system has isolated this, and it explains why prompt-side guideline injection reads near null in
   the industrial reports.

What this is not: a deployable gain, or a headline system result. It is a negative with a measured
mechanism, pre-registered rules and three models, which is publishable as a section ("verifiable
correctness is not enough, and convention knowledge is not enough either; what is missing is the
maintainer's choice of which convention to raise"). The caution from the record applies: a session
that ends in a diagnosis is not a contribution to the reviewer (2026-09-23). The diagnosis here is a
contribution to the paper, and it should be written up as one, but it is not a reason to run more
delivery variants.

## 6. The gaps on the table's sets, and what each component could reach

What one deployable session misses on these sets, and who reaches it *(computed here, matcher 1,
ask-free rows only: X, T, OP, GPT, DX, AP)*:

| | P14 (46) | D12 (47) |
|---|---|---|
| best single ask-free session (Opus, X route) | 0.47 | 0.55 |
| two Opus reps unioned | 0.50 | 0.60 |
| one Opus session ∪ one DeepSeek session | 0.49 | 0.58 |
| one Opus session ∪ one AP session | 0.53 | 0.63 |
| every solo session on disk unioned (Opus ×2, DeepSeek ×3, gpt ×3) | 0.52 | 0.62 |
| every ask-free session on disk unioned | 0.63 | 0.68 |
| **reached by no ask-free session** | **17 (0.37)** | **15 (0.32)** |

Two things follow. **Heterogeneous aggregation buys little:** adding a DeepSeek or gpt session to an
Opus session adds +0.02 to +0.03, and unioning everything solo adds +0.05 to +0.07. The industrial
aggregation gains (Bugbot, SWR-Bench) do not appear here because the reviewers miss the same asks.
**A third of the asks escapes everything ask-free,** and on P14 the exact-convention ceiling sessions
reach 11 of those 17: told the PR's own conventions, the reviewer gets them. The whole conventions
problem on these sets is those eleven.

The 32 asks nothing ask-free reaches, by what they would take (the texts are in each set's
`feedback.json`; the P14 verdicts are in `ceiling-residual-2026-10.md`):

| kind | asks | examples | share of all 93 | the component that would reach it |
|---|---|---|---|---|
| naming judgement | 8 cells, 5 distinct (one rename counted four times on 33145) | `Dense.ciSup`, `toLinearMap_` (33337), `_left`/`_right` orientation, a prime wanting a suffix | 0.05-0.09 | naming thread, worked and parked; orientation needs library-wide facts |
| statement and API design, generality | 7 | turn `iSup`/`iInf` around, phrase as `Function.Surjective`, "something very general that should exist", a UFD version, a `HasProd` twin, an alias | 0.075 | analogue retrieval (`review-design-comparison.md`): readers find the analogue 43 of 43, name retrieval 0 of 43; the measurement is the step |
| proof try-it | 6 | `positivity`, `gcongr`, `simpa using h`, `grind [minimalCover]`, a one-liner from a sibling | 0.065 | a deterministic closer battery (Mathlib's `tacticAnalysis` linters, old-proof replay); DP's misses here were a failed check read as conforming |
| library mechanism knowledge | 3 | `mk_iff`, the `to_fun` attribute, a pre-existing constructor | 0.03 | facts about the library at base; `to_fun` is newer than any model's training |
| migration in progress | 2 (+2 `grind` proofs above) | tag with `grind`, "same here" | 0.02-0.04 | a dated convention; the census has no maturity field |
| scope conflict | 2 | `variable … in` over subsections (library idiom over file idiom) | 0.02 | conventions-nature study 2; the sentence does not carry scope |
| PR-level | 3 | why the old names are bad, the history of #24163, motivation in the description | 0.03 | the PR's own history; no packet carries it |
| documentation structure | 1 | doc interspersed through the code | 0.01 | — |

No kind exceeds about 0.08 of a set's asks. That is the census tail seen from the other side: the
misses are spread over the whole family vocabulary, and no single evidence stage has a ceiling above
the table's minimum detectable difference (about 0.18 on P14, about 5 of 23 on D12). This is the same
reading the detectors dead end reached from the census side.

## 7. Options, with ceilings and costs

Ranked by the most recall each could add on these sets if everything went right, against its cost.

| option | ceiling on these sets | cost | what it needs first |
|---|---|---|---|
| **A. The harness for the free model.** DeepSeek has only ever run under `ape_agent` with contract v2. Opus gains +0.10 (matcher) and +4 obligations (judge) from the X route over the project harness, with the same packet information. Two cells: brief X under `ape_agent` (isolates the brief), then an agentic shell harness over the local server (isolates the tools and the loop). | +0.10 on D12 by the Opus analogy, unmeasured for DeepSeek | $0 generation; the shell harness is a build (a day); 3 reps a cell, one seal with DX | note the X route's confound: Claude Code's system prompt, CLAUDE.md and MEMORY.md were in X's context, so part of its gain may be project text; the DeepSeek cell must carry none |
| **B. Analogue retrieval for the design asks.** Role-based retrieval of the comparison object, delivered as a named, refutable fact. | up to 0.075 of asks a set, the largest never-reached class | CPU for the retrieval; the 43-ask measurement before any reviewer run | the measurement on the labelled analogues (`review-design-comparison.md`) |
| **C. A deterministic closer battery** through `tacticAnalysis` and old-proof replay, as facts in the packet. | about 0.065 a set | compute; a persistent checker makes it minutes a PR | the static-analysis thread; the hand sweep went 0 of 3, so the linters must be shown to fire on these six first |
| **D. The fresh 40-PR set, AP against solo DeepSeek, three reps.** Closes the AP line out of sample and separates "fit to eight PRs" from "a window where solo DeepSeek is weak" (validation small12: DX 0.26). | for DeepSeek on validation-window PRs, about +0.15 to +0.20 at most (0.7 picked × (0.5 − solo's reach there, 0.21 on small12)); nothing for Claude | $0 generation, 3-4 h of `first`; matchers 0.5-1M subscription tokens; workspaces built (37 of 39) | a pre-registration naming the two failed builds' disposition; minimum detectable difference about 0.14 at 75 asks |
| **E. The per-place engine** (architecture B): every picked convention asked at every changed place, filed uncapped, unioned with solo. | 0.40-0.55 of in-census asks simulated on the ten PRs, the only design above +0.10 | about 1,000 calls a PR as specified; 25× the filings at 7% precision | adjudication of whether unasked departures are welcome; without it a 7%-precision generator cannot be told from a detector |
| F. More reps or variants of the AP delivery (top 10, `where`, family examples, no licence) | inside the noise on every fresh cell so far | $0 to small | a stated reason any variant escapes §3's bound |

**Recommendation.** Close the dossier and exam line as a recall lever and record it (§4); keep the
census, the ceiling and the mechanism as the thread's result and write them up (§5). Run D only if
the out-of-sample AP number is wanted for that write-up; it will not change the design verdict unless
the validation window turns out to be where the free tier is weak, which is itself worth knowing for
a $0 run. Pivot the reviewer work to A, because it is the one lever with a ceiling above the noise
that costs nothing and matches the record's own finding that model and harness changes moved the
wall where pipeline additions did not. B and C are the evidence stages with the next-largest
ceilings, both harness-side, both measurable before any reviewer run. E is where the conventions
direction leads if it is to continue, and its prerequisite is the adjudication question, not another
delivery.

## 8. What this does not settle

- **One probe set and one dev set,** 93 asks on 26 PRs, both in-sample for every design since
  stage C, and the dev set inside the Claude models' training window. The fresh set is the only
  untouched set with built workspaces.
- **The gap table in §6 is this note's own reading of the matcher cells and ask texts,** not blind,
  and the kinds are coarse. The per-kind ceilings are upper bounds on these sets, not predictions.
- **The harness lever (A) rests on an Opus analogy with a stated confound.** It is the cheapest
  measurement with a ceiling above the noise, which is why it leads, not because it is known to hold
  for DeepSeek.
- **Whether unasked departures are welcome is still the open adjudication,** and it bounds E, the
  places test and every volume judgement in the record. Nothing here moves it.
- **The ELM budget stands at £321 of £500** (read 2026-10-12); nothing recommended above spends it.
