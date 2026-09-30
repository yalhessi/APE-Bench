# What the capped gpt_5.2 Gr1 sessions were doing (2026-09-30)

These are the 10 capped sessions out of the 32 Gr1 sessions (gpt_5.2, reasoning high, `ape_agent`, one whole-PR session each):
- 8 hit the 80-turn cap.
- 2 hit the 7.2M processed-token cap: 33145 at turn 76 and 33294 at turn 58.
- None reached the $6 cap. Billed cost was $3.6-4.1 on the two token-capped runs.

No session was ever told how much budget it had left. The transcripts contain no notice of remaining turns or tokens.

Scope: one repetition and one configuration, with n=10 capped sessions. Two judgements are approximate:
- the phantom classification (see Method);
- the `would_file` calls, which are one annotator's judgement and not a matcher's.

Read everything here as provisional.

Files: `capped.json` (per session), `traces/<pr>.txt` (one line per call), and the scripts `extract.py`, `metrics.py`, `memloss.py`, `phantom.py`, `last25.py` and `build_capped.py`.

## Summary table

| session | turns (end) | what the last 25 turns were doing | candidates thrown away | dev asks: evidence in hand |
|---|---|---|---|---|
| post 42814 | 80 (turns) | re-checking phantom duplicates (the same `Odd\.isCoprime` greps of Separable.lean and PID.lean about 10 times, the PID grep twice within T77); `Int.mul_ediv_cancel_left` 'No declaration' asked twice; 0 edits all session | medium: `Odd.isCoprime_two` vs existing `Int.isCoprime_two_right`; risk: 2 phantom duplicate claims | n/a |
| val 26185 | 80 (turns) | import-graph sweeps; `Set.SurjOn.mono` signature for the 4th-6th time; 11/25 repeats | medium: PeanoCurve.lean lacks `namespace Counterexample` (found T72-75) | n/a |
| val 32080 | 80 (turns) | #check probes re-deriving the Stone-Čech proof; 5th-6th sweep of phantom `SetRel.IsRefl.comp` files; a new phantom at T79 | medium: top-level `def P`; weak: shorter proof (one failed attempt) | n/a |
| val 34935 | 80 (turns) | instance hunt by regex variants (6 single-grep zero-reasoning turns on one file); phantom `zeroLocus_mul` revisited | weak: `@[simps]`, missing order instances (the deciding `#synth` was the cut-off call) | n/a |
| dev 33066 | 80 (turns) | one call per turn, 18/25 with zero reasoning; scattered declaration_search; repeat of the T32 phantom sweep; 0 edits all session | weak only (conjContinuousAlgEquiv sibling, instOrderIsoClass) | d0001, d0006, d0007: IN_VIEW_UNTARGETED; would file 0/3 |
| dev 33145 | 76 (tokens) | still on the phantom "`Dense.continuous_sup` exists in Lattice.lean": 4th identical declaration_search, 9th-11th read of the file's tail; 2 verified edits | **strong: rename to `Dense.upperBounds_image` / `lowerBounds_image`** (naming_norm established); 2 verified proof tweaks; risk: false name-clash claim | 10 asks: 6 EXAMINED, 4 IN_VIEW_UNTARGETED; likely 2 (d0019, d0020), partial at best 4 (the ciSup/ciInf renames) |
| dev 33285 | 80 (turns) | re-litigating `symm_prodComm` vs `prodComm_symm` (checked since T1); failing scratch examples; 2 edits | **strong: `prodComm_symm` rename (verified); `isComplete_image_iff` generalised to `SemilinearIsometryClass` + deprecated alias (verified)**; 3 more verified edits | d0035 EXAMINED (edit kept the PR's proof), d0036 IN_VIEW_UNTARGETED; would file 0/2 |
| dev 33294 | 58 (tokens) | namespace-resolution questions (which `IsNormal`), header reads, toy `protected def` test; each turn re-sends ~140k | weak only | d0039 IN_VIEW_UNTARGETED; would file 0/1 |
| dev 33321 | 80 (turns) | scattered one-off lookups; the same refused `declaration_search negAddMonoidHom` 3x | **strong: typo "crystallogrphic"** (grep showed both spellings); medium: `ext; simp` closes `invMonoidHom_comp_invMonoidHom` | d0042 EXAMINED (likely); d0043 EXAMINED (no); d0044 IN_VIEW_UNTARGETED (unlikely) |
| dev 33421 | 80 (turns) | 7 sweeps of one file for `add_mem_I\|sub_mem_I`; 5 consecutive regexes for `def fract`; no phantom; 0 edits all session | weak only | none on this PR |

Dev asks on capped PRs, all 19:
- Evidence class: CONSTRUCTED 0, EXAMINED 10, IN_VIEW_UNTARGETED 9, NEVER_RETRIEVED 0. Every ask's code is in the diff.
- Would it have been filed at the cap: likely 3 (d0019, d0020, d0042), partial at best 4 (d0022, d0023, d0025, d0027), no or unlikely 12.

## Patterns, with numbers

**1. A tool defect drives most of the looping.** `declaration_search` matches on the leaf name only, but it prints the query's full name. `declares_identifier` in `src/mathlib_review/evidence/evidence.py` uses `(?:[A-Za-z_][A-Za-z0-9_'.]*\.)?{leaf}\b`, so any declaration with that leaf matches, and the rendered line says "`<query>` is declared in F (before this PR)". Checked against the base snapshot:
- `Dense.continuous_sup` resolves to the root `continuous_sup` in Topology/Order/Lattice.lean.
- `Odd.isCoprime` resolves to `Separable.isCoprime` in FieldTheory/Separable.lean.
- `Order.IsNormal.monotone` resolves to `lp.monotone` in lpSpace.lean.
- `SetRel.IsRefl.comp` matches files inside aesop and plausible.

The session then greps the file for the full name, finds 0, has no memory of having done so, and asks again. Two smaller defects in the same tool:
- `searchable_identifiers` strips a trailing prime, so a search for `Dense.continuous_sup'` becomes a search for `Dense.continuous_sup`.
- A lowerCamel single token such as `negAddMonoidHom` is refused as "not identifier-shaped".

