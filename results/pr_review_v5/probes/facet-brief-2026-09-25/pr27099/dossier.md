# Dossier for PR #27099 (built deterministically from the diff; no review text)

Each changed object, with what changed, and the cells to check for its object kind (see the procedure).

## theorem: `FirstOrder.Language.presburger.realize_one` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_one : Term.realize v (1 : presburger.Term α) = 1`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_finsum`, `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.funMap_one`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.realize_nsmul`

## theorem: `FirstOrder.Language.presburger.natCast_zero` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem natCast_zero : NatCast.natCast 0 = (0 : presburger.Term α)`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.natCast_succ`, `FirstOrder.Language.presburger.funMap_zero`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.zero_nsmul`

## theorem: `FirstOrder.Language.presburger.realize_finsum` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_finsum [AddCommMonoidWithOne M] {β : Type*} [Fintype β] {f : β → presburger.Term α} : Term.realize v (finsum f) = ∑ i, Term.realize v (f i)`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.finsum`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.realize_nsmul`

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## instance: `None` (instance, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: statement_or_type:added, value_or_body:added
- header: `instance : Add (presburger.Term α) where add`
- siblings in this PR sharing a name token: none

## theorem: `FirstOrder.Language.presburger.realize_add` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_add : Term.realize v (t₁ + t₂) = Term.realize v t₁ + Term.realize v t₂`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.realize_finsum`, `FirstOrder.Language.presburger.funMap_add`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.realize_nsmul`

## instance: `None` (instance, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: statement_or_type:added, value_or_body:added
- header: `instance : presburger.Structure M where funMap | .zero, _ => 0 | .one, v => 1 | .add, v => v 0 + v 1`
- siblings in this PR sharing a name token: none

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## theorem: `FirstOrder.Language.presburger.funMap_add` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem funMap_add {v} : @Structure.funMap presburger M _ _ presburgerFunc.add v = v 0 + v 1`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.funMap_one`, `FirstOrder.Language.presburger.funMap_zero`

## doc_comment in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: documentation:added

## definition: `FirstOrder.Language.presburger.finsum` (def, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- header: `noncomputable def finsum {β : Type*} [Fintype β] (f : β → presburger.Term α) : presburger.Term α`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_finsum`

## theorem: `FirstOrder.Language.presburger.realize_zero` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_zero : Term.realize v (0 : presburger.Term α) = 0`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.natCast_zero`, `FirstOrder.Language.presburger.realize_finsum`, `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.funMap_zero`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.realize_nsmul`

## theorem: `FirstOrder.Language.presburger.funMap_one` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem funMap_one {v} : @Structure.funMap presburger M _ _ presburgerFunc.one v = 1`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.funMap_add`, `FirstOrder.Language.presburger.funMap_zero`

## namespace in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## instance: `None` (instance, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: statement_or_type:added, value_or_body:added
- header: `instance : NatCast (presburger.Term α) where natCast`
- siblings in this PR sharing a name token: none

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## module_doc in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: documentation:added

## theorem: `FirstOrder.Language.presburger.realize_succ` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_succ : Term.realize v (succ t) = Term.realize v t + 1`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.realize_finsum`, `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.natCast_succ`, `FirstOrder.Language.presburger.succ`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.succ_nsmul`

## theorem: `FirstOrder.Language.presburger.natCast_succ` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem natCast_succ {n : ℕ} : NatCast.natCast (n + 1) = (n : presburger.Term α) + 1`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.natCast_zero`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.succ`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.succ_nsmul`

## instance: `None` (instance, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: statement_or_type:added, value_or_body:added
- header: `instance : One (presburger.Term α) where one`
- siblings in this PR sharing a name token: none

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## import in `Mathlib.lean` (modified)
- changed: imports:added

## definition: `FirstOrder.Language.presburger.succ` (def, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: name:added, statement_or_type:added, value_or_body:added
- header: `def succ (t : presburger.Term α)`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.natCast_succ`, `FirstOrder.Language.presburger.succ_nsmul`

## theorem: `FirstOrder.Language.presburger.funMap_zero` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem funMap_zero {v} : @Structure.funMap presburger M _ _ presburgerFunc.zero v = 0`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.natCast_zero`, `FirstOrder.Language.presburger.funMap_add`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.funMap_one`, `FirstOrder.Language.presburger.zero_nsmul`

## namespace in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## theorem: `FirstOrder.Language.presburger.realize_natCast` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_natCast [AddMonoidWithOne M] {n : ℕ} : Term.realize v (n : presburger.Term α) = n`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.natCast_zero`, `FirstOrder.Language.presburger.realize_finsum`, `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.natCast_succ`, `FirstOrder.Language.presburger.realize_nsmul`

## definition: `FirstOrder.Language.presburger` (def, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: name:added, statement_or_type:added, value_or_body:added
- header: `def Language.presburger : Language`
- siblings in this PR sharing a name token: none

## definition: `FirstOrder.presburgerFunc` (inductive, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: name:added, statement_or_type:added, value_or_body:added
- header: `inductive presburgerFunc : ℕ → Type | zero : presburgerFunc 0 | one : presburgerFunc 0 | add : presburgerFunc 2 deriving DecidableEq`
- siblings in this PR sharing a name token: none

## doc_comment in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: documentation:added

## instance: `None` (instance, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: statement_or_type:added, value_or_body:added
- header: `instance : Zero (presburger.Term α) where zero`
- siblings in this PR sharing a name token: none

## doc_comment in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: documentation:added

## instance: `None` (instance, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: statement_or_type:added, value_or_body:added
- header: `instance : SMul ℕ (presburger.Term α) where smul`
- siblings in this PR sharing a name token: none

## theorem: `FirstOrder.Language.presburger.succ_nsmul` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem succ_nsmul {n : ℕ} : (n + 1) • t = n • t + t`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.natCast_succ`, `FirstOrder.Language.presburger.succ`, `FirstOrder.Language.presburger.realize_nsmul`, `FirstOrder.Language.presburger.zero_nsmul`

## theorem: `FirstOrder.Language.presburger.realize_nsmul` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem realize_nsmul [AddMonoidWithOne M] {n : ℕ} : Term.realize v (n • t) = n • Term.realize v t`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.realize_one`, `FirstOrder.Language.presburger.realize_finsum`, `FirstOrder.Language.presburger.realize_add`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.realize_succ`, `FirstOrder.Language.presburger.realize_natCast`, `FirstOrder.Language.presburger.succ_nsmul`, `FirstOrder.Language.presburger.zero_nsmul`

## doc_comment in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: documentation:added

## section in `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean` (added)
- changed: namespace:added

## theorem: `FirstOrder.Language.presburger.zero_nsmul` (theorem, added)
- file: `Mathlib/ModelTheory/Arithmetic/Presburger/Basic.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem zero_nsmul : 0 • t = 0`
- siblings in this PR sharing a name token: `FirstOrder.Language.presburger.natCast_zero`, `FirstOrder.Language.presburger.realize_zero`, `FirstOrder.Language.presburger.funMap_zero`, `FirstOrder.Language.presburger.succ_nsmul`, `FirstOrder.Language.presburger.realize_nsmul`

## Removed declarations
none
