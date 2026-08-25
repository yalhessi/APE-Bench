# Coverage ledger — spec (treatment 1 over the 0.9.0 stable core)

*Status: v0.1 draft for iteration. Created 2026-07-15.*
*Baseline it must beat: 0.9.0 3-rep smoke — per-run issue recall 2/6 ± 1, union 4/6, stable 0/6,
control FP 1/3 reps (`dev-pilot-0.9.0-stable-smoke3{,-rep2,-rep3}`).*

## 1. The problem, precisely

The 3-rep baseline shows the generator's issue hits are **stochastic coverage, not capability
limits**: each rep hits a different 1–3 of 6 obligations (`XX.`, `X.X`, `.X.`, `X..`), the union
reaches 4/6, and only 7–9 candidates are emitted per run. The model *can* produce most of the
matching candidates; a single run *doesn't reliably try* the investigations that produce them.

Two prior attempts at this failed the same way and define what the ledger must NOT be:

- **0.8.9 "facet battery"**: the instruction *"examine every target across all concern families"*
  in the system prompt. No effect on volume or semantics — instructed coverage without a
  mechanism is ignored (third confirmation of the project-wide lesson: instruction ≠ structure).
- **v3 apply-all forced findings**: one *finding* per checklist item. Moved recall +27pp but
  produced "checklist doesn't apply" filler findings, because disbelief had no channel other than
  a finding.

The ledger combines what worked in both and removes what failed: **coverage is a recorded,
machine-validated artifact** (structure, not instruction), and **disbelief gets its own channel**
(a `no_request` record, never a finding).

## 2. Core object

One `InvestigationRecord` per **cell = (change target × concern family)** in the work unit's scope:

```jsonc
{
  "schema_version": "ledger1",
  "cell_id": "cell:<target_id>:<family>",
  "primary_change_id": "change:...",
  "concern_family": "proof-golf",          // the existing 8+other taxonomy
  "status": "candidate | no_request | not_applicable | deferred",
  "basis": "<one sentence naming the code element(s) actually inspected and why this status>",
  "candidate_ids": ["candidate:..."],       // required iff status == candidate
  "inspected_entities": ["entity:..."]      // optional, strengthens audits
}
```

Semantics:

- `candidate` — the investigation concluded a maintainer would plausibly request something;
  the candidate objects are unchanged (same schema, same grounded-ask contract, same downstream
  evidence/selection path).
