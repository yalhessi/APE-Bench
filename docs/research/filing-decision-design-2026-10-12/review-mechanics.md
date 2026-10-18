# Adversarial review: the mechanics of the reading (2026-10-12)

Reviewer lens: the reading the draft rests on. Are the six readers' codes consistent, do the numbers
hold, is the "grounds" classification sound, and do §5's predictions follow from the rows?
Re-checked against transcripts, not summaries. Scripts and samples under
`results/pr_review_v5/probes/ask-reading-2026-10-12/review-mechanics/`. No model spend.

Written incrementally; all six checks completed.

## Findings table

| # | what | effect | evidence |
|---|---|---|---|
| 1 | The "24 asks no ask-free session reaches" is 24 only with Opus + AP (`TA1`) counted as ask-free and the `match_D12` seal; the assessment's definition (TA out) gives 29, its seals give 32; five of 47 D12 asks flip between two matcher passes over the same sessions | **changes a number** (§5 and §6's bars sit on a set that moves by 5-8 asks) | §3; `review-mechanics/recompute.py`, the `unblinded.json` recount |
| 2 | The keyword regex behind §1.3 is not on disk. By hand: 64 of 105 K rows on an inadmissible ground (draft 63), on 37 asks (draft 32); but "a guess about maintainers" is **6, not 22** -- the word `maintainer` marks 22 rows, and in 16 the reviewer predicts the ask *correctly* and drops it on something else | **changes the design's diagnosis** (§0/§2 "clears the concern on ... its own guess about maintainers") | §2; `k_grounds.jsonl` |
| 3 | 41 of 105 K rows carry no ground on §3.2's list: 15 technical justifications stated without a check (wrong in hindsight), 13 with no ground at all, 8 a convention judged satisfied, 6 a correct refutation. The authority order does not fire on them (no check was run); only rank 4's "never silence" converts them, which is a volume rule | **changes the design** (§3.2 is incomplete for 40% of the dropped rows; §5's "63 would be filed" understates what §3.2 itself mandates: all 105 K and 102 C rows become dispositions) | §2, §5 |
| 4 | "The AP section changed no knowledge column" is false: 11 asks change DX -> AP; `demand` has three meanings across readers (not delivered / delivered and ignored / neighbour delivered); `demand` vs `none` on K rows tracks the reader, not the row | **changes a number** (14 `demand`; "15 need a fact" is 9-17 by reader); the direction "rarely a fact" survives | §4 |
| 5 | Inter-reader: 25 of 30 re-coded rows agree (K 9/10, C 5/8, V 5/6, O 6/6); all five disagreements sit on three boundaries the protocol does not define (adjacent concern vs the ask's; "at the place" = same declaration vs same aspect; a file read as a "check"). D12c's K share (5% of its misses, vs 28-53% elsewhere) is a reader effect: it codes "the file's established style. Fine." as `C`/`O` where D12a codes it `K` | **changes a number**: §1.1's "81 named-and-cleared vs 65 concluded-fine" is reader-dependent at the tens | §1; `recode.jsonl` |
| 6 | 105 K rows are 88 distinct reasoning passages; 9 passages are counted 2-4 times (the `Dense.ciSup` rename x4, `[Infinite β]` x3, three twin pairs) | cosmetic to number (the draft's §8 notes the gold's double counting but keeps the inflated row counts) | §2 |
| 7 | §5's bullets are classifications, not predictions; only §6's two bars can fail, and both sit on sets this review moves (24 -> 29/32; 32 -> 37) | changes the design's test | §5 |
| 8 | `prepare.py` `hits("T")` counts TA1 under T (prefix match); the `T` column of `asks_all.tsv` is T1 + TA1 | cosmetic (never-reached unaffected) | §3, §6 |
| 9 | 33149 AP1/AP2 were matched on 20 of their 22/24 findings (the harness cap, not the first 20); d0032 unaffected | cosmetic here | §6 |
| 10 | `reached` mixes m1-only and both-matchers rules (5 rows); one `K` row has both matchers at `partial` (d0033 AP2); held-asks table invariant, §1.1 row counts not | cosmetic | §6 |
| 11 | §1.5's family list sums to 22, not 24 (d0004 F10, d0002 F5 dropped); "ignored 45" is 46 | cosmetic | §5 |

**Net.** The arithmetic the draft states from the jsonl holds everywhere I recomputed it. What does not hold
is the layer between the rows and the design: the never-reached set, the composition of the "inadmissible
grounds", the knowledge column, and the K/C/O split are each reader- or definition-dependent at the size of
the effects the design argues from. The design's §0 story -- "it names the concern and clears it on a guess
about maintainers, worth, siblings, plurality" -- is right for about 60 rows and wrong for about 40, where
the reviewer stated a (wrong) technical reason or no reason, and the authority order as written has nothing
to say to those. §6's bars should be re-stated on a fixed never-reached core and a hand-coded ground list,
and the K/V/C/O shares reported with the batch as a factor.

## 1. Inter-reader consistency (30-row seeded re-code)

Sample: `review-mechanics/sample30.py`, seed 2026, strata K 10 / C 8 / V 6 / O 6 (proportional would be
11/10/3/6; V oversampled because the V/K boundary was one of the three asked for); 7 rows from D12a, 2 D12b,
3 D12c, 5 P14post, 6 P14val_a, 7 P14val_b. Each row re-coded from the transcript (`ctx.py`: the turn at the
cited line, the submitted findings at the ask's file, a grep for the declaration), under the protocol's
letter; `recode.jsonl` holds the code and the line evidence.

| reader's code | rows | agree | my code where not |
|---|---|---|---|
| K | 10 | 9 | C (v0094 DX3) |
| C | 8 | 5 | O (p0003 DX2, v0064 AP3, p0007 DX1) |
| V | 6 | 5 | K (d0002 DX1) |
| O | 6 | 6 | -- |
| all | 30 | **25 (83%)** | |

Every disagreement is on a boundary the protocol leaves open, and each is a rule a reader chose, not a
slip:

- **K vs C -- "the ask's concern" against an adjacent one.** v0094 DX3's concern is `rw [this]` against
  `simp only [this]` (l.11, l.37); the ask is to merge the two calls, which it never names. The same
  reading makes d0008/d0009 AP2/AP3 (`[simp]` lemmas, "unfold by hand") `C` rather than `K`; 8 rows in all
  (§2). The K count is sensitive to how near a named concern must be.
- **O vs C -- "at the place".** p0003 DX2 filed two findings at `tprod_nonneg` itself (one of them p0002's
  ask); v0064 AP3 filed `@[simp]` placement and the docstring at `posLog_pow` itself; p0007 DX1 filed at one
  of the four binder-carrying declarations. The P14post and P14val_b readers code these `C` ("nothing on the
  same aspect"); the D12c reader codes a docstring typo at the theorem as `O` (d0003/d0004). D12c's O share
  of its misses is 30%, P14val_b's 8%; part of that is this rule.
- **V vs K -- what counts as a check.** d0002 DX1 "checked" by reading the inline sibling
  (`isUniformEmbedding ... does the same inline. Fine.`); no compile, search or count. The protocol's `V`
  says "ran a check (compile, search, count)"; a file read is a search for one reader and not another.

**Is any batch systematically different?** Yes, D12c. Its reader coded "a long informal proof sketch ...
following the pattern of the existing theorem. That's the file's established style. Fine." (d0004 AP1) as
`O`, and "Consistent ✓" at the sibling statement (d0003 DX2) as `C`; the D12a reader coded "both forms exist.
Consistent." (d0018 DX2) and "maintainers accept these duplicates ... consistent with the file" (d0018 DX3) as
`K`. Same ground, same sentence shape, two codes. D12c has 3 `K` in 60 misses (5%); the other five batches
run 28% to 53%. The draft's §1.1 split (DX: 81 named-or-checked-and-cleared against 65 concluded-fine) moves
by a few tens of rows depending on which rule the sixth reader had used, and the per-family tables (§1.4) that
compare D12 with P14 inherit the difference.

**Quote fidelity.** All 30 quotes were locatable in substance. Two are not at the cited line or not
verbatim: d0045 DX1's l.53 is about the sibling ask (d0046, which DX1 reached; d0045's ground is in its
submitted finding); v0105 DX1's "So the case split is needed" is a paraphrase of l.9/l.12. Several quotes are
condensed with `...` across turns. Usable, but the jsonl's `line` is not always where the decisive sentence
is.

## 2. The "inadmissible grounds" classification (all 105 K rows by hand)

The keyword regex that produced the draft's §1.3 counts is **not on disk** (not in the draft commit
`de7425b6`, not in `aggregate.py`, not in any scratchpad), so its assignments cannot be audited row by row;
the draft's §7 says "a third of the `K` rows unclassified" but names no rows. I classified all 105 from
their full quotes (`review-mechanics/k_grounds.py`, output `k_grounds.jsonl`; codebook in the script,
several codes per row allowed, the first primary):

| ground | draft (K rows, keyword) | by hand, primary | by hand, any |
|---|---|---|---|
| worth / minor / marginal / taste / noise | 27 | 26 | 33 |
| a guess that maintainers would not ask | **22** | **4** | **6** |
| the corpus plurality or a tool's count | 14 | 9 | 10 |
| the file's or PR's siblings | 9 | 7 | 7 |
| the brief's form | 4 | 5 | 5 |
| the PR's own framing | 2 | 3 | 3 |
| a finding budget / triage | (named, uncounted) | 5 | 7 |
| a failed check | 6 | -- (coded `technical`, below) | |
| an outside authority | 1 | 0 (that is a `V` ground; see v0031) | |
| **technical justification, no check run** (wrong in hindsight) | -- | **15** | 16 |
| **unstated** (named, then "Hmm" / "Skip" / moved on) | -- | **13** | 13 |
| a convention judged satisfied at the place, no check | -- | 8 | 8 |
| a correct refutation (v0105: the one-liner does not exist) | -- | 6 | 6 |
| speculative / "limited basis" | -- | 3 | 4 |
| no rule found (d0029) | -- | 1 | 1 |

Rows with at least one ground on the draft's inadmissible list: **64 of 105, on 37 asks** (draft: 63 on 32).
The total agrees; the composition does not, and the composition is what §0, §2 and §3.4 argue from.

**Where the regex went wrong, reconstructed.** The word `maintainer` appears in exactly 22 of the 105
quotes -- the draft's "guess about maintainers" count. In 16 of those 22 the reviewer is *predicting the
maintainer's ask*, often correctly, and then dropping it on a different ground: "A maintainer might ask for a
description? The brief says ..." (v0053/v0056, 4 rows: brief), "A maintainer would flag a garbled sentence
... That's noise" (d0044: worth), "a real maintainer might ask: state this ... as a general UFD-style lemma
... Hmm" (p0005: unstated), "the maintainer might ask to hoist the shared variables. Minor style" (v0060/61:
worth), "A maintainer would ask for a simp lemma. Hmm" (d0008/d0009: adjacent concern). Only 6 are a negative
estimate used as the ground ("maintainers accept these duplicates", "A maintainer likely wouldn't reject them",
"I'm not sure a maintainer would ask", "probability ... 0.35", "I don't think a maintainer would demand
that"). The draft's §0 sentence "clears the concern on ... its own guess about maintainers" rests on 22 rows
of which 16 are the opposite: the reviewer's guess about the maintainer was *right* and something else
cleared it. Similarly, 4 of the plurality rows (d0022/23/25/27 DX1: "both the prefix census and the Dense
namespace census argue for conclusion-named lemmas") are the census arguing *for* the rename; the drop ground
in those rows is unstated (DX1 filed the `*Bounds` pair and said nothing about the four).

**What the hand classification adds that the regex could not see.** 41 of the 105 K rows carry no ground on
the draft's list. 15 are a technical justification stated without a check and wrong in hindsight ("it's a
parameter, so that's fine" p0014; "Fine, it's an abbrev" p0015; "`homMk` takes a presheaf morphism" p0016;
"they can't put things in [a deprecated] namespace" d0038; "`grind` needs `mem_map` plus `Equiv.coe_toEmbedding`.
Not an issue" v0090; "No, because you need to *rewrite hc*" v0055 AP2 -- which AP3 compiled). 13 are the
concern named and then dropped with no ground at all. 8 are a convention (the ask's or a neighbour's) read as
satisfied without a check. 6 are v0105, where the reviewer was right. The design's §3.2 rules none of these
inadmissible; its rank 1 ("a failed check ... becomes a question") does not fire on them because no check was
run; what would convert them is rank 4's "never silence" -- i.e. a volume rule, not an authority rule.

**K is not one code across batches.** The primary grounds by batch: D12a is plurality/budget/unstated (the
four-times-counted rename); D12b siblings/technical; P14val_a worth (11 of 24) and refutation (6); P14val_b
brief/satisfied/worth; D12c has 3 K rows in 90 (its reader coded the same "consistent with the file" clearing
as `C` or `O`, see §1). The grounds vary with the reader as much as with the sessions.

**Adjacent concerns coded K.** d0008/d0009 AP2 and AP3 (4 rows) name "add simp lemmas" / "unfold by hand",
not `grind`; v0053/v0056 AP3 and v0062/v0063 AP1 (4 rows) cite a *neighbouring* convention as satisfied. Under
the protocol's letter ("names the ask's concern or convention") these are `C` or `O`; 8 rows.

## 3. The never-reached count: 24 or 32?

Recomputed from the one reviewer table's `unblinded.json` (`review-mechanics/` scripts; matcher 1 unless
said) and from `asks_all.tsv`:

| definition | P14 (46) | D12 (47) | total |
|---|---|---|---|
| `asks_all.tsv`, every column 0 (DX, AP, X, T, TA, OP, GPT; m1) -- the draft's 24 | 12 | 12 | **24** |
| ask-free rows as the assessment defines them (X, T, OP, GPT, DX, AP; TA excluded), `match_D12` seal | 17 | 12 | 29 |
| same, with the dev-pair seal `match_D12b` for D12 (T and TA present; X/OP/DX/AP re-matched) -- the assessment's 17 + 15 | 17 | 15 | **32** |
| matcher 2 instead of matcher 1 | 19 | 12 / 16 (D12 / D12b) | 31 / 35 |

So the two numbers differ for two reasons, neither stated in the draft:

1. **TA.** The draft's 24 counts Opus + AP (`TA1`) as a reacher; the assessment excludes it from "ask-free"
   (its §6 lists the rows). On P14 five asks are reached by TA1 alone -- p0003 (`HasProd` twin), v0060/v0061
   (`variable ... in`), v0067 (`positivity`), v0068 (`gcongr`) -- and they drop out of the never-reached set
   when TA counts. Whether TA is ask-free on P14 is a judgement the draft has to make explicitly: the AP
   selector was developed on the P14 ten PRs (the table's README: "AP's P14 gain is its discovery sample").
2. **Which D12 seal.** `match_D12` (13 sessions) and `match_D12b` (15 sessions, the dev pair) are two matcher
   passes over overlapping sessions. Between them, d0022/d0023/d0025/d0027 (the one `Dense.ciSup` rename
   counted four times) are reached by X/OP in `match_D12` and by nobody in `match_D12b`, and d0048 the
   reverse. That is five of 47 asks flipping on the never-reached criterion between two matcher passes --
   the matcher noise the draft's §7 mentions in the abstract, here measured on the very set §6 sets a bar on.

Also: `prepare.py`'s `hits("T")` counts every label starting with `T`, so the `T` column of `asks_all.tsv`
is T1 + TA1 (e.g. v0062: T 2, TA 1, but T1 reached it once). The never-reached count is unaffected (TA is
its own column), but anyone reading the T column reads TA twice.

**Which is right for §5 and §6.** Neither as written. §6 sets a bar ("R reaches >= 6 of the 24") on a set
whose membership moves by 5 asks with the TA decision and by 5 more with the seal. The draft should (a) say
whether TA counts and why; (b) take the asks never reached under *both* D12 seals and both matchers as the
hard core (`d0002 d0003 d0004 d0008 d0009 d0018 d0029 d0038 d0045 d0049 d0051` on D12, 11; and on P14 the 12
under TA-counts, 17 without), and report the bar on that core with the soft members listed; (c) note that the
"4 of 93 are one rename counted four times" (its own §8) sits exactly on this boundary.

## 4. The knowledge column: modal code, DX vs AP, demand vs none

`recompute.py` lists every ask whose knowledge code differs across rows or between conditions: 13 of 93.
Within a condition the readers almost always wrote one code for all three rows (3 asks differ: d0035,
v0062, v0063); the variation is **between DX and AP**, on 11 asks -- which contradicts the draft's §1.2
sentence "The AP section changed no knowledge column in any batch" and its own aggregate table (DX demand 14,
AP demand 7; DX mechanism 6, AP 5; AP construction 2).

The ten asks examined, with what the code change means:

| ask | DX | AP | what happened |
|---|---|---|---|
| d0038 | demand | none | the sentence (P108) was held and considered-dropped by all three AP sessions; the reader re-coded `none` because "the sentence was held" |
| v0030 | demand | none | held: used 1, considered-dropped 2; same re-coding |
| v0062 / v0063 | demand (DX2, DX3), none (DX1) | none | DX1, who *verified the old proofs compile* and dropped on a guess, is `none`; DX2/DX3, who called the restyle "style", are `demand`: the knowledge code tracks the row's behaviour, not the ask |
| v0067 | demand | none | AP: the sentence was *absent*, but two AP sessions named `positivity` anyway, so the reader wrote `none` |
| d0049 | none | demand | held and **ignored** 3/3; the D12c reader coded `demand` on AP although the sentence was delivered |
| d0007 | none | demand | out of census (`ap` = n/a) yet the reader says a heavy-imports sentence was in the section and unused: `demand` on AP |
| p0012 | none | demand | P113 absent; a *neighbouring* prime convention was delivered and licensed the miss: `demand` means "the wrong sentence was delivered" |
| v0060 / v0061 | mechanism | none | AP2 derived the maintainer's exact form from the held bullet and dropped it as "overly pedantic": the reader's own verdict is that "the word would not have been enough", yet DX keeps `mechanism` |
| v0093 | none | mechanism | DX sessions never asked the question (`C`); AP sessions asked and built the wrong one-liner: `mechanism` is assigned only to the condition that got far enough to need it |
| d0035 | none | none (2), construction (1) | one AP row is `construction` because that session compiled a (wrong) candidate |

So `demand` has three meanings across the six readers: (i) the sentence was not delivered (D12a, D12b,
P14val_a, P14val_b); (ii) it was delivered and ignored (D12c); (iii) a neighbouring sentence was delivered and
misapplied (P14post). And `demand` against `none` on the DX side is not separable from the behaviour code:
v0106-v0108 DX1/DX3 ("`[Infinite β]` would be idiomatic ... Meh. Not a finding") are `demand`; v0094/v0095 DX3
("a real style point but minor") and d0035 DX2 ("Not worth it") are `none`; v0060 DX2 ("the maintainer might
ask to hoist ... Minor style") is `mechanism`. Same behaviour, three codes, three readers.

**Is "15 of 66 need a fact" robust?** The 15 are mechanism d0018, d0008, d0009, d0002, v0060, v0061; direction
d0045, d0046, d0003, p0006, v0090, v0091; api d0013, p0010; construction d0051. Of these: d0046 was reached by
DX 2 of 3 (the "miss" is DX3's partial, so the modal rule over non-reached rows reports a fact most sessions
had); d0013 was reached by DX1 and the DX2/DX3 partials found a *larger* existing golf (the reader: "four
sessions found it by searching the API"); v0060/v0061 the reader herself discounts; v0090 DX1 wrote "Could be
simplified to just `by grind` ... Not worth"; p0010 the reader calls "contested". A strict reading (no session
had the fact, and having it decides) leaves about 9 (d0018, d0008, d0009, d0002, d0045, d0003, p0006, v0091,
d0051); a loose one that adds v0093's AP-side idiom and d0016's layout rule (which the D12b reader called
"knowledge" and coded `demand`) gives about 17. The draft's direction ("only rarely for want of a fact")
survives; the number 15 is a reader artefact at +-4, and §5's "what it does not reach: the 15 asks" should
not be stated to the ask.

Two further codes are not knowledge codes in the readers' use: `unclear` (6 rows, all v0105) means "the ask
is a question whose true answer is no", a gold defect the draft's §8 already records; `pr_context` (12 rows,
v0053/v0056) sits on rows whose *behaviour* ground is the brief's form, so the same rows are counted once under
"needs PR history" and once under "dropped on a form rule".

## 5. §5's predictions recomputed

From the six jsonl files (`recompute.py`):

| claim in the draft | recomputed | status |
|---|---|---|
| 1 of 558 rows not attended | 1 (d0039 DX1) | holds |
| DX 184 non-reached rows: 81 K+V, 65 C, 17 O | 64+17 = 81; C 65; O 17 | holds |
| "15 of 66 asks need a fact" (mechanism 6, direction 6, api 2, construction 1) | 15 by the modal rule | holds arithmetically; see §4 for what the modal rule hides |
| 105 K rows, 35 V rows | 105 (on 44 asks), 35 | holds |
| 63 of 105 K rows on inadmissible grounds, on 32 asks | **not recomputable**: the keyword regex is not on disk (not in the draft commit, the aggregate, or any scratchpad); by hand 64 rows on **37** asks, with a different composition (§2) | changes a number |
| 34 of the 105 K rows are on asks some other session reached | 34 with "reached" = a DX/AP session's behaviour code; 61 if any of the table's rows counts | holds under one reading; ambiguous |
| on the 24 never-reached asks, 44 K rows, 34 O, 29 C, 24 V, 13 P | 44 / 34 / 29 / 24 / 13 (= 144) | holds, on the 24-set (§3) |
| 24 never-reached by knowledge: none 7, direction 5, mechanism 4, demand 3, pr_context 2, construction 1, api 1, unclear 1 | same | holds |
| 24 never-reached by family: naming 5, statement/API 4, proof 4, PR-level 3, two each derive/generality/registration | F8 5, F1 4, F6 4, F12 3, F7 2, F3 2, F4 2, **F10 1, F5 1** | cosmetic: two asks (d0004, d0002) left out of the list; 22 != 24 |
| 21 of 35 V rows on a failed check or a lower authority | not recomputable (regex) | -- |
| 102 C rows, 16 F6, 16 F2 | 102; F6 16; F2 16 | holds |
| held and ignored 45 (§1.4 and §5) | **46** (aggregate §3: 2+9+2+0+21+12) | cosmetic |
| held, considered, dropped 39, 20 of them K | 39; K 20 | holds |
| used and reached 87 | 87 | holds |
| held asks: AP > DX at 14, < at 4, = at 41 | 14 / 4 / 41 under all three rules ("reached" = behaviour code, = m1, = both matchers): the split rows (v0065, v0066) are not on held asks | holds |
| F2 0 -> 11 of 24; F6 0 and 0 of 18, every held sentence ignored; F8 22 and 19 of 60 | F2 0/11; F6 0/0, held rows 6 all ignored; F8 22/19 | holds |
| §1.2 "the AP section changed no knowledge column in any batch" | **11 asks** change modal code between DX and AP (d0007, d0038, d0049, p0012, v0030, v0055, v0060, v0061, v0062, v0063, v0067, v0093); the aggregate's own table has demand 14 -> 7 | contradicts the aggregate; see §4 |

**Which are predictions and which are definitions.** Every row above is a count of the reading, not a
prediction: the draft's §5 bullets restate the classification (a K row *on an inadmissible ground* "would be
filed" is true by the design's definition of the ground, not a forecast of what the model does under a
prompt). The only statements that can fail are §6's bars (R >= 6 on the never-reached set; R >= 16 of 32 on
the inadmissible-ground asks), and both sit on sets whose membership this review moves (24 -> 29/32; 32 -> 37).
One further point the draft's §3.2 makes but §5 does not carry: rank 4 says the reviewer's own judgement
outputs "a finding or a question with its reasons, never silence". Under that rule *every* K row (105), not
63, and every C row (102) becomes a disposition; the inadmissible-grounds list is not what does the work, the
no-silence rule is. §5's "63 would be filed" understates the volume the design itself mandates.

## 6. prepare.py / aggregate.py joins

Checked (`joins.py`), all 26 PRs x 6 DeepSeek sessions:

- **R-to-session mapping.** For every DX/AP session the packet's `findings_as_matched` (the `R_pr<pr>.json`
  the matcher saw) has the same count and texts as the transcript's own `submit_findings` call, with four
  exceptions below. The seal-to-run join is right. P14_val's AP sessions come from two runs (`ap_rep*` for six
  PRs, `apt_rep*` for 26755 and 36822); each PR exists in exactly one, and the matched list equals that
  transcript's submission, so the fallback picked the judged session.
