import json, sys
D = sys.argv[1]
def code(i):
    d = json.load(open(f"{D}/tmp/a{i}.json"))
    return d.get("new_declaration") or d.get("replacement")
F = []
def add(target, claim, change, severity, evidence):
    F.append(dict(target=target, claim=claim, requested_change=change, severity=severity, evidence=evidence))

add("Metric.isCover_maximalSeparatedSet",
 "`isCover_maximalSeparatedSet` re-proves by hand (by_contra, a manual separation proof of `{x} ∪ maximalSeparatedSet ε A`, `classical`, a cardinality contradiction; ~30 lines) the fact that a maximal ε-separated subset is an ε-cover, which Mathlib already has as `Metric.IsCover.of_maximal_isSeparated` in the directly imported `Mathlib/Topology/MetricSpace/Cover.lean`. Even the separation step duplicates the existing `IsSeparated.insert`.",
 "Prove that `maximalSeparatedSet ε A` is maximal for `fun N ↦ N ⊆ A ∧ IsSeparated ε N` (ideally as a public lemma `maximal_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : Maximal (fun N ↦ N ⊆ A ∧ IsSeparated ε N) (maximalSeparatedSet ε A)`, proved from `IsSeparated.encard_le_packingNumber`, `card_maximalSeparatedSet` and `Set.Finite.eq_of_subset_of_encard_le`), and derive the cover as `.of_maximal_isSeparated (maximal_maximalSeparatedSet h)`:\n\n" + code(12),
 "blocking",
 "file_read of target/Mathlib/Topology/MetricSpace/Cover.lean line 78: `nonrec lemma IsCover.of_maximal_isSeparated (hN : Maximal (fun N ↦ N ⊆ s ∧ IsSeparated ε N) N) : IsCover ε s N` (docstring: 'A maximal ε-separated subset of a set s is an ε-cover of s', Vershynin 4.2.6). MetricSeparated.lean line 72 has `IsSeparated.insert`. lean_verify_edit (line mode, lines 330-361 replaced by the maximality lemma plus the one-line cover proof) -> success: true, no errors, no warnings. A single-declaration version (inline maximality, 6 lines) also compiled: success: true.")

add("Metric.card_minimalCover",
 "`card_minimalCover` states `(minimalCover ε A).encard = coveringNumber ε A`; the subject is `Set.encard`, but the name says `card`, which in Mathlib refers to `Finset.card`/`Nat.card`/`Set.ncard`-style quantities. The file itself uses `encard` in its names (`IsSeparated.encard_le_packingNumber`, `IsCover.coveringNumber_le_encard`, `packingNumber_le_encard_self`).",
 "Rename `Metric.card_minimalCover` to `Metric.encard_minimalCover` (and update its uses).",
 "blocking",
 "naming_norm Metric.card_minimalCover -> verdict `established`: subject `encard`, 84 of 88 base declarations with that subject use the `encard_` prefix, 0 use `card_`; candidate `Metric.encard_minimalCover`.")

add("Metric.card_maximalSeparatedSet",
 "`card_maximalSeparatedSet` states `(maximalSeparatedSet ε A).encard = packingNumber ε A`, a statement about `Set.encard`, but is named with `card_`, against the corpus convention and the file's own `encard` names.",
 "Rename `Metric.card_maximalSeparatedSet` to `Metric.encard_maximalSeparatedSet` and update its uses in `card_le_of_isSeparated`, `isCover_maximalSeparatedSet` and `coveringNumber_le_packingNumber`.",
 "blocking",
 "naming_norm Metric.card_maximalSeparatedSet -> verdict `established`: `encard_` 84/88, `card_` 0; candidate `Metric.encard_maximalSeparatedSet`.")

add("Metric.card_le_of_isSeparated",
 "`Metric.card_le_of_isSeparated` concludes `C.encard ≤ (maximalSeparatedSet ε A).encard`, but its name uses `card` instead of `encard` and does not mention `maximalSeparatedSet` at all, so `Metric.card_le_of_isSeparated` reads like a generic fact about separated sets. Its sibling `IsSeparated.encard_le_packingNumber` uses dot notation on the `IsSeparated` hypothesis.",
 "Rename it to `IsSeparated.encard_le_encard_maximalSeparatedSet`, so that it is used as `h_sep.encard_le_encard_maximalSeparatedSet h_subset h` in the same way as `IsSeparated.encard_le_packingNumber`, and update its use in `isCover_maximalSeparatedSet`.",
 "blocking",
 "naming_norm Metric.card_le_of_isSeparated -> verdict `established`, subject `encard`, `encard_` 84/88, `card_` 0; candidate `Metric.encard_le_of_isSeparated`. lean_verify_edit (line mode, lines 324-358: the lemma renamed to `IsSeparated.encard_le_encard_maximalSeparatedSet (h_sep) (h_subset) (h)`, and its use in `isCover_maximalSeparatedSet` changed to `hC_separated.encard_le_encard_maximalSeparatedSet hC_subset h`) -> success: true, no errors, no warnings. Existing sibling in this file, line 138: `lemma IsSeparated.encard_le_packingNumber (h_subset : C ⊆ A) (hC : IsSeparated ε C) : C.encard ≤ packingNumber ε A`.")

