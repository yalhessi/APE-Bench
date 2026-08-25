# Progress report: an LLM agent that reviews Mathlib PRs

*Status check-in, June 2026. For colleagues catching up — builds from the problem.*

## 1. The goal and why it's not obvious

We want an LLM agent that reviews pull requests to Mathlib (the Lean math library) the way a human
maintainer does. The non-obvious part: **for formal math, correctness is already decided by the
machine.** If a PR compiles, the Lean kernel has verified every proof. So a reviewer's job is *not*
"is it correct?" — it's **acceptability**: is this duplicating something the library already has?
should the lemma be more general? does the name follow conventions? is the proof idiomatic? is it
documented? These are judgment calls about *taste and convention*, not truth — and that is exactly
where LLMs are least calibrated.

## 2. How we measure it (and why measuring it honestly was half the work)

- **Ground truth**: real review comments maintainers left on real PRs. We stratify each by how
  mechanizable it is — V1 (decidable, e.g. "no new axioms"), V2 (checkable by computation: golf,
  duplication, generalization), V3 (codifiable conventions: naming, docs, style), V4 (genuine
  preference). ~88% of maintainer findings are V1–V3 — verifiable or codifiable, not arbitrary.
- **Scoring**: an agent "catches" a finding only if it flags the **same place** *and* the **same
  concern** (an LLM judge confirms the concern matches; location alone is not enough).
