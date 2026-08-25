# PR Review v4 paired three-sample retrieval verdict

## Verdict

Reject the current lexical context-to-ask policy as a stable semantic-recall intervention. Retain the
temporal corpus, safe cutoff, provenance, and prompt-artifact infrastructure, but do not expand this
treatment to the nine-PR pilot.

The no-retrieval baseline produced zero issue-hit samples out of three. Retrieval produced one out
of three, entirely from its first sample, and failed both repetitions. Neither arm produced a
resolution match. The frozen semantic judge has now confirmed every included pair in all six
samples. This is weak directional evidence at most, not a replicated gain.

## Three-sample comparison

| Metric | 0.8.9 baseline | 0.8.11 retrieval |
| --- | ---: | ---: |
| Samples with an included issue hit | 0/3 | 1/3 |
| Pooled included obligation issue recall | 0/3 | 1/3 |
| Pooled included obligation resolution recall | 0/3 | 0/3 |
| Mean PR 33098 model candidates | 2.33 | 3.00 |
| Mean raw PR 33438 candidates | 2.00 | 1.33 |
| Mean included location recall | 0.67 | 0.78 |
| Selected PR 33438 findings | 0/3 | 0/3 |

Per-sample included location coverage was `1/3`, `3/3`, and `2/3` for baseline and `3/3`, `1/3`,
and `3/3` for retrieval. The modest average difference is dominated by sampling variance and does
not translate into stable issue recall.

## New-run audit

- Baseline repetition two generated four PR 33098 candidates. The eligible pairs concern helper
  boilerplate, the wrong `h_nonempty` binder, and the docstring; all are strict issue mismatches.
- Baseline repetition three generated a proposed simp attribute and the same wrong-binder request;
  both are strict mismatches.
- Retrieval repetition three generated a simp attribute, the wrong-binder request, a shorter subset
  proof, and a request to remove or alter local `C`. The last request conflicts with the maintainer's
  desired `C`-based canonical-lemma refactor; all eligible pairs are strict mismatches.
- All 16 new model candidates were evidence-inconclusive and all three new runs selected zero
  findings.

The new generation calls cost $0.571767 in total.

## Design consequence

The retriever currently supplies a similar historical context and its maintainer ask, but not the
adopted resolution that demonstrates the exact transformation. The observed failure is therefore
consistent with the model recognizing broad style pressure without recovering the canonical API or
proof rewrite.

Next implementation priorities:

1. Decompose `pr33098_i01` into target-level atomic obligations and preserve the old frozen metric
   alongside a decomposition diagnostic.
2. Extend precedent artifacts with a temporally valid adopted-resolution object from the historical
   PR, keeping context, ask, and resolution separately hashed.
3. Rank transfer triples by problem-context similarity and resolution applicability, not comment
   text or code-token overlap alone.
4. Keep three samples per arm as the minimum development-screen protocol for stochastic generation.

## Commands to run

No external commands remain for this round. All six samples are generated, ingested,
evidence-checked, selected, location-evaluated, and semantically judged. The next work is an
implementation round: decompose composite gold and build adopted-resolution precedent artifacts
before authorizing another paid smoke.
