# PR #31984 — notes (hard brief: library / design / typeclass / API / siblings / location / PR)

Tool calls: about 29 ptool calls, 6 of them `lean_verify_edit`. Five of those were edits; the sixth, a
first attempt at the generalized `duple`, failed on missing `Decidable` instances and a `simpa` proof,
and was fixed.

## Per dossier object (in dossier order)

- **doc_comment (added, `single`)**: the wording belongs to the other reviewer. I asked none of my questions of it. Nothing to file.
- **`FiniteProbability.single` (def)**: I asked the library question (`PMF.pure` and `stdSimplex.vertex` are the analogues)
  and the API question. It has no `single_weights` simp lemma; that ask is folded into the FiniteProbability API finding.
  I also compiled it under `IsOrderedRing` and it goes through (typeclass finding). The name `single` vs `vertex`/`pure` is naming, so I left it out.
- **doc_comment (added, `duple`)**: wording is out of scope. The inline question comment under it went into the PR-level finding.
- **`FiniteProbability.comp` (def)**: library question: `PMF.bind` is the analogue. The Zulip thread shows the `embDomain (.sigmaMk m)`
  spelling was already discussed, and Eric Wieser was content with it, so I did not ask for a helper. The proof length and
  Aristotle cleanup are proof matters, left to the other reviewer. The Aristotle disclosure went into the PR finding. `comp_weights` is part of the API finding.
- **attribute (added)**: this is the `@[expose] public section` / `open Classical in` layout, which is not in my scope. Nothing filed.
- **`FiniteProbability.duple` (def)**: generality question. I compiled a generalization to `{ι : Type v} (i j : ι)`. That became part
  of the blocking universe finding, since it is what frees `convexCombo₂` from `Type`. Mathlib's `stdSimplex` uses
  `[Semiring 𝕜] [PartialOrder 𝕜]` plus `IsOrderedRing`, the same shape as the `segment`-style `(s t) (hs ht) (h : s+t=1)` encoding, so I raised no encoding complaint about the two-weights form.
- **import in `Mathlib.lean`**: follows the file. If the file moves to `Geometry/Convex` (location finding), this line moves with it. Otherwise fine.
- **`convexCombo₂` (def)**: the key result. `#check` in a compile showed `{M : Type}`; a `Type 1` example fails; the generalized `duple`
  plus `id` family compiles and gives `{M : Type u_2}` (blocking finding). I compared it to `AffineMap.lineMap`/`segment`, which
  the TODO already mentions, so I did not file a sibling finding.
- **namespace (added, `FiniteProbability`)**: location/grouping is fine within the file. Nothing filed.
- **doc_comment (added)**: wording is out of scope. Nothing filed.
- **command (added)**: the `open ConvexSpace` / `variable` line. It carries `IsStrictOrderedRing`, which is covered by the compiled typeclass-weakening finding.
- **module_doc (added)**: I checked it for related work. It does not mention `stdSimplex` (library finding). Its TODO on `ext` supports
  the encoding finding. The wording itself is out of scope.
- **doc_comment (added)** ×2: wording is out of scope. Nothing filed.
- **namespace (added)** ×2: structural only. Nothing filed.
- **doc_comment (added)**: wording is out of scope. Nothing filed.
- **`ConvexSpace` (class)**: I asked the encoding, typeclass-layer, generality and API questions. The encoding finding is advisory
  judgment: a map out of `FiniteProbability R M` makes `ext` redundant via `Finsupp.mapDomain_congr` and removes the universe tie
  and the universe bump. The typeclass finding is compiled: `IsOrderedRing` suffices. I considered "class vs structure" and found it fine.
  There are no instances in the PR, so there is no diamond question. I dropped a standalone "add a Module/AffineSpace instance to
  validate the axioms" ask. It is already the author's TODO, and the encoding finding carries the substantive part, namely settling `ext`.
- **section (added)**: structural only. Nothing filed.
- **`FiniteProbability` (structure)**: encoding: `extends weights : ι →₀ R` plus two Prop fields is reasonable, and I did not ask
  for a subtype. The library question gave `stdSimplex` as the Fintype twin (finding) and `Finsupp.degree` as the existing function
  for the `total` field (finding). Its API is missing FunLike, ext, simp lemmas and map, compared with `stdSimplex`'s at
  StdSimplex.lean:235-301 (finding). Location: `Geometry/Convex/README.md` designates the folder (finding).
- **doc_comment (added)** ×3: wording is out of scope. Nothing filed.
- **section (added)** ×2: structural only. Nothing filed.
- **command (added)**: the `proof_wanted` / `variable` block. The `proof_wanted` lemmas inherit the `M : Type` restriction, which is covered by the blocking finding.

## PR as a whole
- I asked whether it is wanted: yes. Kim's Zulip context shows the plan. Is it one thing: yes. Is there churn: no.
  The description is empty, AI use appears only in a proof comment, and #31923 and the Zulip thread are unlinked (advisory finding).
  No meta code is involved. No declarations are removed or renamed, so there are no deprecation questions.
- Imports: a compile without `Data.ZMod.Defs` and `Algebra.Module.Defs` succeeds (advisory finding).

## Tool results that mattered
- lean_verify_edit: the universe probe failed as predicted (`{M : Type}`), the generalized `duple` fixed it, the `IsOrderedRing`
  weakening passed, and trimming the imports passed.
- file_read StdSimplex.lean: its API and docstring ('free object in the category of convex spaces').
- file_read Geometry/Convex/README.md: the location.
- content_search Weight.lean: `Finsupp.degree`. content_search Finsupp/Basic.lean: `mapDomain_congr`.
- zulip_search: the thread 'extending a finitely support function over a sigma?' and #31923.
- precedent_search: only a hint pointing to `Finsupp.degree`. The other hits were unrelated.
