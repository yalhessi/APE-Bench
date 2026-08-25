# Phase 9 fixed-orchestration repetition 1 verdict

## Verdict

Operational pass. Efficacy comparison pending.

The fixed pipeline executed exactly as designed: both bounded model opportunities terminated with a
request, both supplied structured edits, both edits compiled, and ingestion preserved two
verification artifacts. Together with the deterministic naming request, synthesis produced three
lineage-complete findings and zero control findings.

Do not yet claim a recall gain over holistic review. The cost-matched baseline union exists but has
not been semantically judged, and one fixed-pipeline wrapper verdict was truncated after emitting
explicit `issue_match=true, resolution_match=false` fields. The original parser conservatively
recorded that pair as false/false. The parser now recovers explicit booleans from partial JSON while
retaining a manual-audit marker; the fixed semantic run needs one fresh-cache retry.

## Current automated result

| Metric | Result |
| --- | ---: |
| Model units completed | 2/2 |
| Model requests | 2/2 |
| Verified model edits | 2/2 |
| Deterministic requests | 1 |
| Synthesized findings | 3 |
| Selected control findings | 0 |
| Matched-scope obligations | 8 |
| Automated issue recall | 2/8 = 25% |
| Automated resolution recall | 2/8 = 25% |
| Automated paired-candidate issue precision | 2/3 = 66.7% |

The two unambiguous issue and resolution matches are:

- canonical API recovery for `Metric.isCover_maximalSeparatedSet`;
- naming recovery for `Metric.card_maximalSeparatedSet`.

The wrapper candidate targets the correct `coveringNumber_le_packingNumber` issue and supplies a
compiling high-level API rewrite. Its malformed judge output explicitly began with issue true and
resolution false, consistent with all three earlier Phase 5 judgments. The manual interpretation is
therefore 3/8 issue recall, 2/8 resolution recall, and 3/3 candidate-level issue precision, pending
the mechanical retry.

## Corrected stage accounting

The first finalization artifact incorrectly keyed issue hits by candidate alone, allowing a match on
one obligation to mark another obligation at the same target as recovered. `final-v2` corrects this
to `(candidate_id, obligation_id)` and `(finding_id, obligation_id)` keys:

| Stage | Full PR | Matched scope |
| --- | ---: | ---: |
| Recovered | 2 | 2 |
| Candidate semantics | 2 | 2 |
| Candidate construction | 1 | 1 |
| Source retrieval | 9 | 3 |

The semantic retry should move the wrapper obligation from candidate semantics to recovered if the
judge reproduces its already-emitted boolean verdict.

## Holistic extension

The missing holistic work unit completed with two advisory candidates:

- a real `extenal` module-doc typo, not represented in benchmark gold;
- a request to document `finite_minimalCover`, which is weakly supported and not a frozen maintainer
  obligation.

Combined with the existing matched work unit and control, the baseline union contains eight raw
candidates. Two are on the PR 33438 control. This reinforces the expected precision contrast, but
the semantic judge must quantify matched-obligation recall before comparison.

## Decision

Complete the fixed retry and baseline-union judge. If the outputs are structurally valid, proceed to
repetitions 2 and 3 without changing methods or prompts. Repetition 1 already passes the
implementation-readiness gate; the remaining calls measure stability and comparative efficacy.

## Completed comparison

The fresh retry and cost-matched baseline judge both completed. The fixed retry reproduced the same
automated totals with a valid JSON response for every pair, so the wrapper disagreement is semantic,
not a transport failure.

| Metric | Fixed pipeline | Holistic union |
| --- | ---: | ---: |
| Raw candidates | 3 | 8 |
| Location recall | 4/8 = 50% | 7/8 = 87.5% |
| Automated issue recall | 2/8 = 25% | 3/8 = 37.5% |
| Automated resolution recall | 2/8 = 25% | 1/8 = 12.5% |
| Paired-candidate issue precision | 2/3 = 66.7% | 3/5 = 60% |
| Raw PR 33438 control candidates | 0 | 2 |

The systems recover complementary obligations. The fixed pipeline recovers the canonical API and
`encard_` naming requests exactly. The holistic union recovers two local proof-simplification issues
and the empty-branch issue, but misses canonical API and naming. Its extra extension candidates are a
real documentation typo outside benchmark gold and a weak missing-docstring request.

The semantic judge is not reliable enough to interpret the one-obligation automated recall gap as a
real advantage. It rejects the fixed wrapper candidate as an issue miss because its valid high-level
rewrite omits the maintainer's exact `by_cases!` and renamed-lemma details, despite the rubric saying
a different fix may issue-match. Conversely, it grants exact resolution to a holistic `simpa` proof
for a gold request explicitly asking for `grind`. Under a consistent issue/resolution separation,
the wrapper is issue true and resolution false, while the `simpa` candidate's exact resolution is at
least doubtful.

The final decision is therefore to proceed with repetitions 2 and 3 unchanged. Repetition 1 shows:

- fixed orchestration is substantially more selective and control-safe;
- it trades broad local location coverage for stable recovery of its three registered methods;
- current method coverage, especially nine full-PR source-retrieval misses, remains the dominant
  ceiling;
- repeated results and manual audit are necessary before any efficacy claim.
