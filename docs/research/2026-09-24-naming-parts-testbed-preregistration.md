# Naming-parts testbed and judged check: pre-registration (2026-09-24)

Written before anything below was scored, then revised once, still before scoring, after an
adversarial review (three critics: leakage, baseline fairness, metric validity; "Review" at the end
says what they found and what changed). The implementation is `src/mathlib_review/analysis/
naming_testbed.py` at the commit that adds this file. A later change to any definition is an
amendment, dated, with its reason, in the "Amendments" section, made before a held-out number is
read.

**Question.** Given a theorem's name and its elaborated statement, does the statement-aware
evidence (`naming_parts`, "P") suggest the word Mathlib later renamed the name to more often than
the leading-token census (`naming_norm`, "B"), at a matched rate of flags on names Mathlib did not
rename? And, secondarily, does it put its finger on the renamed token?

This is the todo's step 3 (`docs/todo/naming-from-statement.md`). It measures the evidence, not an
arm; whether an arm files on better evidence is step 4.

## Protocol

1. This file and the harness are committed with P as it stands (`naming_parts` at
   `naming-parts-corpus/2`).
2. P may then be changed looking at the **dev** half only. Each change is an amendment below.
3. P is frozen: its code committed, and its blob digests and the corpus digest written into the
   "Frozen for held-out" section.
4. The held-out half is scored once. The harness writes it with `io.write_once`, so a second
   scoring that produces different bytes is refused, and `primary` refuses two halves scored by
   different P (their `pins` differ).

## Population (primary: temporal)

- **Corpus** `E` = `36a2b22f66b8bb2434674cace18feb371e29c8f7` (2025-11-21, the oldest built
  snapshot). **Renames from** `L` = `b72c03457b221ba87896ffcb09b91929aaebb809` (2026-03-04, the
  newest). Both read through the statement index (`statement-export/1`).
- **Item**: a theorem `old` whose `@[deprecated]` entry at `L` names `new`, such that `old` is a live
  theorem at `E`; `new` does not exist at `E` and is a theorem at `L`; the binder kinds and types
  and the conclusion of `old` at `E` equal those of `new` at `L` (binder names ignored).
- **Strata**: `leaf` (the leaf changed) and `namespace` (only the namespace moved); and `source` /
  `nosource`, whether `old` has a source declaration at `E` (`@[simps]` projections, class fields
  and alias-generated names have none). **The primary is `leaf/source`.** The others are reported.
- **Excluded**: an item whose old or new leaf is an identifier on a deprecation, alias or
  declaration line added by the squash commit of any PR in `dev-raw-0.3.0` (the 138-PR superset of
  every evaluation set), or whose introducing PR is one of them. A rename an evaluation PR made,
  or towards a name one introduced, is that episode's gold. Names the compiler or an attribute
  generates (`eq_<n>`, `eq_def`, `congr_simp`, `inj`, `injEq`, `sizeOf_spec`, `proof_<n>`,
  `match_<n>`, auto-named `inst…`) are excluded from items and controls.
- **Introducing PR**: the PR of the first squash commit in `E..L` whose pickaxe (`git log -S`) on
  the new leaf touches the new name's module file.
- **Components**: connected components of (edit signature) and (introducing PR). The edit
  signature is (leaf tokens removed, leaf tokens added); a pure reordering keys on the tokens that
  moved, a namespace move on the two namespaces. One PR's mirror renames and one cascade's members
  are one component.
- **Split** by component: `dev` if blake2b-8 of the component's smallest member name is even,
  `held-out` if odd.
- **Already inspected** during development, excluded from the held-out score whatever their half:
  `tendsto_of_antitone`, `Cardinal.nat_lt_aleph0`, `fderiv_deriv`,
  `TopologicalSpace.CompactOpens.map_toCompacts`, `continuous_mul_left`, `Ordinal.iSup_pow`,
  `Submodule.starProjection_coe_eq_isCompl_projection` (also gold, 33337).
- **As built** (a population fact, no method run): 2,987 deprecations at `L`; 167 leaf and 47
  namespace items kept; 32 excluded as named by an evaluation PR; 3 with no resolved PR. Primary:
  **dev 71 items in 35 components** (largest 9), **held-out 78 in 38** (largest 7).

## Controls

A theorem live at `E` and at `L` under the same name with the same statement, not the old or new
name of any deprecation at `L`, not generated, with a source declaration. For each item, up to
three: same module first, then the same parent module, leaf token count within one of the item's,
never sharing a token the item's rename removed, in blake2b(`old|control`) order. Controls are
assigned dev first, and a control a dev item uses is never used by a held-out item.

## Methods