- **Finding index** is 0-based and in range for all 1,180 matched findings.
- **AP section extraction** returns the identical text for AP1/AP2/AP3 of every PR (25 conventions each; 22
  on 33305), so reading only AP1's is safe.
- **Two sessions were matched on a truncated list.** On 33149, AP1 submitted 22 findings and AP2 24; the
  matcher saw 20 of each. The missing ones are the file-placement finding and, for AP2, two unused-hypothesis
  findings; the AI-disclosure finding (d0032) is in both matched lists at index 19, so d0032's "AP 3 of 3" is
  not affected, but the two sessions' recall on anything the dropped findings would have reached is a floor.
  The cap is the harness's 20-finding cap (`task_result.json` holds 20; the table's README line 161 records
  33149 hitting it under AP), and it is not the first 20: AP1's dropped findings are its 19th and 21st.
- **The matcher did not see the submissions verbatim**: on 33285 DX1 and 43192 DX1 a finding's "convention"
  reads "practice" in the matched text (the table's harness-blinding scrub). By design; no effect here.
- **`hits("T")` in `prepare.py` counts TA1 under T** (prefix match). See §3.
- **The readers' "reached" code is not one rule.** 202 rows are (reached, reached); 5 rows coded `reached` have
  m2 = partial (v0065 DX2; v0066 DX1, DX2, DX3, AP1 -- all P14val_b), 2 rows coded `P` have m2 = reached, and
  one `K` row (d0033 AP2) has both matchers at `partial`, which the protocol says is `P`. The D12b reader
  wrote "reached = both matchers reached"; P14val_b took m1. `aggregate.py` §3a counts hits by the behaviour
  code; the held-asks table happens not to move under either rule (v0065/v0066 are not held asks), but §1.1's
  row counts do (5 rows move from `reached` to `partial` under the D12b rule).
- `aggregate.py`'s modal knowledge code breaks ties by first-seen row; no tie occurs in the data, so nothing
  depends on it now, but a re-run with one changed row could.

