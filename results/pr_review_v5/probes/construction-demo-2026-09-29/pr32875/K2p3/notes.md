# Pass 3 (statements and the family): PR #32875

The PR changes proofs only. All eight declarations keep their statements, and the model finds no
families. I treated the two `setLIntegral_condKernel_eq_measure_prod` lemmas (kernel and measure)
as one family and every other declaration as a family of one. For each family I compiled usages,
tried generalisations, looked for twins, checked automation and compared binders against the file.
Every compile inserted text into, or replaced a declaration in, the PR's file through
`lean_verify_edit`. There are 51 constructions and 4 findings, all advisory. No blocking finding:
the PR changes no statement, so no consumer loses anything it had.

## `Finset.mem_map_equiv` (c1-c8)

- Usage: `simpa` and `simp` serve simp users in both directions (c1, c2).
- Automation: `grind` cannot use the lemma. It fails on the statement itself (c3) and on the client
  goal `b ∈ t.map e.toEmbedding` given `e.symm b ∈ t` (c4). The trace shows the cause: `mem_map`
  (a `grind =` lemma) yields `e.toEmbedding w = b`, and `grind` never identifies `e.toEmbedding w`
  with `e w`. This is also why the PR's proof needs `simp only [mem_map, Equiv.coe_toEmbedding]`
  before `grind`. With `attribute [local grind =] mem_map_equiv`, `grind` closes both client goals
  (c5). `grind [Equiv.toEmbedding_apply]` proves the statement outright (c6). In the file, only the
  4 basic `mem_*` lemmas carry `grind =`; the `simp 1100` specialisations carry none (c7).
  **Finding 4** (advisory): add `grind =`, or fix the root cause at `Equiv.toEmbedding_apply`.
- Binders and form: implicit `{f : α ≃ β}`, as in all 4 Equiv lemmas of the file. The coercion
  spelling that siblings use is also simp-closed (c8). There is no hypothesis or instance to weaken.

## `Rat.inv_intCast_den_of_pos` (c9-c16)

- Usage: it applies directly, and a client wanting the ℕ-valued `natAbs` form gets it with `omega`
  (c9, c10).
- Generalisation: the PR's proof also proves the `a ≠ 0` / `natAbs` version (c11). `0 ≤ a` fails,
  with `a = 0` as the counterexample (c12).
- Closure: the lemma is a special case of the existing `inv_intCast_den` (c13). The `a ≠ 0` version
  is too, so the family already covers it. The 10-lemma int/nat × num/den grid is complete, and
  binders match (c16).
- Automation: `simp [*]`, which proves the `num` sibling, stops at an `if` here (c14). `simp; omega`
  closes it (c15). None of the siblings is registered. Nothing to request.

## `MeasureTheory.Measure.pi_map_piCongrLeft` (c17-c24)

- Usage: the `MeasurePreserving` form (c17) and the ProductMeasure-style rewrite (c18) both work.
- Closure: the statement is exactly `(measurePreserving_piCongrLeft μ e).map_eq` (c19). That twin
  can take `map_eq := pi_map_piCongrLeft f μ` (c20). The twin's two-step `rw` proof also proves
  `pi_map_piCongrLeft` where it stands now (c21). So the PR shortens one of two independent proofs
  of the same equation. **Finding 1** (advisory): prove it once.
- Binders: `[hι' : Fintype ι']` compiles anonymously (c22). It is the only named Fintype instance
  binder in MeasureTheory (c23). **Finding 2** (advisory).
- Automation: none of the `pi_map_*` siblings is registered, and clients use this lemma by `rw`
  (c24). Nothing to request.

## `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'` (c25-c31)

- Usage: a sequence client applies it directly (c25).
- Binders: the lemma rebinds `{L : Filter ι} [L.IsCountablyGenerated]`, which `section Closed`
  already declares (l.606). Dropping them compiles, including for the l.679 caller (c26). It is the
  only lemma in that section to rebind (c27). **Finding 3** (advisory).
- Twins: the real-valued family has one member (c31). The unprimed version (hypothesis in
  `(μs i F : ℝ)`) and the open/liminf version both compile with the same two-line shape (c28, c29).
  After the PR, the primed lemma is itself `tendsto_of_forall_isClosed_limsup_le` plus `simpa`
  (c30), so any client can reach the NNReal lemma directly. I did not request the missing twins:
  they would be new declarations outside a golfing PR, and no consumer is blocked.

## `limsup_finset_sup'` (c32-c37)

- Usage: in a complete linear order the autoParams discharge all bounds (c32). In a conditionally
  complete order the client passes them (c33).
- Generalisation: weakening `h₁` to `∃ i ∈ s, …` compiles for the ≤ half but not the ≥ half, which
  needs coboundedness for every `i` through `limsup_le_limsup` (c34). `h₁` is as weak as this proof
  allows.
- Closure: `limsup_max` is its two-index case in a complete linear order (c35; the first attempt
  used nonexistent lemma names and established nothing). The primed and unprimed sup versions and
  the inf duals all exist (c36). Binders, autoParam form and registration are uniform (c37).
  Nothing to request.

## `setLIntegral_condKernel_eq_measure_prod`, kernel and measure (c38-c45)

- Usage: rectangle rewriting and the `t = univ` corner work for the measure version (c38, c39), and
  direct application works for the kernel version (c41).
- Closure: each version is the `f = 1` case of its `setLIntegral_condKernel` (c40, c42). Both
  versions of the pair exist.
- Generalisation: neither `ht` nor `hs` can be dropped. `compProd_apply_prod` needs both (c43, c44).
- Binders and registration match the file's 12 Lintegral lemmas (c45). Nothing to request.

## `Metric.exists_lt_mem_ball_of_mem_ball` (c46-c51)

The unedited Pseudo/Defs.lean reports 12 errors in this environment, at l.127-1090 (for example,
the private `dist_nonneg'`). The tool classifies all of them as already in the file. My inserted
examples introduced none except where noted.

- Usage: the CircleTransform pattern works (c46).
- Closure: the statement is `exists_between'` at `dist x y` (c48). The positive-radius strengthening
  follows in two lines (c49). Without an expected type, `exists_between' h` does not see through
  ball membership (c50), so the named lemma is still what clients need.
- Twin: an `EMetric` version holds by the same term (c47) and does not exist (c51). I did not request
  it, for the same scope reason as the portmanteau twins.

## Note on process

My first scratch directory was shared with another reviewer's run, and several of my files were
overwritten after I had compiled them. The `lean` text in `constructions.json` comes from the
compiled payloads, which I recovered and checked against the tool's error messages. It does not come
from the overwritten files.
