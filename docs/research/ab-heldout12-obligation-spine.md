# A vs B on the held-out 12: the per-obligation spine

*Written for the talk revision and the project record. Every number here comes from six runs and
their six audits committed alongside this file; nothing is quoted from an earlier write-up.*

Conditions, both on the same 12 PRs, same model, same cutoff, same judge
(`v4-semantic-v3-v9-rubric`), three repetitions each, all six `complete` with zero coverage gaps:

- **A** — `lead` routing: a delegating lead, a generalist arm, ten specialist arms, the agenda and
  the context map. `configs/pr_review_v5_medium_heldout.yaml`. **$14.59/rep billed.**
- **B** — `solo`: the same prompts and the same submission contract, one whole-PR pass, no
  decomposition. `configs/pr_review_v5_solo_ape_heldout12.yaml`. **$1.90/rep billed.**

A spends **7.7×** what B spends. The two are *not* cost-matched, which matters for every
comparison below.

Routing was **not degenerate in any A rep** (`degenerate_fanout: false`, `degenerate_silent:
false`), so the lead genuinely routed and the numbers are interpretable.

---

## 1. Headline

| endpoint | A (lead) | B (solo) |
|---|---|---|
| mean recall | **0.261** (7, 5, 6 of 23) | 0.130 (4, 4, 1) |
| union recall | 0.304 (7) | **0.348 (8)** |
| stable recall — hit in all 3 reps | **0.217 (5)** | **0.000 (0)** |
| control emission (33304, 33315) | 3, 4, 5 per rep | **0, 0, 0** |
| candidates per hit | 51.7 | **21.0** |
| cost per hit | $2.43 | **$0.63** |

**Neither condition wins.** The mean-recall gap is 13pp; the minimum detectable difference on 23
obligations is ~26pp, and the paired test is 5 A-only against 6 B-only where a sign test needs 6
one way. *"Decomposition buys recall"* is not supported here, and neither is its negation.

Three things *are* supported, and each is a separate claim:

1. **They are complementary.** A-only 5, B-only 6, shared 2 — combined **13 of 23 (57%)** against
   30% and 35% alone.
2. **A is reproducible and B is not.** A's pairwise rep Jaccard is 0.71 / 0.86 / 0.83, with five
   obligations hit in all three reps. B's is **0.14 / 0.00 / 0.00** — not one obligation twice.
   B's union beats A's, but no single B run can be relied on for any particular obligation.
3. **B is the precise one.** Zero control emissions in three reps against A's 3, 4, 5; 2.5× better
   per candidate and 3.9× better per hit.

---

## 2. The spine: every PR, every obligation

`H` = issue hit, `L` = right location and wrong ask, `.` = miss, one character per rep.

### PR 33117 — 1 obligation
| ob | concern | A | B | ask |
|---|---|---|---|---|
| 57bcc9fd | duplication/adv | `HLL` | `HLL` | import `Mathlib.Tactic.ToFun`, replace duplicated `fun_*` lemmas with `@[to_fun]` |

The only obligation both conditions hit in the same rep. Both then lost it twice.

### PR 33145 — 6 obligations (the densest PR in the set)
| ob | concern | A | B | ask |
|---|---|---|---|---|
| e83e6544 | duplication/adv | **`HHH`** | `L.L` | rename `Dense.continuous_upperBounds`/`_lowerBounds`, reprove via `OrderDual` |
| bd8a8d8c | duplication/adv | `LLL` | `HL.` | refactor into `Dense.ciSup`/`ciInf`, reuse by duality |
| 8d887ce4 | duplication/adv | `L..` | `L.L` | generalize to `Dense.ciSup'` |
| 7fef9136 | duplication/adv | `LLL` | `..L` | corresponding `Dense.ciInf'` via the order dual |
| e8e02821 | style/adv | `L..` | `L.L` | restructure the `ciSup` proof around a `by_cases` on `BddAbove` |
| c9a216b7 | style/adv | — | — | swap the sides of the `iSup`/`iInf` equalities |

A's one stable hit in this PR is the naming rename, and it is `naming_norm`-backed. Everything
else is `L`: both conditions found the right declarations six times over and asked for something
other than what the maintainer asked for.

