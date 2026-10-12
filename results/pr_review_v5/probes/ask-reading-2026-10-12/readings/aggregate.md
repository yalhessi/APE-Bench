# Aggregate of the per-ask readings

558 rows from ['D12a', 'D12b', 'D12c', 'P14post', 'P14val_a', 'P14val_b']; 93 asks. One reader per batch; provisional.

## 1. Behaviour at the place, per session row (condition x set)

| condition | set | rows | reached | partial | filed, unmatched | right concern, dropped | checked, read as conforming | attended, concluded fine | attended, asked something else | not attended |
|---|---|---|---|---|---|---|---|---|---|---|
| DX | D12 | 141 | 56 | 12 | 1 | 22 | 9 | 32 | 8 | 1 |
| DX | P14 | 138 | 39 | 7 | 0 | 42 | 8 | 33 | 9 | 0 |
| DX | all | 279 | 95 | 19 | 1 | 64 | 17 | 65 | 17 | 1 |
| AP | D12 | 141 | 55 | 18 | 0 | 16 | 8 | 19 | 25 | 0 |
| AP | P14 | 138 | 57 | 14 | 0 | 25 | 10 | 18 | 14 | 0 |
| AP | all | 279 | 112 | 32 | 0 | 41 | 18 | 37 | 39 | 0 |

## 2. Knowledge the miss needed, per ask (modal code over the condition's rows; reached-only asks excluded)

| condition | set | asks with a miss | none | demand | mechanism | direction | api | construction | pr_context | unclear |
|---|---|---|---|---|---|---|---|---|---|---|
| DX | D12 | 31 | 17 | 5 | 4 | 3 | 1 | 1 | 0 | 0 |
| DX | P14 | 35 | 17 | 9 | 2 | 3 | 1 | 0 | 2 | 1 |
| DX | all | 66 | 34 | 14 | 6 | 6 | 2 | 1 | 2 | 1 |
| AP | D12 | 33 | 19 | 5 | 4 | 3 | 1 | 1 | 0 | 0 |
| AP | P14 | 33 | 22 | 2 | 1 | 3 | 1 | 1 | 2 | 1 |
| AP | all | 66 | 41 | 7 | 5 | 6 | 2 | 2 | 2 | 1 |

### 2a. The asks by knowledge code (DX), with the reader's detail

