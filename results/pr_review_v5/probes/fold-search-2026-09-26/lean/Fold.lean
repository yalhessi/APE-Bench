module

public import Lean

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

@[expose] public meta section

namespace Fold

inductive Kind | defBody | classField | lemmaLhs | lemmaRhs
  deriving Repr, BEq, Inhabited

structure Entry where
  const : Name
  via   : Name
  kind  : Kind
  deriving BEq, Inhabited

def genericList : List Name := [`Eq, `Ne, `Not, `And, `Or, `Iff, `Exists, `ite, `dite, `OfNat.ofNat,
  `Zero.zero, `One.one, `HAdd.hAdd, `HMul.hMul, `HSub.hSub, `HDiv.hDiv, `HPow.hPow, `Neg.neg, `Inv.inv,
  `LE.le, `LT.lt, `GE.ge, `GT.gt, `Membership.mem, `setOf, `Set, `Function.comp, `id, `True, `False,
  `Nat, `Int, `Real, `Complex, `Singleton.singleton, `Insert.insert, `EmptyCollection.emptyCollection,
  `Decidable.decide, `Subtype, `Prod, `Sum, `Sigma, `PSigma, `PProd, `Nonempty, `Inhabited, `sorryAx,
  `DFunLike.coe, `FunLike, `HSMul.hSMul, `SMul.smul, `Top.top, `Bot.bot, `Subtype.val, `Prod.fst, `Prod.snd,
  `Function.Injective, `Function.Surjective, `propext, `Nat.cast, `Int.cast, `NatCast.natCast, `IntCast.intCast,
  `One.toOfNat1, `Zero.toOfNat0, `instOfNat, `instOfNatNat, `Filter.atTop, `Filter.atBot]

def genericConsts : NameSet := genericList.foldl (fun s n => s.insert n) {}

def isGeneric (n : Name) : Bool :=
  genericConsts.contains n || n.isInternalDetail || n.getRoot == `Decidable ||
  (n.components.any fun c => c.toString.startsWith "inst")

/-- The constants of `e` that carry meaning: not logical glue, not instances, not numerals. -/
def sig (e : Expr) : NameSet :=
  e.foldConsts {} fun n acc => if isGeneric n then acc else acc.insert n

def hasConst (e : Expr) (n : Name) : Bool := (e.find? fun s => s.isConstOf n).isSome

initialize instLikeCache : IO.Ref (Std.HashMap Name Bool) ← IO.mkRef {}

/-- An instance, or a constant whose result type is a class (`CommRing.toCommSemiring`,
`Semiring.toModule`, `Algebra.id`): glue, never a concept. -/
def isInstanceLike (n : Name) : MetaM Bool := do
  if let some b := (← instLikeCache.get).get? n then return b
  let env ← getEnv
  let b ← (do
    if isInstanceCore env n then return true
    let some ci := env.find? n | return false
    try
      forallTelescopeReducing ci.type fun _ ty => do
        if ty.isSort then return false
        return (← isClass? ty).isSome
    catch _ => return false)
  instLikeCache.modify (·.insert n b)
  return b

/-- The constants of `e` that carry meaning, instance glue excluded. -/
def sigM (e : Expr) : MetaM NameSet := do
  let mut acc : NameSet := {}
  for n in e.foldConsts ([] : List Name) (fun n l => n :: l) do
    if isGeneric n then continue
    if ← isInstanceLike n then continue
    acc := acc.insert n
  return acc

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

/-- A side that is a hole, or a binder telescope over a hole application: matches anything. -/
def patternLike (e : Expr) : Bool := Id.run do
  let mut b := e
  while b.isForall || b.isLambda do b := b.bindingBody!
  return b.getAppFn.isMVar

def keyed (keys : Array DiscrTree.Key) (en : Entry) : Array (Array DiscrTree.Key × Entry) :=
  if keys.isEmpty then #[] else match keys[0]! with
    | .star => #[]
    | _ => #[(keys, en)]

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
      if !body.hasExprMVar || patternLike body then return #[]
      return keyed (← DiscrTree.mkPath body) { const := n, via := n, kind := .defBody }
    | .thmInfo _ | .axiomInfo _ | .opaqueInfo _ =>
      -- under the module system an imported theorem whose proof is not exposed is not a `thmInfo`
      let (_, _, body) ← forallMetaTelescope ci.type
      let sides? : Option (Expr × Expr) := match body.iff?, body.eq? with
        | some (a, b), _ => some (a, b) | _, some (_, a, b) => some (a, b) | _, _ => none
      let some (a, b) := sides? | return #[]
      let mut out := #[]
      if let some hb := headConst? b then
        if !isGeneric hb && a.hasExprMVar && !patternLike a then out := out ++ keyed (← DiscrTree.mkPath a) { const := hb, via := n, kind := .lemmaLhs }
      if let some ha := headConst? a then
        if !isGeneric ha && b.hasExprMVar && !patternLike b then out := out ++ keyed (← DiscrTree.mkPath b) { const := ha, via := n, kind := .lemmaRhs }
      return out
    | .inductInfo _ =>
      if !isStructure env n then return #[]
      let fields := getStructureFields env n
      if fields.size != 1 then return #[]
      let proj := n ++ fields[0]!
      if !env.contains proj then return #[]
      let some (body, _) ← instantiateEntry { const := n, via := proj, kind := .classField } | return #[]
      if !(← isProp body) || patternLike body then return #[]
      return keyed (← DiscrTree.mkPath body) { const := n, via := proj, kind := .classField }
    | _ => return #[]

def buildTree : MetaM (DiscrTree Entry) := do
  let env ← getEnv
  let mut tree : DiscrTree Entry := DiscrTree.empty
  let mut nDef := 0; let mut nCls := 0; let mut nLem := 0; let mut nErr := 0
  let t0 ← IO.monoMsNow
  -- imported constants through the module data (under the module system `env.constants` does not
  -- enumerate imported theorems), then the file's own constants
  let mut all : Array (Name × ConstantInfo) := #[]
  for mod in env.header.moduleData do
    for ci in mod.constants do all := all.push (ci.name, ci)
  for (n, ci) in env.constants.map₂.toList do all := all.push (n, ci)
  for (n, ci) in all do
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
  let mut all : Array (Name × ConstantInfo) := #[]
  for mod in env.header.moduleData do
    for ci in mod.constants do all := all.push (ci.name, ci)
  for (c, ci) in env.constants.map₂.toList do all := all.push (c, ci)
  for (c, ci) in all do
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
    if !f.isConst || f.isConstOf n then return false
    for a in body.getAppArgs do
      if a.isFVar || a.isConst || a.isSort || a.isLit then continue
      if a.hasLooseBVars || a.isLambda then return false
      -- an instance argument is fine, anything else makes this a real definition
      let ty ← try inferType a catch _ => return false
      if (← isClass? ty).isNone then return false
    return true

/-- Unfold every alias head in `e` once (no re-unfolding of the result's head). -/
def unfoldAliases (e : Expr) : MetaM Expr :=
  Meta.transform e (pre := fun s => do
    if s.isApp then
      if let .const n _ := s.getAppFn then
        if ← isAlias (← getEnv) n then
          if let some s' ← unfoldDefinition? s then return .continue (some s'.headBeta)
    return .continue)

/-- `e`, then up to two successive one-level unfoldings, distinct. -/
def unfoldLevels (e : Expr) : MetaM (Array Expr) := do
  let mut out := #[e]
  let mut cur := e
  for _ in [0, 1] do
    let nxt ← unfoldAliases cur
    if nxt == cur then break
    out := out.push nxt; cur := nxt
  return out

/-- A subterm worth folding: an application whose head is a shape or that carries a non-generic constant. -/
def worthFolding (s : Expr) : Bool :=
  ((s.isForall || s.isLambda) && !(sig s).isEmpty) ||
  (s.isApp && s.nat?.isNone && !s.isAppOf `OfNat.ofNat && !s.isAppOf `Nat.cast && !s.isAppOf `Int.cast && (match headConst? s with
    | some h => h == `ite || h == `dite || h == `Exists || h == `setOf || !(sig s).isEmpty
    | none => false))

def kindStr : Kind → String
  | .defBody => "def" | .classField => "class" | .lemmaLhs => "lemma←" | .lemmaRhs => "lemma→"

/-- The non-atomic proper parts of `s`: its application arguments that are applications, and the
bodies of its binders and of its lambda arguments (compared structurally, bound variables included). -/
def properParts (s : Expr) : Array Expr := Id.run do
  let mut out := #[]
  if s.isForall || s.isLambda then out := out.push s.bindingBody!
  for a in s.getAppArgs do
    if a.isLambda then out := out.push a.bindingBody!
    else if a.isApp && a.nat?.isNone && !a.isAppOf `OfNat.ofNat then out := out.push a
  return out

/-- A naming fold: the head is a non-generic constant and every argument is an atom (variable,
constant, literal, sort), an instance, or a part of some query level. Anything else is a rewrite of
the subterm into another shape rather than a name for it. -/
def isNamingFold (fold : Expr) (levels : Array Expr) : MetaM Bool := do
  let some h := headConst? fold | return false
  if isGeneric h then return false
  for a in fold.getAppArgs do
    if a.isFVar || a.isConst || a.isSort || a.isLit || a.nat?.isSome || a.isAppOf `OfNat.ofNat then continue
    if a.isMVar then return false
    if a.isLambda && !a.bindingBody!.hasLooseBVars then continue   -- a constant type family
    let ty ← try inferType a catch _ => return false
    if ty.isSort then continue                                       -- a type argument
    if (← isClass? ty).isSome then continue                          -- an instance
    if levels.any (fun l => (l.find? (· == a)).isSome) then continue -- a part of the query
    return false
  return true

/-- Fold one subterm `s`, sitting under the bound variables `xs`, and log every kept hit. -/
def foldSub (tree : DiscrTree Entry) (s : Expr) (xs : Array Expr) (seen : IO.Ref (Std.HashSet String)) : MetaM Unit := do
  if (← isClass? (← inferType s)).isSome then return   -- an instance term is not a fold subject
  let levels ← unfoldLevels s
  let sigS ← sigM s
  let mut sigAll : NameSet := {}
  for l in levels do
    for n in (← sigM l).toList do sigAll := sigAll.insert n
  let heads := levels.filterMap headConst? |>.filter (!isGeneric ·)
  let survivors := levels.foldl (fun acc l => acc ++ properParts l) #[]
  for q in levels do
  for en in ← tree.getUnify q do
    let r? ← try withoutModifyingState <| withTransparency .instances do
        let some (pat, fold) ← instantiateEntry en | pure none
        if ← isDefEq pat q then
          let f ← instantiateMVars fold
          pure (if f.hasExprMVar then none else some f)
        else pure none
      catch _ => pure none
    let some fold := r? | continue
    -- matching a simp lemma's right-hand side and producing its left-hand side un-simps the term
    if en.kind == .lemmaRhs then
      if (← getSimpTheorems).isLemma (.decl en.via) then continue
    if heads.any (hasConst fold ·) then continue
    if sigS.toList.any (hasConst fold ·) then continue
    if !((← sigM fold).toList.any fun c => !sigAll.contains c) then continue
    if survivors.any (fun a => (fold.find? (· == a)).isSome) then continue
    let key := s!"{en.const}|{← ppExpr fold}"
    if (← seen.get).contains key then continue
    seen.modify (·.insert key)
    let naming ← isNamingFold fold levels
    let mut msg := m!"#fold {s} ⇒ {fold}   [{en.const}, via {en.via}, {kindStr en.kind}, {if naming then "naming" else "rewrite"}]"
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
  | .lam .. =>
    visit tree e.bindingDomain! xs seen
    lambdaBoundedTelescope e 1 fun ys body => visit tree body (xs ++ ys) seen
  | .forallE .. =>
    visit tree e.bindingDomain! xs seen   -- a hypothesis is a fold subject too
    forallBoundedTelescope e (some 1) fun ys body => visit tree body (xs ++ ys) seen
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

elab "#fold_cands " t:term : command => runTermElabM fun _ => do
  let e ← Term.elabTerm t none
  Term.synthesizeSyntheticMVarsNoPostponing
  let e ← instantiateMVars e
  let tree ← getTree
  let levels ← unfoldLevels e
  logInfo m!"#fold_cands {e}  levels: {levels.toList}"
  for q in levels do
    let cands ← tree.getUnify q
    logInfo m!"  {cands.size} candidates for {q}: {cands.toList.take 40 |>.map (·.via)}"
    for en in cands.toList.take 40 do
      let ok ← try withoutModifyingState <| withTransparency .instances do
          let some (pat, _) ← instantiateEntry en | pure "no pattern"
          let u ← isDefEq pat q
          let pp ← ppExpr pat
          pure (if u then "unifies" else s!"fails: {pp}")
        catch ex => do
          let m ← ex.toMessageData.toString
          pure s!"error: {m}"
      if ok != "no pattern" then logInfo m!"    {en.via}: {ok}"

/-- Try one named entry against a term: is it in the tree's candidates, and does it unify at each level? -/
elab "#fold_try " n:ident " : " k:str t:term : command => runTermElabM fun _ => do
  let via ← realizeGlobalConstNoOverloadWithInfo n
  let kind : Kind := match k.getString with
    | "def" => .defBody | "class" => .classField | "lhs" => .lemmaLhs | _ => .lemmaRhs
  let e ← Term.elabTerm t none
  Term.synthesizeSyntheticMVarsNoPostponing
  let e ← instantiateMVars e
  let tree ← getTree
  let en : Entry := { const := via, via := via, kind := kind }
  for q in ← unfoldLevels e do
    let cands ← tree.getUnify q
    let inTree := cands.any (·.via == via)
    let keysQ ← withReducible <| DiscrTree.mkPath q
    let r ← try withoutModifyingState <| withTransparency .instances do
        let some (pat, fold) ← instantiateEntry en | pure "no pattern from the entry"
        let keysP ← withReducible <| DiscrTree.mkPath pat
        let ok ← isDefEq pat q
        let pp ← ppExpr pat
        let fold ← instantiateMVars fold
        let pf ← ppExpr fold
        let levels ← unfoldLevels e
        let sigS ← sigM e
        let mut sigAll : NameSet := {}
        for l in levels do
          for n in (← sigM l).toList do sigAll := sigAll.insert n
        let heads := levels.filterMap headConst? |>.filter (!isGeneric ·)
        let survivors := levels.foldl (fun acc l => acc ++ properParts l) #[]
        let f1 := heads.any (hasConst fold ·)
        let f2 := sigS.toList.any (hasConst fold ·)
        let f3 := !((← sigM fold).toList.any fun c => !sigAll.contains c)
        let f4 := survivors.any (fun a => (fold.find? (· == a)).isSome)
        let f5 := fold.hasExprMVar
        let cls ← isClass? (← inferType q)
        pure s!"pattern {pp}\n    keys pattern {format keysP}\n    keys query   {format keysQ}\n    unifies: {ok}{if ok then s!"  fold: {pf}" else ""}\n    filters: head-survives={f1} sig-survives={f2} nothing-new={f3} part-survives={f4} mvars={f5} query-is-instance={cls.isSome} worth={worthFolding q}\n    sig(q)={sigS.toList} sig(fold)={(← sigM fold).toList} heads={heads}"
      catch ex => do let m ← ex.toMessageData.toString; pure s!"error: {m}"
    logInfo m!"#fold_try {via} against {q}: in candidates = {inTree} ({cands.size} candidates)\n    {r}"

elab "#fold_stats" : command => runTermElabM fun _ => do
  let _ ← getTree
  logInfo m!"tree ready"

end Fold

end