add("Metric.card_le_of_isSeparated",
 "`card_le_of_isSeparated` is `IsSeparated.encard_le_packingNumber` composed with `card_maximalSeparatedSet`, but its proof re-derives the former by unfolding the `⨆` in `packingNumber` (`le_iSup_of_le C <| le_iSup_of_le h_subset <| le_iSup_of_le h_sep (by simp)`), duplicating the existing lemma. Once `isCover_maximalSeparatedSet` uses `IsCover.of_maximal_isSeparated`, it also has no use in the file.",
 "Prove it from the existing lemma: `(h_sep.encard_le_packingNumber h_subset).trans_eq (card_maximalSeparatedSet h).symm`. If no downstream use is planned, drop it, since `IsSeparated.encard_le_packingNumber` plus `card_maximalSeparatedSet` already give it.\n\n" + code(2),
 "advisory",
 "lean_verify_edit declaration_name=Metric.card_le_of_isSeparated with the term-mode proof above -> success: true, no errors, no warnings. `IsSeparated.encard_le_packingNumber` exists at line 138 of the reviewed file.")

add("Metric.coveringNumber_le_packingNumber",
 "`coveringNumber_le_packingNumber` unfolds `coveringNumber` by hand (`iInf_le _ (maximalSeparatedSet ε A)`, then `simp [..., iInf_pos, ...]`) instead of using the file's existing `IsCover.coveringNumber_le_encard`. It also splits on `packingNumber ε A ≠ ⊤` and then has to undo the negation with `simp only [ne_eq, Decidable.not_not] at h_top`.",
 "Split on `packingNumber ε A = ⊤`, close the `⊤` case with `simp [h_top]`, and use `IsCover.coveringNumber_le_encard` for the other case:\n\n" + code(3),
 "advisory",
 "lean_verify_edit declaration_name=Metric.coveringNumber_le_packingNumber with the proof above -> success: true, no errors, no warnings. `IsCover.coveringNumber_le_encard (h_subset : C ⊆ A) (hC : IsCover ε A C) : coveringNumber ε A ≤ C.encard` is at line 135 of the reviewed file.")

add("Metric.coveringNumber_two_mul_le_externalCoveringNumber",
 "`coveringNumber_two_mul_le_externalCoveringNumber` begins with `rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty)`. That case split is unnecessary: `h_nonempty` is never used, and the transitivity chain proves the empty case as well.",
 "Remove the case split and write the proof as a term:\n\n" + code(4),
 "advisory",
 "lean_verify_edit declaration_name=Metric.coveringNumber_two_mul_le_externalCoveringNumber with the one-line term proof -> success: true, no errors, no warnings (longest line 99 characters, within the 100 limit).")

add("Metric.coveringNumber_subset_le",
 "The first three calc steps of `coveringNumber_subset_le` (`coveringNumber_le_packingNumber`, the `ring_nf` rewrite, `packingNumber_two_mul_le_externalCoveringNumber`) re-derive `coveringNumber_two_mul_le_externalCoveringNumber`, which this PR proves just above. The step `packingNumber ε A = packingNumber (2 * (ε / 2)) A` is closed by `ring_nf`, a normalising tactic, where a single rewrite is enough. The calc steps also start in the same column as `calc`, unlike the other calc blocks in the file (lines 191-194), whose steps are indented.",
 "Use the PR's own `coveringNumber_two_mul_le_externalCoveringNumber`, replace `ring_nf` with `rw [mul_div_cancel₀ _ two_ne_zero]`, and indent the steps under `calc`:\n\n" + code(9),
 "advisory",
 "lean_verify_edit declaration_name=Metric.coveringNumber_subset_le with the calc above -> success: true, no errors, no warnings. The reviewed file's lines 409-418 show `calc coveringNumber ε A` followed by `_ ≤ ...` lines at the same indentation.")

