import json
nd = r'''@[to_additive]
protected lemma IsMulIndecomposable.subset (v : ι → M) (s : Set ι) :
    {i | IsMulIndecomposable v s i} ⊆ s :=
  fun _ h ↦ h.1'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","declaration_name":"IsMulIndecomposable.subset","new_declaration":nd}))
nd2 = r'''@[to_additive /-- The "base" of `v` relative to a morphism `f`.

In the case that `v` is the set of roots of a crystallogrphic root system, and `S = ℚ`, this is the
base of the root system associated to `f`. -/]
def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  {i | IsMulIndecomposable v {j | 1 < f (v j)} i}'''
json.dump({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","declaration_name":"IsMulIndecomposable.baseOf","new_declaration":nd2}, open("%s/tmp/e7.json" % __import__("sys").argv[1], "w"))
