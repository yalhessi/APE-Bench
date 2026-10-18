# Decompose the PR, shrink the conventions per part: what the second adversarial round left of the idea (2026-10-09)

**The idea** is the user's (2026-10-09):
- split the PR into parts;
- use syntax, then cheap semantic calls, to cut the census's ~400 conventions to a handful per part;
- review the parts with those conventions.

**The user's two questions.**
1. How do we decompose the entire PR into parts such that each part needs only a subset of
   conventions?
2. Can we choose a correct subset given a partial PR?

**The round's files** (`decompose-and-shrink-review-2026-10/`): the draft under review with the user's
words (`draft.md`), the briefs as sent (`briefs.md`), and the four reports as returned (`R1_decomposition.md`,
`R2_subset_selection.md`, `R3_behaviour_record.md`, `S_steelman.md`).

Nothing was run beyond counting. Every count below that a reviewer computed is that reviewer's own
exploratory figure, marked *(R1)*, *(R2)* and so on. Those figures are not pre-registered and not
re-checked here.

## 0. The answer

**Q1: decompose into overlapping lenses, not a partition, and keep the whole PR in view.**
- The lenses: the declaration (with its doc-comment and attributes), its family, its file and the
  PR, with library search as a tool in every lens. `components.py` already builds these.
- Coverage of *places* then holds by construction, so it tells us little.
- The real limits are three:
  - **Context:** about a third to a half of asks need something outside the part.
  - **Emission:** one decision spread over parts cannot be said as one.
  - **Demand.**
- And nothing in the record shows that splitting the *reviewer* adds recall. The failure on record is
  the decision to file, not where the reviewer looked.

**Q2: an applicable subset, yes; a demanded one, no; and "sound" and "5-10" cannot both hold.**
- **Syntax alone:** part kind cuts ~400 to about 134 (proof parts) or 234 (declaration parts), and it
  leaks.
- **Syntax with frequency ranking:** the right convention in a part's top 10 for 0.36 to 0.46 of asks
  inside the census's era, and 0.22 out of it.
- **The best on record:** stage F's per-PR Opus selector, 0.45 at 10.
- **A sound set is tens of conventions a part.** Cutting it to 5-10 means predicting which situations
  a maintainer would raise, which no design has done (AUC 0.56-0.64).

**The binding unknown is behaviour, not selection.**
- DP's licence to file has only been measured on lists where every convention was true.
- Wrong conventions under it either get overridden (stage G) or filed through (13 of 14 unasked
  detector facts).
- Its false-departure rate at unasked places has never been measured.
- Two architectures survive, below (§4). Four measurements, none decided, would settle which unknown
  binds (§5).

## 1. The round

- **Who ran it.** Four Opus 5.5 subagents, read-only and independent: R1 on decomposition and
  coverage (Q1); R2 on subset selection (Q2); R3 on behaviour, cost and the decomposition record; S,
  the steelman.
- **Cost.** About 541k subagent tokens. The primary week went from 96% to 97% and the five-hour
  window to 7% (read 05:42 and 05:55 EDT).

## 2. Q1: how to decompose

- **What the record supports** (R1, R3, S): overlapping lenses anchored on change targets, where a
  target sits in several units at once.
  - Today's units come from the change graph, and after the repack 32 of 38 request groups sit inside
    one unit and 3 of 42 obligations span units (`docs/todo/batching-work-units.md`).
  - Disjoint parts packed by hash and size split families. 47% of units once held no declaration.
- **Context is the real limit.**
  - About 45% of asks need context from outside one part *(R1, 600 facet asks)*: family or siblings
    17-18%, library 12%, design 6%, PR 5-6%, file 4%.
  - On the census's own grain labels, 71-77% of asks are line or declaration grain *(R1)*. The record
    says 24% need more than one declaration.
  - **AI-generated PRs, the eventual target, lean further outside parts.** PR grain is 18-21% against
    about 9% on the rest *(R1, R2)*, and only 49-53% of their asks are local to one part *(R1)*.
