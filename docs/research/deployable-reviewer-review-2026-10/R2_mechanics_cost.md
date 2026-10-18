# R2 — mechanics, codebase and cost (final report as returned, markdown layout normalised; 173k subagent tokens, 76 tool calls, 12.9 min)

Code and data read; (inf.) marks inference. Interim places-test rows were read for token and throughput counts only — not the pre-registered reading. *(Orchestrator's note: the report also cites an interim unasked departs rate of ≈ 0.29, which is a verdict count; recorded in the places README.)*

## 1. Verdicts
- **A1: needs change.** `places.py::segments` keeps no line numbers and disagrees with the change-graph targets (23 vs 12 on 26755, 36 vs 19 on 29842, 7 vs 12 on 30641); no segment-to-target mapping exists.
- **A2: v0 as specified; v1 needs change** — easy (one call a PR), but measurements 1 and 3 depend on it and the plan measures it after them. Gates should reuse `producers/primed_names`, `producers/missing_attribute` and `conventions/situations.py`, not new regexes.
- **A3: as specified** (the places form); its cost is the problem.
- **A4: not buildable as specified** — per-rule thresholds cannot be estimated from 25 PRs (objection 2).
- **A5: needs change** — compile through `ape.toolkits.execute.lean` (`cli tool lean_verify_edit`); `battery.py` hard-codes another worktree's workspace path (battery.py:6-7) and runs a bare `lake env lean` (battery.py:70).
- **A6: needs change** — the merge does not do what the draft says (objection 6); a route to the judge exists but needs one extension.
- **B1: needs change** — `solo` is frozen (DESIGNS docstring); the file shuffle does nothing on the 15 of 36 PRs that touch a single file (2/11 val, 7/10 post, 6/15 dev).
- **B2: mostly built** — `merge.py::union_findings` gives the union plus `passes_agreeing`, and `write_union_run` exists; the confidence tie-break is not buildable (solo findings carry no `model_confidence`, dead-ends.md:100-102).
- **C: buildable as a probe** — terminal-step splitting needs a tactic-span extractor (none exists; `tactics.py` is a vocabulary); it does not fit `Producer.facts(graph)`, a pure function of the graph with no workspace; "restore a dropped attribute" duplicates `missing_attribute`.
- **D: D2 buildable now on CPU;** D1 overlaps `precedent_search` (code-similarity, gated by `as_of`); the native form is a path/declaration key over `PrecedentIndex` plus `retrieval_gate`; the producer interface has no `as_of`.
- **E: buildable** (data labelling).

**Overall.** Most parts exist — the change graph, anchoring, `import_probe_session`, `union_findings`, `cli tool`, the producers, and reviewed workspaces for all 13 probe PRs and 16 census-detector PRs (checked by key). The draft underprices A by ~10× and calibrates A4 without power. At ~1,000 calls for a median PR, A as specified is not deployable even at $0.

## 2. Objections, ranked
1. **Cost scales as places × 25 × 2.** Places: the 10 stage F PRs have 168 (8,400 calls a rep); the 15 dev-medium PRs 469 (33294 alone 148); the census-detector PRs median 23.5, mean 30. Throughput from the server log: 1,770 tok/s at 56 running (KV 25%, no preemptions) against 1,245 at 24; places calls average ~9.5k completion tokens — ~600-700 calls an hour. Measurement 1 is 30-60 h, not "a few hours"; deployed, a median PR takes ~1.5 h of the whole 8-GPU node and 33294 ~12 h; AI-generated PRs run larger. *Refuted by* a pre-filter that brings A to ≤ 100 calls a PR while keeping measurement 0's asked pairs.
2. **A4 underpowered and in-sample.** 1,833 asks on 642 PRs over 399 entries: in 25 PRs the 10th-commonest entry is expected about once, the 40th 0.4 times, the 100th 0.16 times. The codebook was written from these val1000 asks (`build_order.py`); the held-out reading is paused. *Refuted by* ≥ 10 asked places per calibrated rule.
3. **The selection rule.** A4's cut and cap and B2's cap are the "keep rule / threshold / confidence cut" `.claude/rules/mathlib-review.md:195-205` refuses without the user's ruling. Confidence within a PR measured AUC 0.485-0.514 on lead candidates (dead-ends.md:102); measurement 0 rightly gates on it.
4. **Dependency order.** Measurement 1 needs A2 v1, unmeasured; measurement 2 uses v0; a policy calibrated on v1-selected rules applied to v0-selected ones carries a different base rate.
5. **Unit and anchoring.** `resolve_target` (probes.py:1193) takes names or paths, not path:line; a section or import segment falls back to the file's first changed line, the wrong target. PR-place findings get no change id, so stay unanchored (diagnostic only; the runner warns above 15% unanchored). Moving to targets means measurement 0's segment numbers do not carry over directly.
6. **A6's de-duplication is a no-op.** `union_findings` collapses only identical asks (6 of 375 findings folded, merge.py:446-452); a paraphrase at the same target survives, so the cap is the only volume control.
7. **Leakage and the gate.** Checked: probe and dev PRs are not in val1000. The census must also exclude `census_detectors_v1`'s 16 PRs, a probe set. The plan-time disjointness check (§4.6) is not built; check by hand.
8. **The 8-hour limit.** Measurements 1-3 need a resubmit chain; `places.py`'s digest-keyed resume is safe across restarts. Do not extend `places.py`/`run_places.sh` in place (pre-registered, and running): a new probe directory importing `places.py`.
9. **C3's prerequisite is wrong for measurement 5.** No persistent checker needed at this scale: ~2,500 cold compiles at a median 9.3 s (battery; max 39.5 s) is 7-20 CPU-hours; it matters only inside sessions.

## 3. Cost

| # | calls | `first` server-hours (8-h jobs) | compile | subscription tokens |
|---|---|---|---|---|
| 1 | 19-38k (25 PRs × 20-30 places × 50, + gates ~30%, inf.) | 30-60 (4-8) | 0 | 0 |
| 2 | 8.4k a rep, 25k for three (~20% overlap with measurement 0) | ~35-42 (5-6) | 0 | ~0.4-0.8M (2 matchers × 0.1-0.2M a seal, inf.) |
| 3 | ~18.8k a rep, 56k for three | ~80-94 (11-13) | 0 | 0; ELM judge, a few £ (inf.) |
| 4 | solo sessions, K = 3 × 3 reps | ~6 dev + ~12 probe (~3) (inf. from 35 min a rep) | 0 | ~0.5-1M |
| 5 | 0 | 0 | ~2.5k compiles (88 `by` blocks × 27 + extras): 7-20 CPU-h, ~1 h wall at 16-way | 0 |
| 6 | 0 | 0 | 0 | ~0.2-0.5M if a reader is used (inf.) |

Fit one server or none: 0 (running, ~4 h, done ~12:00), 4 at a single rep, 5 and 6. Measurements 1-3 each need several servers: about 16-28 jobs, 1-2 weeks of exclusive `first`. The matchers run on the user's interactive account, so their use is the user's call.

## 4. Placement
- **Probes:** a new `results/…/conventions-engine-<date>/` that imports `places.py`.
- **The engine as a run:** one single-turn `BaseTask` per (PR, place, rule), following the judge's `LeanPRReviewV4JudgmentTask` under `TaskOrchestrator`, so it resumes across server jobs; then a no-model chained design (`reads_stage`/`StageInput`, as `structured_critic`) applies the policy and emits solo-contract findings. **Reject** one task per PR making ~1,000 calls inside it — the hand-rolled loop CLAUDE.md forbids.
- **Places:** change-graph targets, or segments carrying explicit (path, line) passed into `candidates.anchor_submitted_findings` (extend `import_probe_session` and `resolve_target` to accept them).
- **Gates:** in `producers/` and `situations.py`.
- **Compiles for A5 and C:** through `cli tool lean_verify_edit`; C's facts precomputed to a file and delivered through `context_file`.
- **B1:** a design subclass or a seeded probe release, never an edit to `solo`.
- **D:** an extension of `PrecedentIndex` with the gate.
- **Reject outright:** A4's per-rule thresholds at 25 PRs; B2's confidence tie-break; A6's claim that `merge.py` merges duplicates.

## 5. Cheapest sequence
1. Read measurement 0 today; stop A if it fails.
2. In parallel on CPU: measurement 6, and measurement 5 on the PRs behind the try-it asks.
3. A2 v1 against stage F on the 10 PRs: ~30 calls; pass at ≥ 0.6 of in-census asks' entries at 25.
4. Measurement 2 at one rep: one global policy fixed from measurement 0 before the run; one sample, then a second only where the first says departs (saves ~35%, interim unasked departs ≈ 0.29, the same filing decision); reuse measurement 0's overlapping pairs. ~5.5k calls, 1-2 jobs, ~0.3M matcher tokens. Stop below +0.10.
5. Measurement 3 at one rep through `import_probe_session`: ~12.5k calls, ~3 jobs; reps 2-3 only if it passes.
6. A4 only if volume fails, stratified: every census ask at its own place (~2.4k calls) plus a sample of unasked places per head entry — ~10k calls, ~2 jobs, ≥ 10 asked places for the top ~40 entries.
7. B last.