**2. How much of each session the phantom hits took** (approximate, upper bound):

| | capped (10) | uncapped (22) |
|---|---|---|
| turns following a phantom hit, median per session | 20 | 0 |
| share of all turns | 22% of 774 | 7.6% of 712 |

In 8 of the 10 capped sessions, 16 to 29 turns followed phantom hits. 33145 is the clearest case. It is a single-file PR with 6 theorems, and the session made 58 calls on Lattice.lean over 21 turns: 21 reads, 11 of them of the file's tail at different offsets, and 37 greps, 34 of which returned 0 matches. Claude's sessions got the same multi-file phantom results (for example `Order.IsNormal.monotone`, a 1054-character result) and did not loop.

**3. Capped sessions almost never built anything.**

| | capped | uncapped |
|---|---|---|
| lean_verify_edit attempts that proposed a change | 10 in 774 turns (0.013 per turn) | 73 in 712 turns (0.10 per turn) |
| sessions that never proposed an edit | 8 of 10 | 7 of 22 |

There is no compile-fix loop anywhere. Failed edits never exceed 2 on one declaration, and there are none at all in the capped set apart from 33285 (2 of 8 failed). Across the 250 last-25 turns:

| turn class | turns |
|---|---|
| new lookups (often a regex variant of the same question) | 121 |
| exact or near repeats | 82 |
| phantom-follow | 35 |
| construction | 4 |
| tool error or the cut-off turn | 8 |

**4. Signs that the session does not keep what it has learned.**
- Exact repeats of a call whose earlier answer was already negative: 43 in capped sessions (5.6 per 100 turns) against 21 in uncapped ones (2.9 per 100 turns).
- Turns with zero reasoning tokens: 32% in capped sessions against 10% in uncapped ones.
- In all 10 capped sessions the zero-reasoning share rises after the first 20 turns: 33066 from 2 of 20 to 17 of 20, 34935 from 1 to 14, 42814 from 2 to 13.
- Calls per turn fall from 2-4.6 in the first quarter to 1-1.5 in the last. The long uncapped sessions drift the same way, only less.
- The total volume of reasoning tokens does not degrade consistently: over the last 10 turns it is higher than over the first 10 in 7 of the 10 capped sessions.

