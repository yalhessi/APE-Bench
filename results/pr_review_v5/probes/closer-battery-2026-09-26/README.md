# Closer battery on the missed asks (2026-09-26)

**Question.** The user's, 2026-09-26: *"how do we get the model to realize that a duplicate
exists? How do we get it to comprehensively search for an answer?"* This probe asks whether the
mechanical asks the pipeline missed are surfaced by **fixed procedures run exhaustively over the
objects of a kind**, rather than by a reviewer noticing anything. The labels are
`results/pr_review_v5/adjudications/miss-warrants-2026-09-26/finding_mechanism.jsonl` (one reader,
provisional): 31 of the 38 misses of both sets have such a procedure, 7 are judgment.

**Method.** Each variant is the PR's reviewed file with **one edit**, compiled with `lake env lean`
from the PR's reviewed workspace (`workspaces/<base>+<fp>`); `controls.py` compiles the unedited
file. `outcomes.json` has each variant's exit, wall time and errors; `battery.py` and `battery3.py`
hold the edits. Two workspaces on Lean 4.26 need `-Dexperimental.module=true` for a file compiled
outside `lake build`. The edits were **targeted**: the ask said which edit to try. What this
measures is whether the procedure's *output* is the maintainer's ask when the procedure lands on
the right object, and what a compile costs. The exhaustive run over every object, with its yield and
its non-gold output, is the next step, not this one.

## Outcomes

| miss | the ask | procedure | outcome | s |
|---|---|---|---|---|
| v0062, v0063 (30458) | "does the old proof not work?" | old-proof replay: the pre-PR proof under the new variables | **both compile** | 37 |
| v0016 (26755) | "how many `noncomputable`s are still necessary?" | drop each `noncomputable`, compile | **all four compile without it** | 9-10 |
| v0131, v0132 (36822) | "simp?" at a dropped `@[simp]` | diff lint (attribute removed from an unchanged declaration); `(attr := simp)` fix | **fix compiles** | 36 |
| 95eb6cac0fc0 (33294) | `h.map_iSup` for `Order.IsNormal.map_iSup h` | dot-notation lint; rewrite | **compiles** | 8 |
| 63fdc033749f, 1c71d01c03a4 (33145) | prove the `inf` lemmas from the `sup` ones in `αᵒᵈ` | dual application on a sup/inf pair with near-identical proofs | **both compile** (`hS.continuous_sup (α := αᵒᵈ) hf h`) | 7 |
| b12613af1b38 (33285) | one `simp` for `rw [L]; ext; simp` | closer battery | bare `simp`: unsolved goals; `simp [L, Subtype.ext_iff]` (the lemmas already in the proof, plus `ext_iff`): **compiles** | 13 |
| v0067 (30641) | "can `positivity` do this (untested)?" | closer battery | no: the goal is `∈ Set.Ici 0`; after unfolding, `positivity` still fails | 9-39 |
| v0068 (30641) | "can `gcongr` do this?" | closer battery | no: `gcongr` makes no progress (no `@[gcongr]` lemma for `log⁺`) | 39 |
| v0092 (32875) | "`simpa using`?" | shape rewrite `simp only [..]; exact e` → `simpa only [..] using e` | no, verbatim: the `using` term's `_` are stuck (`CommMonoid ?m`) | 17 |
| v0105 (34091) | "a one-liner using `infinite_pigeonhole_card_lt`?" | `exact?`/`apply?` **inside the file**, the lemma in scope | neither names it; `apply?` gives 7 generic partial matches. The lemma has the **same hypotheses** `(f : β → α) (h : #α < #β)` 11 lines up | 6-9 |
| 168d80d11d79 (33149) | replace the `axiom` Parseval with Mathlib's | `exact?` on the axiom as a theorem; then a name search | `exact?` fails (custom `fourier3D`); `grep -i parseval` on the base finds **`AddCircleMulti.lean:237`, Parseval on `UnitAddTorus d`**; and `axiom` is itself a lint | 38 |

## Reading

- **Eight of the fifteen asks tried are produced outright** by a procedure that has no
  false-positive mode, and a ninth by the closer list seeded with the proof's own lemmas: an old proof that compiles, a `noncomputable` that compiles away, a dropped
  attribute, a dot-notation rewrite that compiles, a dual that compiles, a fix for a removed
  `@[simp]` that compiles. Each such output *is* a maintainer ask, so the exhaustive run can file
  every hit.
- **Three maintainer questions are answered "no"** (`positivity`, `gcongr`, `simpa using`,
  verbatim). Gold counts them as asks; a reviewer with the battery would not post them, which is
  right, and the recall metric will not credit it.
- **Search by unification does not find the duplicates; search by shape or name does.** `exact?`
  missed the pigeonhole one-liner with the lemma in scope, and missed Parseval behind custom
  definitions. A hypothesis-shape match in the same file, and a docstring word match on the
  library, find both at once. The comprehensive search for "does this already exist" therefore has
  three radii, all mechanical: unification on the goal; the file and family matched on hypothesis
  shape and name tokens; the library matched on the concept words of the docstring and name.
- **Cost.** 6-40 s per variant, the file's own elaboration; the sweep is parallel by construction.
- **Not measured here:** the yield and the non-gold output of the exhaustive run, which is what
  Step 1b of `docs/plans/2026-09-25-align-decisions-with-maintainers.md` builds.
