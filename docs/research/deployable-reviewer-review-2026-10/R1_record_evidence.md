# R1 — the record and the evidence (final report as returned, markdown layout normalised; 160k subagent tokens, 44 tool calls, 8.0 min)

## 1. Verdicts
- **A (engine): keep, narrowed.** The only component aimed at the two largest gap classes. A2 v1 and A4 must be measured alone first, and every threshold restated against DX's 3-rep union.
- **B (aggregated solo): narrow.** Keep the union, drop the agreement rank and cap. The undecorrelated union is already on disk.
- **C (exhaustive execution): narrow, then fold in.** Keep old-proof replay, drop the terminal-step sweep; the rest belongs in the static-analysis-pass todo.
- **D (history): defer.** D2 stays a CPU probe only, threshold restated.
- **E (census robustness): defer,** except the cross-map duplicate merge and the triggers for the ~40 token-triggered entries A2's gates need.

**Overall.** The draft's comparator is the single DX rep. The record already holds a better deployable reviewer than that: DX unioned over its three reps. Against that union only A has a ceiling that clears noise; C adds at most +2 of 46, D at most +1, and B's design part (decorrelation) about one ask. Two parts of the draft rest on cited evidence the record has since contradicted or not tested: B2's agreement signal was refuted out of sample, and "the filing decision lost" was measured on Claude only. A4 is a selection design, which the user ruled must wait (2026-09-22).