**5. Context size is not the constraint.** The final prompt was 60k-145k tokens. What exhausted the two token-capped sessions was re-sending that context on every turn: 33294 opened at 60.6k tokens (a 166k-character diff), and 33145 re-sent about 95k per turn on average.

**6. How a session that submits decides to stop.** Nothing in the harness triggers it; the model decides in one turn.
- The 5 turns before `submit_findings` look like any other turns: greps, `#check`, sometimes a final edit.
- The submit turn carries a reasoning spike: median 10k tokens, up to 25k, against 2-5k per turn otherwise. The whole review is composed in that turn from the bare call/result history.
- In the 5 longest uncapped sessions (73, 61, 60, 51 and 49 turns), the submit came after an edit phase, and most submitted findings name a declaration that had a verified edit (7/7, 2/3, 1/1, 3/3, 6/9).
- 8 of the 10 capped sessions never started an edit phase.

**7. What the cap threw away is smaller than "19 of 24 missed asks are on capped PRs" suggests.**
- None of the 19 asks was constructed.
- The 9 IN_VIEW_UNTARGETED asks were never targeted by any call: the OrderDual proofs, the term-mode golfs, the docstring wording, the have-names and the import split.
- The asks Claude reached are mostly constructive (OrderDual one-liners, golfs), and the capped Gr1 sessions did not attempt that kind of work at all.
- Filing at the cap would plausibly have reached 3 asks and part of 4 more, and in at least 4 sessions it would also have filed phantom-based false duplicates.

## Harness implications, at the altitude of this evidence

- **Fix `declaration_search` first.**
  - Print the declared name rather than the query.
  - Require the prefix, or label leaf-only matches as such.
  - Stop stripping primes.

  This is the single largest driver the evidence shows. It is a code fix, not a model or prompt change, and it also removes the false duplicate claims that a submit-at-cap fallback would otherwise file.
- **Submit-at-cap fallback** (force one `submit_findings` turn when the budget is near its end). It is cheap and would recover the strong candidates in 3 sessions (33145, 33285, 33321), which is about 3 of the 19 dev asks plus about 4 partial. It is worth adding, but on this evidence it does not close the gap.
- **A working-notes tool or incremental submission.** It fits the lost-conclusion pattern: repeated negative lookups, file tails reread, the same refused call made 3x. Nothing here tests it. The same goes for carrying reasoning across turns (for example the Responses API with reasoning items) and for showing the model its remaining budget. All three are untried designs, not supported conclusions.
- **Bigger caps are not supported.** Only 4 of the 250 last-25 turns were construction. More turns mostly buy more of the same loop, and on the token cap each extra turn costs 100-145k tokens.

## Method

- Traces come from each session's `last_turn_file` (the full conversation) and the `*_raw.jsonl` usage records. Turn k is the k-th assistant record.
- A "near" repeat is one of:
  - a read of the same file with an overlapping line range;
  - a search whose identifier-token set is a subset or superset of an earlier search's;
  - a declaration_search of the same name;
  - a `#check` set that is a subset of an earlier one.
- A phantom is a declaration_search "before this PR" hit for a namespaced query whose file does not declare `<Prefix>.<leaf>`, and has no `namespace <Prefix>` together with a leaf declaration. The check ran against the base snapshot, using the exact sha for 10 of the 32 sessions and c2a50c8 for the rest.
- "Follow" means a later read, grep, goto or hover of a phantom file. It is an upper bound, because such a file can also be read for a legitimate reason (33285's LinearIsometry.lean is a changed file; 34935's T74-79).
- Classes for the last 25 turns: construct, then phantom_follow, then repeat, then tool_error, then new_lookup; the first that matches wins.
- Evidence classes for the dev asks:
  - IN_VIEW_UNTARGETED: the code is in the diff or in a file read, but no call targets it.
  - EXAMINED: a call targets that declaration or that issue.
  - CONSTRUCTED: a verified edit implements the ask.

## Per-session phases

See `capped.json` for phases, repeat counts and per-turn classes. Each line of `traces/<pr>.txt` is one call with its summarised result.
