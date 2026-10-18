# R1 — mechanism lens (final report as returned, markdown layout normalised; 156k subagent tokens, 59 tool calls, 9.1 min)

**1. Verdict: narrow.** "Understanding" exists as a separable failure, but in the record it is small (≈3–5 of DP1's 16 misses; ≈4–5 of Claude E1's 10) and sits in mid-rank/tail conventions (P041 r23, P100 r18, P254 r107, P153 r130), while the planned first slice targets the head, whose misses are search/execution and decision. The exam as designed cannot separate understanding from the decision: it supplies the convention and the place, frames the case as applicable, and leaves unasked departures unscored. Run a cheap diagnostic replay on misses already on disk first (§5); it gives the user the stage-by-stage map they asked for. "Designs tried point away from understanding," not "understanding cannot matter."

**2. Objections, ranked**

**O1. Same sentence, different outcome: the misses are not the representation.** In stage G 6 of the 10 E-only asks were G1 `partial` (v0030, v0060, v0061, v0067, v0068, v0092; read: `match_G_val/unblinded.json` m1). E1 reached all six with the *same* sentences, asserted. DP's gains include asks on record as decision misses: p0007 "Mathlib does not require", p0000 "too minor", v0029 "would not ask to revert" (README 1146-1153; plan l.32-60). *Refuted if* given sentence + place + "it applies", the model still fails to produce the merged change on most misses.

**O2. The slice targets the wrong conventions.** Top-10 entries hold 8 of 39 asks (fact sheet); DP1 misses 5 (v0067 P005, v0105 P011, v0092/v0093 P018, p0005 P063): `standard`-form entries whose fix is place-specific (`infinite_pigeonhole_card_lt`, `positivity` at l.194, `simpa using h`) — Phase 1's `try_it_not_tried` class (19 of 67, `mechanisms.md` l.55). My keyword scan of `findings.jsonl` across all six DE/DP reps (unmatched, inferred) finds v0093 and v0067 filed in none.

**O3. The exam scores the wrong distinction.** "Asked" under its framing tests ≈ what E tests; "conforming" is easy (detector facts valid 19 of 20, 20 of 20). The recall-losing distinction is asked-vs-unasked (stage H, AUC 0.56–0.64), which it leaves unscored. It also rewards over-broad scope (widening P153 to every iff passes all asked cases at no cost on conforming code).

**O4. Dossier ingredients were mostly tried; prevalence cuts both ways.** Stage H's record (rule + positives + negatives + rate): `examples` AUC 0.641, `retrieve` 0.591; deciders learned the base rate (README 840-848). `naming_norm`'s `coe_` 48:9 misled all three reviewers on d0045 (`mechanisms.md` l.49-53). DP1 itself counted `homMk` 25 vs `mkHom` 7 on p0016 and still wrote "NOT a clear naming violation"; the maintainer: "there is an hesitation in mathlib".

**O5. Upstream losses dominate.** E 0.74 → F 0.49 when the convention must be picked from the diff; GE1 never considered 11 of 23 (`cross_model.md`). The "one-line index, open when relevant" use is a retrieval design; F's checklist result (+0.03 with 25) argues against more dilution.

**O6. Some conventions have no strict reading.** P133 vs P014 are opposite rules on one situation (census `results.md` l.165-171); v0064's maintainer: "consider my suggestion optional"; p0010 is a ":robot: says:" relay citing the lattice library's `_left`, while local `commutator_le_left` matches the PR's reading (`feedback.json`; DP1 reasoning read).

**O7. Single-rep noise inflates the mechanism table.** v0068's "check failed" miss was filed under `gcongr` in DP2 (and a DP3 finding mentions `gcongr`) (DP2 finding read; matcher not run); DE1 filed p0014; DE1/DX1 reached v0066.

**3. Four questions**
(a) Partly. The discriminating evidence is whether the session *claims the code conforms* versus *agrees it departs and declines*. Decision: p0007, p0003 (G1), v0030 (GE1), v0029. Understanding (a specific false claim): p0004 (E1 uses the sentence's own precondition "directions used separately"; the maintainer's reason was usefulness, "I don't see any reasonable application"), 29842 ("a generalization, not a new concept"), v0093 (DP1 tested `exact` without `simp`, not `simpa using h`). Some "conforms" claims are a disguised bar: p0016 after its own 25:7 count, v0105 "necessary". `_left`/`_right` (p0010): DP1 checked argument position against local siblings — a comparison-class error, but the convention is contested; a dossier fixes it only by encoding a finer, tail-sized rule.
(b) As designed, itself: it bypasses retrieval/localisation and strips the decision. In the record, reach at the place tracked assertion, not representation (E vs G). Testable on the 39: does an ask's exam pass co-occur with its DE/DP reach?
(c) Fatal for exam-calibrated authority, not for a diagnostic. 16 of 39 probe asks are in entries ranked >100 (≤4 census asks, three unused), with no held-out exam — where the understanding misses cluster. A perfect understanding fix adds ≈3–5/39 (+0.08–0.13) even under the exact brief; ask-free, multiply by the retrieval loss.
(d) The oracle replay (§5).

**4. Reject outright**
- The representation map scored by exam, before the exam is shown to predict review reach (O3).
- Exam-calibrated authority (strict when passed): strict application filed 13 of 14 unasked detector facts (dead-ends, "Convention detectors"); maintainers raise ≤5%.
- Prevalence as an authority signal in the dossier (O4; the `by_cases!` retraction).
- Dossiers for the head's search-type entries (P005, P011, P018, P063, P004, P007): route those misses to the closer battery (8 of 15 asks came out verbatim from exhaustive procedures, `todo/README.md` l.113).
- Self-written dossiers validated by an exam drawn from the same cases (circular).
- Outside my lens, worth keeping: revealed preference (did Mathlib later conform the flagged code?) is the only gold-free read of the unasked 95%.

**5. First experiment: oracle replay ladder, DeepSeek, $0.** Units: the in-census asks DE1 or DP1 missed on the 39 (≈22). Per prompt (PR model + hunk at the ask's place + exact sentence), three forms: **U** "does this conform? if not, write the change"; **A** "a maintainer asked for this convention here; write the change"; **A+X** A plus DP's two examples. Three samples each, two blind matchers. Per ask: U right → lost to decision/localisation in review; U wrong, A right → scope/applicability (may be a disguised bar; read the reasoning); A wrong, A+X right → fix shape a representation can fix; A+X wrong → execution/search. **Pre-stated:** representation-fixable (A wrong ∧ A+X right, plus reasoning-confirmed scope cases), stable 2 of 3: **≤ 4 of 22 → drop the understanding thread** (dead-ends entry); **≥ 7 of 22 and in entries with ≥ 10 census asks → proceed** to a narrow dossier slice on those; between → replay GE1's misses. Cost: ~200 single-turn local calls, < 1 server-hour after the 12-minute start; matchers ~60–100k subagent tokens. Limit: in-sample on the probe asks, so it diagnoses the miss locus, not a gain.

**Read vs inferred.** Read: README C/F/G/H/D, `cross_model.md`, the disposition plan, dead-ends, `mechanisms.md`, the census head, maintainer comments, DP1 reasoning on 43167/42814. Rep 2–3 stability notes are my keyword scan, unmatched. Miss classes are mine, not blind.