- **none** (34): d0001 (D12): 'isometry linear equivalence' for `H ≃ₗᵢ[𝕜] K` (a LinearIsometryEquiv); the three reached sessions (DX2, DX3, AP3) all got it by comparing w; d0004 (D12): the proof has a 12-line sketch up front; the maintainer wants it distributed to the steps. The sibling theorem's proof in the same file has ; d0005 (D12): a whitespace rule (blank line after `section`); every session had the two lines in front of it, three of them while rewriting that very span; d0006 (D12): the proof's `have`s are `this`, `this1`, `this2`, `thisα`, `thisα'`, `thisU`; DX1 named the concern and dropped it on the ground that the id; d0007 (D12): the ask is the import weight: `Analysis/Normed/Operator/ContinuousAlgEquiv` now pulls in Hilbert-space theory (`InnerProductSpace.Adjoint`, ; d0022 (D12): the same rule the sessions applied to the `*Bounds` pair (name after the conclusion, not the `Continuous` hypothesis), where the naming cens; d0023 (D12): the same rule the sessions applied to the `*Bounds` pair (name after the conclusion, not the `Continuous` hypothesis), where the naming cens; d0025 (D12): the same rule the sessions applied to the `*Bounds` pair (name after the conclusion, not the `Continuous` hypothesis), where the naming cens; d0026 (D12): matcher: reached only if a finding both reuses the bounded lemma and collapses h2; DX1 filed the reuse (finding 4), never the h2 shortening; d0027 (D12): the same rule the sessions applied to the `*Bounds` pair (name after the conclusion, not the `Continuous` hypothesis), where the naming cens; d0035 (D12): judgement: a one-line golf of a golf, weighed and dropped as not worth filing; the maintainer's term needs `mem_comap.mpr` to make `add_mem`; d0036 (D12): the merged form `simp [symm_apply_eq, Subtype.ext_iff]` is the author's own golf of `equivRange_symm_apply` in the same diff (Banach.lean), ; d0039 (D12): dot notation is general knowledge and the PR itself writes `hf.map_iSup (bddAbove_of_small _)` in Family.lean (DX3 l.25 read it as 'Good'); ; d0041 (D12): counted one changed line (GroupExtension/Defs.lean:49), not Inverses.lean:23; at Inverses:23 only verified the path (l.93 'correct'); d0047 (D12): finding 4; d0048 (D12): the maintainer's `round_eq_div` names only the head symbol of the right-hand side; the sessions that renamed spelled the whole term (`round_; d0049 (D12): the inline `have : Tendsto (2 * ·) (𝓝[≥] x) (𝓝[≥] (2 * x))` is a general fact; seeing that needs reading the proof's steps for generality, a; p0003 (P14_post): the file's HasProd/tprod pairing (`le_hasProd_of_le_prod`/`tprod_le_of_prod_le`, `hasProd_le_of_prod_le`) was read by every session and used; p0004 (P14_post): the `alias ⟨_, _⟩` pattern was in view in the same file (Basic.lean:158 in DX3/AP1 tool results); no session asked which direction a user wo; p0005 (P14_post): every session found the general WfDvdMonoid lemma (`squarefree_iff_irreducible_sq_not_dvd_of_exists_irreducible`, `squarefree_iff_no_irreduc; p0007 (P14_post): attention/form: four consecutive signatures repeating `{D : ℤ}` were in the diff; no DX session remarked on it; p0012 (P14_post): DX2 and DX3 both wrote the maintainer's exact name `commutator_sup_left_of_normal` (DX2 even searched for it, l.23) and did not file; the mi; p0014 (P14_post): the mechanism was on screen for every session (`isoMk`'s `:= by cat_disch` in the same diff; the structure fields' defaults in Presheaf.lean; p0015 (P14_post): the follow-up ('other definitions below' = `mkHom`'s `naturality`) needs the same mechanism applied to the next declaration; p0016 (P14_post): `PresheafOfModules.homMk` (Presheaf.lean:220) was read by every session; the maintainer concedes it has 'different parameters' and still pre; v0031 (P14_val): the file's sibling title 'The Bhatia-Davis inequality on variance' (line 419) is in the hunk's neighbourhood; the literature name was checke; v0055 (P14_val): line 68: 'the precedent comment (ADedecker, PR #21065, same file/lemma) literally suggested a rewrite of this exact proof' -- the precedent ; v0064 (P14_val): the file's own `{x : ℝ}` lines were in every session's file_read (line 5); the letter was never looked at; the maintainer calls the ask opti; v0065 (P14_val): line 7 read the proof with h₂a; no remark on the name; v0068 (P14_val): gcongr in fact fails here (AP1/AP3 tested: 'gcongr did not make progress'); the maintainer's question is answered 'no'; v0092 (P14_val): none: the sessions attended the term's readability (`congrFun rfl`, the `_ _ _`) rather than the two-call shape; AP1 wrote the maintainer's ; v0093 (P14_val): none: the DX sessions read the 268 -> <10 ms hunk as a finished golf ('nice golf', 'Fine') and never looked for a shorter form.; v0094 (P14_val): none: every session saw the two-call tail and could write the one-call form; DX1/DX3/AP1 rated it 'would not request' / 'minor' / 'marginal'; v0095 (P14_val): none: every session saw the two-call tail and could write the one-call form; DX1/DX3/AP1 rated it 'would not request' / 'minor' / 'marginal'
- **demand** (14): d0016 (D12): (inferred) the style guide's calc layout — `calc` steps indented under the first line, or `:= calc` on the statement line with the terms bel; d0029 (D12): P157 (compound side left, the rewriting direction) was in no packet; only DX3 asked the orientation question and answered 'no convention'; d0032 (D12): DX2 (l.4) and DX3 (l.4) wrote in reasoning that the PR is 'clearly a fake / AI-generated proof' and never filed a disclosure request; what t; d0038 (D12): the maintainer's form `IsFundamentalSequence.of_isNormal` (conclusion's namespace, `.of_h`); the DX sessions judged the `X_of_isNormal` spel; d0043 (D12): the idiom 'a `Set` is written `{j | p j}`, not a predicate passed across the defeq' — the sessions all saw the defeq and most used it as a l; p0000 (P14_post): the session established the justification itself (modern convention is `motive`) but did not know a maintainer wants that reason stated in t; v0029 (P14_val): P185 (a purely stylistic change to another author's prose is left alone); DX1 had the fact the AP sessions used ('Mathlib has both') and rea; v0030 (P14_val): P278 (docstrings in full words, not identifier abbreviations); spelling out never appeared among DX1's options; v0062 (P14_val): lean_verify_edit of the pre-PR bodies at lines 33-37 compiled; called it 'a coherent scope/minimal-diff style finding' and filed only the Ba; v0063 (P14_val): as v0062; v0067 (P14_val): P005 (a finishing tactic closes what it can); the sibling at line 172 '(by simp; positivity)' was in its file_read; positivity never conside; v0106 (P14_val): demand: DX1 and DX3 both named the instance-implicit form (`[Uncountable β]`, `[Infinite β]` 'would be idiomatic') and dropped it as 'explic; v0107 (P14_val): demand: DX1 and DX3 both named the instance-implicit form (`[Uncountable β]`, `[Infinite β]` 'would be idiomatic') and dropped it as 'explic; v0108 (P14_val): demand: DX1 and DX3 both named the instance-implicit form (`[Uncountable β]`, `[Infinite β]` 'would be idiomatic') and dropped it as 'explic
- **mechanism** (6): d0002 (D12): the structure constructor `ContinuousAlgEquiv.mk` whose continuity fields are autoparams (`:= by fun_prop`); a name search for a twin (`toCo; d0008 (D12): `grind [minimalCover]` closes the dite+choose_spec accessors (with `attribute [grind .] finite_empty` for the finite one); no session named ; d0009 (D12): `grind [maximalSeparatedSet]` plus `attribute [grind .] IsSeparated.empty`; same block of reasoning as d0008 in every session (the seven dit; d0018 (D12): `to_fun` attribute (Mathlib/Tactic/ToFun.lean, 49 lines, present at the reviewed state; 0 in-tree uses of `@[to_fun]`); the maintainer calls; v0060 (P14_val): `variable [IsLeftCancelMul α] in` before one lemma, no sub-sections; never considered; the sections themselves were read as the file's conve; v0061 (P14_val): as v0060
- **direction** (6): d0003 (D12): the sibling `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv` (same file, pre-existing) is stated as `∃ U, f = U.conj…`; t; d0045 (D12): old `coe_` -> new `toLinearMap_` for the CLM->LinearMap coercion whether written as an ascription `(f : E →ₗ[𝕜] K)` or `.toLinearMap` (the s; d0046 (D12): reached from the `.toLinearMap` surface form plus the census 21 v 7; the finding offers rename-or-restate; p0006 (P14_post): `def … : Prop := A ∧ B ∧ C` with a hand-written `_def := Iff.rfl` → `@[mk_iff] structure … : Prop where`; the sessions read the def-with-∧ f; v0090 (P14_val): old: explicit proof, or `simp only [lemmas]; grind` -> new: tag the lemmas `@[grind =]` and write `grind` alone (the grind roll-out, vihdzp); v0091 (P14_val): same as v0090: tag `den_inv`/`num_intCast` `@[grind =]` so `grind` alone closes it; no session mentions a tag here, all six re-prove the goa
- **api** (2): d0013 (D12): `Metric.isSeparated_insert_of_notMem` / `IsSeparated.insert` in MetricSeparated.lean; found by the sessions that searched the `IsSeparated` ; p0010 (P14_post): the robot's analogues (`inf_sup_left : a ⊓ (b ⊔ c)`, `Submodule.mul_sup`, `sup_le_sup_left`) put the sup in the second argument for `_left`;
- **construction** (1): d0051 (D12): the generalisation `2` → `k` with `1 < k` appears only when one asks what the proof uses of `2` (the sessions' own proof-reading was about `
- **pr_context** (2): v0053 (P14_val): #24163 and the #21065 consensus 'to change the definition' live in those GitHub threads; precedent_search handed every session #21065's revi; v0056 (P14_val): the plan to state ('generalize lemmas first, the definition later') is the author's reply in the thread; no packet input carries it
- **unclear** (1): v0105 (P14_val): unclear: the merged file (source clone, 450920a530) keeps the case split, so the one-liner the maintainer asked about was never written; for

## 3. The applicable-conventions section: held, and what the session did

AP rows 279: held 177, absent 60, n/a 42.

| held and … | reached | partial | K dropped | V | C | O | E |
|---|---|---|---|---|---|---|---|
| used | 87 | 5 | 0 | 0 | 0 | 0 | 0 |
| considered_dropped | 0 | 8 | 20 | 10 | 1 | 0 | 0 |
| ignored | 2 | 9 | 2 | 0 | 21 | 12 | 0 |
| null | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### 3a. Per ask where the section held the convention: DX hits -> AP hits (of 3), AP use

- d0005 (D12): DX 0 -> AP 1; ignored 2, used 1
- d0010 (D12): DX 3 -> AP 3; used 3
- d0011 (D12): DX 3 -> AP 3; used 3
- d0012 (D12): DX 3 -> AP 3; used 3
- d0013 (D12): DX 1 -> AP 1; used 1, ignored 2
- d0014 (D12): DX 3 -> AP 3; used 3
- d0015 (D12): DX 3 -> AP 2; ignored 3
- d0019 (D12): DX 3 -> AP 3; used 3
- d0020 (D12): DX 3 -> AP 3; used 3
- d0021 (D12): DX 3 -> AP 3; used 3
- d0022 (D12): DX 0 -> AP 0; considered_dropped 1, ignored 2
- d0023 (D12): DX 0 -> AP 0; considered_dropped 1, ignored 2
- d0024 (D12): DX 3 -> AP 3; used 3
- d0025 (D12): DX 0 -> AP 0; considered_dropped 1, ignored 2
- d0027 (D12): DX 0 -> AP 0; considered_dropped 1, ignored 2
- d0028 (D12): DX 3 -> AP 3; used 3
- d0031 (D12): DX 3 -> AP 3; used 3
- d0032 (D12): DX 0 -> AP 3; used 3
- d0033 (D12): DX 3 -> AP 2; used 2, considered_dropped 1
- d0034 (D12): DX 3 -> AP 3; used 3
- d0035 (D12): DX 0 -> AP 0; considered_dropped 3
- d0036 (D12): DX 0 -> AP 0; ignored 3
- d0038 (D12): DX 0 -> AP 0; considered_dropped 3
- d0039 (D12): DX 0 -> AP 0; ignored 2, considered_dropped 1
- d0041 (D12): DX 0 -> AP 1; ignored 2, used 1
- d0045 (D12): DX 0 -> AP 0; considered_dropped 3
- d0046 (D12): DX 2 -> AP 1; used 3
- d0047 (D12): DX 2 -> AP 2; used 2, considered_dropped 1
- d0048 (D12): DX 0 -> AP 0; used 3
- d0049 (D12): DX 0 -> AP 0; ignored 3
- p0002 (P14_post): DX 3 -> AP 3; used 3
- p0003 (P14_post): DX 0 -> AP 0; ignored 3
- p0005 (P14_post): DX 0 -> AP 0; ignored 2, considered_dropped 1
- p0007 (P14_post): DX 0 -> AP 1; used 1, considered_dropped 1, ignored 1
- p0009 (P14_post): DX 3 -> AP 3; used 3
- p0010 (P14_post): DX 0 -> AP 0; ignored 1, considered_dropped 2
- p0011 (P14_post): DX 3 -> AP 3; used 3
- p0014 (P14_post): DX 0 -> AP 1; used 1, ignored 2
- p0015 (P14_post): DX 0 -> AP 0; ignored 2, considered_dropped 1
- p0016 (P14_post): DX 1 -> AP 0; considered_dropped 2, ignored 1
- v0016 (P14_val): DX 3 -> AP 3; used 3
- v0029 (P14_val): DX 0 -> AP 3; used 3
- v0030 (P14_val): DX 0 -> AP 1; considered_dropped 2, used 1
- v0055 (P14_val): DX 2 -> AP 2; used 2, considered_dropped 1
- v0060 (P14_val): DX 0 -> AP 0; ignored 2, considered_dropped 1
- v0061 (P14_val): DX 0 -> AP 0; ignored 2, considered_dropped 1
- v0062 (P14_val): DX 0 -> AP 2; ignored 1, used 2
- v0063 (P14_val): DX 0 -> AP 2; ignored 1, used 2
- v0068 (P14_val): DX 0 -> AP 0; considered_dropped 3
- v0092 (P14_val): DX 0 -> AP 0; considered_dropped 1, ignored 2
- v0093 (P14_val): DX 0 -> AP 0; ignored 1, considered_dropped 2
- v0094 (P14_val): DX 1 -> AP 2; considered_dropped 1, used 2
- v0095 (P14_val): DX 1 -> AP 2; considered_dropped 1, used 2
- v0105 (P14_val): DX 0 -> AP 0; considered_dropped 3
- v0106 (P14_val): DX 0 -> AP 3; used 3
- v0107 (P14_val): DX 0 -> AP 3; used 3
- v0108 (P14_val): DX 0 -> AP 3; used 3
- v0131 (P14_val): DX 3 -> AP 3; used 3
- v0132 (P14_val): DX 3 -> AP 3; used 3

Held asks: AP > DX at 14, AP < DX at 4, equal at 41.

## 4. The grounds on which a named concern was dropped (K rows), verbatim

- d0018 DX2: "are `Meromorphic.fun_neg`, `fun_add`, ... `fun_prod` even *needed*? ... In `MeromorphicAt`/`MeromorphicOn` both forms exist. Consistent."
- d0018 DX3: "these are defeq so the lemma is basically identical to `neg`. But maintainers accept these duplicates in MeromorphicAt (existing `fun_neg`). So consistent with the file."
- d0018 AP2: "So `fun_add` is a definitional duplicate of `add`. Hmm, that's a duplication concern but it's intended for `fun_prop` (which needs both forms)."
- d0029 DX3: "should the equality be oriented `⨆ s : S, f s = ⨆ i, f i`? ... Orientation convention: Mathlib often states `sSup` over a smaller set = over a bigger... no convention. Skip."
- d0047 AP2: "Do I want to file it? Let me think about the value. The convention: 'Declarations sharing a namesp[ace]...' (l.25) I'm now unsure whether to file the placement finding."
- d0022 DX1: "Our names `Dense.continuous_upperBounds`, ..., `Dense.continuous_sup`, `Dense.continuous_inf` name the hypotheses (continuity of f). Hmm, so both the prefix census and the Dense namespace census argue"
- d0022 DX2: "`continuous_sup` sounds like 'continuity of sup' which is misleading-ish ... for naming_norm, `Dense.continuous_sup` came back subject_unresolved, so unmeasured."
- d0022 DX3: "should the name be `Dense.iSup` / `Dense.ciSup`? What's the convention for lemmas `⨆ i, f i = ⨆ s : S, f s`? Hmm. (l.20) Let me focus and be strategic."
- d0023 DX1: "Our names `Dense.continuous_upperBounds`, ..., `Dense.continuous_sup`, `Dense.continuous_inf` name the hypotheses (continuity of f). Hmm, so both the prefix census and the Dense namespace census argue"
- d0023 DX2: "`continuous_sup` sounds like 'continuity of sup' which is misleading-ish ... for naming_norm, `Dense.continuous_sup` came back subject_unresolved, so unmeasured."
- d0023 DX3: "should the name be `Dense.iSup` / `Dense.ciSup`? What's the convention for lemmas `⨆ i, f i = ⨆ s : S, f s`? Hmm. (l.20) Let me focus and be strategic."
- d0025 DX1: "Our names `Dense.continuous_upperBounds`, ..., `Dense.continuous_sup`, `Dense.continuous_inf` name the hypotheses (continuity of f). Hmm, so both the prefix census and the Dense namespace census argue"
- d0025 DX2: "`continuous_sup` sounds like 'continuity of sup' which is misleading-ish ... for naming_norm, `Dense.continuous_sup` came back subject_unresolved, so unmeasured."
- d0025 DX3: "should the name be `Dense.iSup` / `Dense.ciSup`? What's the convention for lemmas `⨆ i, f i = ⨆ s : S, f s`? Hmm. (l.20) Let me focus and be strategic."
- d0027 DX1: "Our names `Dense.continuous_upperBounds`, ..., `Dense.continuous_sup`, `Dense.continuous_inf` name the hypotheses (continuity of f). Hmm, so both the prefix census and the Dense namespace census argue"
- d0027 DX2: "`continuous_sup` sounds like 'continuity of sup' which is misleading-ish ... for naming_norm, `Dense.continuous_sup` came back subject_unresolved, so unmeasured."
- d0027 DX3: "should the name be `Dense.iSup` / `Dense.ciSup`? What's the convention for lemmas `⨆ i, f i = ⨆ s : S, f s`? Hmm. (l.20) Let me focus and be strategic."
- d0008 AP1: "'I weighed proposing `rw [minimalCover, dif_pos h]` instead of the `↓reduceDIte` list, but the idiom is identical in all four siblings, so I did not file it' (golf considered was dif_pos, not grind)"
- d0008 AP2: "'A maintainer might suggest adding `[simp]` lemmas for the value in both cases instead of unfolding the definition in six places ... I'll not file this; too speculative given the lemmas exist.' (adjac"
- d0008 AP3: "'the four lemmas ... all start with the same 2-line `by_cases`/`simp only [...]`, i.e., they unfold the definition by hand. A maintainer would ask for a simp lemma. Hmm' (l.34); submitted 'no use site"
- d0009 AP1: "as d0008 (l.45, 'idiom is identical in all four siblings, so I did not file it'); at the place it filed instead the redundant `: Set X` ascription on `isSeparated_maximalSeparatedSet` (finding 9)"
- d0009 AP2: "as d0008 (l.45, 'too speculative given the lemmas exist'); filed `finite_maximalSeparatedSet` at 306 (finding 11) written with the same dance 'with `finite_minimalCover` as the template'"
- d0009 AP3: "as d0008 (l.34/46); at the place it filed the line break and `: Set X` ascription on `isSeparated_maximalSeparatedSet` (finding 7), re-verifying the lemma with the dance intact (l.34)"
- d0038 DX1: "'Namespace/naming: new names `isFundamentalSequence_of_isNormal`, ... Are these consistent with Mathlib conventions?' (l.7) → 'In this very file, `lt_opow_of_isSuccLimit`, `add_le_iff_of_isSuccLimit` "
- d0038 DX2: "'Which naming does Mathlib prefer: since these are hypothesis-carrying lemmas, `_of_isNormal` suffix seems reasonable (cf. `add_le_iff_of_isSuccLimit`) ... the naming tool examines the leading prefix "
- d0038 DX3: "ran `naming_norm Ordinal.isFundamentalSequence_of_isNormal` → 'insufficient_evidence ... subject_unresolved' (l.35); then 'is `Ordinal.cof_eq_of_isNormal` the right name, or should it be `Ordinal.IsNo"
- d0038 AP1: "cites P108 verbatim: 'here they moved it out of the `IsNormal` namespace. Hmm, but `Order.IsNormal` namespace is where `map_iSup` lives ... The naming pattern `_of_isNormal` matches `cof_eq_of_isNorma"
- d0038 AP2: "'Hmm — the opposite convention! The change moved `IsNormal.isFundamentalSequence` OUT of the `IsNormal` namespace ... Given `Ordinal.IsNormal` is deprecated, they can't put things in its namespace. Fi"
- d0044 AP1: "'Also there's a typo in the module docstring! "even though the existence ultimate statement does not"' (l.14); 'A maintainer would flag a garbled sentence ... include the typo as a separate small find"
- d0035 DX1: "'the golf is fine ... Could be golfed further to `simpa only [...] using add_mem h.1 h.2`? Hmm. Not a finding.' (l.16; again l.47)"
- d0035 DX2: "'Could be `simpa only [...] using add_mem h.1 h.2`? Hmm, that's a possible style ask: combine into one line. Not worth it. Actually, maybe the whole proof could be `by simp [SetLike.le_def, ...]`? Hmm"
- d0035 AP1: "cites P040 at the place: '"A short tactic block that a single term proves is written as that term." ... `inf_comap_le_comap_add`: by-block; fine.' (l.43); earlier '`simpa only ... using add_mem h.1 h."
- d0035 AP3: "'Actually maybe the whole thing is `fun m h ↦ add_mem h.1 h.2` after `simpa`? Hmm ... hard. Is the new proof acceptable? It's a reasonable golf ... could be a one-liner term `simpa [...] using ...`. N"
- d0043 AP1: "'`pairwise_baseOf_div_notMem` derives `s = baseOf` — uses `.refl` (definitional unfolding of `baseOf`!) ... relies on definitional unfolding' (l.38) → 'Filing a marginal finding dilutes precision. I'l"
- d0043 AP3: "'Does any proof `unfold baseOf` or rely on defeq unfolding? In `pairwise_baseOf_div_notMem`: ... `.refl _` proves `s ⊆ IsMulIndecomposable v {i | 1 < f (v i)}`' (l.29); 'cross-module defeq unfolding' "
- d0048 DX1: "`round_eq'` — the prime name. Mathlib style: primes in theorem names are discouraged. Actually … they do exist (e.g. `tendsto_floor_right'`). Hmm."
- d0006 DX1: "`replace this` chains and `have this ...` naming — Mathlib style: avoid reusing the name `this` … reviewers often ask for descriptive names. Hmm, that's a style ask. … The "this" idiom is widely used "
- d0033 AP2: "a maintainer would likely just close the PR. But our job is to list concrete requests. (l.16) … I could file as a blocking finding on the whole PR: "this PR should be closed". Hmm. … I'll fold in[to F"
- p0005 DX1: "So the new lemma could be derived from `squarefree_iff_irreducible_sq_not_dvd_of_exists_irreducible`? ... The PR's proof uses Nat version + natAbs. That's fine and probably simpler."
- p0005 DX2: "So for ℤ the general lemma already applies ... a real maintainer might ask: state this in Algebra/Squarefree/Basic.lean as a general UFD-style lemma ... or keep in Data/Nat/Squarefree. Hmm."
- p0005 DX3: "whether a maintainer would request a **general** version ...? That's already `squarefree_iff_irreducible_sq_not_dvd_of_ne_zero`. ... So a shorter proof ... Whatever."
- p0005 AP3: "the convention 'A lemma that merely instantiates, reshapes or combines existing lemmas ... is not added'. Hmm, this new lemma does reshape into a Nat-indexed form which is what's used. I'd hesitate."
- p0006 DX1: "would a maintainer prefer the def to be `structure IsFundamentalDiscr (D : ℤ) : Prop where ...`? Hmm, that's a stylistic choice; Mathlib uses defs with `∧` often."
- p0006 DX3: "one could define it as a structure with fields and get projections. But then `h.1` etc. wouldn't work. Common Mathlib practice ... is to use a `def` with `∧` ... E.g., `Nat.Prime` is a def with `∧`. O"
- p0012 DX1: "The private theorem `commutator_sup_left'` has a prime in its name. Mathlib style: private lemmas... `commutator_sup_left'` is fine, but hmm — actually, maybe a maintainer would object that the privat"
- p0012 DX2: "Possible asks: avoid prime naming; the general statement could/should be public? Or the private helper could be avoided. Hmm. (l.23: declaration_search for `Subgroup.commutator_sup_left_of_normal` — '"
- p0012 DX3: "But then the name would need to change (`commutator_sup_left_of_normal`?). Hmm. ... That seems backwards from the PR's focus."
- p0012 AP1: "'A name carries a prime only to distinguish it from an unprimed sibling that is the primary form' ... Here it does distinguish from `commutator_sup_left`. So arguably fine. ... I'm not sure a maintain"
- p0012 AP3: "the primed one is arguably the general version, so it should get a proper descriptive name like `commutator_sup_left_of_normal` or similar; and it needs a docstring if kept private. Hmm. Which is the "
- p0007 AP2: "all with `{D : ℤ}`! ... Per the convention, a `variable {D : ℤ}` line should declare it once. Hmm! Is that a real ask? ... probability a maintainer asks for a `variable` line here: maybe 0.35. Skip it"
- p0014 DX2: "Notable: `mk`'s `map_id` field lacks the `:= by cat_disch` default? Actually it's a parameter, so that's fine"
- p0015 AP3: "(C) `mkHom`: the library has `PresheafOfModules.Hom` structure with `app`, `naturality := by cat_disch`. The new `mkHom` uses `where app := app; naturality := naturality` without the default. Fine, it"
- p0016 DX1: "a maintainer might point out that `mkHom` should be `PresheafOfModules.homMk`? No, `homMk` takes a presheaf morphism. Hmm."
- p0016 DX2: "naming the new one `mkHom` invites confusion — maybe name it `mkHom'`? ... could be named `homMk`... no, that collides with the existing `homMk` meaning. Hmm. Weak."
- p0016 AP1: "The census of `homMk` vs `mkHom`: `homMk` is the standard Mathlib name ... So `mkHom` in this PR deviates from the sibling convention `homMk`. Hmm, but the PR's docstring says ..."
- p0016 AP3: "a plausible maintainer reaction: why not call it `homMk` or place it as `Hom.mk'`? Eh — I have limited basis. (l.51: 'Alternatively `homMk`. Let me check the naming_norm tool ... Let me not.')"
- v0090 DX1: "Could be simplified to just `by grind` (with `mem_map` having `@[grind =]`)? Not worth."
- v0090 DX3: "Possibly also note that `simp only [mem_map, Equiv.coe_toEmbedding]` is unnecessary because `grind =` attribute on `mem_map`... hmm."
- v0090 AP1: "`mem_map_equiv` has `@[simp 1100]` but not `grind =`. ... `grind` needs `mem_map` (which has `grind =`) plus `Equiv.coe_toEmbedding`. Not an issue."
- v0090 AP2: "since mem_map is `@[grind =]`, maybe `grind` alone closes it, saving the line? Actually that doesn't address the speed."
- v0093 AP3: "could it be one line? `simpa only [...] using tendsto_of_forall_isClosed_limsup_le h`? Hmm, `simp only ... at h` then exact is fine."
- v0094 DX1: "The residual `have ... simp only [this]` could be compressed to `rw [← congrArg (· (s ×ˢ t)) ρ.disintegrate, compProd_apply_prod hs ht]`, but the local hypothesis is at least as readable, so I would n"
- v0094 DX3: "`simp only [this]` ... `rw [this]` would be more idiomatic. ... this is a real style point but minor."
- v0094 AP1: "`simpa only [this] using (compProd_apply_prod hs ht).symm` would be a single tactic. Is that better? Marginally. ... Marginal. I'd rather not file that."
- v0095 DX1: "The residual `have ... simp only [this]` could be compressed to `rw [← congrArg (· (s ×ˢ t)) ρ.disintegrate, compProd_apply_prod hs ht]`, but the local hypothesis is at least as readable, so I would n"
- v0095 DX3: "`simp only [this]` ... `rw [this]` would be more idiomatic. ... this is a real style point but minor."
- v0095 AP1: "`simpa only [this] using (compProd_apply_prod hs ht).symm` would be a single tactic. Is that better? Marginally. ... Marginal. I'd rather not file that."
- v0106 DX1: "since `Uncountable` is a class, could be `[Uncountable β]`? But it's a hypothesis; using it as an explicit argument is fine. Similarly `Infinite β` is a class but used explicitly. Fine."
- v0106 DX3: "make `[Infinite β]` an implicit instance argument to `exists_infinite_fiber` ... that's a real API question! ... `[Infinite β]` would be idiomatic. But then users who have `hβ : Infinite β` explicitly"
- v0107 DX1: "since `Uncountable` is a class, could be `[Uncountable β]`? But it's a hypothesis; using it as an explicit argument is fine. Similarly `Infinite β` is a class but used explicitly. Fine."
- v0107 DX3: "make `[Infinite β]` an implicit instance argument to `exists_infinite_fiber` ... that's a real API question! ... `[Infinite β]` would be idiomatic. But then users who have `hβ : Infinite β` explicitly"
- v0108 DX1: "since `Uncountable` is a class, could be `[Uncountable β]`? But it's a hypothesis; using it as an explicit argument is fine. Similarly `Infinite β` is a class but used explicitly. Fine."
- v0108 DX3: "make `[Infinite β]` an implicit instance argument to `exists_infinite_fiber` ... that's a real API question! ... `[Infinite β]` would be idiomatic. But then users who have `hβ : Infinite β` explicitly"
- v0092 AP1: "maybe the intended cleaner proof: `simpa only [pi_pi, this] using Fintype.prod_equiv e.symm _ _ (congrFun rfl)`? no. Let's test whether `Fintype.prod_equiv _ _ _ (fun _ ↦ rfl)` compiles."
- v0105 DX1: "Let me think about golf for `exists_infinite_fiber` ... Could use `infinite_pigeonhole_card f ℵ₀` — needs ... `#α < (ℵ₀).ord.cof`. So the case split is needed."
- v0105 DX2: "could `exists_infinite_fiber` be proven *from* `infinite_pigeonhole_card_lt` by deriving `Infinite (fiber)` from `#α < #(fiber)`? In the *infinite α* case yes; in the finite α case no. Right, the case"
- v0105 DX3: "could be proved from `infinite_pigeonhole_card_lt` in both cases uniformly? ... If #α is finite (say 3), a fiber of cardinality 5 is finite and > 3. So the conclusion doesn't follow."
- v0105 AP1: "`obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h hβ; exact ⟨a, ha.le⟩` Wait! That would be a much shorter proof. ... OK so branch 1 is needed and not derivable from `infinite_pigeonhole_card_lt`."
- v0105 AP2: "could it be shorter? ... The requirement is `#α < ℵ₀.ord.cof = ℵ₀`, i.e. α finite. If α is infinite ... take θ = succ #α. So the split is needed. Fine."
- v0105 AP3: "could `exists_infinite_fiber` just be derived from `infinite_pigeonhole_card_lt`? ... So both proofs use a case split on whether α is infinite. ... Fine, no proof-golf finding that I can substantiate."
- v0053 DX2: "The PR description is empty. A maintainer might ask for a description? The brief says don't report general risks... no description isn't a finding per se."
- v0053 DX3: "A maintainer might ask for a PR description explaining the generalization/naming... The brief says findings must be about the reviewed code... the PR description is not recoverable, so no."
- v0053 AP3: "'PR title/description state the change': left -- the title `feat(TangentCone): generalize some lemmas to TVS` states exactly what the diff does"
- v0056 DX2: "The PR description is empty. A maintainer might ask for a description? ... no description isn't a finding per se."
- v0056 DX3: "The brief says findings must be about the reviewed code ... the PR description is not recoverable, so no."
- v0056 AP3: "'PR title/description state the change': left -- the title ... states exactly what the diff does"
- v0029 DX3: "maybe the planted issue is that the PR mixes content changes with typo fixes (scope). E.g. ... "left-hand side" (hyphenation preference) ... Hmm, those are all doc."
- v0062 DX1: "card_le_card_div_left and card_le_card_div_right with their *original* proofs compile under the new sections (so those proof rewrites are unnecessary too) ... arguably *neutral* ... A maintainer likel"
- v0062 DX2: "(i) Is card_le_card_div_right provable with the have/obtain? They changed `have ⟨_, ha⟩ := ht` to `obtain ⟨b, hb⟩ := ht`. Fine, arguably style."
- v0062 DX3: "the PR changed `have ⟨_, ha⟩ := ht; ...` to `by obtain ⟨b, hb⟩ := ht; exact ...`. That's the style requirement in Mathlib (no `have` for destructuring? ...)"
- v0062 AP1: "card_le_card_div_left was changed from `have ⟨_, ha⟩ := hs; ...` to by-block with `obtain`. The convention says `;` not used to put several tactics on one line -- the PR *removed* a `;` there. Good."
- v0063 DX1: "(twin of v0062, same finding covers both lemmas) 'arguably *neutral* ... A maintainer likely wouldn't reject them.'"
- v0063 DX2: "They changed `have ⟨_, ha⟩ := ht` to `obtain ⟨b, hb⟩ := ht`. Fine, arguably style."
- v0063 DX3: "That's the style requirement in Mathlib (no `have` for destructuring? ...)"
- v0063 AP1: "the PR *removed* a `;` there. Good."
- v0060 DX2: "the outer section DivisionMonoid has a variable block after the two inner sections that duplicates [DecidableEq α] and {s t}; the maintainer might ask to hoist the shared variables. Minor style."
- v0061 DX2: "the maintainer might ask to hoist the shared variables. Minor style."
- v0061 AP2: "that seems overly pedantic and I don't think a maintainer would demand that ... the whole point of the sections is to state the differing assumptions concisely. I'd not ask for that."
- v0065 AP3: "posLog_pow proof uses simp_all in the hn case; also uses h₂a name. Meh."
- v0066 AP3: "own candidate 'rw [posLog_eq_log (one_le_pow₀ (not_le.1 ha).le), posLog_eq_log (not_le.1 ha).le, log_pow]' -- 'That's roughly the same length. So no proof-golf finding.'"
- v0067 AP3: "So plain simp does not close it -- the Finset.sum_nonneg listing is needed (well, positivity would do it, but the author's simp [...] is fine)."
- v0068 DX1: "The first step could be done with gcongr? Hmm: apply monotoneOn_posLog _ _ (norm_sum_le s f) then the subgoal is ... (moves on to the argument order; no test, no finding -- inferred)"
- v0068 DX2: "Hmm, could use gcongr? Actually a nice proof-golf: use Real.log_nonneg? Hmm ... Eh."
- v0055 DX2: "(A) Can lim_zero's proof be shortened to essentially ADedecker's suggestion? Already equivalent. Might be worth noting as a style/precedent finding? ... the current code matches the spirit. I'd rather"
- v0055 AP2: "Could be merged into fewer lines? ... Merging rw ... at hc into the simpa? Could one write simpa [tendsto_norm_atTop_iff_cobounded] using ...? No, because you need to *rewrite hc*"

## 5. Checks read as conforming (V rows), verbatim

- d0045 DX1: "Candidate B (naming): ... should be `toLinearMap_starProjection_...` per corpus (naming_norm: `toLinearMap_` 21 vs `coe_` 7). Hmm, but I argued `coe_` is justified by the generic coercion."
- d0045 DX2: "its LHS is `(K.orthogonalProjection : E →ₗ[𝕜] K)`, a coercion-ascription ... Subject `→ₗ` with `coe_` 48 plurality. So `coe_` there is right per the corpus."
- d0045 DX3: "for `coe_orthogonalProjection_eq_linearProjOfIsCompl` the subject `→ₗ` (coercion_ascription) prefers `coe_` 48 of 124 ... So for the bundled lemma, `coe_` is the plurality ✓."
- d0045 AP1: "Yaël Dillies: '`coe` should be a prefix' ... So the PR rename to `coe_orthogonalProjection_...` and `coe_starProjection_...` is well-motivated. Good ... I shouldn't object to that."
- d0045 AP2: "the `coe_` prefix of `coe_orthogonalProjection_…`/`coe_starProjection_…` matches the sibling ... plus the maintainer ruling on Zulip '`coe` should be a prefix' ... `naming_norm` reports `coe_` vs `toL"
- d0045 AP3: "that uses the coercion from ContinuousLinearMap to LinearMap, hence `coe_` prefix. Good, that's consistent with `coe_orthogonalProjection_apply` in Basic.lean."
- d0047 DX3: "my proposed rearrangement breaks because of the `end Complex` convention ... Which explains the author's choice! (l.33) I decided to drop it because the author's arrangement keeps the private helper o"
- d0008 DX2: "searched the corpus for `↓reduceDIte` and `rw [... dif_pos`: 'Both are common enough in Mathlib. So the `simp only [..., ↓reduceDIte]` idiom is acceptable — I won't flag it.'"
- d0009 DX2: "'the boilerplate `simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]` is not the standard Mathlib idiom ... Should I flag it?' (l.32) → corpus search → 'common enough ... I won'"
- d0038 AP3: "'That convention would say `Ordinal.IsNormal.cof_eq` etc. should be kept in the `IsNormal` namespace' (l.7), 'a maintainer might ask these to be in the `IsNormal` namespace ... The naming_norm for `co"
- d0035 AP2: "thought of 'the whole thing: `fun m h ↦ add_mem h.1 h.2`' (l.22), tested `intro m h; exact add_mem h.1 h.2` → failed ('`add_mem`'s implicit `?m` can't unify. So the `simp only` is needed. So the curre"
- d0043 DX2: "ran `precedent_search` on the exact definition text (l.45) — 'Not very informative' (l.48) — and filed the `[LinearOrder S]` instance instead (finding 2, line 49)"
- d0002 DX1: "there might already be a way: `e.toAlgEquiv`... the structure is by extension. Let me check `AlgEquiv.isUniformEmbedding` above does the same inline. Fine."
- d0002 DX3: "Is there a duplicate? could this be defined via `AlgEquiv.toContinuousAlgEquiv`? Let's search for existing `toContinuousAlgEquiv` or similar."
- d0002 AP1: "I. `ofAlgEquiv` duplication in Equiv.lean: the API mirrors `AlgEquiv.isUniformEmbedding`'s inline `{e with ...}`. Could be golfed using `ofAlgEquiv`"
- d0002 AP2: "is there an existing way to build a `A ≃A[R] B` from an `AlgEquiv` with continuity? There's `AlgEquiv.isUniformEmbedding` which constructs one inline with `{ e with ... }`. So `ofAlgEquiv` generalizes"
- d0002 AP3: "is `ofAlgEquiv` maybe duplicating an existing `FunLike`-based coercion: `e.toContinuousAlgEquiv`? Let's search for `toContinuousAlgEquiv`."
- p0000 DX1: "Many current PRs use `motive`. Recent Mathlib has been moving to `motive`. So fine."
- p0000 DX2: "So `motive` is the direction of travel; the PR is right. So the PR's rename matches convention. Hmm. What is left to ask?"
- p0000 DX3: "The Zulip result explicitly says naming conventions say `motive`. Good."
- p0000 AP2: "the renamed binder `C → motive` is the decided Mathlib convention for recursors (Zulip: 'naming arguments to recursors')"
- p0000 AP3: "So `motive` is indeed the modern Mathlib convention ... the rename is aligned with the library convention — good, no finding there."
- p0010 DX1: "the file's local convention (`commutator_mono_left/right`, `commutator_le_left/right`, `commutator_top_left/right`, `commutator_bot_left/right`) uses `_left`/`_right` to denote argument position ... F"
- p0010 AP2: "Precedent from Order: `disjoint_sup_left : Disjoint (a ⊔ b) c ↔ ...` — there, `sup_left` refers to the sup appearing in the left argument ... Exactly analogous. ... Good, no naming finding."
- p0010 AP3: "the corpus doesn't clearly have a convention for our pattern; `commutator_sup_left` (distributivity with the sup in the left argument) is a plausible reading. ... Is there a risk the maintainers would"
- v0090 AP3: "lean_verify_edit with body `grind`: `grind` alone fails for mem_map_equiv; the `simp only [mem_map, Equiv.coe_toEmbedding]` pre-step is needed"
- v0093 AP2: "lean_verify_edit with `exact tendsto_of_forall_isClosed_limsup_le h` alone (l.41) failed: 'the `simp only at h` IS needed ... a maintainer might ask to merge into one `simpa`? Can't.'"
- v0029 DX2: ""left hand side"->"left-hand side": correct. ... grep found only one "hand side" occurrence in that file. Nothing to ask."
- v0031 DX1: "Actually no, Wikipedia title is 'Popoviciu's inequality on variances' plural."
- v0031 DX2: "line 7: 'Changing to "variances" seems wrong/less standard' -> line 19: 'Actually the standard English formulation is "Popoviciu's inequality on variances" (Wikipedia).'"
- v0031 DX3: "'changing "inequality on variance" to "on variances" is a semantic wording change, not a typo fix' (line 18) -> '(plural) is the standard literature name. So the change is fine.' (line 24)"
- v0031 AP1: "line 7: 'That's an inconsistency within the file' (Bhatia-Davis singular) -> 'The Zulip shows the author of that lemma (Kei Tsukamoto) called it "Popoviciu's inequality on variances". So plural is int"
- v0031 AP2: "'the plural matches the standard name of the result' (line 73); submission: 'the plural is a correction, not a regression; nothing filed' (line 76)"
- v0068 AP1: "lean_verify_edit with 'gcongr; exact norm_sum_le s f' -> 'gcongr did not make progress' (line 24); submission notes cite it (line 44)"
- v0068 AP3: "gcongr did not make progress -- so the gcongr convention doesn't apply here (can't be done). Good, that removes that finding."

## 6. Reach by family (asks, sessions reached of 3) per condition

| family | asks | DX hits (of 3n) | AP hits |
|---|---|---|---|
| CORR | 2 | 6 | 6 |
| F1 | 20 | 15 | 17 |
| F10 | 10 | 17 | 20 |
| F12 | 6 | 6 | 8 |
| F2 | 8 | 0 | 11 |
| F3 | 4 | 6 | 6 |
| F4 | 6 | 12 | 12 |
| F5 | 2 | 3 | 3 |
| F6 | 6 | 0 | 0 |
| F7 | 3 | 3 | 3 |
| F8 | 20 | 22 | 19 |
| F9 | 6 | 5 | 7 |