- **The catch**: getting this ruler right took several iterations, and each one moved the numbers.
  A path-format bug was silently dropping half the matches; pure-location matching over-counted via
  coincidence; and the gold itself contained non-actionable comments (approvals, "I'll wait for
  another opinion") that we had to filter. **Every loose version of the metric flattered the agent.**
  The headline numbers below are on the corrected ruler (57 PRs, 115 actionable findings).

## 3. The reviews we study, and what maintainers actually flag

**Dataset.** 138 closed Mathlib (`leanprover-community/mathlib4`) PRs that received maintainer
review. Of these, **72 (52%) drew at least one actionable maintainer finding; 66 (48%) drew none** —
the maintainers raised nothing requiring a change. (We use "has an actionable finding," not the
GitHub review state, as the acceptable-vs-not signal: maintainers routinely "approve with comments,"
so the formal verdict — 100 approved / 38 comment-only — is noisy.) Across the 72 PRs there are
**143 actionable findings** — 115 anchored to a specific line, 28 PR-level. **~85% are blocking**
(would need addressing before merge), ~15% advisory. Recall is measured on the 57 PRs / 115
line-anchored findings (PR-level findings can't be located precisely enough to score).

**Two ways to slice the findings — and they line up, which is the key to reporting success vs failure.**

*By mechanizability (V1–V4) — our primary axis, because it predicts where models succeed:*

| stratum | what it is | share | dominant concern types |
|---|---|---:|---|
| V1 | decidable | 5% | no-axioms policy |
| V2 | checkable by computation | **46%** | proof golf, generalization, duplication, dead/out-of-scope code |
| V3 | codifiable convention | **41%** | naming, documentation/docstrings, style & attributes |
| V4 | genuine preference | 8% | design taste |

**92% of findings are V1–V3** — verifiable or codifiable, not arbitrary — and most are blocking.

*By concern type (what kind of issue):* proof-quality/golf 19%, naming 15%, generalization 9%,
documentation 8%, attributes/API 5%, duplication 4%, style 3%, scope 3%, policy 3% (remainder mixed;
concern-type is keyword-derived and approximate).

**These two slices align, and that alignment is exactly the success/failure boundary.** V2 is
essentially *{golf, generalization, duplication, scope}* — findings where **many valid alternatives
exist and the maintainer picks one**. V3 is essentially *{naming, documentation, style}* —
**deterministic conventions with one right answer**. Models succeed on V3 and fail on V2 (§5) — not
because V2 is harder *math*, but because there is no single target to agree on. **So report by
stratum: mechanizability is what determines whether the agent and the maintainer can land on the
same specific finding, and the V2-vs-V3 line is precisely where models flip from failing to
succeeding.**

**One real finding from each stratum, and how you'd check it:**

- **V1 — decidable.** *"Mathlib has a no-axioms policy. Please don't introduce any new axioms."*
  (GalerkinRegularity.lean:50) → **Check:** scan the file for the `axiom` keyword. A syntactic test
  settles it — no judgment, no compilation.
- **V2 — checkable by computation.** The `n = 0` case of a proof should just be `by simp_all`
  (Pointwise.lean:231) → **Check:** compile the proposed proof; if `simp_all` closes the goal, the
  golf is valid — the kernel decides it. (Duplication and generalization check the same way: submit a
  Lean snippet that compiles *iff* the finding holds — "the existing lemma proves the new one," or
  "the more general statement type-checks.")
- **V3 — codifiable convention.** *"why not call it `injective_of_eq_imp_le`?"* (Defs.lean:329) →
  **Check:** against the written Mathlib naming convention (a name should spell out its statement).
  Codifiable — there is a rulebook — but *not* machine-decidable: applying it needs judgment, and the
  kernel says nothing.
- **V4 — genuine preference.** *"Is it definitely easier to use this definition rather than `obtain`
  on `Set.Finite.exists_minimal`? It would be nice to connect to the `Minimal`/`MinimalFor` API."*
  (Argmin.lean:143) → **Check:** nothing mechanical — a design-taste call about API ergonomics,
  settled only by maintainer discussion. (Fittingly *advisory*, not blocking.)

The ladder is the point: **V1 a syntactic scan, V2 the kernel, V3 a convention rulebook + judgment,
V4 pure taste.** Verification reaches V1–V2 fully; V3–V4 is where "verifiable correctness is not
enough" begins to bite.

## 4. What we built

Two review agents that share everything (materialization, tools, scoring) so they're comparable:

1. **Holistic agent** — one agent reads the PR and the library and reports the issues it judges
   worth raising.
2. **Decomposed checkers** — focused agents for golf / duplication / generalization, each of which
   must attach a **Lean snippet that the kernel re-compiles at submission**. So every finding they
   report is *verified by construction* — no trusting the model's claim.

## 5. Does a workspace help? (tools vs prompting-only)

Same model (gpt_5.4), same 30 PRs, same acceptability task — the diff pasted into the prompt vs an
agent with a workspace (read / search / **verify**):

- **Prompting-only flags ~7× more** — 69 findings vs 10 — at ~half the precision. Without tools to
  disconfirm, the model asserts ungrounded guesses.
- **The workspace grounds it**: it checks a concern before raising one (and drops what it can't),
  yielding far fewer, higher-precision findings.

This is the **tools axis of the same threshold story** (§6): no grounding floods (recall↑ /
precision↓); grounding is conservative (recall↓ / precision↑). The point is that **verification
doesn't only validate findings — it suppresses ungrounded ones**, which is why the workspace and the
verified checkers both behave conservatively.

## 6. Headline results

On 57 PRs. *findings* = total raised; *precision* = share of raised findings that hit a real
maintainer concern (same place + same concern); *recall* = of that stratum's gold; all topical-gated.

**Combined — all 115 findings**

| model · approach | findings | precision | recall |
|---|---:|---:|---:|
| gpt_5.4 holistic | 33 | **36%** | 10% |
| gpt_5.4 guidelines | 31 | 29% | 9% |
| gpt_5.4 decomposed (verified) | 125 | 13% | 11% |
| gpt_5.2 holistic | 168 | 24% | **31%** |
| gpt_5.2 guidelines | 151 | 24% | 28% |
| gpt_5.2 decomposed (verified) | 86 | 15% | 13% |

**V2 — golf / duplication / generality (56 findings; "many valid options")**

| model · approach | findings | precision | recall |
|---|---:|---:|---:|
| gpt_5.4 holistic | 33 | 6% | 4% |
| gpt_5.4 guidelines | 31 | 10% | 4% |
| gpt_5.4 decomposed (verified) | 125 | 9% | **14%** |
| gpt_5.2 holistic | 168 | 11% | **27%** |
| gpt_5.2 guidelines | 151 | 12% | 25% |
| gpt_5.2 decomposed (verified) | 86 | 9% | 16% |

**V3 — naming / docs / style (53 findings; "one right answer")**

| model · approach | findings | precision | recall |
|---|---:|---:|---:|
| gpt_5.4 holistic | 33 | **27%** | 15% |
| gpt_5.4 guidelines | 31 | 16% | 11% |
| gpt_5.4 decomposed (verified) | 125 | 4% | 8% |
| gpt_5.2 holistic | 168 | 12% | **34%** |
| gpt_5.2 guidelines | 151 | 11% | 28% |
| gpt_5.2 decomposed (verified) | 86 | 7% | 9% |

Two things jump out. **Down each table**: more findings → more recall, less precision (gpt_5.2 floods
5× and trades precision for recall) — the agents sit at different points on one frontier. **Across the
V2 and V3 tables**: the conservative single agent (gpt_5.4 holistic) is far stronger on V3 conventions
than V2 computation (15% vs 4% recall); the **verified checkers invert that** — best V2 recall (14%),
worst V3 (8%). Conventions have one right answer; V2 has many, and the agent picks different ones than
the maintainer.

Four findings, in plain terms:

1. **No setting recovers maintainer findings both reliably and precisely.** The best recall (gpt_5.2,
   31%) comes with 24% precision (3 of 4 findings off-target); the best precision (gpt_5.4, 36%) comes
   with 10% recall. Even with correctness free, predicting *which* improvements a maintainer will ask
   for — and only those — is far from solved.
2. **Supplying the official Mathlib guidelines did not help** — same or slightly lower, on *both*
   models. Telling the agent the rules doesn't close the gap; the agent already "knows" them and
   still can't predict the specific call. This is a robust negative.
3. **The big model-to-model difference is a *threshold*, not capability.** gpt_5.4 is conservative
   (flags little, approves most PRs); gpt_5.2 is eager (flags 5× more). The eager model scores
   higher recall — but at lower precision, and mostly by catching *easy* conventions (typos,
   docstring/name mismatches) the conservative model declines to raise. **The two models bracket the
   maintainer's threshold; neither is calibrated to it.**
4. **Verification gives a stable floor.** The decomposed checkers' recall barely moves between models
   (11% → 13%), because the kernel gate — not the model's mood — bounds what they emit. The
   free-text agent swings wildly (10% → 32%). Where the two architectures are complementary (gpt_5.4),
   combining them ~doubles coverage; where the base agent already floods (gpt_5.2), it doesn't.

## 7. The throughline

**"Verifiable correctness is not enough."** The agent can find and even kernel-verify valid
improvements; what it cannot do is predict the *specific, calibrated judgment* of which improvements
this community would request. The hardest stratum is V2 (golf/dup/generality) — the one where
verification *should* help — precisely because there are many valid improvements and the maintainer
picks a particular one; the agent picks different ones. Conventions (V3) are easier because they're
more deterministic. The wall is **calibrated judgment**, not finding or verifying.

## 8. Open questions / next

- **Calibration is the real axis.** Can we move an agent's flag/no-flag threshold to match the
  maintainer's — neither under-flagging (gpt_5.4) nor flooding (gpt_5.2)? This should happen *during*
  review (a priority policy), not as a wasteful post-hoc filter.
- **Does the calibration target even reproduce?** Maintainer "blocking vs advisory" is itself a fuzzy
  judgment; we should bound the task's ceiling with inter-annotator agreement.
- **Multi-seed / more models** to firm up single-run numbers.

*Caveats: single run per configuration; recall uses an LLM judge (spot-checked, well-calibrated,
~10–15% topical-match slack); precision stays kernel-anchored.*
