import Mathlib
/-! `#fold e` : the library concepts that `e`, or a subterm of it, is an unfolded instance of.

Three kinds of fold target in one discrimination tree:
* `defBody`    : a definition whose body unifies with the subterm (`QuotSMulTop`, `MulAction.orbit`);
* `classField` : a one-field `Prop` structure or class whose field type unifies (`Submodule.IsPrincipal`);
* `lemmaSide`  : a rewrite lemma (`Eq`/`Iff`) one of whose sides unifies, folding into the other side
                 (`Subgroup.finiteIndex_iff`, `Pi.single_apply`).
A hit is kept only when the fold replaces the subterm's distinctive constants by a new named concept:
the fold contains neither the subterm's head symbol nor any of its non-generic constants, and it
introduces a non-generic constant the subterm lacks. Under a binder `x`, a fold `F … x` with `x` last
and absent from `F …` is also reported as the function-level fold `F …`. -/
open Lean Meta Elab Command

namespace Fold

inductive Kind | defBody | classField | lemmaLhs | lemmaRhs
  deriving Repr, BEq, Inhabited

structure Entry where
  const : Name
  via   : Name
  kind  : Kind
  deriving BEq, Inhabited

def genericList : List Name := [``Eq, ``Ne, ``Not, ``And, ``Or, ``Iff, ``Exists, ``ite, ``dite, ``OfNat.ofNat,
  ``Zero.zero, ``One.one, ``HAdd.hAdd, ``HMul.hMul, ``HSub.hSub, ``HDiv.hDiv, ``HPow.hPow, ``Neg.neg, ``Inv.inv,
  ``LE.le, ``LT.lt, ``GE.ge, ``GT.gt, ``Membership.mem, ``setOf, ``Set, ``Function.comp, ``id, ``True, ``False,
  ``Nat, ``Int, ``Real, ``Complex, ``Singleton.singleton, ``Insert.insert, ``EmptyCollection.emptyCollection,
  ``Decidable.decide, ``Subtype, ``Prod, ``Sum, ``Sigma, ``PSigma, ``PProd, ``Nonempty, ``Inhabited, ``sorryAx,
  ``DFunLike.coe, ``FunLike, ``HSMul.hSMul, ``SMul.smul, ``Top.top, ``Bot.bot, ``Subtype.val, ``Prod.fst, ``Prod.snd,
  ``Function.Injective, ``Function.Surjective, ``propext, ``Nat.cast, ``Int.cast, ``NatCast.natCast, ``IntCast.intCast,
  ``One.toOfNat1, ``Zero.toOfNat0, ``instOfNat, ``instOfNatNat, ``Filter.atTop, ``Filter.atBot]

def genericConsts : NameSet := genericList.foldl (fun s n => s.insert n) {}

def isGeneric (n : Name) : Bool :=
  genericConsts.contains n || n.isInternalDetail || n.getRoot == `Decidable ||
  (n.components.any fun c => c.toString.startsWith "inst")

/-- The constants of `e` that carry meaning: not logical glue, not instances, not numerals. -/
def sig (e : Expr) : NameSet :=
  e.foldConsts {} fun n acc => if isGeneric n then acc else acc.insert n

def hasConst (e : Expr) (n : Name) : Bool := (e.find? fun s => s.isConstOf n).isSome

def skipName (n : Name) : Bool :=
  n.isInternal || n.isInternalDetail || n.hasMacroScopes ||
  (n.components.any fun c => let s := c.toString
    s.startsWith "_" || s.startsWith "proof_" || s.startsWith "match_" || s.startsWith "eq_" || s == "casesOn" ||
    s == "rec" || s == "recOn" || s == "noConfusion" || s == "noConfusionType" || s == "brecOn" || s == "below" ||
    s == "binductionOn" || s == "ibelow" || s == "injEq" || s == "sizeOf_spec" || s == "ofNat" || s == "toCtorIdx") ||
  [`Lean, `Std, `Mathlib, `Aesop, `Batteries, `Qq, `ProofWidgets, `Plausible, `LeanSearchClient, `Tactic, `IO, `EIO, `BaseIO, `ST, `System, `Array, `List, `String, `Char, `UInt8, `UInt16, `UInt32, `UInt64, `USize, `ByteArray, `FloatArray, `Float, `Thunk, `Task, `Option, `Except, `StateT, `ReaderT, `ExceptT, `Id].contains n.getRoot