- **B**, `naming_norm` as its context tool computes it: the text signature of `old` read from `E`'s
  source (`parse_major_declarations`, exact full-name match), `conclusion_subject`, `norm_index(E)`,
  `prefix_verdict`. One flag, at token 0, iff the verdict is `established` or `emerging`.
- **P**, `naming_evidence(old at E, corpus E, index E, exclude=[new])`. Flags are
  `evidence.flags(min_n=5)`: rows other than `aligned`, `same_lhs` and `prime` with `n >= 5`,
  ranked by **strength**, the Wilson 95% lower bound of `k/n`. An item's score is its top flag's
  strength. (`prime` is shown to an arm but is not a flag: its count is one corpus-wide habit,
  identical for every name.)
- **Leave-self-out, both methods**: every item and control is a live theorem at `E`, and a PR's
  declaration never is. So P subtracts the name's own contribution from every count it reads (the
  lexicon keeps it: one sentence in ~236k), and B subtracts the name's own count from its subject's
  prefix population.
- **Suggested words, both methods**: a suggested single word is itself; a suggested whole name
  contributes the tokens it adds to the old leaf (multiset difference). B's suggestions are its
  dominant prefix and its `rename_candidates`; P's are each row's `suggests`. A namespace
  suggestion `X.` is compared with the new name's namespace.

## Outcomes

- **The edit**: `difflib` opcodes from old leaf tokens to new leaf tokens (a prime is its own
  token). Changed positions: old indices in `replace` / `delete` opcodes; for a pure reordering,
  the positions whose token differs; an insertion adds none. Added words: new tokens minus old
  tokens, as multisets. Shape: `first` / `interior` / `last` (one token substituted), `added`,
  `removed`, `reordered`, `several`.
- A flag **points** if it suggests an added word, or a namespace flag names the new namespace.
- A flag **localises** if its token positions meet the changed positions, or a namespace flag names
  the new namespace. There is no other path.
- **At `τ` and `k`**: P's kept flags are its top `k` with strength at least `τ`; B's is its one
  flag. An item *points* / *localises* if a kept flag does.
- **Chance-corrected localisation**: `loc - π`, where `π` is the probability that as many distinct
  positions as the kept flags claim, placed at random among the old tokens, would localise.

## Primary comparison (held-out), and the reading rule

