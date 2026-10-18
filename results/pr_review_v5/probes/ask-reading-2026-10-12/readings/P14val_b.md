# Batch P14val_b -- readings (one reader; counts provisional)

PRs 28649, 29842, 30458, 30641 (P14_val), 15 asks. Sessions: DX1-3 (solo DeepSeek), AP1-3 (DeepSeek + conventions section). Line numbers are transcript lines.

## v0053 (PR 29842, F12, P041) -- "How does this interact with #24163? ... in #21065 I thought the consensus was to change the definition. If you've changed your mind, explain why in the PR description."
Maintainer wants the design choice (generalize the lemmas rather than the definition of `tangentConeAt`) motivated in the description, against two earlier PRs.
- DX1 `C` -- precedent_search handed it #21065 (line 17); line 45: "let me look at how the sibling PR (#21065, #20859, #24227) did things, since ADedecker/Yury had a plan ... Hmm, no; generalizing in place is standard." Never considered the description.
- DX2 `K` -- line 7: "The PR description is empty. A maintainer might ask for a description? The brief says don't report general risks... no description isn't a finding per se."
- DX3 `K` -- line 69: "A maintainer might ask for a PR description explaining the generalization/naming... The brief says findings must be about the reviewed code... the PR description is not recoverable, so no." (Line 48-54: searched Zulip for #21065's discussion, "#21065 has the identical generalization".)
- AP1 `P` -- filed "Add a PR description stating both halves" under held bullet 11 (title/description say what moves where); matcher: generic description ask, partial.
- AP2 `P` -- same, "Write a PR description that (a) lists the declarations whose hypotheses were weakened ... (b) states ... only moved".
- AP3 `K` -- line 53 "OK, include it", then submission notes line 55: "'PR title/description state the change': left -- the title ... states exactly what the diff does".
- Knowledge `pr_context`: #24163 and the "consensus to change the definition" live in GitHub threads the packet does not carry; but every one of the six sessions had #21065's review comments from precedent_search and read them only as a proof-golf precedent, never as a design precedent (nobody asked "what is the plan relative to #21065?", though DX1 came within a sentence of it). AP: P041 absent; neighbouring bullet 11 held, used by AP1/AP2 (partial), considered_dropped by AP3.
- Verdict: the specific half is knowledge (pr_context: #24163, the consensus) that no session could see; the generic half (motivate a design change in the description, P041) is judgement -- DX2/DX3 named it and dropped it on "the brief says findings must be about the reviewed code / not recoverable", a harness-form ground; AP's held title/description convention bought two partials by describing the diff, which is not what the maintainer asked.

## v0056 (PR 29842, F12, P041) -- "[author: prefer to merge a 'generalize lemmas' PR first, then generalize the definition] I'm fine with this, please just write something to this effect in the PR description."
Maintainer wants the author's stated plan (lemmas first, definition later) written into the description; a reply in the v0053 thread.
- DX1 `C`, DX2 `K`, DX3 `K`, AP1 `P`, AP2 `P`, AP3 `K` -- same place and same reasoning as v0053 (quotes there).
- Knowledge `pr_context`: the plan is the author's reply; nothing in the packet carries it. A session could at most ask "state the relation to #21065 and the plan in the description", which would be partial here too.
- Verdict: unreachable in substance without the thread (pr_context); the reachable form -- "describe the design plan" -- was dropped by DX2/DX3 as out of the brief's scope and replaced by AP1/AP2 with a diff summary (partial). Twin of v0053: one design-motivation ask counted twice.

## v0029 (PR 28649, F10, P185) -- "I disagree with this one, please revert." on `left hand side` -> `left-hand side` (Upcrossing.lean:698)
Maintainer wants the hyphenation hunk dropped: a taste change to another author's prose.
- DX1 `C` -- line 19: "Upcrossing 'left hand side' -> 'left-hand side': fine (though Mathlib has both)."
- DX2 `V` -- line 44: "correct. ... grep found only one 'hand side' occurrence in that file. Nothing to ask." (content_search at line 9)
- DX3 `K` -- line 24: "maybe the planted issue is that the PR mixes content changes with typo fixes (scope). E.g. ... 'left-hand side' (hyphenation preference) ... Hmm, those are all doc."
- AP1 `reached` -- "no style-guide rule mandates the hyphenated form, so the PR gains only the rewriting of another author's sentence"; AP2 `reached` -- "purely cosmetic rewrite of the original author's prose"; AP3 `reached` -- "about 20 files use each ... left to the original author". Bullet 10 (= P185) held, used by all three.
- Knowledge DX `demand`, AP `none`: DX1 had the AP sessions' evidence ("Mathlib has both") and DX3 the exact concern ("hyphenation preference"); what neither had is that maintainers revert such hunks.
- Verdict: judgement flipped by a stated demand -- the cleanest case in the batch: 0/3 -> 3/3 on one sentence that says what maintainers do, with no new fact about the code.

## v0030 (PR 28649, F10, P278) -- "spell out `mgf` instead?" (Moments/Basic.lean:25, `mgfs` -> `MGFs`)
Maintainer wants the abbreviation written out ("moment generating functions").
- DX1 `P` -- filed "Revert the capitalisation to the library's lowercase spelling"; spelling out never among its options.
- DX2 `P` -- line 16: "The title of the module doc is 'Moments and moment generating function' -- spelled out. So the project spells out terms. Hmm. Which direction would a maintainer request? Options: (a) Revert ... (b) Keep the capitalization and also fix line 30".
- DX3 `P` -- line 35: "this says 'moment generating function' spelled out; so capitalization in the results list is a style choice." Filed "Preferably revert".
- AP1 `P` -- line 19: "this convention would ask to spell out 'moment generating functions'? That'd be a change to pre-existing text ... the most defensible ask is consistency" (held, considered_dropped).
- AP2 `reached` -- line 26: "a maintainer might ask to spell out 'moment generating functions'" -> filed it as the primary fix (held, used).
- AP3 `P` -- line 33: "the full-word convention would prefer 'moment generating functions'. Hmm! ... Hmm, but then the docstring is verbose." Filed the revert (held, considered_dropped).
- Knowledge DX `demand` (P278), AP `none`.
- Verdict: all six attended the line and asked for a change there; the DX three had the fact (the file spells the term out) but not the demand, so they asked for case consistency; with the demand delivered, one of three used it and two dropped it on "pre-existing text" / "verbose" -- the same hesitation AP2 voiced (line 29, "beyond typo fix... Hmm") and overrode.

## v0031 (PR 28649, F10, out of census) -- "I'm not sure about this one" (`Popoviciu's inequality on variance` -> `on variances`)
Maintainer doubts the pluralisation.
- DX1 `V` -- line 10: "Actually no, Wikipedia title is 'Popoviciu's inequality on variances' plural."
- DX2 `V` -- line 7 "seems wrong/less standard" -> line 19 "Actually the standard English formulation is 'Popoviciu's inequality on variances' (Wikipedia)."
- DX3 `V` -- line 18 "a semantic wording change, not a typo fix" -> line 24 "(plural) is the standard literature name. So the change is fine."
- AP1 `V` -- line 7 saw the sibling "Bhatia-Davis inequality on variance" and called it "an inconsistency within the file", then line 28: "The Zulip shows the author of that lemma ... called it 'Popoviciu's inequality on variances'. So plural is intentional; leave."
- AP2 `V` -- line 76 submission: "the plural is a correction, not a regression; nothing filed".
- AP3 `reached` -- the sibling title at line 419: keep singular or change both.
- Knowledge `none`: the sibling is in the file; three sessions' first instinct was the maintainer's.
- Verdict: judgement -- five sessions started where the maintainer is ("not a typo fix", "seems wrong") and let a recalled Wikipedia title (or the original contributor's Zulip wording) overrule the in-file neighbour; the one that filed read the neighbour as the ground. A check against outside authority defeated a doubt the maintainer kept.

## v0062 / v0063 (PR 30458, F1, P329) -- "does the old proof not work?" / "same here" on `card_le_card_div_left` / `_right` (Finset/Basic.lean:1251, 1260)
Maintainer wants the one-line pre-PR bodies back; the generalization did not need the `obtain`/`exact`/`(b := ...)` restyle. One finding covers both lines, so the two asks are twins.
- DX1 `K` -- lines 33-37 lean_verify_edit the pre-PR bodies; line 38: "with their *original* proofs compile under the new sections (so those proof rewrites are unnecessary too) ... arguably *neutral* ... A maintainer likely wouldn't reject them." Filed the Set/Finite.lean twin (finding 4) and the Basic.lean ones, not this pair.
- DX2 `K` -- line 7: "They changed `have ⟨_, ha⟩ := ht` to `obtain ⟨b, hb⟩ := ht`. Fine, arguably style." Then O: the DivInvMonoid-level finding at 1258.
- DX3 `K` -- line 13: "That's the style requirement in Mathlib (no `have` for destructuring? ...)". Then O: section hypotheses (1256), section names (1246).
- AP1 `K` -- line 7: "The convention says `;` not used to put several tactics on one line -- the PR *removed* a `;` there. Good." Bullet 19 (= P329) held; AP1 used it on the Basic.lean line splits (finding 3) but at this place another held bullet made the rewrite look like an improvement (ap_use ignored here).
- AP2 `reached`, AP3 `reached` -- both verified "the pre-PR proofs compile verbatim" and asked to restore them (held, used).
- Knowledge: DX1 `none` (it had the fact and the frame, "a coherent scope/minimal-diff style finding"), DX2/DX3 `demand` (read the restyle as style, not as something maintainers push back on), AP `none`.
- Verdict: judgement under a delivered demand. The decisive fact (old bodies compile) was established by DX1, AP2 and AP3; DX1 dropped it on a guess about maintainers ("wouldn't reject"), AP2/AP3 filed it because the section said maintainers ask exactly this ("What happened to the old proof? Does simp not work anymore?" is the bullet's example). AP1 shows the cost of a list: a second convention (no `;`) read the same hunk as an improvement.

## v0060 / v0061 (PR 30458, F2, P329 + P369) -- "you don't need to section these off ... collect the common variables ... `variable [IsLeftCancelMul α] in` before this lemma" / "following the above suggestion" (lines 1249, 1258)
Maintainer wants the old single section with `[DivisionMonoid α]`, and the one-lemma cancellation hypotheses bound per lemma with `variable ... in`, not two nested one-lemma sections.
- DX1 `P` (m1 partial / m2 no) -- filed "Rename section LeftCancel to section IsLeftCancelMul" (sections kept).
- DX2 `K` -- line 13: "the maintainer might ask to hoist the shared variables. Minor style."; note line 43: "keeping the lemma outside both cancellation subsections is a defensible way ... so I am not asking for it."
- DX3 `P` (m1 partial / m2 no) -- section rename; line 42 "why not put it in that section ... instead of nesting" considered, not filed.
- AP1 `P` / v0061 `O` -- moved `card_le_card_div_self` into `LeftCancel` (sections kept); bullet 23 (= P369) held, applied to the trailing variable block only.
- AP2 `P` / v0061 `K` -- line 42, with bullet 23 quoted: "each inner section holds exactly one lemma ... A maintainer might ask to inline the variables into the lemma statements? Hmm, that seems overly pedantic and I don't think a maintainer would demand that." Line 65: "bind `[IsLeftCancelMul α]` ... in the individual lemmas' signatures? ... the file's existing convention for the mul analogues is sections. So keep sections."
- AP3 `P` / v0061 `O` -- same move as AP1; line 50 on section names "I'll skip filing it (uncertain)".
- Knowledge DX `mechanism` (`variable ... in`; nobody wrote it, though AP1's own linter output at line 35 printed `omit ... in`), AP `none` (held; AP2 reasoned to the maintainer's form).
- Verdict: judgement, twice over. The convention was delivered and AP2 derived the exact ask from it, then overruled it with a prior about maintainers ("overly pedantic") and an analogy (the mul lemmas use sections) -- the same two grounds that sank DX1 on v0062. The `in` mechanism is the missing word for the DX sessions, but the AP reading shows the word would not have been enough.

## v0064 (PR 30641, F8, P105) -- "`x` might be more conventional for a real number ... consider my suggestion optional" (`{a : ℝ}` in `posLog_pow`)
- DX1 `C` (line 7, checked the statement's truth for negative `a`), DX2 `C` (line 14, simp-normal form), DX3 `C` (line 16, `@[simp]` fitness), AP1 `C` (line 17, its own replacement keeps `a`), AP2 `C` (line 7, simp lemma shape), AP3 `C` -- line 7: "is `{n : ℕ} {a : ℝ}` the right binder form? ... Compare `posLog_neg (x : ℝ)` ... Existing file has mixed styles. Not worth."
- Knowledge `none` (P105 absent in AP; the file's `{x : ℝ}` lines were in every file_read).
- Verdict: attention. Six sessions read the binder list, one of them next to a sibling with `x`, and none read the letter; the maintainer himself marks it optional, and the file is mixed, so this is a taste ask at the floor of what a reviewer can be expected to say.

## v0065 (PR 30641, F8, out of census) -- "There's no `ha` in scope, so this could be `ha`, right?" (`h₂a`)
- DX1 `O`, DX3 `O`, AP1 `O` -- each replaced the whole proof with a one-liner (the name goes away unmentioned).
- DX2 `reached` (m2 partial) -- "plus the leftover-looking hypothesis name `h₂a` ... This also removes the confusingly named `h₂a`", inside the proof-replacement finding.
- AP2 `reached` -- its case-split rewrite (held bullet on `obtain`/`rcases` forms) introduces `ha`.
- AP3 `K` -- line 22: "also uses `h₂a` name. Meh."
- Knowledge `none`. Verdict: attention and form -- the three sessions that rewrote the proof made the ask moot without stating it, and the matcher cannot credit a rename that is only implied; AP3 saw it and spent one word.

## v0066 (PR 30641, F1, P060) -- "Can you prove the ≤ version here directly?" (`have : 1 < |a ^ n|` then `this.le`)
- DX1, DX2, DX3, AP1 `reached` (m1; m2 partial) -- all four replaced the whole case bash with a `log_pow`/`mul_max_of_nonneg` one-liner, so the line disappears rather than becoming `1 ≤ |a ^ n|`.
- AP2 `O` -- its restructure (finding 8) keeps `have : 1 < |a ^ n| := by simp [one_lt_pow₀ ha hn]` and `posLog_eq_log this.le`: the exact pattern the maintainer objected to, re-emitted.
- AP3 `K` -- line 22: wrote a candidate with `posLog_eq_log (one_le_pow₀ (not_le.1 ha).le)` -- the ≤ form -- then "That's roughly the same length. So no proof-golf finding."
- Knowledge `none` (P060 absent in AP; AP3 had the direct lemma in its own draft).
- Verdict: form for the four (a bigger golf subsumes the ask and the matcher splits), judgement for AP3 (the right form, dropped on line count), and a miss of attention for AP2 (rewrote the place and kept the `<`/`.le` detour).

## v0067 (PR 30641, F1, P005) -- "Can `positivity` do this (untested)?" (`simp [Finset.sum_nonneg (fun i _ ↦ norm_nonneg (f i))]` for `0 ≤ ∑ ‖f t‖`)
- DX1 `C` (line 33, "could be done with gcongr? Hmm"), DX2 `C` (line 56, term form "let me test ... if yes, it's a cleaner one-line", not filed), DX3 `C` (line 38, "A cleaner canonical way: monotoneOn_posLog (norm_nonneg _) (Finset.sum_nonneg ...)", not filed).
- AP1 `C` -- line 17 read the sibling's `(by simp; positivity)` and took only its inline shape.
- AP2 `P` -- line 7: "`positivity` could prove `∑ t ∈ s, ‖f t‖ ≥ 0` and `0 ≤ ‖∑‖` ... Let me test that as a proof-golf/style suggestion"; filed the sibling-style `(by simp [Finset.sum_nonneg])` instead.
- AP3 `K` -- line 54: "(well, `positivity` would do it, but the author's `simp [...]` is fine)".
- Knowledge DX `demand` (P005), AP `none` (absent, but two sessions named it anyway).
- Verdict: judgement. The answer to the maintainer's question sits in AP3's parenthesis and in AP2's draft; both chose the author's form or the file's sibling form over the finishing tactic. The DX three reached for a term-mode golf and never for `positivity`, with the sibling's `positivity` on screen.

## v0068 (PR 30641, F1, P094) -- "Can `gcongr` do this (or do you need to provide the side condition manually)?" (`apply monotoneOn_posLog ... (norm_sum_le s f)`)
- DX1 `K` -- line 33: "The first step could be done with `gcongr`? Hmm" then the argument order, no test (inferred: moved on). DX2 `K` -- line 10: "could use `gcongr`? ... Eh." DX3 `C` -- term form only.
- AP1 `V` -- line 24 lean_verify_edit: "gcongr did not make progress"; notes at 44. AP2 `P` -- line 36 "I doubt it works. Let me test to be sure. If gcongr fails, then this convention doesn't apply"; line 40 it fails; filed the sibling-form restructure of the step (partial on form, not on gcongr). AP3 `V` -- line 27: "gcongr did not make progress -- so the gcongr convention doesn't apply here (can't be done). Good, that removes that finding."
- Knowledge `none`; bullet 8 (= P094) held by all three AP sessions, all three checked it.
- Verdict: the check was right and the maintainer's guess was wrong ("untested" in the twin ask, and this one allows "or do you need to provide the side condition manually?"). A reviewer that files only verified changes cannot produce this ask; only a question-form finding ("gcongr does not fire on `MonotoneOn`; the side condition stays manual") could match it, and nothing in either condition emits that.

## v0055 (PR 29842, F1, P018) -- "you can make it more compact: rw [...] at hc; simpa using Tendsto.congr' this <| ..." (`lim_zero`, line 120)
- DX1 `reached` -- line 68: "the precedent comment (ADedecker, PR #21065, same file/lemma) literally suggested a rewrite of this exact proof" tipped it. DX3 `reached`. AP1 `reached` (via the inlining bullet 3). AP3 `reached` (via the merging bullet 4, verified, cites #21065).
- DX2 `K` -- line 35: "Can lim_zero's proof be shortened to essentially ADedecker's suggestion? Already equivalent. Might be worth noting as a style/precedent finding? ... the current code matches the spirit. I'd rather not."
- AP2 `K` -- bullet 4 cited at the place five times (lines 41, 44, 56, 59, 68): "Merging `rw ... at hc` into the `simpa`? ... No, because you need to *rewrite hc*"; note line 73: "the final `simpa using` is the sanctioned ... form. No request." The merged form was never built.
- Knowledge DX `none`, AP `construction` (AP2).
- Verdict: 4 of 6 reached; the two misses are judgement on the same evidence -- DX2 held the maintainer's own precedent and read the code as already matching it, AP2 held the convention and argued the merge impossible instead of compiling it (AP3 compiled it).

# Batch summary (P14val_b: 15 asks, 90 session-asks; one reader, counts provisional)

**Behaviour, DX (45):** reached 6, P 7, C 10, K 16, V 4, O 2, A 0, E 0.
**Behaviour, AP (45):** reached 13, P 11, K 9, V 4, C 4, O 4, A 0, E 0.
`K` is the modal DX code: in 16 of 45 the solo session wrote the ask's concern down and dropped it. Nothing was unattended.

**Knowledge, per ask (15):** DX -- none 6 (v0031, v0064, v0065, v0066, v0068, v0055), demand 5 (v0029, v0030, v0062, v0063, v0067), mechanism 2 (v0060, v0061: `variable ... in`), pr_context 2 (v0053, v0056). AP -- none 12, pr_context 2, construction 1 (v0055/AP2). No `api`, `direction` or `unclear` in this batch.

**AP held the convention on 8 asks** (v0029, v0030, v0055, v0060, v0061, v0062, v0063, v0068); absent on 5 (v0053, v0056 P041; v0064 P105; v0066 P060; v0067 P005); n/a 2. What happened when held:
- v0029: used 3/3 (0/3 -> 3/3; DX1 had the same evidence, "Mathlib has both", and read it as licence).
- v0062/v0063: used 2/3; AP1 read the hunk under another held bullet (no `;`) as an improvement. DX1 had verified the old proofs compile and dropped it: "a maintainer likely wouldn't reject them."
- v0055: used 2/3; AP2 cited the bullet five times and never built the merge.
- v0030: used 1/3; AP1/AP3 cited it and dropped it ("pre-existing text", "verbose"); DX 0/3 asked for case consistency instead.
- v0060/v0061: used 0/3; AP2 derived the maintainer's form from the bullet and dropped it as "overly pedantic ... I don't think a maintainer would demand that"; AP1/AP3 spent the bullet on the trailing variable block.
- v0068: used 0/3, correctly: all three tested `gcongr` and it fails.

**Three most instructive readings.**
1. **v0062/v0063.** The decisive fact (the pre-PR bodies compile verbatim) was established by DX1, AP2 and AP3 alike. DX1 filed the Set/Finite.lean twin and dropped this pair on a guess about maintainers; AP2/AP3 filed it because the section's example says maintainers ask exactly "What happened to the old proof?". The delta is not knowledge of the code, it is permission to ask.
2. **v0060/v0061 with v0062 as its mirror.** AP2 reasoned from the held bullet to the exact ask and then overruled itself ("overly pedantic", "the mul analogues use sections"). A stated demand beats the prior when the bullet's example matches the hunk (v0062), and loses to it when the reviewer has to carry the convention one step further than the example (v0060). Held-and-dropped is the AP condition's own K.
3. **v0068 (and v0067).** The gold includes untested questions, and here the question's answer is no: `gcongr` does not fire, and all three AP sessions proved it. A reviewer that files only verified changes cannot match this ask; a question-form finding that reports the check's result could. v0053/v0056 are the same shape at PR level: every session held #21065 from precedent_search and read it as a proof-golf precedent, never as a design precedent, and the only thing that could reach the ask is a question.

Also worth carrying: v0031, where five sessions started where the maintainer was ("not a typo fix", "seems wrong") and let a recalled Wikipedia title or the contributor's Zulip wording overrule the in-file neighbour; a check against outside authority defeated a doubt the maintainer kept.
