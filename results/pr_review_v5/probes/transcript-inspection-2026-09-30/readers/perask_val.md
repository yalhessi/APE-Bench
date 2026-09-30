# Why Gr1 (gpt_5.2, reasoning high) missed asks Claude reached: validation small12

Scope: 7 asks on 4 PRs that Claude reached (≥2 of 4 matcher cells) and Gr1 missed on both matchers. Gr1 submitted on all 4 PRs, voluntarily, at 21 to 51 turns of an 80-turn cap (`config.json` `max_turns: 80`), so the budget was never binding. Gr1 wrote no visible text and no reasoning survives in the transcripts (0 text items, 0 reasoning items in all 4). Every claim about *why* it made a call is therefore inference from the calls themselves.

Sources: Gr1 transcripts from `gr_map.json`; Claude sessions from `model-gap-val-small12/pr{29842,30641}/X{1,2}` and `construction-demo-2026-09-29/pr{32875,34091}/X{1,2}`; matcher notes from `match_reasoning/matches.{1,2}.json`. Per-call dumps are in `val/gr1_<pr>{,_full}.txt` and the touch table in `val/touch.json`.

## Per-ask table

| PR | ask | what the maintainer asked | class | why Gr1 missed it, from its calls | lever | conf. |
|---|---|---|---|---|---|---|
| 29842 | v0055 | shorten the tail of `lim_zero` (rewrite `hc` first; merge `apply Tendsto.congr'` into `simpa`) | EXAMINED_NOT_CONSTRUCTED | Hovered exactly lines 119-120 (T10, T11) and looked up the proof's lemmas (T1, T2, T28). Never compiled a variant and never called `precedent_search`. Submitted 0 findings. | compile one shorter variant per modified proof, plus `precedent_search` (which is how Claude X1 found the shape) | medium |
| 30641 | v0064 | rename `a` to `x` in `posLog_pow` (the maintainer called it optional) | IN_VIEW_UNTARGETED (borderline EXAMINED) | `log_pow (x : ℝ) (n : ℕ)` was in view (T2, T3). T8 compiled `(a : ℝ) (n : ℕ)`, log_pow's binder layout with `a` kept; T19 reverted. No call was about the variable name. | copy the mirrored lemma's whole signature; keep the T8 result | low |
| 32875 | v0094 | kernel `setLIntegral_condKernel_eq_measure_prod`: `simp only; exact` into `simpa [this] using` | EXAMINED_NOT_CONSTRUCTED | Read the site (T1), looked up `Kernel.compProd_apply_prod` (T9), ran `#check` on it (T22), then never came back. No edit. About 17 of 51 turns went to Pseudo/Defs errors that predate the PR. | a compiled shorter-variant attempt for every changed proof; drop errors that predate the PR | medium |
| 32875 | v0095 | the measure version of the same (`simpa`) | EXAMINED_NOT_CONSTRUCTED | Same as v0094: T1 read, T9 lookup, T22 `#check`, no edit. | same, handling the kernel and measure twins as one decision | medium |
| 34091 | v0106 | `[Infinite β]` on `exists_infinite_fiber` | IN_VIEW_UNTARGETED | Both call sites pass `(by infer_instance)` in the prompt (6 times) and in 4 search results. Gr1's caller searches were about API breakage, deprecation and naming. It found the Finite sibling's file (T6) and never opened it. No edit. | a signature pass: explicit class-valued hypothesis plus callers passing `by infer_instance`; read the located sibling | med-high |
| 34091 | v0107 | `[Uncountable β]` on `exists_uncountable_fiber` | IN_VIEW_UNTARGETED | Its most-worked lemma: `get_lean_goal` on the signature line (T31), then a compiled edit (T33) that kept `(hβ : Uncountable β)` and changed only `trans'`. | same signature pass; one more variant on an edit already being made | medium |
| 34091 | v0108 | `[Infinite α]` on `exists_infinite_fiber'` | IN_VIEW_UNTARGETED | Its caller `... (by infer_instance)` was in the prompt and in T2/T14/T17/T21. Its calls were naming searches (T3, T23, T29) and a docstring finding. | same signature pass | med-high |

