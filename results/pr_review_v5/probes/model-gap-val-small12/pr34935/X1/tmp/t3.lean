@[simp] lemma add_eq_sup : I + J = I ⊔ J := rfl

set_option hygiene false in
open Lean Meta Elab Tactic in
example (n : ℕ) : True := by
  run_tac do
    let e ← elabTerm (← `(Monoid.npow n I)) none
    let w ← withTransparency .instances (whnf e)
    logError m!"npow unfolds to: {w}"
    let e2 ← elabTerm (← `(I ^ n)) none
    let w2 ← withTransparency .instances (whnf e2)
    logError m!"hpow unfolds to: {w2}"
    let e3 ← elabTerm (← `(n • I)) none
    let w3 ← withTransparency .instances (whnf e3)
    logError m!"nsmul unfolds to: {w3}"
    let ok ← isDefEq e e2
    logError m!"default defeq npow vs hpow: {ok}"
  trivial
