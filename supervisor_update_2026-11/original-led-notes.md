# Notes on the original-led revision

Prepared for 4 November 2026. Presentation: [HTML](original-led.html),
[PDF](original-led.pdf), [Markdown and speaker notes](original-led.md).

This revision follows the [October deck](../supervisor_update_2026-10/slides.md).
The added “Four parts, at two levels” overview from `meeting-v2` is omitted.
The original “1 · The problem” divider remains. There is no duration target.

## What stayed, and what changed

| October material | Location in this copy | Treatment |
|---|---|---|
| Problem divider and theoretical framing, slides 2–8 | 2–8 | Verbatim, including notes |
| Design-space divider and prior-work comparison, 9–10 | 9–10 | Same content; comparison table uses a smaller layout class |
| Literature findings, 11 | 11 | Same five comparisons; uses the detailed November reference's qualifications |
| Thesis and solo baseline, 12–13 | 12–13 | Same thesis; four questions stated explicitly |
| Q1: decomposition, 14 | 14–15 | Same comparison, with context fragmentation and repeated understanding explicit |
| Q2: reasoning/harness/model and residuals, 15–16 | 16–17 | Model table retained; interpretation moved to notes; residual population corrected |
| Q3: conventions, census, ceiling, 17–19 | 18–21 | Motivation added; original convention formulation retained; reporting views corrected |
| Q4: delivery and the example, 20–21 | 22–23 | Same question and example, with later qualifications |
| Subsequent convention experiments | 24–29 | Validity, library evidence, acquired bank, focused application |
| Status and next design, 22–23 | 30–31 | Updated status and questions for discussion |
| Five-point synthesis and sources, 24–25 | 36–38 | Synthesis updated and moved to backup; original source list retained |

Backups 32–35 retain the GPT disposition positive, preparation pilot, practice
check and exploratory `dslope` suggestion. The [detailed November reference](slides.md)
and [experiment map](experiment-map.md) preserve further material; this copy does
not attempt to present every experiment.

## What motivated the conventions work

There were several stages, rather than a single origin. These are contemporaneous
records, not a claim that the work was planned in the order of this presentation.

1. **10–11 September: missed and changing idioms, and an inadequate denominator.**
   The [drift plan](../docs/plans/2026-09-10-convention-drift-mechanics.md) starts from
   reviewers failing to reach for conventions Mathlib was adopting. The
   [catalogue](../docs/research/mathlib-convention-catalogue.md) explains that proposed
   discovery mechanisms had been fitted to a few familiar examples. It sought a
   denominator against which discovery could fail. Its binding-linter inventory also
   highlighted that many already encoded rules were handled by CI. These documents
   preserve early interpretations; their hypotheses are not all current conclusions.

2. **29 September: characterize the conventions themselves.** The opening of
   [conventions-nature](../docs/todo/conventions-nature.md), recorded in `b291e80d`,
   quotes the user's concern: “it's really learning what conventions hold at a given
   point and in a given window/scope that is fundamentally hard.” The motivating
   design-ask reading found a one-sentence principle behind 30/31 asks, but only eight
   documented principles. The resulting questions were count, scope, conflict and
   maturity. This directly motivates the census used in the October slides.

3. **30 September: test knowledge as a lever on missed asks.** The
   [residual audit](../results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.md)
   studied 67 residual asks: 37 reached by nobody and 30 reached only by Claude.
   In 63, every missing reviewer had inspected the object. Both readers identified
   convention/mechanism knowledge in 25. Its stated consequence, also recorded in the
   [replan](../docs/plans/2026-09-30-post-carryover-replan.md), was to test try-it evidence
   and convention supply directly instead of funding another coverage intervention.

4. **4 October: establish whether supply can help in the best case.** In the
   [ceiling-probe brief](../docs/todo/conventions-ceiling-probe.md), recorded in
   `898a7be5`, the user asked for a ceiling before further designs: if conventions are
   useful, briefing the reviewer should improve judgments. Entries were deliberately
   selected from the target asks. The positive therefore motivates testing transfer;
   it does not establish autonomous selection or applicability.

The presentation uses stages 2–4 as its bridge. The earlier drift/catalogue work
stays in these notes so that the motivation is traceable without adding a historical
detour to the main talk.

## Empirical corrections carried forward

The [evidence register](evidence.md) remains the source for the later results.
In particular: the 67 residuals are not all Claude successes; the ceiling uses
in-census reporting within each comparison; the single “≤5% of applicable places”
interpretation is withdrawn; and the stated-grounds evidence does not establish
that taste is a small residual. Historical recovery, a checked alternative and a
useful request remain distinct. The bank and pilot usefulness panels are unfinished.

The fragmentation slide expresses the user's design assessment, supported by the
context/overlap record. It does not claim that the experiments isolated fragmentation
as the cause of the measured cost or recall differences.
