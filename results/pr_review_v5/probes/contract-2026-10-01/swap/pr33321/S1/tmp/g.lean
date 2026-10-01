def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  {i | IsMulIndecomposable v {j | 1 < f (v j)} i}
