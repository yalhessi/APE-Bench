# Evidence tiers and traces — the warrant channel is one tier wide, and three tools are invisible

**Status** — open; every item below is a code fix plus re-measurement on committed runs
**Cost** — no generation spend

## 1. `repository_measurement` is declared everywhere and produced by nothing

`schema/evidence.py:146` declares four tiers. Across the three held-out A reps, **907 findings carry
exactly two**: `verified_compile` (17/23/20, 6.6% pooled) and `model_assertion` (everything else).
**Zero `repository_measurement`, zero `lexical_rule`.**

Motivating example: `naming_norm` returned a counted population 52 times in rep1 alone, including
`Dense.continuous_upperBounds → upperBounds 27/27 established` — the one obligation condition A hits
in all three reps. `_EVIDENCE_BY_METHOD` maps `naming_norm.v1 → repository_measurement`, but that
table is read only by the deterministic v4 path; no v5 code path reaches it. So "27 of 27 lemmas use
this prefix" serialises identically to "this name would be clearer".

This is the missing tier the convening talk's §13 and §20 both depend on, and it is one hop.

What would close it: have v5 finalisation read the arm's `naming_norm` trace row for the invocation
and stamp the tier when the arm cites the verdict; pin the hop with a test in the style of
`fe7a8a7`'s. Then re-report the tier distribution on the three committed reps.

## 2. Two collectors can never say anything

`pr5_A_lead_heldout12_v2_rep1`, assertions by collector: `local_context` **268 / 268 inconclusive**;
`policy` **151 / 151 inconclusive**; `repository_search` 200 assertions of which 7 supports, 19
contradicts, 174 inconclusive; only `lean_compile` (33 supports of 141) and `issue_kind_verifier` (5
of 6) are decisive. Pooled packet outcomes over three reps: **847 packets, 39 supported (4.6%), 66
contradicted, 737 inconclusive**.

Corrected mechanism: `local_context` **is** structurally incapable — `evidence.py:290-293` hardcodes
`inconclusive` with `assertion_scope: context`, and `evidence.py:526-528` computes supports and
contradicts only over `assertion_scope == 'claim'`. `policy` is not: 121 of its 151 assertions come
from a real `lint-style.py` run reporting `violation=False`, so it *ran* and found nothing — which
is a verdict the packet then discards as inconclusive. Those are different bugs and need different
fixes.

What would close it: give `policy` and `repository_search` a decisive verdict shape (the search
collector already returns counts and simply never claims), or stop running them and record the
collection cost saved. Re-measure packet status on the three committed reps.

## 3. `naming_norm`'s veto fires on a tool failure, not a corpus fact

**213 of 213 naming_norm calls in rep1 carry `result_count` 0 on 161 of them (76%)**; rep2 212
(76%), rep3 207 (75%), fanout 67%, forced 60%. `context_tools.py:622-639` has exactly one branch
that writes `result_count: 0`, conditioned on
`subject.token is None or subject.confidence != "high" or population is None`, and it returns "The
corpus has no counted opinion about this declaration's subject … Submit nothing on naming unless a
maintainer precedent says otherwise."

So three times in four the arm is told the corpus has no opinion when what actually happened is that
the tool could not resolve the subject. See [specialist-arm-contents.md](specialist-arm-contents.md)
for what that does to the naming arm's submit rate.

## 4. Three tools write no trace row, and one of them gates an unrun condition

- **`proof_profile` appends no trace on any path.** `_append_trace` is defined at
  `context_tools.py:40` and called at :153, :221, :276, :411, :625 and :671 — never inside
  `_register_proof_profile` (:440-553). Every v5 trace file records exactly four tool names. Yet
  `configs/bases/v5_solo.yaml:37` grants `proof_profile` to the solo arm and its own comment says
  "every call lands in `context_trace.jsonl` — which is both how the grant is shown to have been real
  and what the leak audit reads." Conditions B and C use that grant.
- **`naming_norm` has three untraced `success: False` returns** (:587-590, :592-593, :617-620), all
  before any append — the defect `e86498d` fixed for `precedent_search` one commit earlier in the
  same session, where the `refuse()` helper exists precisely so a refused call is distinguishable
  from a call never made. (The *consequence* claim — that the 213 traced calls are a loose lower
  bound — was checked and does not hold; fix the code anyway, because the next failure mode will
  differ.)
- **`investigation_id` is null on all 285 candidate rows** while `context_trace.jsonl` keys every
  retrieval call by `invocation_id`. Reconstructing the key as
  `work_unit_id + '#' + (spec_id or 'generalist')` joins only 110 of 159 candidate invocations. On
  that 69%-clean join, candidates from sessions that called `precedent_search` match gold 5/33
  (15.2%) against 59/528 (11.2%) — indicative, underpowered, not trustworthy at that join rate.
  Correction: this is *not* a serialization drop; `investigation_id` is assigned nowhere in the v5
  tree, so it is an unimplemented field, and the fix is to carry `invocation_id` instead.

Carrying `invocation_id` through to `candidates_discovered.jsonl` and pinning it with a key-set test
is what makes PROJECT-STATUS §6's outstanding question — does retrieval change reviewer output? —
answerable on runs already paid for.

## What would close the group

One commit for the three trace fixes plus a strengthened test: change
`test_every_context_tool_records_a_gate` from "every trace row has a gate" to "every registrar in
`_REGISTRARS` appends a row on every return path". Then one commit for the tier promotion, and
re-report tiers and per-tool gold-match rates on the six committed held-out runs.
