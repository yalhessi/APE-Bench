# Why the measured ceiling is not 100%: every miss of the conventions probe, with its verdict (2026-10-09)

The user (2026-10-09): *"this work is about closing the gap to the measured ceiling. It's worth stopping
and investigating what the roadblocks are that prevent the ceiling from being 100% at this point. Are
the remaining missed obligations not captured by conventions? What is the verdict behind why each miss
happened?"*

**The units.** The 46 maintainer asks of stage L/D's two probe sets (validation small12 and
post-cutoff, 14 PRs); 39 of them are in census.

**The table.** `ceiling-residual-2026-10/table.py` (output `table.txt`) merges every matched session at
every ask:
- the conventions ceiling probe's rounds C, D1, D23, F, G, L, M and R;
- the generation-suppression probe's W and targeted rounds.

A **ceiling session** is one briefed with the exact conventions in any form:
- Claude E1 and the targeted Claude D and G runs on 42184;
- gpt-5.5 GE, GD and GR;
- DeepSeek DE and DP;
- Qwen LE.

Nothing new was run.

## 1. Three ceilings, not one

| | in-census asks (39) | all asks (46) |
|---|---|---|
| unbriefed, union of every unbriefed session (Claude X, DeepSeek DX, gpt-5.5 GB, Qwen LB) | | 25 |
| DeepSeek DP, a session, mean of three reps | 0.64 | 0.65 |
| DeepSeek DP, union of its three reps (matcher 1) | 29 | |
| Claude E1, one session | 0.74 | 0.70-0.73 |
| **every ceiling session, any model, any rep (either matcher)** | **34** | **40** |

**So the per-session gap has two parts.**
- **Instability within a condition.** DP reaches 24-27 asks a rep but 29 in union.
- **Differences between models and conditions.** Five asks DP never reaches are reached by Claude E1
  or gpt-5.5.

What no condition has ever reached is **6 asks of 46**.

**Asks outside the census are not the obstacle.** Of the 7 out-of-census asks, ceiling sessions
reach 6. They are mostly facts about the PR that unbriefed reviewers also find (four of the six are
reached unbriefed too).

## 2. The six asks nothing reaches