- **Measure**: *point* with `k = 1` (P's single strongest flag), over held-out primary items with at
  least one added word. A word suggestion cannot be met by chance or by multiplicity, which
  localisation can: at these name lengths three random positions localise ~92% of items.
- **`τ*`**: the smallest threshold, among the scores the dev controls take, at which P flags no more
  dev controls than B does. **Matched** iff such a threshold exists below 1; if not, the reading is
  *inconclusive (unmatched)* whatever else holds.
- **`Δ`** = P's point rate at `τ*` minus B's, with a 95% interval by paired cluster bootstrap over
  components (2,000 resamples, seed 20260924). The component-mean `Δ` is reported beside the
  item-weighted one.
- **Control guard**: the same bootstrap over the held-out controls' per-control `P - B` flag
  difference (controls attached to their item's component); its upper end must be at most +3 pp.
- **P better** iff matched, `Δ >= +10 pp`, the interval excludes 0, and the control guard holds.
- **Not shown to be >= 10 pp better (provisional)** iff the interval's upper end is below +10 pp.
  This does not close the todo. Closing it needs a replication on a second population, and a list
  of the untried designs: another substrate, relations without parts, camelCase-aware tokens
  (`String.splitCase` exists in Mathlib), an order model (P has none), and another ranking statistic.
- Anything else: **inconclusive**.
- **Power, stated before scoring**: at ~70 eligible items in ~38 components the 95% half-width is
  roughly 8-17 pp (simulated by the metric critic on the real component sizes), so the minimum
  effect detectable at 80% power is about +15 pp, and above +20 pp if components are internally
  correlated. A true +10 pp is read *P better* well under half the time.

**Secondary, reported, no rule**: point at `k = 3`; localisation and chance-corrected localisation at
`k = 1` and `k = 3`; the comparison restricted to **B-measurable** names (signature found, subject
resolved, population present), with `τ` re-matched on B-measurable dev controls -- if P wins the
primary but not here, the win is reported as coverage, not as better evidence where both tools
speak; singleton components only; by edit shape; which row kind P's top flag was and how often it
pointed; the funnel counts; the `namespace` and `nosource` strata.

## The judged check (step 4, paid)

Run after the held-out testbed is scored, whatever its result: the testbed measures the evidence
and this measures the arm, and a better tool the arm ignores is the todo's "built but not the
lever" outcome, which is worth knowing.

- `bench_cli --arm naming --pr 33337 --pr 33421 --negatives-per-pr 3` with procedure variant
  `statement_naming` (the naming arm holds `naming_statement` beside its standing tools, and a
  supplement says what it returns and how to weigh a count; it names no declaration and carries no
  gold), config `configs/pr_review_v5_verdicts_fanout4.yaml` (the a3-a5 configuration), attempts
  1-3. Retrieval is live (`4442b34`); in a3-a5 it was dead.
- **A site passes** at >= 2 of 3 attempts filing a rename there: ce7b5d2e at d2466bcc (the coercion
  lemma) and 6b02b611 at 4dc53e21 (`round_eq'`). The null on disk is 0 of 3 at both (a3-a5).
- **The wall moves** iff at least one site passes. The sibling hit 64e1164f must stay >= 2 of 3;
  filings at negative units are reported beside it.
- Stated now, from exercising the tool once by hand at these sites: at d2466bcc the evidence argues
  *against* the gold (the corpus names `ContinuousLinearMap.toLinearMap` `coe` in 62 of 72 aligned
  tokens), so a pass there is not expected; at 4dc53e21 the prime row names what differs from
  `round_eq` (`HDiv.hDiv`, word `div`).
- If the wall moves, the change is attributed to the tool only after a baseline bench with live
  retrieval (same config, `baseline` variant, three attempts) stays at 0 of 3 there; that run is
  conditional on this one passing, so it is not pre-spent.
- Cost: a3-a5 billed $1.06 for three attempts of this fixture.

## Frozen for held-out

Frozen 2026-09-24 after amendment 1, at the commit that adds this section. P is `naming_parts` as
committed in `18e580a`, unchanged since; the harness is `naming_testbed` after amendment 1. Every
scored half records these pins, and `primary` refuses two halves whose pins differ:

- `naming_corpus`: `5108d95019454caf91f3c82fbcd49b2336bd42ed69ca899d9b7f463bd25dd145`
- `src/mathlib_review/analysis/naming_testbed.py`: `e2a37bd6eab6e7e599ba0e17749f91d9afa74964`
- `src/mathlib_review/evidence/operators/naming_norm.py`: `5e2e9d4e4fc531773df55d11111260ee3939ec43`
- `src/mathlib_review/evidence/operators/naming_parts.py`: `38a386ec79f98e4600826cbb7bd0bc11174f94ab`
- `src/mathlib_review/retrieval/statement_export.lean`: `4654dd65591161540a4ba31347278515aeb43083`
- `src/mathlib_review/retrieval/statement_index.py`: `6a2cd073062ed8d75278c92b888dbb641de4f42c`
- `statement_index_manifest`: `0cef0080716755f373978606d0b2776a8fb64395710c3cf39afe91c9669eea43`

## Amendments

**1 (2026-09-24, after scoring dev, before any held-out number).** Dev (`dev_a1.json`, 71 primary
items, 213 controls): at `τ*` = 0.867, matched to B's 5.2% dev-control rate, P points in 3 of 66
eligible items and B in 1 (inconclusive). With no threshold, P's strongest flag suggests a word the
rename added in **33 of 66 (50%)**, B's in 1 -- but P then flags every control. Per kind, on dev:
`word_mismatch` fires on 65% of items and 34% of controls, `unnamed_part` on 37% and 32%,
`namespace` on 44% and 30%, and the strengths overlap. So the evidence names the right word far
more often than it separates renamed names from never-renamed ones. **P is not changed**: the
features that might separate them (a mismatch whose word the corpus never uses for the part; the
preferred word's share) overlap on dev too, and tuning a detector on 66 items would fit noise. Two
secondaries are added, with no rule: *unthresholded point@1* with the control flag rate it costs,
and the AUC of P's score (items against controls) beside B's. The harness change moves its pin, so
dev is rescored (`dev_a2.json`) by the harness that scores held-out.

## Review (2026-09-24, before commit)

Three adversarial critics read the first draft and the harness; every blocker and major issue they
raised was taken, as follows.

- **Localisation was mostly detection plus chance** (metric critic, blocker): the mean changed
  fraction of an old name is 0.6, so one random position localises 60% of items and three 92.5%,
  and B's token-0 flag is at chance by construction. The primary became *point*; localisation is a
  secondary, reported beside its chance correction.
- **Suggestions were compared unevenly**: B's candidate names were split into tokens (including the
  old remainder, which let B "point" at words the name already had) while P's analogue rows
  suggested whole names that could never match a word. Both are now normalised to the words a
  suggestion adds. Only P's position-less flags could localise through a suggestion; that path is
  gone.
- **Clusters leaked across halves** (leakage critic, blocker): 11 PRs had items in both halves,
  mirror twins among them (`csSup_…` / `csInf_…`, `mul_le_mul_left` / `_right`); and every pure
  reordering and namespace move shared the empty signature, one 60-item cluster, all held-out.
  Components now join signature and introducing PR, and empty signatures key on what moved.
- **Insertion-neighbour credit** handed B's token-0 flag 17 items where token 0 was kept. An
  insertion now adds no position.
- **`τ*` could fail silently and the control guard was absolute**: the match is now recorded and an
  unmatched reading is inconclusive; the guard is a bootstrapped bound. `τ` is chosen among observed
  scores, and ranking uses the Wilson bound, because raw shares put a 4-of-5 row above a
  900-of-1,000 one and made `names_nothing` rows (a word's alignment rate, ~1.0 for most words)
  pass every grid value.
- **B cannot read ~60% of names** (baseline critic): its text parser rejects conclusions headed by
  `↔`, `∈`, `∀`, `∃`. The primary measures the tools as deployed; the B-measurable secondary says
  whether a win is coverage.
- **Generated and sourceless names** entered items and controls; generated ones are excluded and
  sourceless ones are their own stratum.
- **P was not frozen and nothing tied the halves to one P**: the protocol above, pins and
  `write_once`.
- **The eval-PR filter** read only deprecation lines; it now reads declaration lines and excludes
  by introducing PR. **Known limit**: leaf-level exclusion cannot catch a convention carried over
  from an evaluation episode (dev holds `epsilon0 -> epsilon_zero`, which applies eval PR 33198's
  `aleph1 -> aleph_one` decision), and 14 dev items come from PRs merged in January 2026, the window
  `eval-set-selection.md` proposes for the next evaluation set: those PRs go on its exclusion list.
- **Power**: the negative reading was relabelled provisional and needs replication.
- Minor, taken: controls sharing a removed token with their item were false alarms by construction
  and are excluded; the prime row's share was one corpus-wide constant (0.40) for every name, so it
  could not be a flag -- it is reported as such here, and whether to give it a per-name share is a
  dev-half decision (an amendment if made).

## Result (held-out, scored once, 2026-09-24)

`results/pr_review_v5/naming_testbed/{heldout_a1,primary_a1}.json`; pins equal to the frozen ones.
Held-out primary: 78 items in 38 components, 65 with an added word; 228 controls.

| measure | P | B | Δ | 95% interval | reading |
|---|---|---|---|---|---|
| **point@1 at `τ*` = 0.867 (primary, matched)** | 0 / 65 | 2 / 65 | **−3.1 pp** | [−10.5, 0.0] | **not shown to be >= 10 pp better (provisional)** |
| control flag rate at `τ*` | 4.8% | 1.8% | | guard [0.0, +6.3] | the guard would also have failed |
| loc@1 at `τ*` | 2.6% | 5.1% | −2.6 | [−11.5, +5.6] | |
| loc over chance @1 | +2.1 | −0.1 | +2.2 | [−2.6, +7.8] | |
| B-measurable only, point@1 (`τ` = 0.793) | 9.4% (of 32) | 6.2% | +3.1 | [−15.8, +22.2] | inconclusive |
| **unthresholded point@1** (amendment 1) | **41.5%** | 3.1% | **+38.5** | **[+23.2, +54.8]** | P then flags 100% of controls |
| AUC of the score, items vs controls | 0.668 | 0.530 | | | |

**What it says, at the altitude it supports.** As a *detector* -- does this name need renaming? --
the statement evidence is not shown to beat the prefix census at the census's own false-alarm rate:
at that rate it barely fires (0 of 65 point), its score separates renamed names from never-renamed
ones only weakly (AUC 0.67), and 65 items in 32 components cannot resolve less than ~15 pp. As a
*namer* -- given that a name is renamed, what to? -- its strongest row proposes the word Mathlib
actually chose in 27 of 65 held-out renames (41.5%; 33 of 66 on dev), against 2 for the census. Both
halves agree. Names depart from the corpus's habits almost everywhere, renamed or not, so the rows
cannot be the reason to ask; they are good at saying what to ask for once there is a reason.

This is not the todo's closed negative: the primary is provisional by construction, and the
untried designs remain -- another ranking statistic (the dev breakdown says row *kind* separates
better than row strength: `word_mismatch` fires on 65% of renamed names and 34% of controls), an
order model, camelCase-aware tokens, relations without parts, and a second population to replicate
on. It bears directly on the arm: a tool whose rows fire on most names is a precision risk if the arm
reads a row as a reason to file, which is what step 4's negatives measure.