No ask fell under NEVER_RETRIEVED, SEARCHED_WRONG_TERM, CONSTRUCTED_NOT_FILED or FILED_DIFFERENT.

## How Claude got there

- **v0055:** reached only by X1. Its `precedent_search` on the new proof returned ADedecker's suggestion for this lemma on PR #21065. X1 then compiled a 3-line version (success) and filed it. X2 compiled an equivalent one-liner and chose not to file ("The gain is one line ... I do not think a maintainer would ask for it"). So one Claude session also did not file after building it.
- **v0064:** reached only by X1, and as a side effect. X1 filed a *binder* finding that copied log_pow's whole signature, `(x : ℝ) (n : ℕ)`. X2 filed `(a : ℝ) (n : ℕ)` and was not credited. That is the same signature Gr1 compiled at T8.
- **v0094/v0095:** both X sessions compiled `rw [← (Kernel.)compProd_apply_prod hs ht, _.disintegrate]`. X1 also compiled the `conv_rhs` pattern it had read in the sibling lemmas at Integral.lean:44-67.
- **v0106-v0108:** both X sessions made one compiled edit over lines 78-122 putting instance binders on all three lemmas. X1 read the sibling `Finite.exists_infinite_fiber [Infinite α] [Finite β]` (Data/Fintype/Pigeonhole.lean:80-95). X2 used the callers plus a `precedent_search` hint.

## Per Gr1 session: what it touched, what it built

| PR | turns / calls | compiled edits (ok) | findings | declarations edited | touched, never edited | notes |
|---|---|---|---|---|---|---|
| 29842 | 30 / 49 | 0 (0) | 0 | none | `lim_zero` (lookups, hovers at 119-120); `tangentConeAt_closure` (T7); the `of_closure`/`closure` alias (T17-T29, 7 lookups of one name); `uniqueDiffWithinAt_closure` and `mono_closure` only indirectly (searches for `uniqueDiffWithinAt_iff`, `UniqueDiffWithinAt.mono`) | only the as-is compile |
| 30641 | 21 / 42 | 5 (3) | 3 | `posLog_pow` (T7, T8, T19), `posLog_norm_sum_le` (T11, T12: typeclass only) | `posLog_zero`, `posLog_one` (searches) | T8's explicit-binder signature compiled and was dropped |
| 32875 | 51 / 88 | 8 (4) | 3 | `mem_map_equiv`, `Rat.inv_intCast_den_of_pos`, `pi_map_piCongrLeft` (the first three in diff order) | both condKernel lemmas (T1, T9, T22); Portmanteau `..._real_le'` (T10, T21, T50 `#check`); `limsup_finset_sup'` (T19, T27, T49); `exists_lt_mem_ball_of_mem_ball` (T3, T34, T48 as an `example`) | about 17 turns on Pseudo/Defs errors that predate the PR, with no finding |
| 34091 | 34 / 64 | 2 (2) | 6 | `infinite_pigeonhole_card_lt` (T19), `exists_uncountable_fiber` (T33) | `exists_infinite_fiber`, `exists_infinite_fiber'`, `le_range_of_union_finset_eq_univ`; the two LinearAlgebra callers only through file reads and compiles | roughly 20 calls on duplicate hunting (uncountable fiber) and on `le_range` naming/deprecation; none filed |

For comparison, Claude compiled 3-4 edits on 29842, 6-7 on 30641, 27-46 on 32875 and 8-10 on 34091. On 29842 Gr1 made more calls than Claude (49 against 20-24) but compiled nothing.

