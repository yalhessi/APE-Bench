# LLM agent for Mathlib PR review — progress (June 2026)

**The twist:** in formal math, correctness is *free* (Lean kernel decides it). Review is about
**acceptability** — duplication, generality, naming, docs, idiom — i.e. taste/convention, where LLMs
are weakest. → Question: **can an agent predict the specific change a maintainer would request?**

---

### The data
- **138** reviewed mathlib4 PRs · **72 (52%)** had ≥1 actionable finding · **66 (48%)** clean.
- **143** findings (115 line-anchored, scored) · **~85% blocking**.

### Findings sort into 4 verifiability tiers — and the tier predicts whether the model succeeds

| tier | what it is | share | example | how it's checked |
|---|---|---:|---|---|
| **V1** | decidable | 5% | "no new axioms" | grep for `axiom` |
| **V2** | checkable by computation | **46%** | "this case should be `by simp_all`" | compile the proof — kernel decides |
| **V3** | codifiable convention | **41%** | "why not name it `injective_of_eq_imp_le`?" | naming rulebook + judgment |
| **V4** | genuine preference | 8% | "is this API really easier than `obtain`?" | maintainer discussion only |

**92% are V1–V3 (verifiable/codifiable).** V2 = *many valid options, maintainer picks one* (golf,
dup, generality). V3 = *one right answer* (naming, docs, style).

### How we measure
- Gold = real maintainer comments. A hit = **same place AND same concern** (LLM judge).
- Honest ruler took work: a path bug hid half the matches; location-only over-counted; gold had
  non-actionable comments. **Every loose metric flattered the agent.**

### What we built
- **Holistic agent** — reads PR + library, reports what it judges worth raising.
- **Decomposed checkers** (golf/dup/generality) — each attaches a **Lean snippet the kernel
  re-compiles at submission** → verified by construction, no trusting the model.

---

### Tools vs prompting-only (gpt_5.4, same 30 PRs, same task)
- **Prompting-only: 69 findings** · **workspace: 10** (~7×), at ~half the precision.
- No tools → asserts ungrounded guesses (recall↑/precision↓); workspace **grounds + suppresses**
  unverified findings (recall↓/precision↑). Same threshold axis, on the tools dimension.

### Results (57 PRs / 115 findings)

| model · approach | findings | precision | recall all | rec V2 | rec V3 |
|---|---:|---:|---:|---:|---:|
| **5.4** holistic | 33 | **36%** | 10% | 4% | 15% |
| 5.4 guidelines | 31 | 29% | 9% | 4% | 11% |
| 5.4 decomposed (verified) | 125 | 13% | 11% | **14%** | 8% |
| **5.2** holistic | 168 | 24% | **31%** | 27% | 34% |
| 5.2 guidelines | 151 | 24% | 28% | 25% | 28% |
| 5.2 decomposed (verified) | 86 | 15% | 13% | 16% | 9% |

*precision = findings hitting a real maintainer concern (same place+concern); denominators all=115,
V2=56, V3=53; topical-gated.*

- **Frontier**: more findings → more recall, less precision (5.2 floods 5×: 36→24% prec for 10→31% recall).
- **V2 vs V3**: conservative single agent catches conventions not computation (V3 15% / V2 4%); verified checkers invert it (V2 14% / V3 8%).

1. **Recall is low** — predicting *which* improvements a maintainer wants is far from solved.
2. **Guidelines didn't help** (both models) — it "knows" the rules, still can't make the call.
3. **Model gap = flagging *threshold*, not capability** — 5.4 conservative (under-flags), 5.2 eager
   (over-flags); they *bracket* the maintainer, neither calibrated.
4. **Verification = stable floor** — checker recall barely moves across models (11→13%); free-text
   swings (10→32%).

### Throughline
**"Verifiable correctness is not enough."** The agent can find *and kernel-verify* valid
improvements; the wall is the **calibrated judgment** of which ones this community would request.

### Next
- **Calibration** — move the flag/no-flag threshold to the maintainer's (during review, not a
  wasteful post-filter).
- Reproduce the target (inter-annotator agreement on blocking-vs-advisory); multi-seed/more models.

*Caveats: single run/config; recall via LLM judge (spot-checked, ~10–15% slack); precision kernel-anchored.*
