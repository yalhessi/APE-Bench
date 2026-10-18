    exact Iic_disjoint_Ici.2 hle

example [Preorder α] (x : α) : Disjoint atTop (𝓟 (Iio x)) := disjoint_atTop_principal_Iio x
example [Preorder α] [NoBotOrder α] (x : α) : Disjoint atBot (𝓟 (Ici x)) :=
  disjoint_atBot_principal_Ici x
example [Preorder α] [NoBotOrder α] (x : α) : Disjoint (pure x) atBot := disjoint_pure_atBot x
example [PartialOrder α] [Nontrivial α] : Disjoint (atTop : Filter α) atBot := disjoint_atTop_atBot