**Evidence used:**
- the two matchers' notes in every round (`match_*/matches.*.json`);
- DP1's reasoning, sorted in stage D's interim table (`conventions-ceiling-2026-10-04/README.md`);
- Claude E1's notes (stage C, Result 3);
- the ladder's answers at the ask's own place (`conventions-ladder-2026-10-08/`; unmatched, the
  session's own unblinded reading, provisional).

| ask | what the maintainer asked | in census? | what every reviewer did instead (matchers' notes) | at the place, alone (ladder) | verdict |
|---|---|---|---|---|---|
| 42814 **p0004** | an `alias` for the reverse implication of an iff, or drop it ("I don't see any reasonable application") | P153, rank 130 | golfed the iff's proof, every round | the bare sentence proposes the alias 2 of 3; told, 3 of 3 | **attended, asked another question.** E1 read the sentence's precondition literally ("no iff here has its directions used separately"). DP applied the convention to the file's other iffs. The maintainer's reason (no application) is not in the sentence |
| 42814 **p0005** | does this hold in any UFD or normalization monoid? | P063 (rank 9), P086 | golfed the `Int` proof, every round | the bare sentence points to the generic UFD lemma 1-2 of 3; told, 2 of 2 | **attended, judged on the merits.** "The Int- and Nat-specific lemmas are inherently specific" (E1); "its ℤ-specific content is used" (DP1). A generalisation declined |
| 34091 **v0105** | "surely this is a one-liner using `infinite_pigeonhole_card_lt`?" | P011, rank 5 | golfed the neighbouring lemmas (`infinite_pigeonhole_card_lt`, `exists_uncountable_fiber`), every round | judged: `conforms` 5 of 6; told with examples: 2 of 3 propose proving it from `infinite_pigeonhole_card_lt`; told without, truncated 3 of 3 | **attended the region, chose the wrong declaration, and judged the case split necessary** (DP1). Claude E1 never attended it. A proof search is also involved |
| 32875 **v0091** | "Same here." (tag the Rat lemma with `grind`, a reply to v0090) | no, the reply is unreadable alone; its parent is P315 | passed the lemmas to `grind` as local hints rather than tagging them | not in the ladder | **the right idea in another form** (a local hint, not an attribute), and on the second lemma of a pair. Out of census only as a labelling artefact |
| 29842 **v0053** | how does this interact with #24163; the earlier consensus (#21065) was to change the definition | P041, rank 23 | a generic "add motivation to the PR description" (`partial`) | every form gives generic motivation | **information outside the PR**: the history of two other PRs and a past consensus. No packet carries it |
| 43167 **p0010** | `_left`/`_right` look swapped against the library's orientation (`inf_sup_left`), relayed from a bot | P254, rank 107 | nobody notices; DE1 says the names are wrong but proposes another | no form gets it, even told | **information outside the PR**: the library's orientation. The local sibling (`commutator_le_left`) agrees with the PR, and the ask is a bot's |

**Counting the six:**
- **Two need information no packet carries:** a PR's history, and the library's naming orientation.
- **Four are the reviewer at the right place doing something else.** Usually it golfs the proof, or it
  judges the code fine on its merits. At the place, asked the convention's question alone, the model
  produces three of those four (p0004, p0005, v0105), at least sometimes. The fourth (v0091) is a
  matter of form.
- **This is the work-enumeration finding again**, for the strongest reviewers with the conventions in
  hand. That finding: 8 of 10 never-hit obligations were "located and wrongly asked"
  (`docs/plans/2026-09-23-work-enumeration.md`).

## 3. What DP misses that another condition reaches

These are DP's stable misses (no rep, matcher 1) that some other ceiling session reaches.

| ask | reached by | DP's own reason (stage D interim table, rep 1) | at the place (ladder) | verdict |
|---|---|---|---|---|
| 30641 **v0067**, "can `positivity` do this?" | Claude E1 only | `positivity` used for other arguments, the `simp` kept: never at the place | the bare sentence proposes `positivity` 2 of 3; told, 3 of 3 | **attention**: the convention swept elsewhere |
| 32875 **v0092**, "`simpa using`?" | Claude E1, gpt-5.5 GD1 | "`simpa only [...]` does not elaborate", and a different change filed | every form proposes the merged `simpa` | **execution**: a failed check read as conforming, where the maintainer asked a question |
| 32875 **v0093**, `by simpa using h` | gpt-5.5 GD1 only | tested `exact` without the `simp`: type mismatch | the bare sentence 2 of 3; told, 3 of 3 | **execution**: the wrong variant checked |
| 43192 **p0016**, `homMk` rather than `mkHom` | gpt-5.5 GD1, GE1 | counted `homMk` in ~25 files against `mkHom` ~7, then "NOT a clear naming violation" | every form renames, even the bare place | **the decision against its own evidence.** The maintainer: "there is an hesitation in mathlib" |
| 30641 **v0064**, `x` rather than `a` for a real ("consider my suggestion optional") | Claude E1 only | "everything else uses the area's letters" | the bare sentence 2 of 3; with examples 0 of 3; told, 3 of 3 | **an optional ask, judged on the merits.** The examples made the model judge `conforms` |

**Two more that DP reaches in only one rep:**
- 42184 **p0003**, a `HasProd` sibling. It is reached by six other ceiling sessions. DP1 compared the
  wrong pair ("`HasProd.nonneg` does not exist, but neither does the additive twin").
- 29842 **v0056**, motivation in the PR description. Reached by DE3 and DP2.

## 4. The answer

**Are the remaining misses outside the conventions? Almost none are.**
- Five of the six never-reached asks are in census. The sixth is a "same here" reply under an
  in-census convention.
- Of the seven out-of-census asks, six are reached.
- The census holds the knowledge behind what is missed. What the reviewers lack is elsewhere.

**What stands between the per-session ceiling and 100%**, in the order it costs, with provisional counts:

1. **Instability and model differences.**
   - The DP session mean is about 25 of 39 in-census asks.
   - Its three-rep union reaches 29.
   - The union over all ceiling models reaches 34.
   - So about 9 of the 14 asks a DP session misses are reached by some other session.
2. **At the place, but asked something else** (golfed the proof, judged it fine on its merits, or
   applied the convention at a neighbouring place): p0004, p0005, v0105, v0067, p0003, p0016, v0064.
   - **At the place, alone, the model writes the asked change for most of them.** That points at how
     a session distributes its questions over the places it reads, not at what it knows.
   - The ladder reading is unmatched, so this count is provisional.
3. **Execution.** A check was run on the wrong variant, and the failure was read as "the code
   conforms" rather than filed as the maintainer's question (v0092, v0093).
4. **Information outside the packet:** a PR's history (v0053), the library's orientation (p0010).
5. **Form:** the right idea in another form (v0091).

**What this says about the next design.**
- Items 1 and 2 are most of the gap. Both are about how a session spends its attention, not about the
  conventions.
- Item 2 is exactly what asking each convention's question at each place would catch: the ladder's
  form, and the decompose-and-shrink round's architecture B. That is evidence for the user's
  decomposition direction.
- **The caveat:** the false-departure rate of that form at places no maintainer asked about is
  unmeasured (that round's M3).

## 5. Limits

- One probe set: 46 asks, 14 PRs.
- The verdicts are this session's own reading of matcher notes, DP1's reasoning (rep 1, read in stage
  D's interim) and E1's notes, none blind.
- The ladder column is unmatched.
- The union mixes models, briefs and reps, so it is a bound on what the conditions together reach,
  not a design.