## 2. Objections, ranked
1. **The wrong baseline.** DX's 3-rep union is a deployable reviewer that already beats solo: dev union 11 against a mean of 7.67 with control findings 0, 0, 2 (`local-ds41-2026-10-06/README.md:201-212`); probe union 16 against a mean of 13. A costs ~12,600 calls on the 13 probe PRs (252 places × 25 rules × 2, computed from `items.json`); B costs three sessions. Measurement 3's bar (+3 over DX's mean) is about DX's own union (+3.3). *Refuted if* A ∪ DX beats DX ∪ DX ∪ DX at matched volume.
2. **B2's agreement signal was tested out of sample on solo passes, and it is chance** (`ensemble-union-2026-10-02/README.md`, dev, Opus passes): hit rates by k 0.50 / 0.67 / 0.29 / 0.44, within-PR AUC 0.482, saturated at gold anchors (64 of 90 paired findings at k = 4). The draft cites only the earlier in-sample 0.29-0.89; the 2026-10-01 plan ruled agreement "a label, never a vote" (line 138). *Refuted if* agreement is monotone in hit rate on decorrelated DeepSeek passes.
3. **A4 is underpowered, contaminated, and selection under another name.** 1,833 asks over 759 PRs with feedback: 25 PRs carry ~50-60 asks over 399 entries, so nearly every per-rule threshold rests on 0-1 positives (inferred). The census sentences were written from these PRs' asks, so departs at asked places is inflated there. Stage H's per-rule `rate` design was the worst (2 of 12 at an ask, AUC 0.602, "ranks the wrong rules first", Result 6). It repeats `dead-ends.md` "Publication as selection" (user ruling 2026-09-22); plan 2026-10-01:138 also declined category suppression until adjudication labels exist. *Refuted if* leave-PR-out on the other-years asks (211-248, mapped to the census but not used to write it) keeps ≥ 0.6 of asked pairs at ≤ 10 filings a PR.
4. **Measurement 0's cap reading is optimistic for deployment.** The test holds 1,431 pairs (~110 a PR); 25 rules give 6,300 (~485 a PR) — 4.4× the competition for 10 slots at a base rate of 42/6,300 = 0.7%. The decoys are other rules; A4's real population is unasked places of rules in play (the confounded secondary readout), where stage H measured 0.56-0.64. Stated model confidence has been at chance three times (`selection-signal.md`: 0.486-0.516).
5. **"The filing decision is where in-session delivery lost" was measured on Claude only.** Stages F (+0.03) and G (+0.00) were Opus without the precedence paragraph. On DeepSeek DP's precedence moved +0.20 / +0.18 with no volume effect (Result 7). AP (stage F's picks under DP's precedence on DeepSeek) — the dossiers round's step 3, decompose's M4 — never ran. Tried and failed on Claude, untried on DeepSeek; not "cannot work".
6. **C's ceiling over solo is +2 of 46.** The targeted battery's successes on probe PRs are v0016, v0062, v0063, v0131, v0132; DX reaches v0016, v0131, v0132 in all three reps (`ceiling-residual-2026-10/table.txt`). The terminal-step finishers went 0 of 3 on their own asks (v0067, v0068, v0092 fail to compile). Measurement 5's "≥ 5 produced" is therefore already met by the targeted record and says nothing about gain over solo; on dev 0 to +1 (`after-structure.md` §3). It repeats the detectors dead end (execution-checkable leaders hold 7% of census asks); the reopen condition is not met.
7. **D's ceiling is at most 1.** Of the six never-reached asks only v0053 is history-shaped; p0010 is the library's orientation, an analogue, not history. D1 as drafted reads other PRs' comments on the same file — Mode A precedent priming (13 vs 11 on 41 PRs), whose reopen needs recognition or ranking, not priming. The survey's distinction ("one PR's own history") does not describe D1.
8. **A3 has no tools, but most pool rules need one:** the steelman of round 2 counted 19 of 26 pool rules needing a compile or lookup; the "bare sentence writes the change at the place" premise is unblinded and unmatched (ladder README:157-181).

## 3. Reject outright
- B2's ranking and cap by agreement (2).
- A4's per-rule thresholds fitted on 25 val1000 PRs (3); report suppression rates as a reading only.
- C1's terminal-step sweep: 0 of 3 targeted; the can/does gap of the linter-as-oracle dead end (81% of missed gold already had a candidate at the line); Mathlib ships it as `tacticAnalysis`.
- D1 as priming on other PRs' comments.
- Measurement 5 as stated.

## 4. Missing from the draft
- DX's 3-rep union as the comparator for measurements 2-4.
- An AP arm in measurement 2: the same picks delivered in-session under DP's precedence, so the engine is tested against its cheaper rival.
- Analogue retrieval (`after-structure.md` §4, `review-design-comparison.md`): design asks are 23-24% of round-1 asks, comparison asks 9-10%; three of dev's nine never-reached obligations are analogues; p0010, p0003, v0105 are analogue-shaped. The record ranks it the highest ceiling; D is the weaker evidence-source choice.
- The static-analysis pass and Mathlib's linters (`static-analysis-pass.md`) as C's implementation; the persistent checker C depends on is unbuilt.
- A2 v1 measured alone before measurement 3 (which bundles selection, engine and calibration — decompose §7 rejected three variables at once).
- Calibration on other-years asks; the memory caveat (census merges predate DeepSeek-V4.1).
- AI-generated PRs: places and volume scale with size (PR 33149 alone holds 67 of the 375 union findings); report recall and volume by label (CLAUDE.md).
- The ladder's blind matching before measurement 2 (already generated).
- What A can reach on dev: of the nine obligations no Opus cell reaches, five are conventions a check can state (dot notation twice, `@[to_fun]`, a primed name, a sibling rename), three analogues, one documentation structure; +3 on dev needs nearly all the convention-shaped ones, and dot notation and primes overlap the detectors already built.
- The closest prior for A3 is D1 `structured` (forced per-cell verdicts): on Opus consistency, not a frontier; on gpt_5.2 98% `no_issue`; never run on DeepSeek.
- A naming clash: the draft's D1/D2 collide with the record's D1 (`structured`) and D2 (critic).

**Most recall each could add** (inferred unless marked): **A** — DX misses 30 of 46 (read); ceiling sessions reach 24 of those, DP 20 (computed); at v0's 22/33 retrieval and a cap of 10, **+3 to +6 of 46** over DX's union in-sample, **+1 to +3 of 23** on dev. **B** — +3 of 46 and +3.3 of 23 (read, undecorrelated); decorrelation +1 to +2 at most. **C** — +2 of 46 (v0062, v0063, read); 0 to +1 on dev. **D** — at most +1 (v0053). **E** — 0 directly.

## 5. Order, and the cut
1. Measurement 0; also read asked against unasked-exact (A4's real population).
2. Restate every threshold against DX's 3-rep union, from runs on disk ($0).
3. The ladder's blind matching.
4. A2 v1's recall@25 alone (decompose's M2, ~2 h on `first`).
5. A4 on the other-years asks, capped and uncapped recall.
6. Measurement 2, with the AP arm and the DX-union comparator.
7. Measurement 3.
8. B's decorrelation (local, cheap) and the D2 CPU probe, at any point.

**Cut: measurement 5** — threshold already met by the targeted record, gain over solo capped at +2, and it needs the unbuilt persistent checker; old-proof replay moves into A5 or the static-analysis pass.

Nothing written to the repository; nothing run beyond counting; the places test's outputs not read.