add("Metric.exists_set_encard_eq_coveringNumber",
 "`exists_set_encard_eq_coveringNumber` first `simp`s `h` into an explicit finite cover `C'`, only to build the `Nonempty` instance for `ENat.exists_eq_iInf`, and then re-proves finiteness of the minimiser from `C'` in a separate bullet. Both detours are unnecessary. `A` always covers itself (`IsCover.rfl`), so the index type is nonempty unconditionally. Finiteness follows directly from `hC` and `h` via `Set.encard_ne_top_iff`.",
 "Shorten the proof to:\n\n" + code(5),
 "advisory",
 "lean_verify_edit declaration_name=Metric.exists_set_encard_eq_coveringNumber with the 5-line proof above -> success: true, no errors, no warnings. `IsCover.rfl` is at Cover.lean line 58.")

add("Metric.exists_set_encard_eq_packingNumber",
 "`exists_set_encard_eq_packingNumber` case-splits on `A` being empty only to build the `Nonempty` instance from a singleton `{a}`. The instance holds unconditionally, because `∅ ⊆ A` and `IsSeparated.empty`. The `specialize`/`simp_rw ... at h ⊢` sequence and the `rwa [hC]` finiteness bullet can also be collapsed.",
 "Drop the case split and write:\n\n" + code(6),
 "advisory",
 "lean_verify_edit declaration_name=Metric.exists_set_encard_eq_packingNumber with the proof above -> success: true, no errors, no warnings. `IsSeparated.empty` is at MetricSeparated.lean line 49.")

add("Metric.minimalCover",
 "`minimalCover` is defined by `if h : coveringNumber ε A ≠ ⊤ then … else ∅`, so `isCover_minimalCover` and `card_minimalCover` carry the side condition `coveringNumber ε A ≠ ⊤`. That condition is not needed. A minimum-cardinality internal cover always exists: `A` covers itself and `ℕ∞`'s infimum is attained (`ENat.exists_eq_iInf`). Only finiteness depends on `coveringNumber ε A ≠ ⊤`. The junk value `∅` makes the API weaker than it has to be.",
 "State `exists_set_encard_eq_coveringNumber` without the hypothesis and without the `Finite` conjunct, and define `minimalCover` as its `choose` without the `dite`. `minimalCover_subset`, `isCover_minimalCover` and `card_minimalCover` then hold unconditionally, and only `finite_minimalCover` takes `h : coveringNumber ε A ≠ ⊤`. Update the docstring to match:\n\n" + code(16),
 "advisory",
 "lean_verify_edit (line mode, lines 233-276 replaced by the block above) -> success: true, no errors, no warnings. The rest of the file still compiles, since nothing downstream uses the minimalCover lemmas with the hypothesis. The same does not hold for `maximalSeparatedSet`: packing numbers can be `⊤` without being attained, so its hypotheses stay.")

add("Metric.minimalCover",
 "`minimalCover` is preceded by `open Classical in`, which is unnecessary. The `dite` on `coveringNumber ε A ≠ ⊤` is decidable through `ℕ∞`'s `DecidableEq` instance, and the sibling `maximalSeparatedSet` uses the same `dite` pattern without `open Classical`. Mathlib discourages `open Classical` in front of definitions because it can install non-canonical `Decidable` instances into the term.",
 "Delete the `open Classical in` line before the `minimalCover` docstring.",
 "advisory",
 "lean_verify_edit (line mode, lines 248-253 replaced by the same docstring and definition without `open Classical in`) -> success: true, no errors, no warnings. `maximalSeparatedSet` (line 303) compiles as the PR leaves it with no `open Classical`.")

add("Metric.isCover_minimalCover",
 "`isCover_minimalCover`, and its siblings `minimalCover_subset`, `finite_minimalCover`, `card_minimalCover`, `maximalSeparatedSet_subset`, `isSeparated_maximalSeparatedSet` and `card_maximalSeparatedSet`, all open with the `simp?`-style line `simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]` (or the `maximalSeparatedSet` analogue), repeated seven times, just to reduce a `dite` whose condition is a hypothesis in context.",
 "Reduce the `dite` directly: use `rw [minimalCover, dif_pos h]` in the lemmas that already have `h`, and `unfold minimalCover; split_ifs with h; exacts [...]` in the unconditional ones. Do the same for the `maximalSeparatedSet` lemmas. For the minimalCover block:\n\n" + code(11),
 "advisory",
 "lean_verify_edit (line mode, lines 255-276 replaced by the four lemmas above) -> success: true, no errors, no warnings.")