- **Hence "anchors, not contexts"** (S): the part narrows where to look, never what the model can
  read.
- **Emission across parts.** In 12 of 15 multi-declaration asks the arm saw every target and could not
  say them together. With the `patch_set` channel fixed, the reviewer filed none (gpt-5.2 and Qwen
  only; untested on Opus or DeepSeek).
- **Splitting the reviewer itself has no support** (R1, R3).
  - The coordination passes on Claude reached 5-6 of 11 asks, the same as the plain brief.
  - Work-enumeration's no-generalist condition reached 3 of 10, against solo's 0.40.
  - The family division reached 1 of 10 obligations, against the ten arms' 3.
  - The closest strong-model test is D1 `structured` on Opus: per-declaration × six concern cells with
    forced verdicts. It reached 10 and 10 of 23 against the hygiene mean of 8.3, and bought
    consistency, not a frontier.
- **Convention groups and code parts are different splits.** Shrinking needs a code-part key to
  *filter* conventions. It does not need the review split by convention group (R1).

## 3. Q2: a correct subset from a partial PR

**What each shrinker achieves** (recall@k: the share of asks whose census entry is in the part's or
PR's top k):

| shrinker | at 5 | at 10 | at 25 | source |
|---|---|---|---|---|
| none (global frequency) | 0.12 | 0.20 | 0.35 | R1, computed |
| lexical / kNN over census hunks | | 0.16-0.26 | | R2, computed |
| part kind + frequency, val1000 leave-PR-out | 0.38 | 0.36-0.46 | 0.52 | R2, R1, computed (two classifiers) |
| part kind + frequency, other years (out of era) | | 0.22 | | R2, computed |
| the ask's own family (an oracle) | 0.38 | 0.50-0.55 | 0.62 | R1, R2, computed |
| stage F, Opus selector per PR | 0.18 | 0.45 | 0.67 | the record |
| a model ranker per part over all 438 entries | | 0.5-0.65 | 0.7-0.8 | R2, inferred, untested |

- **Syntax shrinks, but leaks.**
  - Part kind keeps 134 entries for proof parts and 234 for declaration parts, and 19-25% of asks fall
    outside their entry's usual part kind *(R2)*.
  - Only 8 of the 41 entries with ten or more asks have 90% of them in one part kind *(R2)*.
  - The object predicts the family for proof, prose, layout, binders, names and PR asks (85-100%), but
    not for statements or families (29-68%), where the design conventions spread *(R1)*.
  - So hard syntactic gates suit only the token-triggered entries: imports, attributes,
    `variable`/section, named arguments, primes, docstring prose. That is about 40 entries *(R2)*.
    Elsewhere part kind should rank, not filter.
- **Sound and 5-10 are incompatible.**
  - Stage G's 52 rules alone fired 19.6 times a PR, up to 20 at one place *(R2)*. Over 438 entries a
    sound set is likely tens a part.
  - Maintainers raise 1 in 20 to 1 in 400 of the places a convention's situation occurs. Cutting to
    5-10 is therefore a demand prediction, which failed (stage H).
- **What a partial view cannot select:**
  - library scope against file scope (30458);
  - migrations in progress (32875's `grind`);
  - "keep the old proof";
  - the PR's theme;
  - the individual reviewer's preference.

  Five of DP's seven gains on DeepSeek needed siblings, the file, the old version or the PR's purpose
  *(R2)*.
- **The ceiling for any shrink.**
  - 8.9% of asks have no principle.
  - About one ask in ten brings a principle the census lacks.
  - Out of era, 15% of principled asks fall under entries absent from val1000.
  - So even perfect selection reaches about 0.75-0.82 of all asks.

## 4. The two architectures still standing

Both decompose into anchors that keep the whole PR in view, rank conventions per part, and restrict
scrutiny to validity (a quoted line, a compile, a lookup), with a failed check filed as a question
rather than dropped.

| | A. one whole-PR reviewer, per-part shortlists as a ledger (R1, R3) | B. situation-scoped exhaustive checks, unioned with solo (S) |
|---|---|---|
| **mechanism** | the solo session reviews as now, and receives per part a ranked list of conventions with DP's delivery | every census entry with a trigger; every (part, entry) whose trigger holds gets one DeepSeek turn in the ladder's bare-sentence form; every `departs` is filed and unioned with the solo review |
| **keeps** | whole-file judgement, unbriefed reach, one emitter | no filing bar (it is the session's decision that F and G lost on); census-wide coverage |
| **needs** | shortlist recall at about 10 per part; tolerance to wrong entries under precedence | a trigger for each of 438 entries; discrimination at unasked places |
| **its risk** | wrong entries overridden (G) or filed (detectors); F's dilution | volume: perhaps 10-30 filings per ask *(S, inferred)*; a detector with a model in it if `departs` stays near 0.79 at unasked places |
| **ceiling** | 0.85 in census × hit@10 × DP application ≈ 0.25 (at F's 0.45) to 0.38 (at 0.7) *(S)* | 0.85 × 0.64 at the place × 0.79 departs ≈ 0.40-0.43, against DX's 0.19 *(S)* |

**R3's estimate for the draft as written.** 25-60 distinct conventions a PR against at most 2.8 true
ones. At stage G's decoy filing rate (0.2-0.3 per wrong convention a PR) that is 5-18 false filings a
PR. Asks reached a finding would fall from DP's 0.62 to about 0.10-0.21, where stages F and G failed
their guards.

## 5. The measurements that would settle the unknowns, cheapest first (none decided)

| | what it settles | how | cost | threshold, as each reviewer stated it |
|---|---|---|---|---|
| **M1** (R1, S) | does a syntactic decomposition hold the places, and how short can its lists be | rebuild val1000's change graphs and components (`build_structure.py`, no model). Situate each ask in a lens. Rank census entries per (lens, changed part, declaration kind) by frequency, trained on other PRs, and by same-part retrieval. Score on val1000 leave-PR-out and on the 211-248 other-years held-out asks | CPU, minutes, $0 | places in the right lens ≥ 85%; recall@10 ≥ 0.50 with a median ≤ 100 (part, convention) pairs a PR carries step 2; < 0.35 means the semantic step must do all of it and beat 0.45 |
| **M2** (R2) | can a model choose per part better than a per-PR selector | DeepSeek ranks all 438 per part (the part, the PR text and diff, the sentences) on the 287 held-out units; it also states how many apply | about 290 calls, 1-2 h on `first`, $0 | recall@10 ≥ 0.60 means yes; ≤ 0.45 means no better than per PR; a median "applies" count over 15 rules out a sound 5-10 |
| **M3** (S) | does the bare sentence discriminate at places no maintainer asked about | the ladder's U form at stage H's 199 unasked flagged places beside its asked ones | about 2 h on `first`, $0 | `departs` at unasked places ≥ 0.7: a per-place engine (B) passes its triggers through |
| **M4** (R3) | does DP's licence survive wrong conventions | each of stage F's ten PRs: its exact entries filled to 10 with its stage F picks that sit behind no ask, DP's delivery, three reps, matched | 30 sessions, about 1 h on `first`; matchers 0.3-0.5M subscription tokens | holds if reach ≥ DE + 0.10 with decoy filings ≤ 1 a PR; collapses at ≤ DE + 0.05, or ≥ 3 decoy filings a PR, or findings above DP + 3 |

- **M1 and M2** bear on selection (Q2), and M1 also bears on the decomposition (Q1).
- **M3 and M4** bear on behaviour, which R3 and S argue is what binds. M4 is a best case for
  architecture A: ten PR-wide entries, so if it collapses, the per-part version does too. M3 bears on
  architecture B.
- **Not proposed before these:** any per-part review run (R3: it would bundle decomposition,
  selection and precedence, three variables, as stage D could not separate its own three).

## 6. Making the census robust for this use (S, R2)

- **Situation fields per entry:**
  - the part types it applies to;
  - a trigger, tagged syntactic or semantic;
  - `not_when` and `check_kind` (stage G's rule-writer rubric is the template; it wrote 52);
  - scope by area and era;
  - maturity.
- **Validation out of sample.** Each trigger must fire at its own held-out asks' places, with its
  firing density measured on census PRs as stage H did.
- **Merges and saturation.** Merge the readers' duplicates through the cross-map (312 `same` pairs).
  Resume the paused saturation reading.
- **The tail.** Give the 286 thin entries semantic triggers tied to a part type, not syntactic ones
  fitted to one to three examples.

## 7. Rejected, with the evidence

| proposal | why | reopens if |
|---|---|---|
| Rationale (correctness, conciseness...) as a scoping key or a review split | The top five rationales each tag 416-488 asks (25-29%), so none shrinks. "Correctness" is 34 asks (2%). A rationale reviewer is the family division again (all four) | a rationale is found that separates part kinds |
| Family or part kind as a hard filter | Leaks 19-25% of asks. Only 8 of 41 frequent entries sit ≥ 90% in one part kind (R2) | a better part labeller brings the leak under 5%; token-triggered entries are exempt |
| Concurrent agentic sub-reviews per part with no whole-PR session | No-generalist 3/10 against solo 0.40; the family division 1 against 3; the specialists' abstentions 104 of 136 `already_correct`; whole-file judgement lost (R1, R3, S) | a matched probe shows the same per-part conventions reach more as concurrent parts than as one whole-PR packet |
| A hard top-5-10 cut | Stage F's entries behind asks sit at ranks 7-22; sound sets are tens a part (R2, S) | a ranker reaches recall@10 ≥ 0.6 per part (M2) |
| A demand cut ("would a maintainer raise it here") as the selection criterion | Stage H, AUC 0.56-0.64; artifact-only selectors 0.62 (R2, R3, S) | a new signal: the reviewer, the PR's theme, the file's regularity |
| Lexical or kNN retrieval over census hunks as the ranker | 0.16-0.26 at 10, below the frequency prior *(R2, computed)*; Mode A priming did not transfer | same-part retrieval in M1 beats frequency |
| DP's examples inside a per-place engine | In the ladder the examples lowered `departs` (88 against 93 of 117) and flipped three asks the bare sentence reached (S; provisional, unmatched) | the ladder's blind matching reverses it |
| Scrutiny as verify-and-drop | Stage G lost 8 asks that had a candidate at the place that way. Scrutiny checks validity only, and a failed check becomes a question (S, R3) | -- |
| Opus for this shape over three reps | About 140 part-sessions a rep is 6-8 five-hour windows of the user's interactive account (R3) | a cheaper Claude route |
| Decomposition, selection and precedence bundled in one first run | Three variables at once (R3) | -- |
| `coverage_gaps` read as coverage of the work | It counts mandatory jobs that did not succeed, not whether the plan was adequate (R1) | -- |
| A shrink keyed on declaration shape alone | The facet-keyed join dead end (fit 4-8%) (R1) | -- |
| Disjoint parts packed by hash and size | Split families across units; 47% of units held no declaration (R1, `batching-work-units.md`) | -- |

## 8. What this does not settle

- **The reviewers' computed figures are exploratory and unchecked here.** R1's and R2's part
  classifiers differ, and their in-era recall@10 (0.46 against 0.36) differs with them.
- **Every behavioural figure comes from 33-39 asks on one probe set.** The ladder figures are
  unmatched.
- **Demand stays open.** Architecture B's gain cannot be told from volume until whether unasked
  filings are welcome is adjudicated (`docs/todo/adjudication-rubric.md`). Whether the recall-only
  goal tolerates more volume is the user's call.