### PR 33149 — 4 obligations (a PR that adds axioms)
| ob | concern | A | B | ask |
|---|---|---|---|---|
| 3dacf72e | correctness/**blocking** | **`HHH`** | `...` | remove the new `axiom` declarations |
| f54010d8 | correctness/**blocking** | **`HHH`** | `...` | remove `cMoser`, `cGronwall`, `cSobolev`… and prove them |
| 61f68eed | duplication/**blocking** | `LLL` | `H..` | use Mathlib's existing Parseval identity instead of axiomatising one |
| 3e19231d | correctness/blocking | — | — | rewrite the file to Mathlib standards |

**The clearest complementarity in the set.** A finds the axioms every single rep and never the
duplication; B finds the duplication once and never the axioms. Both are blocking.

### PR 33285 — 2 obligations
| ob | concern | A | B | ask |
|---|---|---|---|---|
| 073625ed | proof-golf/adv | **`HHH`** | `...` | golf to `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2` |
| 585e5e0b | proof-golf/adv | `L.L` | `...` | replace the injectivity/`ext`/`rfl` tail with one `simp` |

A's `proof_golf` arm hit the first in all three reps with three differently-worded but equivalent
requests. B did not reach either.

### PR 33294 — 2 obligations
| ob | concern | A | B | ask |
|---|---|---|---|---|
| 7f098f6a | naming/adv | `.LL` | **`HHL`** | rename to dot-notation `IsFundamentalSequence.of_isNormal` |
| 8e276803 | style/adv | `...` | `...` | `rw [h.map_iSup …]` instead of `rw [Order.IsNormal.map_iSup h …]` |

B twice proposed method-style naming; A located it twice and asked for something else.

### PR 33304, 33315 — CONTROLS, 0 obligations
Nothing is correct to report. **A emitted 3, 4 and 5 candidates; B emitted 0, 0, 0.**

### PR 33305 — 1 obligation
| ob | concern | A | B | ask |
|---|---|---|---|---|
| cc44bb99 | style/**blocking** | `...` | `...` | wrap the over-long doc-comment line (~line 20) |

Neither condition ever located it. One of only two obligations in the set that nobody saw.

### PR 33321 — 3 obligations
| ob | concern | A | B | ask |
|---|---|---|---|---|
| c9739efc | docs/adv | **`HLH`** | `...` | finish the docstring sentence and fix "crystallogrphic" |
| 5ffba48e | style/adv | `LLL` | `...` | redefine `baseOf` as a set comprehension |
| 0bb42bd2 | docs/adv | `LLL` | `...` | add an "Implementation details" section on ordered coefficients |

A located all three in every rep and converted one. The two it missed are both "restructure this"
asks answered with smaller edits — the under-reaching signature in its purest form.

### PR 33337 — 2 obligations
| ob | concern | A | B | ask |
|---|---|---|---|---|
| ce7b5d2e | naming/adv | `...` | `..L` | rename `orthogonalProjection_coe_eq_…` to `toLinearMap_…` |
| 64e1164f | naming/adv | **`HHH`** | `.HL` | rename `coe_starProjection_eq_isComplProjection` to `toLinearMap_…` |

A's stable hit is the `naming_norm` result: the arm cites the counted population for the
conclusion's subject. The sibling obligation, the same rename on a neighbouring lemma, is missed
every rep by A — it asks for one and not the other.

### PR 33362 — 1 obligation
| ob | concern | A | B | ask |
|---|---|---|---|---|
| 695ae9fd | scope/adv | `...` | `..H` | move the declarations inside `namespace Complex` |

B-only, and the kind of thing that needs the whole file in view.

### PR 33421 — 3 obligations
| ob | concern | A | B | ask |
|---|---|---|---|---|
| 6b02b611 | naming/adv | `.L.` | `LH.` | rename `round_eq'` to `round_eq_div` |
| 38e72250 | duplication/adv | `...` | `LLL` | factor out the repeated `Tendsto (2 * ·)` argument |
| 55f65304 | generalization/adv | `...` | `LH.` | generalize `two_mul_fract_eq_one_iff_exists_int` to arbitrary `k` |

A did not reach this PR's obligations at all. B located all three and converted two, once each.

---

## 3. The split is structural, not random

Union hits over three reps, by concern family:

| concern | A | B |
|---|---|---|
| correctness | **2** | 0 |
| docs | **1** | 0 |
| proof-golf | **1** | 0 |
| duplication | 2 | 3 |
| naming | 1 | **3** |
| scope | 0 | **1** |
| generalization | 0 | **1** |

**A owns correctness, docs and proof-golf** — including both blocking axiom obligations. **B owns
scope, generalization and naming.** Duplication is the contested middle.

The shape is recognisable: A wins where a specialist has a *checkable warrant* — an axiom is
present or not, a proof golfs or does not, a typo is a typo — and where `naming_norm` supplies a
counted population. B wins where the judgement requires holding the whole file at once: this
lemma belongs in that namespace, this specialised lemma should have been stated generally, this
name should be dot-notation. That is close to the `VERIFIABLE_BY_COMPILE` / `AWAITING_A_WARRANT`
split the evaluation layer already declares, but it is not identical — naming moved to B's column
here even though A now has the norm tool.

---

## 4. The failure is the ask, not the attention

Of the 23 obligations:

- **13 hit** by at least one condition.
- **10 never hit.** Of those, **8 were correctly located and wrongly asked**, and only **2 were
  never located at all**.

So **21 of 23 obligations (91%) were found by somebody**, and the system asked for the wrong thing
on 8 of them. The two genuinely invisible ones are both `style`:

- PR 33294 — `rw [h.map_iSup …]` instead of the fully-qualified rewrite.
- PR 33305 — an over-long doc-comment line. Blocking, and a line-length lint.

**This is the single most useful reframing in the data.** The problem is not retrieval, coverage
or attention; those are close to solved on this set. The problem is converting a correctly
identified site into the transformation a maintainer actually demanded. The `L` columns above are
where the work is — `LLL` rows in 33145, 33321 and 33421 are the system standing on the right
declaration for three consecutive runs and asking for something smaller each time.

---

## 5. Inside A: the specialists are not doing the work

Pooled over three reps, A produced 907 findings of which 71 matched an obligation. By the arm that
produced them:

| arm | matches | findings | per-finding | billed (3 reps) |
|---|---:|---:|---:|---:|
| **generalist** | **64** | 772 | 8.3% | $23.32 (63%) |
| naming | 3 | 7 | **42.9%** | $2.17 |
| proof_golf | 3 | 14 | **21.4%** | $0.96 |
| duplication | 1 | 27 | 3.7% | $2.85 |
| correctness, docs, generality, proof_idiom, style, api_reuse | **0** | 87 | 0% | $7.05 |

**90% of A's matched output comes from its generalist arm** — the whole-PR reviewer sitting
*inside* the decomposed condition. The ten specialists take 37% of delegated spend and return 10%
of the matches. Six arms matched nothing at all across three repetitions, `api_reuse` and
`family_design` submitted nothing whatsoever, and `correctness` submitted zero candidates in rep1
while the *generalist* found both axiom obligations.

The counter-reading, which is real and should not be dropped: `naming` at 42.9% and `proof_golf`
at 21.4% are five times the generalist's per-finding rate. They are precise and tiny. The
decomposition is not producing bad findings, it is producing almost none — and what A gains over
B may be its generalist having the agenda and the map, plus 7.7× the budget, rather than the
specialists existing.

---

## 6. What each condition emits that gold never asked for

| | A | B |
|---|---|---|
| findings over 3 reps | 907 | 126 |
| matched an obligation | 71 (7.8%) | 9 (7.1%) |
| **off-gold** | 836 | 117 |
| of which `blocking` severity | **503** | 51 |
| off-gold on control PRs | **12** | **0** |
| largest off-gold concern | style (348) | style (25) |
| published / diagnostic | 76 / 760 | 18 / 99 |

**The per-finding match rate is the same** — 7.8% against 7.1%. A's recall advantage is bought
entirely with volume, which is the artifact the record already retracted once for the generalist
arm ("dominates on quality" at 0.08 vs 0.09 hits per candidate while emitting 4× as many). At
matched emission the advantage would very likely vanish.

A also issues **503 blocking demands across three reps that correspond to no maintainer ask**. For
a tool whose value proposition is saving reviewer attention, that is the number that matters most
and it is not a recall number.

---

## 7. What this cannot support

- **Not a winner.** 13pp against a ~26pp MDD, 5 vs 6 discordant. Do not present A as beating B.
- **Not cost-matched.** A spent 7.7× B. Any A advantage is at that price.
- **Provisional gold.** The held-out set is 31/33 `migration_proposal` and 2 `curator_confirmed`;
  everything here is provisional until the R1b sitting.
- **One model, one set, three reps.** `gpt_5.2` throughout; 12 PRs; n=23 obligations.
- **Condition C does not exist.** The off-the-shelf-agent floor has never been run: its config
  refuses to be read until the transcript leak audit exists and has been shown to fire on a
  planted lure, and that audit has not been built.

## 8. The three sentences for the talk

1. On a real held-out set the scaffolded reviewer and a plain whole-PR agent recover **different**
   obligations — 5 and 6 uniquely, 2 shared — and together reach 57% of what maintainers asked for
   against ~30% each.
2. The scaffolded reviewer is the **reproducible** one (5 obligations in all three runs against
   zero) and the plain agent is the **precise** one (no output at all on control PRs, against 3-5
   per run), so the architectures are answering different questions about the same PR.
3. Across both, **91% of obligations were correctly located and only 57% correctly asked** — the
   open problem in automated review is not finding the right line, it is naming the change the
   maintainer wanted.
