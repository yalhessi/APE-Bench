# P14val_a readings (PRs 32875, 34091, 26755, 36822; reader: one, counts provisional)

Transcript line numbers are those of `grep_session.py` / `show_session.py`. Quotes are the sessions' own words; anything inferred is marked.

## v0090 (32875, F3, P315) `Mathlib/Data/Finset/Image.lean:75` — "Both of these should probably be tagged with `grind`."
Ask: the two lemmas fed to `simp only [mem_map, Equiv.coe_toEmbedding]` before `grind` should carry `@[grind =]` so `grind` alone closes `mem_map_equiv` (the `simp only` prelude is the symptom). Reached by nobody.
- DX1 K: "Could be simplified to just `by grind` (with `mem_map` having `@[grind =]`)? Not worth." (l.41); filed revert (<10 -> 25 ms).
- DX2 O: "Note `mem_map` has `@[simp, grind =]`. The PR description says the new proof is SLOWER" (l.21); filed drop `grind`, goal closable by rewriting.
- DX3 K: "Possibly also note that `simp only [...]` is unnecessary because `grind =` attribute on `mem_map`... hmm." (l.37); then found the eric-wieser precedent that *adds* `@[simp, grind =]` to `keys_cons` (l.49) and still filed revert.
- AP1 K: "`mem_map_equiv` has `@[simp 1100]` but not `grind =`. ... `grind` needs `mem_map` (which has `grind =`) plus `Equiv.coe_toEmbedding`. Not an issue." (l.46); filed revert, citing the delivered 'automation only when not markedly slower' convention.
- AP2 K: "since mem_map is `@[grind =]`, maybe `grind` alone closes it, saving the line? Actually that doesn't address the speed." (l.25); filed revert.
- AP3 V: tried the body `grind` alone (l.25): "`grind` alone fails for mem_map_equiv; the `simp only [...]` pre-step is needed" (l.28); filed a `simp only` one-liner without `grind`.
AP: P315 absent from the section; two delivered conventions ('`grind` replaces an explicit proof only when ... not markedly slower', 'a lighter tactic ... not heavy automation') were cited by all three AP sessions as the ground for filing the opposite change.
Verdict: judgement under a wrong anchor plus a missing direction. All six stood at the place, knew the `grind =` mechanism (saw it on `mem_map`) and were one step from the ask ("grind alone?"), but the PR's own profile made 'slower, so revert' the finding, and the move the maintainer makes — change the library's attributes, not the proof — was never considered: the sessions treat the attribute set as fixed input to review the proof against. The AP section selected on `grind` in the diff and delivered the grind-skeptical conventions, which pushed further from a grind-adoption maintainer.

## v0091 (32875, F3, out of census) `Mathlib/Data/Rat/Lemmas.lean:303` — "Same here."
Ask: tag `den_inv` and `num_intCast` `@[grind =]` so `grind` alone proves `inv_intCast_den_of_pos`. Reached by nobody.
- DX1 O: "Since I can't find an equally short fast proof, my 'revert' suggestion is the right one." (l.55).
- DX2 O: tested `simp [*]`, `simp only [...]; omega` (l.71); filed drop `grind` (goal closable by explicit rewriting).
- DX3 O: "either revert or find a bet[ter proof]" (l.11); filed `grind` not needed.
- AP1 O: "there's a lighter route, but it's not obviously shorter/better than grind." (l.40); filed revert.
- AP2 O: tested `simp only [...]; omega` (l.36); filed `omega` after `if_neg`.
- AP3 O: "`rw [den_inv, num_intCast, if_neg ha0.ne', Int.natAbs_of_nonneg ha0.le]` compiles! That's a clean 1-line replacement" (l.28); filed that.
AP: n/a (out of census). Verdict: the same anchor as v0090 with no near-miss at all — no session mentions a tag for either lemma; every one re-proves the goal with a lighter tactic, the exact opposite of what the maintainer asked (knowledge: `direction`, the grind roll-out's 'tag, don't re-prove').