def headConst? (e : Expr) : Option Name :=
  match e.getAppFn with
  | .const n _ => some n
  | _ => none

initialize treeRef : IO.Ref (Option (DiscrTree Entry)) ← IO.mkRef none

abbrev IndexEntry := Array DiscrTree.Key × Entry

initialize foldExt : PersistentEnvExtension IndexEntry IndexEntry (Array IndexEntry) ←
  registerPersistentEnvExtension {
    mkInitial := pure #[]
    addImportedFn := fun as => pure as.flatten
    addEntryFn := fun s e => s.push e
    exportEntriesFn := id }

/-- The pattern an entry contributes, with fresh metavariables, and the fold it produces. -/
def instantiateEntry (en : Entry) : MetaM (Option (Expr × Expr)) := do
  let env ← getEnv
  match en.kind with
  | .defBody =>
    let some ci := env.find? en.via | return none
    let some v := ci.value? | return none
    let c ← mkConstWithFreshMVarLevels en.via
    let (ms, _, _) ← forallMetaTelescopeReducing (← inferType c)
    let v := v.instantiateLevelParams ci.levelParams c.constLevels!
    let body ← Core.betaReduce (mkAppN v ms)
    return some (body, mkAppN c ms)
  | .classField =>
    let c ← mkConstWithFreshMVarLevels en.via
    let (ms, _, body) ← forallMetaTelescopeReducing (← inferType c)
    if ms.isEmpty then return none
    let self := ms.back!
    if (body.find? fun s => s.isMVar && s.mvarId! == self.mvarId!).isSome then return none
    return some (body, ← inferType self)
  | .lemmaLhs | .lemmaRhs =>
    let c ← mkConstWithFreshMVarLevels en.via
    let (_, _, body) ← forallMetaTelescopeReducing (← inferType c)
    let sides? : Option (Expr × Expr) := match body.iff?, body.eq? with
      | some (a, b), _ => some (a, b) | _, some (_, a, b) => some (a, b) | _, _ => none
    let some (a, b) := sides? | return none
    return some (if en.kind == .lemmaLhs then (a, b) else (b, a))

/-- The keys of one constant's entries, computed in a scope whose metavariables are discarded. -/
def entriesOf (env : Environment) (n : Name) (ci : ConstantInfo) : MetaM (Array (Array DiscrTree.Key × Entry)) :=
  withoutModifyingState <| withReducible do
    match ci with
    | .defnInfo d =>
      if isInstanceCore env n then return #[]
      let (_, _, body) ← lambdaMetaTelescope d.value
      let body ← instantiateMVars body
      if body.getAppFn.isMVar || body.isSort then return #[]
      if let some h := headConst? body then
        if h.toString.endsWith "match_1" || (`casesOn).isSuffixOf h || (`rec).isSuffixOf h then return #[]
      if !body.hasExprMVar then return #[]
      return #[(← DiscrTree.mkPath body, { const := n, via := n, kind := .defBody })]
    | .thmInfo t =>
      let (_, _, body) ← forallMetaTelescope t.type
      let sides? : Option (Expr × Expr) := match body.iff?, body.eq? with
        | some (a, b), _ => some (a, b) | _, some (_, a, b) => some (a, b) | _, _ => none
      let some (a, b) := sides? | return #[]
      let mut out := #[]
      if let some hb := headConst? b then
        if !isGeneric hb && a.hasExprMVar then out := out.push (← DiscrTree.mkPath a, { const := hb, via := n, kind := .lemmaLhs })
      if let some ha := headConst? a then
        if !isGeneric ha && b.hasExprMVar then out := out.push (← DiscrTree.mkPath b, { const := ha, via := n, kind := .lemmaRhs })
      return out
    | .inductInfo _ =>
      if !isStructure env n then return #[]
      let fields := getStructureFields env n
      if fields.size != 1 then return #[]
      let proj := n ++ fields[0]!
      if !env.contains proj then return #[]
      let some (body, _) ← instantiateEntry { const := n, via := proj, kind := .classField } | return #[]
      if !(← isProp body) then return #[]
      return #[(← DiscrTree.mkPath body, { const := n, via := proj, kind := .classField })]
    | _ => return #[]

