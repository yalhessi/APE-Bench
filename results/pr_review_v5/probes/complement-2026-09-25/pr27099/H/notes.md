# PR 27099 notes (hard-questions reviewer)

Tool calls: about 22. Compiles: 5 (lines 66-134 splice succeeded; ofNat without no_index failed, then succeeded with it; round-trip example: first attempt failed at a bad `intro`, second attempt the only error was the sorry policy).

- **realize_one**: checked it against ring's `realize_one`. It holds only for the canonical instance, which feeds finding 1 (state the realize lemmas under a compatibility class). Nothing specific to it beyond that.
- **natCast_zero**: considered asking for the `((0 : ℕ) : Term)` coercion form in place of `NatCast.natCast 0`. Dropped: simp still fires, because `Nat.cast` is reducible and realize_natCast's proof uses it, so this is statement style only.
- **realize_finsum**: generality compile. `[AddCommMonoid M] [One M]` suffices (finding 3). The encoding change makes its proof `simp only …; exact Finset.sum_map_toList _ _` (finding 2).
- **section (1st)**: no questions apply.
- **instance Add (Term)**: sibling check against Ring/Basic.lean:104-108, which has `add_def`. The `_def` lemma is missing here (finding 6). No diamond: Term has no other Add.
- **realize_add**: same as realize_one. It is rfl for the canonical instance only (finding 1).
- **instance presburger.Structure M**: the main typeclass question. Every other ModelTheory language gives its canonical structure as a def: Order.lean:202-204, Ring/Basic.lean:214-218, Graph.lean:52 and Basic.lean:775, the Order and Ring docstrings explaining why. A compile showed the structure → operations → instance round trip is not a defeq (`exact rfl` fails). Filed as blocking (finding 1). I also checked ultraproducts as a possible diamond: `Filter.Product` has no Add instance, so no diamond there. Dropped.
- **section (2nd)**: nothing.
- **funMap_add**: considered sibling consistency with ring's `addFunc` abbrevs, which fix the `presburgerFunc 2` vs `presburger.Functions 2` type. Dropped: the `@`-form works for simp, and this is style.
- **doc_comment (several)**: wording is the other reviewer's job. The finsum docstring's admission that the result depends on choice motivated finding 2.
- **finsum (def)**: encoding judgment backed by a compile. A List-indexed sum is computable and its realize lemma needs no commutativity (finding 2). The name clashes with root `finsum` (Finprod.lean:96), so I asked for `protected` rather than a rename (finding 5).
- **realize_zero**: covered by finding 1.
- **funMap_one**: covered by finding 1 (these become the compatibility-class fields).
- **namespace blocks**: no issue.
- **instance NatCast (Term)**: this instance plus `instOfNat` makes numerals `OfNat.ofNat`, and simp cannot evaluate `realize v (2 : Term)`. Shown by compile; `realize_ofNat` needs `no_index` (finding 4). The `Nat.unaryCast` encoding itself is fine semantically.
- **module_doc**: its TODO says the author wants to generalize finsum/NatCast/SMul, which supports findings 2 and 3. Location `ModelTheory/Arithmetic/Presburger/` is a new folder; searching the library found no other Presburger material. Nothing to file.
- **realize_succ / succ (def)**: considered asking whether `succ` earns a def, since it is just `t + 1` and realize_succ is realize_add plus realize_one. Dropped: #27100 may use it and I have no evidence either way.
- **natCast_succ**: same statement-form point as natCast_zero. Dropped.
- **instance One (Term)**: `one_def` is missing (finding 6).
- **import in Mathlib.lean**: correct alphabetical placement, and a new file needs it. Nothing to file.
- **funMap_zero**: covered by finding 1.
- **realize_natCast**: generality. It needs AddMonoidWithOne for the RHS cast, so it cannot be weakened. Its missing ofNat companion is finding 4.
- **Language.presburger (def)**: library check. There is no existing Presburger language. It is a reduct of `Language.ring`, and I considered asking for an `LHom` into ring. Dropped as scope creep with no precedent requiring it. Also considered a `card_presburger`/`Fintype Symbols` analogue of `card_ring`. Dropped: no user need shown.
- **presburgerFunc (inductive)**: matches the `ringFunc` design (inductive indexed by arity, deriving DecidableEq). Nothing to file.
- **instance Zero (Term)**: `zero_def` is missing (finding 6).
- **instance SMul ℕ (Term)**: I looked for a diamond and found none, because Term has no AddMonoid and so no other ℕ-action. `nsmulRec` yields `0 + t` for `1 • t`, which is harmless semantically. Dropped.
- **succ_nsmul / zero_nsmul**: they duplicate the root `succ_nsmul` / `zero_nsmul` (Group/Defs.lean:582/578) in name and statement. A compile showed `protected` works (finding 5).
- **realize_nsmul**: generality compile. `[AddMonoid M] [One M]` suffices (finding 3).
- **PR as a whole**: it is one coherent thing (a language only), the motivation is linked (#27100), and there is no meta code. Zulip had no prior discussion. The precedent search returned unrelated hits. Nothing filed.