## v0093 (32875, F1, P018 P040) `Mathlib/MeasureTheory/Measure/Portmanteau.lean:650` — suggestion `Tendsto μs L (𝓝 μ) := tendsto_of_forall_isClosed_limsup_le (by simpa using h)`
Ask: the two-line tail `simp only [measureReal_eq_coe_coeFn, toReal_limsup] at h; exact lemma h` becomes a term with `by simpa using h` in argument position (no lemma list: both are simp lemmas). Reached by nobody (Opus T reached it twice).
- DX1 C: "Hmm, that's a big simplification — 268ms -> <10ms. Fine." (l.7); checked the simp-at-h for correctness (l.18-29) and moved on.
- DX2 C: "this is a *much* shorter proof of a lemma that took 268ms. Nice. ... is `simp only [...] at h` a 'flexible'/fragile proof? It's fine." (l.58).
- DX3 C: "`Portmanteau.lean:649-650`: nice golf." (l.64).
- AP1 C: "that feeds `exact`. It IS squeezed. ✓" (l.54) — checked the delivered squeeze convention only; P018/P040 never named here. AP held, ignored.
- AP2 V: tried `exact tendsto_of_forall_isClosed_limsup_le h` alone (l.41, fails) and reasoned `simpa only [...] using lemma h` cannot work since the simp is on `h`: "a maintainer might ask to merge into one `simpa`? Can't." (l.46). AP held, considered_dropped.
- AP3 K: "could it be one line? `simpa only [...] using tendsto_of_forall_isClosed_limsup_le h`? Hmm, `simp only ... at h` then exact is fine." (l.49); its message: "`simp only [...] at h` line 649 ... feed[s] a non-flexible, exact-style step, so squeezing is right". AP held, considered_dropped.
Verdict: DX is judgement (a hunk the PR's own profile marks as its biggest win is read as finished); AP is a missing idiom — both AP sessions that asked the maintainer's question built the wrong one-liner (`simpa only [...] using lemma h`, `exact lemma h`) and concluded it cannot be merged, never trying `lemma (by simpa using h)`. The same delivered P018 was *used* by AP2/AP3 at Integral.lean (v0094/v0095, reached) where the merged form was a plain `rw [this, lemma]`; the convention moves the reviewer only when the merged form is easy to construct.

## v0094 / v0095 (32875, F1, P018 P401) `Mathlib/Probability/Kernel/Disintegration/Integral.lean:55` and `:147` — `simpa [this] using (Kernel.compProd_apply_prod hs ht).symm` / "simpa"
Ask: the twin tails `simp only [this]; exact (compProd_apply_prod hs ht).symm` become one call. DX 1/3, AP 2/3 (the matchers accept a one-line `rw [this, lemma]`).
- DX1 K: "could be compressed to `rw [← congrArg (· (s ×ˢ t)) ρ.disintegrate, compProd_apply_prod hs ht]`, but the local hypothesis is at least as readable, so I would not request it." (submission notes).
- DX2 reached: `rw [this, Kernel.compProd_apply_prod hs ht]` for both twins, on the ground that "the pre-PR proof of this lemma was a plain `rw`, so the file's own style is `rw` here".
- DX3 K: "`rw [this]` would be more idiomatic. ... this is a real style point but minor." (l.11).
- AP1 K: "`simpa only [this] using (compProd_apply_prod hs ht).symm` would be a single tactic. Is that better? Marginally." (l.37) ... "Marginal. I'd rather not file that." (l.40); its message: "Consecutive tactic calls merged — considered at the Kernel/Portmanteau hunks; the current forms are already minimal single calls feeding a term; no ask." AP held, considered_dropped.
- AP2 reached: filed under the delivered 'consecutive calls merged' convention, one `rw` for both twins. AP held, used.
- AP3 reached: same, verified to compile; also offers dropping the `have` via `conv_rhs => rw [← ρ.disintegrate ...]`. AP held, used.
Verdict: judgement on identical evidence — all six saw the two-call tail and could write the one call; the three misses rated it "would not request / minor / marginal", the three hits rated it worth a finding (two of them with P018 as the licence). The same convention, delivered to all three AP sessions, moved two and was held-and-dropped by the third, so here it changes the threshold, not the knowledge.

## v0016 (26755, F12, P100) `Finset/Basic.lean:1` — "How many `noncomputable`s from this file are still necessary? `coeMonoidHom` looks like it can be computable too?"
All six reached: each drops `noncomputable` from `Finset.coeMonoidHom`; DX2/AP1/AP3 also from the `commMonoid`/`divisionMonoid`/`divisionCommMonoid` siblings, AP1/AP3 after compiling each without the modifier. AP held (P100, the sibling-family convention), used by AP1/AP3 as the frame ("applied to some members of the family and not others without a stated reason"). Nothing to read.

## v0109 / v0110 (34091, F10, out of census) `Pigeonhole.lean:67` — docstring "greater than its codomain's"; "Similarly in comments below"
All six reached: the self-contradictory docstring ("domain's ... greater than its domain's") is filed by every session, and the two sibling docstrings with it. Nothing to read.

## v0131 / v0132 (36822, F3, P098) `Order/Interval/Set/Disjoint.lean:78` and `:82` — "simp?"
All six reached: each finds that `@[simp]` was replaced by a bare `@[to_dual ...]`, verifies `by simp` now fails, and asks for `@[to_dual (attr := simp) ...]`, citing the `(attr := ...)` form used on the file's other siblings. AP held (P098), used. Nothing to read.

## v0106 / v0107 / v0108 (34091, F2, P392) `Pigeonhole.lean:80, :97, :89` — `[Infinite β]`, `[Uncountable β]`, `[Infinite α]` instead of `(hβ : Infinite β)` etc.
Ask: a class-typed hypothesis is an instance-implicit binder. DX 0/3, AP 3/3.
- DX1 K: "since `Uncountable` is a class, could be `[Uncountable β]`? But it's a hypothesis; using it as an explicit argument is fine. Similarly `Infinite β` ... Fine." (l.24).
- DX2 C: discusses only the call site `exists_infinite_fiber u' h (by infer_instance)` (l.9, l.35); the binder form is never raised.
- DX3 K: "make `[Infinite β]` an implicit instance argument ... that's a real API question! ... `[Infinite β]` would be idiomatic. But then users who have `hβ : Infinite β` explicitly... Meh. Not a finding." (l.43).
- AP1 reached (finding 5, once for the family); AP2 reached (finding 4, after a whole-library search showing explicit `: Infinite` hypotheses occur only on these three lines; instance forms compiled); AP3 reached (finding 2, plus the two call sites, whole-file recompilation). AP held, used by all three.
Verdict: knowledge of the `demand` kind. Two of three solo sessions produced the maintainer's exact form and rated it not enforced ("fine", "unusual", "Meh"); the delivered sentence — the same observation stated as what maintainers ask — turned it into three filings. This is the cleanest case in the batch of the conventions layer doing what it is for: it did not add a fact, it moved the threshold on a fact the reviewer already had.

## v0092 (32875, F1, P018 P401) `MeasureTheory/Constructions/Pi.lean:462` — "`simpa using`?"
Ask: merge `simp only [pi_pi, this]; exact Fintype.prod_equiv _ _ _ (congrFun rfl)` into one `simpa ... using` call. DX 0/3, AP 0/3 (AP2 partial; Opus T reached it twice).
- DX1 C: "Or simply `Fintype.prod_equiv e _ _ fun _ => rfl`. It's fine." (l.32).
- DX2 C: "Using `_` placeholders for explicit args is arguably less readable but not a rule violation." (l.35).
- DX3 O: filed the hand-rolled `have` block against `Equiv.piCongrLeft_preimage_univ_pi` (finding 2) — a different change at the declaration, not the tail.
- AP1 K: "maybe the intended cleaner proof: `simpa only [pi_pi, this] using Fintype.prod_equiv e.symm _ _ (congrFun rfl)`? no." (l.43), then tests `fun _ ↦ rfl` instead. AP held, considered_dropped (no ground stated).
- AP2 P: `exact Equiv.prod_comp e (fun i ↦ μ i (s i))` under the 'direct lemma' convention; keeps two steps. AP held, P018/P401 ignored here.
- AP3 C: "The `congrFun rfl` is opaque/opaque-ish style; maybe prefer explicit `fun _ ↦ rfl`? Hmm." (l.25). AP held, ignored.
Verdict: attention and judgement — every session read this tail, but the salient feature for all six was the odd term (`congrFun rfl`, the three underscores), not the two-call shape; the one session that wrote the maintainer's merged form (AP1) dropped it with a bare "no". The same P018 that AP2/AP3 used thirty lines away at Integral.lean (v0094/v0095) was not applied here, where the merged form needed the `simpa ... using` idiom rather than a plain `rw`.

## v0105 (34091, F1, P011) `Pigeonhole.lean:86` — "Surely this is a one-liner using `infinite_pigeonhole_card_lt`?"
Ask: a reviewer's question whether the new case-split proof of `exists_infinite_fiber` collapses to one application of the (just generalised) `infinite_pigeonhole_card_lt`. Reached by nobody in any condition (0 of 7 rows).
- DX1 K: "Let me think about golf for `exists_infinite_fiber` ... So the case split is needed." (l.12, again l.27).
- DX2 K: "In the *infinite α* case yes; in the finite α case no. Right, the case split is needed." (l.52).
- DX3 K: "could be proved from `infinite_pigeonhole_card_lt` in both cases uniformly? ... a fiber of cardinality 5 is finite and > 3. So the conclusion doesn't follow." (l.9).
- AP1 K: wrote the maintainer's candidate verbatim — "`obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h hβ; exact ⟨a, ha.le⟩` Wait! That would be a much shorter proof." — and refuted it: "branch 1 is needed and not derivable" (l.16). P011 held, considered_dropped.
- AP2 K: "So the split is needed. Fine." (l.9). AP3 K: "no proof-golf finding that I can substantiate." (l.12).
Verdict: not a miss of knowledge or judgement. All six asked the maintainer's exact question and answered it correctly: the merged file (source clone, 450920a530, 2026-02-25) keeps the two-branch proof, with `[Infinite β]` and `aleph0_le_mk β` as the only changes, so the one-liner was never written (inferred: the author answered the question in discussion). Gold here counts a reviewer's question whose answer was "no"; a reviewer that "reached" it would have had to raise a request the PR correctly declined. Knowledge column: `unclear` (read as a hunch, not an obligation). Note for the gold: this ask should probably be excluded or marked as a question, since no correct reviewer can hit it.

# Batch summary — P14val_a (PRs 32875, 34091, 26755, 36822; 15 asks, 90 session rows; one reader, counts provisional)

**Behaviour at the place** (45 rows per condition). DX: reached 17, K (right concern, dropped) 15, C (attended, fine) 8, O (asked something else) 5, A 0. AP: reached 28, K 9, O 3, C 2, V 2, P 1, A 0. No session failed to attend any of the fifteen places: every miss in this batch is a decision taken at the place, and in 24 of the 45 DX+AP non-reached rows (15+9) the session's own reasoning names the maintainer's concern before dropping it.

**Knowledge column** (per ask). DX: none 9, demand 3 (v0106-v0108), direction 2 (v0090, v0091), unclear 1 (v0105). AP: none 11, direction 2, mechanism 1 (v0093), unclear 1. Nothing in this batch was an `api`, `pr_context` or `construction` miss; the only missing *fact* is the grind roll-out's "tag the lemma, don't re-prove" (v0090/v0091), which no session knew to apply although all six knew the `grind =` attribute exists.

**Where AP held the convention** (11 of 15 asks; 3 absent-or-n/a asks are v0091, v0109, v0110, and v0090 is absent):
- v0106/v0107/v0108 (P392, class hypothesis as instance): used 3/3; DX 0/3 → AP 3/3. Two DX sessions had written the form and rated it unenforced; the sentence supplied the demand. The batch's one clean gain, three asks on one PR.
- v0094/v0095 (P018): used 2/3, considered_dropped 1/3 (AP1: "Marginal. I'd rather not file that"); DX 1/3 → AP 2/3. Same evidence in all six, threshold moved by the sentence.
- v0016, v0131, v0132 (P100, P098): used 3/3, but DX also 3/3; the convention was redundant with what solo already does.
- v0093 (P018, P040): 0/3 — ignored 1, considered_dropped 2; the merged form needed `lemma (by simpa using h)`, which AP2/AP3 did not find (they tried `simpa only [...] using lemma h` and `exact lemma h`, both fail).
- v0092 (P018, P401): 0/3 — AP1 wrote the maintainer's `simpa ... using` form and dropped it with "no"; AP2/AP3 applied other conventions at the place.
- v0105 (P011): considered_dropped 3/3, correctly (see below).
- v0090: absent; worse, two delivered conventions (automation only when not slower; lighter tactic over `grind`) were cited by all three AP sessions as the ground for the opposite request.

**The three most instructive readings.**
1. **v0090/v0091 — an anchor plus a direction.** All six sessions saw `mem_map` already carries `grind =`, four asked "then `grind` alone?", one (AP3) ran `grind` alone and saw it fail — exactly the evidence for "tag `Equiv.coe_toEmbedding`". None took the step, because the PR's own profile (<10 → 25 ms) had already fixed the finding as "slower, so revert", and the conventions selected on `grind` in the diff reinforced it. The reviewer treats the library's attribute set as fixed and reviews the proof against it; the maintainer changes the attributes. A design that cannot represent "the fix is upstream of the hunk" cannot reach this family, and a blind selector that keys on the diff's tactic names will keep delivering the grind-skeptical half of a two-sided corpus.
2. **v0106-v0108 — demand, not knowledge.** DX1: "could be `[Uncountable β]`? ... using it as an explicit argument is fine." DX3: "`[Infinite β]` would be idiomatic ... Meh. Not a finding." AP: 3/3, one with a whole-library search, one with the instance forms compiled. The sentence added no fact; it changed what counts as asked-for. This is what the conventions layer is for, and it worked on the one ask-family in the batch where the form was known and cheap to construct.
3. **v0093 against v0094/v0095 — the same sentence, two outcomes.** P018 ("consecutive calls merged") was delivered to the same three AP sessions for both places. At Integral.lean the merged form is `rw [this, lemma]`: AP2/AP3 filed it. At Portmanteau the merged form is `lemma (by simpa using h)`: AP2 tested two wrong one-liners and concluded "Can't", AP3 answered its own "could it be one line?" with "is fine". A convention moves a reviewer only when the conforming form is easy to construct; where it needs an idiom the model lacks, the sentence is held and dropped. The lever there is the construction step (try the form, in Lean), not another sentence.

**A note on gold.** v0105 ("Surely this is a one-liner using `infinite_pigeonhole_card_lt`?") was never implemented: the merged file keeps the case split. All six sessions asked the question and answered "no" by the right argument (finite α). A reviewer cannot reach this ask without making a request the PR correctly declined; it should be marked as a question in the gold, or excluded from recall.

**Left unread:** nothing; all 15 asks of the batch are read. Token use was well under the 400k budget.
