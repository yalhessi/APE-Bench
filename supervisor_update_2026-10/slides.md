---
marp: true
theme: default
paginate: true
size: 16:9
math: katex
style: |
  section {
    font-size: 24px;
    padding: 40px 56px;
  }
  section.lead h1 { font-size: 52px; }
  section.lead h2 { font-size: 30px; font-weight: normal; color: #555; }
  section.section-title { background: #1d2b53; color: white; }
  section.section-title h1 { color: white; font-size: 56px; }
  section.section-title p { color: #c7d0e8; font-size: 28px; }
  h1 { font-size: 40px; color: #1d2b53; }
  h2 { font-size: 30px; color: #1d2b53; }
  table { font-size: 20px; }
  section.small table { font-size: 16px; line-height: 1.25; }
  section.small { font-size: 20px; }
  section.small h1 { font-size: 34px; margin-bottom: 8px; }
  blockquote { border-left: 6px solid #e0a020; background: #fff8e6; padding: 8px 18px; font-style: normal; }
  pre { font-size: 18px; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
  .cols3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; }
  .box { border: 2px solid #1d2b53; border-radius: 10px; padding: 12px 18px; }
  .muted { color: #666; font-size: 20px; }
  .case-panel { border: 2px solid #d6dcea; border-radius: 12px; padding: 10px 16px; }
  .case-panel h2 { font-size: 24px; margin: 0 0 4px; }
  .case-panel p { margin: 6px 0; }
  .case-panel pre { font-size: 16px; margin: 6px 0; }
  .above { color: #1a7f37; font-weight: bold; }
  .below { color: #b3261e; font-weight: bold; }
  .side { color: #8a6d00; font-weight: bold; }
  footer { font-size: 16px; color: #888; }
footer: "Mathlib PR review · progress since the AI for Math convening · October 2026"
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Reviewing Mathlib PRs: progress since the convening

## Supervisor update · October 2026

**Yousef Alhessi** · University of Edinburgh

<!--
Part 1 of the deck: the problem formulation. Later parts cover what was built and measured since
17 September, and what is next.
-->

---

<!-- _class: section-title -->

# 1 · What problem are we solving?

APE-Bench's task, our task, and the order that connects them

---

# APE-Bench's formulation: the direction is given

A task is built from a real Mathlib commit. The commit's diff is turned into a natural-language
**instruction**; the file before the commit is the **starting state**.

```text
input     instruction  I   +   starting state  s₀            (the file before the commit)
output    an edit            s₀ → s₁
success   s₁ compiles   ∧   a judge agrees s₁ satisfies I     ("dual verification")
```

<div class="cols">
<div class="box">

**What is hard.** Reaching the target: multi-file coordination, library knowledge, the proof itself.
The best evaluated agent completes 47 of 100 tasks.

</div>
<div class="box">

**What is given.** The direction. The instruction says *what* to change. The reference commit says
what "done" looks like, and the judge checks against it.

</div>
</div>

<p class="muted">Xin, Yuan, Jin, Fleuriot, Li — APE-Bench, arXiv 2504.19110 (v3, Feb 2026).</p>

---

# Our problem: nobody hands the reviewer an instruction

A pull request arrives. It **already compiles**. The maintainer reads it and writes the
instructions: rename this, this is a duplicate, derive the dual instead of re-proving it.

```text
input     a PR as the maintainer first saw it     s₀         (no instruction)
output    a set of asks, each naming a direction and a target      s₀ → sᵢ
success   the asks a maintainer would have made        (and nothing that would waste their time)
```

<div class="box">

APE-Bench asks: *given the ask, can you reach the state?*
We ask: *given the state, can you produce the ask?*

Both halves are needed for AI-written contributions. The second is the one maintainers are paying
for by hand today.

</div>

---

# The formulation: a partial order on contribution states

For a PR against base commit $b$, let $S_b$ be every state the contribution could be edited into.
The PR as submitted is one state, $s_0$.

- $C \subseteq S_b$ — the states that **compile**. Decidable, cheap, the kernel's job.
- $\preceq$ — the community's **preference** between states. A *partial* order: two golfs of one
  proof, or two defensible names, are often incomparable.
- $M \subseteq C$ — the states a maintainer would **merge**. Upward closed: improving a
  merge-ready state keeps it merge-ready. Not decidable. Seen only through what maintainers do.

A **review** of $s_0$ is a set of asks. Each ask names a direction (the *issue*) and a target
(the *fix*): $s_0 \prec s_i$. The maintainer's review plus the author's responses trace one path
$s_0 \to \cdots \to s^\ast \in M$ when the PR merges.

<div class="box">

**Verifiable correctness is not enough** is the statement $M \subsetneq C$: every PR we score is
in $C$, and what the maintainer asks for is the distance from $s_0$ to $M$ and beyond.

</div>

---

# The picture

```text
                          ·  s*   the maintainer's target           ·  s'  the reviewer's target
                           \                                        /
      merge-ready  M  ──────\──────────────────────────────────────/────────────────────
                             \                                    /
                              ·  s″  right direction, short of M (under-reach)
                               \                                /
                                \                              /
   compiles  C   ·· s₀ ·········································  the PR as submitted
                                 \
                                  ·  s‴   a change nobody asked for, not above s₀ (noise)

   s₀ ≺ s″ ≺ s*        s₀ ≺ s'        s' and s* incomparable, both in M        s‴ ⊀ s₀
```

The three questions the evaluation asks, in these terms:

| the judge's question | in the order |
|---|---|
| same place | the ask touches the declaration the maintainer touched |
| same issue | the ask's **direction** is the maintainer's |
| strict fix | the ask's **target** is $s^\ast$ |

---

<!-- _class: small -->

# Case 1 · merge-ready or not: three distances to $M$

Three December 2025 PRs from the convening talk's twelve. All three compiled.

<div class="cols3">
<div class="case-panel">

## #33304 — in $M$ already

Fix file references in docstrings. Merged with no request.

<span class="above">s₀ ∈ M.</span> The correct review is **empty**; anything emitted here moves
sideways or down.

</div>
<div class="case-panel">

## #33305 — one step below

The same kind of PR. One **blocking** ask: an over-long doc-comment line.

<span class="below">s₀ ∉ M,</span> one mechanical step from the boundary. Neither reviewer
located it in six runs.

</div>
<div class="case-panel">

## #33149 — far below, closed

Navier–Stokes regularity, AI-assisted, 469 lines, 19 new `axiom`s, vacuous definitions.

<span class="below">Every ask blocking.</span> The compiler answered correctly; the meaning
was wrong.

</div>
</div>

<div class="box" style="margin-top:12px">

$M$ is not a lint set: #33305's boundary is a line-length rule, #33149's is "the definitions do not
say what you claim". **Blocking** asks draw the line of $M$; **advisory** asks are moves inside it.
Of the 23 scored asks on the twelve PRs, 4 are blocking and 19 advisory.

</div>

---

<!-- _class: small -->

# Case 2 · taste we can live with: two targets, both in $M$

PR #33098: four `minimalCover` lemmas, each proved by cases on whether the covering number is finite.

<div class="cols">
<div class="case-panel">

## $s_0$ — as submitted

```lean
lemma minimalCover_subset : minimalCover ε A ⊆ A := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h,
      not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h)
      .choose_spec.1
  · simp [minimalCover, h]
```

</div>
<div class="case-panel">

## two one-line targets, both compile

**Maintainer:** "This and the next three lemmas can be proven with this"
```lean
  grind [minimalCover]
```

**Our reviewer:**
```lean
  simpa [minimalCover, h]
```

</div>
</div>

<div class="box" style="margin-top:8px">

$s_0 \prec s'$, $s_0 \prec s^\ast$, and the PR merges with either. The order between them is a
**convention in motion**: `grind` was in 0% of Mathlib files in January 2025, 14.5% by May 2026.
The judge scores *same issue, not the strict fix*; the formulation reads that as a divergence
inside $M$, not a miss below it.

</div>

---

<!-- _class: small -->

# What else the order lets us say precisely

| Situation | In the order | Where we have seen it |
|---|---|---|
| **Under-reach** | right direction, target short of $s^\ast$; often still outside $M$ | #33117: reviewer asks to *delete* the hand-written `fun_neg`; maintainer asks to *generate* it with `@[to_fun]`. 8 of the 10 asks never hit were located and asked wrongly. |
| **Lateral target** | same direction, target of the same rank as $s_0$ | #33285: maintainer golfs to one term-mode line; our reviewer proposes a `simpa` proof of two or three lines, three runs out of three, no shorter than the PR's own two. |
| **Gold is a lower bound** | the maintainer names *one* path; other upward edges exist | A finding absent from the maintainer's review is *unaligned*, not wrong. Nothing in the evaluation yet adjudicates the ~90% of findings that are off-gold. |
| **Noise on a clean PR** | $s_0 \in M$; any ask is sideways or down | #33304, #33315: the scaffolded reviewer emitted 3–5 findings per run; the whole-PR reviewer 0. |
| **The order is dated** | $\preceq_t$ at the base commit, not today's | `toLinearMap_` vs `coe_`: the library counts 4,707 to 50 *against* the maintainer's rename; the convention lives in the review archive. |
| **A fix is a path, not an edge** | intermediate states may leave $C$ | `@[to_fun]` beside the hand-written twins is a name clash; the resolution is one atomic patch set, not a sequence of asks. |
| **AI-generated PRs** | states far below $M$ with long paths | #33149, the one AI-assisted PR in the twelve: four blocking asks, closed. Distance to $M$ is the maintainers' cost, which is the quantity we want to cut. |

---

<!-- _class: small -->

# What the formulation does not give us

- **$\preceq$ is never observed directly.** Each PR shows one chain: what was asked and what the
  author then did. "Incomparable" and "never compared" look the same in the data.
- **$M$ is seen only through merges.** An advisory ask the author ignored while the PR still merged
  says $s_0$ was already in $M$ at that site. A closed PR may be abandoned rather than rejected;
  the data keeps those apart.
- **Acceptable divergence has no adjudicator yet.** The judge can say *same issue, different fix*.
  Only a maintainer can say the other fix was fine too. That study is deferred until the output burden
  is low enough to ask for it.
- **The order is dated.** Conventions drift (the `grind` curve), so the reference is the order at the
  PR's date. A reviewer that knows only the library as it stands reads the order backwards.

<div class="box">

The project's question in these terms: from $s_0$ alone, produce asks whose targets lie in $M$,
preferring the maintainers' own $\preceq$. Measure direction (*issue recall*) and target
(*resolution recall*) against the one path on record, and treat what is off that path as
unadjudicated, not wrong.

</div>