add("Metric.maximalSeparatedSet",
 "The `maximalSeparatedSet` API lacks a finiteness lemma. `minimalCover` has `finite_minimalCover`, and `maximalSeparatedSet` is documented as 'a finite ε-separated subset', but no `finite_maximalSeparatedSet` is stated. The fact is only reachable through `(exists_set_encard_eq_packingNumber h).choose_spec.2.1`, which forces users to unfold the definition.",
 "Add the counterpart of `finite_minimalCover` next to `maximalSeparatedSet_subset`:\n\n" + code(8),
 "advisory",
 "lean_verify_edit (line mode, lemma inserted at line 311) -> success: true, no errors, no warnings. declaration_search Metric.finite_maximalSeparatedSet -> count 0, 'No declaration ... exists at the base commit or in the files this PR changes'. The model lists only `_subset`, `isSeparated_`, `card_`, `card_le_of_isSeparated` and `isCover_` for it.")

add("Metric.exists_set_encard_eq_coveringNumber",
 "`exists_set_encard_eq_coveringNumber` (and its sibling `exists_set_encard_eq_packingNumber`) spells the bounded existential as `∃ C, C ⊆ A ∧ …`. Mathlib uses binder notation `∃ C ⊆ A, …`, as the neighbouring `exists_finite_isCover_of_totallyBounded : ∃ N ⊆ s, N.Finite ∧ IsCover ε s N` in Cover.lean does, and Lean itself displays the goal in that form.",
 "Write the statements as `∃ C ⊆ A, C.Finite ∧ IsCover ε A C ∧ C.encard = coveringNumber ε A` and `∃ C ⊆ A, C.Finite ∧ IsSeparated ε C ∧ C.encard = packingNumber ε A`. The term is identical, so the proofs are unchanged.",
 "advisory",
 "lean_verify_edit declaration_name=Metric.exists_set_encard_eq_coveringNumber with only the statement changed to `∃ C ⊆ A, …` and the PR's proof kept -> success: true. An earlier failed probe printed the PR's goal as `⊢ ∃ C ⊆ A, C.Finite ∧ IsCover ε A C ∧ C.encard = coveringNumber ε A`, confirming the same term.")

add("Metric.finite_minimalCover",
 "The statement of `finite_minimalCover` is broken across two lines (`lemma finite_minimalCover :` / `    (minimalCover ε A).Finite := by`) even though it fits well within 100 characters on one line.",
 "Join it to `lemma finite_minimalCover : (minimalCover ε A).Finite := by`.",
 "advisory",
 "lean_verify_edit declaration_name=Metric.finite_minimalCover with the one-line signature -> success: true, no errors, no warnings.")

add("Metric.isSeparated_maximalSeparatedSet",
 "`isSeparated_maximalSeparatedSet` states `IsSeparated ε (maximalSeparatedSet ε A : Set X)`. The type ascription `: Set X` is redundant, because `maximalSeparatedSet ε A` already has type `Set X`, and it forces the statement onto a second line.",
 "Drop the ascription: `lemma isSeparated_maximalSeparatedSet : IsSeparated ε (maximalSeparatedSet ε A) := by`.",
 "advisory",
 "lean_verify_edit declaration_name=Metric.isSeparated_maximalSeparatedSet without the ascription, on one line -> success: true, no errors, no warnings.")

add("module_doc in Mathlib/Topology/MetricSpace/CoveringNumbers.lean",
 "The module docstring, which this PR rewrites, still reads 'the extenal covering number of a set `A`' in the `externalCoveringNumber` bullet of 'Main definitions'. 'extenal' is a typo.",
 "Change 'extenal' to 'external' in the `externalCoveringNumber` bullet of the module docstring.",
 "advisory",
 "file_read target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean line 25: `* `externalCoveringNumber`: the extenal covering number of a set `A` for radius `ε` is the minimal`. The model lists the module_doc as modified by this PR.")

add("Metric.coveringNumber_le_packingNumber",
 "The new main statements `coveringNumber_le_packingNumber`, `coveringNumber_two_mul_le_externalCoveringNumber` and `coveringNumber_subset_le` are listed under 'Main statements' in the module docstring but have no docstrings. The pre-existing comparison theorem in the same `Comparisons` section, `packingNumber_two_mul_le_externalCoveringNumber`, does have one.",
 "Add docstrings in the style of the existing one, e.g. `/-- The covering number of a set `A` for radius `ε` is at most its packing number for radius `ε`. -/` on `coveringNumber_le_packingNumber`, and similar one-line docstrings on `coveringNumber_two_mul_le_externalCoveringNumber` and `coveringNumber_subset_le`.",
 "advisory",
 "file_read lines 365-418: `packingNumber_two_mul_le_externalCoveringNumber` (line 367) has a docstring; `coveringNumber_le_packingNumber` (393), `coveringNumber_two_mul_le_externalCoveringNumber` (402) and `coveringNumber_subset_le` (409) have none.")

json.dump(F, open(f"{D}/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(F))