def buildTree : MetaM (DiscrTree Entry) := do
  let env ← getEnv
  let mut tree : DiscrTree Entry := DiscrTree.empty
  let mut nDef := 0; let mut nCls := 0; let mut nLem := 0; let mut nErr := 0
  let t0 ← IO.monoMsNow
  for (n, ci) in env.constants.toList do
    if skipName n then continue
    let es ← try entriesOf env n ci catch _ => (do pure #[])
    if es.isEmpty && !(ci matches .defnInfo _ | .thmInfo _ | .inductInfo _) then continue
    for (keys, en) in es do
      tree := tree.insertCore keys en
      match en.kind with
      | .defBody => nDef := nDef + 1
      | .classField => nCls := nCls + 1
      | _ => nLem := nLem + 1
  let t1 ← IO.monoMsNow
  logInfo m!"fold index: {nDef} definition bodies, {nCls} one-field classes, {nLem} lemma sides, {nErr} errors, {(t1 - t0) / 1000}s"
  return tree

/-- Compute every entry of the current environment and record it in the extension, so a module
importing this one carries the index in its olean. Run once, at the end of this file. -/
elab "#fold_build" : command => runTermElabM fun _ => do
  let env ← getEnv
  let t0 ← IO.monoMsNow
  let mut n := 0
  for (c, ci) in env.constants.toList do
    if skipName c then continue
    let es ← try entriesOf env c ci catch _ => pure #[]
    for e in es do
      modifyEnv fun env => foldExt.addEntry env e
      n := n + 1
  logInfo m!"fold index recorded: {n} entries, {((← IO.monoMsNow) - t0) / 1000}s"

def getTree : MetaM (DiscrTree Entry) := do
  if let some t ← treeRef.get then return t
  let entries := foldExt.getState (← getEnv)
  let t ← if entries.isEmpty then buildTree else do
    let t0 ← IO.monoMsNow
    let mut tree : DiscrTree Entry := DiscrTree.empty
    for (keys, en) in entries do tree := tree.insertCore keys en
    logInfo m!"fold index: {entries.size} entries from the olean, {((← IO.monoMsNow) - t0) / 1000}s"
    pure tree
  treeRef.set (some t)
  return t

/-- Unfold alias definitions at the query side: a definition whose body is one application of
another constant (`Ideal.span s := Submodule.span α s`), so the query reaches keys stated with the
underlying constant. -/
def isAlias (env : Environment) (n : Name) : MetaM Bool := do
  let some (.defnInfo d) := env.find? n | return false
  if isInstanceCore env n then return false
  lambdaTelescope d.value fun _ body => do
    let f := body.getAppFn
    return f.isConst && body.getAppArgs.all fun a => a.isFVar || a.isConst || a.isSort || a.isApp && a.getAppFn.isConst && a.getAppArgs.all (·.isFVar)

def unfoldAliases (e : Expr) : MetaM Expr :=
  Meta.transform e (pre := fun s => do
    if let .const n _ := s.getAppFn then
      if ← isAlias (← getEnv) n then
        if let some s' ← unfoldDefinition? s then return .visit (← Core.betaReduce s')
    return .continue)

/-- A subterm worth folding: an application whose head is a shape or that carries a non-generic constant. -/
def worthFolding (s : Expr) : Bool :=
  s.isApp && s.nat?.isNone && !s.isAppOf ``OfNat.ofNat && !s.isAppOf ``Nat.cast && !s.isAppOf ``Int.cast && (match headConst? s with
    | some h => h == ``ite || h == ``dite || h == ``Exists || h == ``setOf || !(sig s).isEmpty
    | none => false)