**Does the final submission leave out something its own successful variants had established?**
- **30641: yes, once.** The T8 edit `@[simp] lemma posLog_pow (a : ℝ) (n : ℕ)` compiled, and the submission reverted to the implicit binders. The explicit signature is what Claude filed as a style finding in both sessions. Every other successful edit was filed.
- **32875: no.** The successful `example` compiles were empty wins or no improvement: at T35 `simpa` proves `mem_map_equiv` only because the lemma is already a simp lemma, and the in-place T45 failed; T48's `simpa [mem_ball] using exists_between' h` is longer than the PR's term.
- **34091: no.** Both successful edits were filed.
- **29842: not applicable.** It made no edits.

## Reached versus missed on these PRs

- **What Gr1 reached:** v0065 (matcher 1 only) and v0066 through its one-line `posLog_pow` proof, compiled at T8/T19. v0092 partially, through its Pi edit (T38). v0109 and v0110, docstring domain/codomain errors readable straight from the diff, which all five sessions reached. On 29842 it reached nothing: 0 findings, and nobody reached v0053 or v0056.
- **What separates them:** every ask Gr1 reached is either a text error visible in the diff, or a proof golf on a declaration it compiled an edit for. Every ask it missed is either on a declaration it never edited (`lim_zero`, both condKernel lemmas), or a signature choice (variable name, binder kind) on a declaration it did edit (`posLog_pow` T8, `exists_uncountable_fiber` T33) while it varied only the proof.

## Synthesis

1. **The evidence reached Gr1 every time.** None of the 7 misses is NEVER_RETRIEVED or SEARCHED_WRONG_TERM. For the four binder/name asks the deciding evidence was in the initial prompt or an early tool result (`by infer_instance` at both call sites; `log_pow (x : ℝ)`).
2. **What was missing was a construction.** In every miss Gr1 never compiled the maintainer's change. For the three proof asks (v0055, v0094, v0095) it compiled nothing at all on the declaration, after lookups and hovers aimed squarely at the lines in question. Claude compiled the change in every session that reached.
3. **Gr1 builds shallow and early.** Across the 4 sessions it made 15 compiled edits (9 successful). Over the same four PRs Claude made 45 (X1) and 66 (X2) per session. On 32875 all its edits went to the first three changed declarations in diff order. The other five got reads and `#check` only, and both asks it missed sit in those five.
4. **When it did build, it varied the proof and left the signature alone.** `posLog_pow` T8/T19 and `exists_uncountable_fiber` T33 both kept the PR's binder names and kinds. The only signature variant it compiled (T8's explicit binders) was reverted and not filed. This matches the record's note that the pipeline's arms at 34091 checked line breaks and never compiled binder changes.
5. **Its effort went to investigations that ended without findings.** About 17 of 51 turns on 32875 chased the Pseudo/Defs errors that predate the PR; Claude X1 dismissed the same errors in one line. About 13 turns on 29842 went to one alias, looked up 7 times. Roughly 20 calls on 34091 hunted duplicates and deprecation. Re-querying the same name fits reasoning being discarded between turns, but that is an inference: no reasoning text survives.
6. **Gr1 did not use the two retrieval tools behind two of Claude's reaches.** It never called `precedent_search` in these 4 sessions, although it had the tool. Claude's `precedent_search` produced the v0055 shape (X1) and a hint on the binder issue (X2 on 34091). Claude X1 also opened the Finite sibling file; Gr1 had located that file (T6) and did not open it.
7. **Two of Claude's reaches are weak evidence of a model gap.** v0055 and v0064 were each reached by 1 of 2 Claude sessions. v0064 came as a side effect of a binder finding. On v0055 the other Claude session built the golf and declined to file it. The stable gap is v0094/v0095 and v0106-v0108, where both Claude sessions compiled and filed.
8. **The most plausible levers, none tested:** (a) require one compiled variant, proof *and* signature, for every changed declaration before `submit_findings`, with `precedent_search` run on each changed proof; (b) a signature pass: explicit class-valued hypotheses against callers passing `by infer_instance`, and the binder names and kinds of the lemma being mirrored; (c) a rule that errors predating the PR get noted once and dropped. A larger budget is not indicated: all four sessions stopped on their own well under the 80-turn cap. Everything here is n=1 Gr1 run per PR, provisional.