- `no_request` — the investigation ran and concluded no ask is warranted. The basis must name
  what was inspected ("proofs of `card_maximalSeparatedSet` and `maximalSeparatedSet_subset` are
  single-step after the dite reduction"). **This is where defends live** — they are ledger
  content, never findings, preserving the v3 assertion-channel lesson.
- `not_applicable` — the family cannot apply to this target kind (e.g. `documentation` on an
  import-header target). Expect these to be mechanically pre-fillable over time (§7).
- `deferred` — the cell was out of budget for this call and MUST appear in a later sub-batch
  (§4). A run whose final merged ledger still contains `deferred` cells is incomplete, exactly
  like a work unit that failed.

## 3. Contract changes

- `submit_candidates` → `submit_review(investigations=[...], candidates=[...])`; prompt version
  bump; runner/ingestion version `ledger1`.
- **Ingestion validates completeness**: the scoped cell matrix (targets in the work unit × 8
  families) must be exactly covered — no missing cells, no duplicate cells, `candidate` cells must
  reference ≥1 ingested candidate, `no_request`/`not_applicable` must carry a non-empty basis.
  Violations are re-prompted once, then recorded as ingestion failures (visible in the run
  manifest, like work-unit failures today).
- Candidates keep the existing intake checks (primary-subject grounding etc.). The ledger adds no
  new candidate fields — it wraps them.

## 4. Budget and sub-batching

A work unit with `T` targets defines `8T` cells. Single calls handle ≤ `max_cells_per_call`
(initial: 24). Larger matrices are split **deterministically by family group** into sub-batches
(same work unit, `ledger_batch` index), mirroring the windowing precedent: batches are work,
never silent drops. The merged ledger is validated for completeness at the run level.

Initial family grouping per call (keeps related investigations together):
`[correctness, proof-golf, generalization]`, `[duplication, naming]`, `[documentation, style, scope]`.

## 5. What the ledger buys diagnostically (even before any recall gain)

Per-cell accounting makes every missed obligation classifiable, mechanically:

| miss class | ledger signature | responsible component |
|---|---|---|
| judgment miss | gold obligation's cell = `no_request` | the taste gap, now measurable per cell |
| taxonomy miss | cell = `not_applicable` | family definitions |
| instantiation miss | cell = `candidate`, judge says wrong aspect | generation quality |
| budget miss | cell = `deferred` in final ledger | sub-batching bug (should be impossible) |
| coverage miss | cell missing | ingestion bug (should be impossible) |

This is the v3 funnel methodology rebuilt inside v4: the union-vs-per-run gap stops being a
mystery and becomes a table. The **false-`no_request` rate on gold cells** is the ledger's own
quality metric, and the audit protocol samples `no_request` bases exactly like judge verdicts.

## 6. Pre-registered experiment

Paired against the 0.9.0 baseline, same three work units, **3 reps per arm**, frozen judge:

- **Success**: mean per-run issue recall ≥ 3/6 (i.e. at or above the baseline *union*), control
  FP ≤ 1/3 reps, zero duplicate findings, candidate volume ≤ 3× baseline.
- **Rubber-stamp failure signature** (the named risk): recall unchanged AND ≥ half of the
  gold-obligation cells are `no_request` with generic bases. Response: escalate to per-family
  passes (§8 Q1), not to more prompt language.
- **Flood failure signature**: recall up but control FP > 1/3 reps or volume > 3× — the evidence
  gate then carries the burden; check whether the control FPs are `supported` packets (selection
  policy problem) or leaked unsupported candidates (bug).

Prerequisites (independent small fixes, land before the arm): selection dedup; naming-family
support threshold (comparative evidence required — one sibling pattern match is a prior, not
support). Both were exposed by rep2 of the baseline.

## 7. Interactions with existing machinery

- **Deterministic discovery** pre-fills `correctness` cells whose compile/linter checks ran:
  status `candidate` (with the deterministic candidate) or `no_request` ("target compiles").
  The model is told these cells are already resolved — spend budget elsewhere.
- **Control PRs**: ledger `no_request` records make control abstention *explicit and auditable*
  (today it's just the absence of findings).
- **Evidence/selection: unchanged.** The ledger governs generation only. Nothing about
  publication weakens; candidate floods still cost nothing downstream unless evidence supports
  them.
- **Sibling propagation (treatment 2, later)** composes naturally: a `candidate` cell can seed
  re-investigation of sibling targets' same-family cells. Out of scope for v0.1.

## 8. Open questions (iterate here)

1. **Single-turn matrix vs per-family passes.** v0.1 = single turn + validation (cheapest). If
   rubber-stamping appears, per-family passes (one model turn per family group, ledger merged)
   isolate attention per family at ~3× call cost.
2. **Should `no_request` bases be adjudicated?** A mini-judge could score bases against gold
   obligations ("was this no defensible?") — expensive, maybe only in audits. v0.1: manual sample
   in the standing audit, 5 bases per run.
3. **Cell granularity: target vs entity.** Multi-declaration targets may hide per-declaration
   misses inside one cell. v0.1 keeps target-level; revisit if the miss table shows instantiation
   misses concentrated in multi-entity targets.
4. **`other` family**: keep as a 9th optional cell (no completeness requirement) so genuinely
   novel observations have somewhere to go without breaking the matrix.
5. **Cost**: expected +30-80% prompt tokens per unit (ledger instructions + record output). The
   smoke arms will price it; if per-family passes become default, revisit `max_cells_per_call`.

## 9. Out of scope for v0.1

Norm discovery / repository expectation evidence (treatment 3 — targets the two never-hit
knowledge-frontier obligations, which no amount of coverage fixes); sibling propagation
(treatment 2); any selection-policy change beyond the two prerequisite fixes; multi-sample
union-of-reps as a *production* strategy (interesting, but it dodges the consistency problem the
ledger is meant to solve — keep it as a comparison row, not an arm).

## 10. Review response (2026-07-17)

### Findings

1. **High: the ledger proves response completion, not investigation completion.** A sentence in
   every cell can still be generated mechanically after shallow inspection. The proposal risks
   turning the ineffective facet instruction into mandatory JSON. Require structured inspection
   provenance, not only `basis`.

2. **High: successful deterministic checks must not close a concern family.** "Target compiles"
   means no compiler failure, not that there is no correctness request. Likewise, passing a linter
   does not resolve style review. The proposed prefill would suppress genuine investigation.

3. **High: "gold cell" evaluation is invalid under the current taxonomy.** The decomposed
   `encard_` rename is labeled `style` in gold, while a correct candidate would naturally use
   `naming`. A semantic hit could therefore coexist with a false `no_request` in the supposed gold
   cell. Obligations need curated acceptable-family sets, or diagnostics must follow semantic
   candidate matches rather than exact family equality.

4. **High: the experiment is not budget matched.** The smoke units contain 8, 4, and 2 targets.
   With the 24-cell limit, one ledger repetition requires approximately seven calls versus three
   baseline calls. Any gain could come from extra sampling or family isolation rather than the
   ledger. The cost estimate also appears too low.

5. **Medium: the status model forces unjustified certainty.** `deferred` covers budget exhaustion,
   but there is no honest disposition for "investigated but insufficient context." Without
   `inconclusive` or `needs_followup`, uncertainty will become either a filler candidate or a false
   `no_request`.

6. **Medium: the success criterion does not measure the intended consistency gain.** Mean recall
   of 3/6 can still consist of entirely different hits in every repetition. Also, 3/6 is not "at or
   above" the baseline union of 4/6. Require per-obligation hit frequency and reduced variance.

7. **Medium: the premise is stated too strongly.** The baseline proves four obligations are
   sometimes recoverable. It does not prove all misses are coverage failures. Two obligations were
   never recovered and plausibly require missing repository knowledge.

8. **Medium: candidate scope and synthesis remain unchanged.** The ledger still inherits work-unit
   boundaries and cannot express episode-wide propagation, competing fixes, or one coherent "same
   here" finding. That is acceptable for Treatment 1, but it should not be presented as solving the
   broader graph-review problem.

### Verdict

Pursue the ledger next, but as a **targeted diagnostic for stochastic investigation coverage**, not
as the general solution. The three stable repetitions make this a well-motivated experiment: 3/6,
2/6, and 1/6 issue recall; 4/6 union; zero obligations stable across all runs.

Revise it to an **investigation ledger v0.2**:

```json
{
  "scope": {
    "primary_change_id": "change:...",
    "related_change_ids": []
  },
  "concern_family": "naming",
  "disposition": "candidate | checked_no_request | not_applicable | inconclusive | needs_followup",
  "inspection_methods": ["local_read", "repository_search"],
  "inspected_entity_ids": ["entity:..."],
  "artifact_refs": [],
  "candidate_ids": [],
  "followup": null,
  "basis": "..."
}
```

Key modifications:

- Store deterministic compile/lint outcomes as check results, not final ledger dispositions.
- Require inspection methods and source references.
- Add `inconclusive` and `needs_followup`.
- Allow related targets and future scope expansion.
- Evaluate obligation misses through semantic matching plus acceptable family mappings.
- Audit every gold-intersecting cell in the smoke, not five random bases.
- Apply selector/dedup fixes to both arms before comparison.

### Revised experiment

Use three arms:

1. Existing baseline.
2. Budget-matched family-group passes without a ledger.
3. Family-group passes with the ledger.

This distinguishes extra inference budget, attention isolation, and ledger accountability. Compare
each against a cost-matched union-of-samples row.

Success should require:

- mean issue recall improves over the budget-matched arm;
- at least two obligations are recovered in two or more repetitions;
- false `checked_no_request` decreases on the four recoverable obligations;
- the two never-hit obligations remain separately classified as the knowledge frontier;
- zero selected control findings under the corrected selector;
- paired issue precision does not decline.

After that, sibling propagation and repository-norm discovery should become separate treatments
composed over the ledger.

### Commands to run

No external commands yet. The specification should be revised before implementation or another
paid run.