def kindStr : Kind → String
  | .defBody => "def" | .classField => "class" | .lemmaLhs => "lemma←" | .lemmaRhs => "lemma→"

/-- The non-atomic proper subterms of `s` with no loose bound variables. -/
def properApps (s : Expr) : Array Expr := Id.run do
  let mut out := #[]
  for a in s.getAppArgs do
    if a.isApp && !a.hasLooseBVars && a.nat?.isNone && !a.isAppOf ``OfNat.ofNat then out := out.push a
  return out

/-- Fold one subterm `s`, sitting under the bound variables `xs`, and log every kept hit. -/
def foldSub (tree : DiscrTree Entry) (s : Expr) (xs : Array Expr) (seen : IO.Ref (Std.HashSet String)) : MetaM Unit := do
  let sigS := sig s
  let headS := headConst? s
  let survivors := properApps s
  let s' ← unfoldAliases s
  let queries := if s' == s then #[s] else #[s, s']
  for q in queries do
  for en in ← tree.getUnify q do
    let r? ← try withoutModifyingState <| withTransparency .default do
        let some (pat, fold) ← instantiateEntry en | pure none
        if ← isDefEq pat q then
          let f ← instantiateMVars fold
          pure (if f.hasExprMVar then none else some f)
        else pure none
      catch _ => pure none
    let some fold := r? | continue
    if headS.any (hasConst fold ·) then continue
    if sigS.toList.any (hasConst fold ·) then continue
    if !((sig fold).toList.any fun c => !sigS.contains c) then continue
    if survivors.any (fun a => (fold.find? (· == a)).isSome) then continue
    let key := s!"{en.const}|{← ppExpr fold}"
    if (← seen.get).contains key then continue
    seen.modify (·.insert key)
    let mut msg := m!"#fold {s} ⇒ {fold}   [{en.const}, via {en.via}, {kindStr en.kind}]"
    if let some x := xs.back? then
      if fold.isApp && fold.appArg! == x && !(fold.appFn!.containsFVar x.fvarId!) then
        msg := msg ++ m!"\n      as a function of {x}: {fold.appFn!}"
      else if xs.size > 0 then
        msg := msg ++ m!"\n      (pointwise only, under {xs})"
    logInfo msg

partial def visit (tree : DiscrTree Entry) (e : Expr) (xs : Array Expr) (seen : IO.Ref (Std.HashSet String)) : MetaM Unit := do
  if worthFolding e then foldSub tree e xs seen
  match e with
  | .app .. =>
    for a in e.getAppArgs do visit tree a xs seen
    visit tree e.getAppFn xs seen
  | .lam .. => lambdaBoundedTelescope e 1 fun ys body => visit tree body (xs ++ ys) seen
  | .forallE .. => forallBoundedTelescope e (some 1) fun ys body => visit tree body (xs ++ ys) seen
  | .mdata _ b => visit tree b xs seen
  | _ => pure ()

elab "#fold " t:term : command => runTermElabM fun _ => do
  let e ← Term.elabTerm t none
  Term.synthesizeSyntheticMVarsNoPostponing
  let e ← instantiateMVars e
  let tree ← getTree
  let seen ← IO.mkRef ({} : Std.HashSet String)
  visit tree e #[] seen
  if (← seen.get).isEmpty then logInfo m!"#fold {e}: no fold"

elab "#fold_decl " n:ident : command => runTermElabM fun _ => do
  let c ← realizeGlobalConstNoOverloadWithInfo n
  let ci ← getConstInfo c
  let tree ← getTree
  let seen ← IO.mkRef ({} : Std.HashSet String)
  logInfo m!"#fold_decl {c} : type"
  visit tree ci.type #[] seen
  if let some v := ci.value? then
    if !(← isProp ci.type) then
      logInfo m!"#fold_decl {c} : body"
      visit tree v #[] seen
  if (← seen.get).isEmpty then logInfo m!"#fold_decl {c}: no fold"

elab "#fold_stats" : command => runTermElabM fun _ => do
  let _ ← getTree
  logInfo m!"tree ready"

end Fold
