# Second adversarial review: the stated-grounds reading (2026-10-16)

Under review: `results/pr_review_v5/probes/stated-grounds-2026-10-16/` (PROTOCOL.md, RESULTS.md, `select.py`,
`selected.jsonl`, `readings/`, `score.py`), committed as `6d703ea9`, which read the user's picture (maintainers
reason from evidence and a short set of values; taste is a small residual) as **SUPPORTED** by the
pre-registered rule: preference + authority 24% (line: a third), principle 27% (line: a tenth), principle +
scope's form + currency + fact 73% (line: two thirds), on 246 agreed grounds out of 318 selected asks.

Everything below was computed for this review from the committed readings, the census labels and codebook
(`results/pr_review_v5/adjudications/conventions-census-v1/reader_A/`), and the ask bodies rebuilt by
`census/provenance/materialise_bodies.py` into scratch (identical to the bodies the probe used; never
committed). The scripts are scratch-only; every number can be rebuilt from the committed files plus the
rebuilt bodies. Quotations are at most eight words of an ask. No model calls, no spend.

**The reviewer is a Claude model too.** My own readings (40 unselected asks, 30 selected asks) are a third
reading from the same model family as the probe's two readers. They test the coding rules, not the model's
bias; a human or another family is still needed for that (§3).

| attack | what it finds | changes the verdict? |
|---|---|---|
| 1. `fact` on the picture's side | With `fact` neutral, preference + authority is **35.1%** (bootstrap 95%: 28-43%), above the one-third falsifier, for both readers and on agreed items | **Yes**: from supported to "at the falsifier line" |
| 2. Selection | The 17% selected are long, first-person, explanatory asks. Reading 40 unselected asks: 11 state a ground the markers missed, mostly scope's form. 6 are bare golfs, 14 bare convention enforcement | Narrows what the result covers. It does not hide a large mass of taste |
| 3. Coding | κ 0.91, but the two readers are near-duplicates. They quote the identical phrase in 68% of notes, and their notes share 60% of tokens against 2% when paired at random. My reading agrees on 25 of 30, and 4 of the 5 changes move toward the rival. The category boundaries follow wording, not content | Adds 2-5 points to the rival share. The boundaries matter more than the agreement suggests |
| 4. The principle category | Readability is coded principle or preference by the grammar of the sentence. 8 of 19 generality grounds restate the ask. The scope layer is mostly "the library" | Moves the shares by 3-8 points. "Scope layer appears" is not supported |
| 5. What it says about amendment 1 | It speaks to the content of stated reasons only. It is silent on the attention rival, scope dependence and the 63% of asks with no ground. The "hedging 28%" contradiction is mostly politeness | Limits the claim's altitude |

---

## 1. Does `fact` belong on the picture's side?

**The argument.** The rule counts `fact` toward the picture. But the rival named in PROTOCOL.md (preference and
authority, behind it the amendment's demand-and-attention picture) also predicts facts. A maintainer who
decides by taste still writes "this already exists", "this doesn't compile" and "`simp` can do it". Facts
come with asks that are not discretionary (a wrong docstring, a duplicate PR). They are also cited
selectively for a form already chosen: the premise review (§1.2) found scope cited "where it agrees". A
category that both pictures predict at a similar rate does not separate them. Counting it for one side moves
the picture's share from 61% to 73%.

**Re-scored with `fact` neutral (dropped from the denominator), registered lines otherwise unchanged:**

| | denominator | preference + authority | principle | principle + scope + currency | rule |
|---|---|---|---|---|---|
| reader A | 182 | 35.7% | 37.4% | 58.8% | CONTRADICTED (≥ 1/3) |
| reader B | 187 | 34.2% | 41.2% | 61.0% | CONTRADICTED |
| both agree | 168 | **35.1%** (95% 28.0-42.9%) | 39.9% | 60.7% | CONTRADICTED |
| registered, both agree | 246 | 24.0% (95% 18.7-29.3%) | 27.2% | 73.2% | SUPPORTED |

The marginals stay even under the re-score: head 34%, tail 36%, AI-authored 35%, other PRs 35%. So the
result is stable, and it sits on the line. Reweighting by reviewer, so that each reviewer counts by their
share of all 1,833 asks, gives 25.1% registered and 36.3% fact-neutral. The reviewer skew in §2 does not
drive it.

**Is "neutral" fair to the picture?** Partly not. The 78 agreed facts are of two kinds by my reading of the
notes:
- **26 correctness or mechanical facts** (a counterexample, a typo, it does not render or parse, a duplicate PR,
  the CI import, a wrong deprecation target). Every reviewer would ask for these. They are neutral.
- **49 design facts** ("an existing lemma does this", "inference already finds it", "the hypothesis is
  redundant"). The user's picture can claim these: the concern already has a design, so it should not get a
  second one.
- **3 worth judgements** coded `fact` (v0199, "of limited value since we are coercing"; v1185; v0394). The
  protocol's own definition puts worth under `preference`.

With the correctness facts neutral and the design facts kept for the picture, the registered rule gives
26.8% / 70.0%: supported. With the 8 first-person readability items (§4) recoded as preference as well, it
gives 30.5% / 66.4%: mixed. Even this middle scoring is a few items from either line.

**A fair rival-side category.** The rival has two parts, and neither is `authority` as coded:
- **Discretion.** First-person taste plus worth and cost: "not worth it", "I'm not convinced we need", and
  review bandwidth (v2181, "extremely tiny potential upside"; v2169). A ruling by a person or a Zulip thread
  belongs here (v0946, v0192, v1623, v0609).
- **Attention**, meaning which place gets an ask. No ground category can show it (§5).

Citations of a codified document (style guide, naming page, library note, linter: 9 of the 19 `authority`
items, plus v1329's "we track `erw` uses as technical debt") are the picture's "a decision made once,
reused". The 5 AI-disclosure policy asks are process asks, not reasons about code, and are neutral.

Scored that way, with discretion as the rival, codified documents for the picture, facts and policy asks
neutral, and design facts neutral, the shares are rival 31.3%, picture 68.7% (n 163). That is supported, by
under two points on each line. Moving the 8 first-person readability items to preference gives 36.2%:
contradicted.

**Sensitivity over every combination of the contested choices.** The choices are:
- fact: picture or neutral;
- codified-document authority: as coded, picture, or with library-rule scope items also rival;
- AI policy: rival or excluded;
- readability: as coded, first-person to preference, or all to preference;
- cost: `other` or rival.

That gives 72 scorings:
- fact on the picture's side: rival 19-33%, picture 66-78%; **34 of 36 SUPPORTED**, 2 mixed.
- fact neutral: rival 28-48%, picture 50-68%; **30 of 36 CONTRADICTED**, 4 mixed, 2 supported.

**Verdict on this attack.** The SUPPORTED verdict is produced by where `fact` is counted. It is not produced
by the balance of values against taste. Under defensible scorings the rival share centres near the one-third
line.

**Smallest fix.** A dated amendment to RESULTS.md that reports the fact-neutral score and the
correctness/design split beside the registered one. It should restate the conclusion as "mixed at the
registered lines" and add one sentence: the rule placed `fact` before anyone asked whether the rival predicts
facts. No new reading is needed.

---

## 2. Selection: are the 83% different?

**How the selected 318 differ from the 1,515 unselected asks:**

| | selected | unselected |
|---|---|---|
| median words outside code | 26 | 7 |
| 12 words or fewer | 22% | 66% |
| bare suggestion block (≤ 3 words of prose) | 0.9% | 36.0% |
| any first-person pronoun | 54% | 20% |
| hedge words (premise review's list, preference-marker words removed) | 46% | 22% |
| phrased as a question | 35% | 32% |
| AI-authored PR | 17.6% | 13.3% |
| census entry in the head (top 50) | 44% | 50% |

- **Selection rate by the convention's rationale tag:** compactness 11%, automation 14%, readability 16%,
  consistency 16%, discoverability 22%, maintainability 24%, generality 24%, process 26%, correctness 26%,
  mathematics 40%. Golfs and convention asks are under-selected. Mathematical content and generality asks are
  over-selected.
- **Selection rate by census rank:** ranks 1-100 15-16%; past rank 100 25%.
- **Selection rate by reviewer** (27 reviewers with 20 or more asks): 4% to 47%. j-loreaux 46 of 141 (33%);
  YaelDillies 6 of 107 (6%; P014's main reviewer); erdOne 10 of 109 (9%). Reweighting by reviewer barely
  moves the shares (§1), but it cannot correct selection within a reviewer, who explains the asks that need
  explaining.
- **The markers' false positives are not even.** 49 of 318 are `none` on both readers (15%). For the currency
  marker it is 18 of 37 (49%), so the currency count (7) rests on a noisy door.

**Reading 40 unselected asks** (seeded draw, `random.Random(20261018).sample` over the sorted unselected cids).
Each was coded by me for a ground stated in the text and, where none is stated, for the ground a reader could
reconstruct:

| | n of 40 | cids |
|---|---|---|
| **a ground is stated, the markers missed it** | **11** (95% 16-43%) | |
| — scope's form | 4 | v0667 ("the style of the other"), v0377 ("The usual abbreviation of"), v0210 ("a bit unusual: more standard style"), v1721 ("to match `Pi.map`") |
| — fact | 3 | v0595, v1569, v2136 |
| — principle | 2 | v1001 (the motivating API), v0672 (generality) |
| — preference | 2 | v0823 ("I actually prefer this in the docs"), v1826 (worth, then a golf) |
| implicit: a library convention enforced bare (spacing, docstring form, dot notation, `exact`, binders, naming) | 14 (22-50%) | v0174 v1412 v1552 v0345 v0157 v2280 v2007 v0330 v1684 v1548 v0172 v2114 v0214 v0300 |
| implicit: discretionary golf or alternative, no reconstructible reason beyond the reviewer's choice | 6 (7-29%) | v1678 v1933 v0724 v0635 v2291 v2125 |
| implicit: principle (API completeness, an iff) | 2 | v0781 v1662 |
| implicit: fact / correctness | 2 | v0141 v0287 |
| implicit: authority (title and AI policy) | 1 | v1785 |
| implicit: currency (register with `to_dual`) | 1 | v1501 |
| question for information | 2 | v1889 v0000 |
| unreadable without context | 1 | v0541 |

What this says:
- **The markers miss about as many stated grounds as they find.** About 28% of the unselected state one, so
  census-wide roughly 685 of 1,833 asks (37%, range 28-50%) state a ground, not 17%. About 63% state none.
  The misses lean toward **scope's form** (4 of 11) because the consistency pattern lacks "usual",
  "standard", "to match" and "the style of". Fixing that would raise the picture's share, not lower it.
- **The unselected do not hide a large mass of explicit taste.** Explicit preference is 2 of 40. Bare
  discretionary golfs are 6 of 40. Over the census, taste-like asks (agreed preference plus the unselected
  rate) come to about 19% (11-31%) of all asks. Above all, the unselected are **bare convention enforcement**:
  14 of 40, about 29% of the census (18-42%). Read as text, these can be reasoned instantiation or fiat. A
  bare suggestion that inserts spaces in `h | h` cannot show which.

**Does it change the verdict?** Not toward the rival. It changes the altitude. "Taste is small" holds on the
asks that state a ground, and my 40-ask reading does not contradict it on the rest. But that reading is one
reader on 40 items, and its largest class is undecidable by grounds.

**Smallest fix.**
- Widen the consistency marker to "usual", "standard", "to match", "the style of", "like the other".
- Read a seeded 100 of the unselected with two readers. Use the same codebook plus three codes:
  `implicit_convention`, `discretionary` and `question`. Then state a census-level share.
- Until then, RESULTS should say "of the asks that state a ground (17% by the markers; about a third by a
  40-ask check)".

---

## 3. Coding: is 93% agreement informative?

**The readers are one reader twice.**
- κ on the primary code is 0.912 (observed 0.928, chance 0.178).
- The secondary code is identical in 258 of 318 (81%).
- The scope level is identical in 28 of 28.
- Where both readers quote the ask, they quote **the identical phrase** in 181 of 265 notes (68%).
- Note-token Jaccard is 0.60 for the same item, against 0.02 for items paired at random.
- Agreement falls with confidence: 99% at A's "high", 91% at "medium", 79% at "low" (39 items).

Two runs of one model on one prompt with one packet measure determinism. They do not measure whether the
construct is reliable. The 93% is an upper bound on agreement with any differently-trained reader.

**My reading of 30 agreed items**, seeded and stratified by code (8 principle, of which 5 readability; 5
preference; 5 authority; 5 scope's form; 4 fact; 1 currency; 1 other; 1 none). I agree on **25 of 30**:

| cid | readers | mine | why |
|---|---|---|---|
| v2181 | other | preference (worth/cost) | closes a PR for "extremely tiny potential upside"; the protocol puts worth under preference |
| v0199 | fact | preference (worth) | "of limited value since we are coercing" is a worth judgement resting on a fact |
| v0693 | principle | preference | "I'm not sure if this is more readable", then "opaque to me": first-person readability |
| v1329 | authority | scope's form / principle | "we track `erw` uses as technical debt" is the library's stance, not a ruling |
| v0901 | currency | fact | the ask fixes an alias whose target is itself deprecated; it does not cite a newer form |

Four of the five move toward the rival or out of the picture: two neutral to rival, one picture to rival, one
picture to neutral. One moves rival to picture. That is small at n = 30, but every move comes from a rule the
readers applied by wording:

- **Principle against preference turns on grammar.** "I find this more readable" (v1176) is coded
  preference. "I think things would be more readable" (v1777) and "I like it better because it's more
  readable" (v0542) are coded principle. "would be nicer to read" (v1931) is preference, and "slightly easier
  to read" (v0926) is principle. Within one census convention, P024 (grind only when the explicit proof is
  worse), grunweg's two asks argue readability and are coded principle (v0693, v2295). vihdzp's "I prefer the
  original proofs" (v1297) is coded preference. The code tracks how verbose the maintainer is, not the kind of
  decision.
- **Authority against scope's form turns on whether a document is named.** "Let's follow the style guide"
  (v1162) and "violating the style guide for no reason" (v1859) are authority. "mathlib style prefers spaces
  around slashes" (v0212) and v1373's doubt that "this conforms to the naming convention" are scope's form. That makes
  16 items with one kind of ground (a codified, library-wide rule), split 9 to 7 between the two sides by
  wording.
- **Worth is applied unevenly.** v1168 ("marginally useful … I prefer not to merge") is preference. v2181,
  v0199, v1185 and v0394 (worth or cost) are `other` or `fact`.

**Does it change the verdict?** Recoding the boundary items by content moves the rival share by 2-5 points
either way (§1's grid). With `fact` on the picture's side, that keeps SUPPORTED. With `fact` neutral, it keeps
the result at or above the line.

**Smallest fix.**
- Three boundary rules, stated before any re-read. (a) Readability is principle only when a checkable reason
  is given (rendering, which tactic is transparent, what the reader must remember), whatever the grammatical
  person; otherwise preference. (b) A codified library rule gets one code whether named or paraphrased. (c)
  Worth or cost is preference, as the protocol says.
- Re-read the ~30 boundary cids named here and in §1 with two readers.
- Put a 30-item subset in front of a non-Claude reader or the user.

---

## 4. The principle category

**Counts per ask, not per reader.** RESULTS gives "generality 18, readability 15" and "library 35, file 14,
area 8". `score.py` sums these over **both** readers and exact strings, so they are about double the ask
counts. Normalised over reader A's 67 agreed principle items, the counts are:
- generality 17, readability 12, usability 7, clarity or disambiguation 4;
- discoverability 3, informative naming 3, maintainability 3, automation 2, simplicity 2;
- about 14 singletons (import minimality, type-alias opacity, defeq abuse, name clashes, …).

The top five cover 64% (the codebook's rationale tags: 80%). Scope's form per ask is library 17, file 7,
**area 4**.

**Is readability a principle or a dressed preference?**
- 19 agreed items make a readability claim: 12 coded principle, 7 coded preference.
- Of the 12 coded principle, 8 frame the claim in the first person (v0209, v0693, v2295, v1679, v2089, v1978,
  v1777, v0542).
- Only about 5 of the 19 give a reason for why the form reads better (v0209 rendering in the editor, v0693
  transparent tactics, v1978 what the match ignores, v0542 nothing to remember, v1000 argument order), and
  those 5 fall in both codes.

So as coded, "readability" is mostly a first-person judgement in impersonal grammar. Moving the 8
first-person items to preference gives 27.2% registered (still supported) and 39.9% fact-neutral.

**Is generality a principle or a content request?**
- It is a real library principle; one maintainer states it as Mathlib's aim (v2100, "In Mathlib we aim to
  prove everything").
- As a ground it mostly restates the ask. In 8 of the 19 generality items the stated reason is only that a
  stronger or more general statement holds (v2173, v1449, v2096, v1823, v1288, v1491, v1389, v0484).
- The other 11 add something: duplication, an unused hypothesis, the conclusion matching more, the library's
  aim.

A request for the stronger theorem is what any reviewer, taste-driven or not, would make. So generality
grounds confirm that maintainers ask for mathematical content. They do not separate the pictures. Counting the
8 restatements as `none` gives 24.8% registered and 36.9% fact-neutral.

**Would the user's picture predict this distribution?** In part:
- It predicts named general values, and generality and readability lead.
- It also predicts that stated values mirror the rationales of the conventions being enforced, and they do
  not. Compactness tags 17% of the codebook's conventions and is never stated as a principle; golfs
  arrive as bare suggestion blocks (36% of unselected asks carry three words of prose or fewer) or as
  "nicer". Consistency tags 34% and appears only as 28 scope's-form
  asks. Generality tags 6% and is 25% of stated principles.
- The distribution follows **which asks are contestable**: generality and mathematics asks are selected at 24%
  and 40%, compactness at 11%. "Maintainers explain the asks someone might dispute" predicts it at least as
  well.
- The picture's specific claim, a short list **instantiated by scope**, finds little support. Area-level scope
  is cited in 4 asks of 246 (1.6%), and "the library does X" is one global convention, not a scope-dependent
  one.
- The same convention gets opposite grounds. P014's one stated ground is a principle (v0029, "more robust to
  changes to the `simp` set"). The opposite rule P133 is grounded as scope's form in my unselected sample
  (v0210, "a bit unusual: more standard style"). Principle and scope grounds come with both sides of a
  coexisting contradiction, so a principle-coded ground does not show that the decision was reconstructible.

**Smallest fix.**
- In RESULTS, report per-ask counts, and report generality-as-restatement apart from other principle grounds.
- Replace "The scope layer appears (11%…)" with "scope's form 11%, almost all library-wide; area-level 1.6%".

---

## 5. What the result can and cannot say about the earlier picture

The plan's amendment 1 lists the record's contradictions of the picture. Against each:

- **"Maintainers hedge 28% of asks."** Not addressed by the probe. Computed here: 546 of 1,833 asks (29.8%)
  match the premise-style hedge list. Of these, 448 carry only politeness forms ("I think", "maybe", "could
  you"), and 23 mark the ask as negotiable ("optional", "nit", "feel free", "won't insist"). Explicit
  negotiability is in 41 asks (2.2%). **This weakens the amendment's contradiction:** hedging is mostly
  courtesy and is not evidence of taste.
- **"80% state no ground."** Partly a marker artifact. The 40-ask check puts asks that state a ground at about
  37% (28-50%), so about 63% state none. The probe can say nothing about those 63%. The largest identifiable
  class among them is bare convention enforcement (§2), which grounds cannot classify.
- **"Readers coded 15 of the 41 hardest asks preference or history."** Not contradicted. That is a different
  population (the never-reached asks), and taste is expected to concentrate there. Among stated grounds,
  first-person preference is 16%, about 2.2% of all asks; the two numbers are compatible.
- **"P014 / P133 coexist, separated by reviewer."** The probe cannot test this (1 of P014's 17 asks is
  selected, none of P133's 7). What it does show (§4) is that each side's ground reads as principle or scope.
  So "the ground is a principle" and "two maintainers decide oppositely" are compatible: a principle is what
  a maintainer cites for a choice, which does not make the choice reconstructible.
- **"Scope decides" (area and reviewer collinear).** Not supported by the grounds: area-level scope is 1.6% of
  stated grounds.
- **"A decision at a place" and the demand rival (about 5% of applicable places; about 10% per real departure
  after stage H step 2).** Untouched. A stated ground explains *what* was asked. It cannot explain why this
  place got an ask and its siblings did not. The SUPPORTED verdict should not be read as evidence against the
  attention rival, which was the strongest the round named.
- **Currency.** 7 agreed asks (3%), from a marker whose door is half false positives. This says nothing for
  or against the currency layer beyond the deprecation mechanics already known.

**What it can say:** when a Mathlib maintainer gives a reason, the reason is usually checkable or names a
general value, and first-person taste is a minority (16% of stated grounds; 13-22% under the recodings here).
That is a real and useful result about the content of stated reasons.

**What it cannot say:**
- that taste is small in review overall (63% of asks state no ground);
- that decisions are reconstructible (opposite decisions carry principle grounds);
- that scope is a layer;
- anything about where asks fall.

---

## Smallest fixes, in order of cost

1. **RESULTS amendment, no reading.** Contains the fact-neutral and split scores and the 72-scoring
   sensitivity, and the conclusion restated as "mixed at the registered lines". It corrects the per-ask counts
   (principle names, scope levels), drops "the scope layer appears", and narrows "What it says" to the content
   of stated reasons. Update the `docs/questions.md` line, which now says "supported in every marginal", to
   match.
2. **Boundary rules and a re-read of about 30 cids** (§1, §3), two readers, before any further score. Better, a
   30-item subset read by a non-Claude reader or by the user.
3. **The unselected:** a seeded 100 read with `implicit_convention` / `discretionary` / `question` codes, and a
   widened consistency marker, before any census-level claim about taste.
4. **For the picture itself:** the stated-grounds probe cannot reach its strongest rival. R4 (silence) and the
   stage-H departures reading are the tests that can. The grounds result should not be cited as having
   discharged the attention rival.

## Verdict

**Weakened.** The SUPPORTED verdict comes from counting technical facts on the picture's side. It holds in 34
of 36 scorings that do so, and fails in 30 of 36 that treat facts as neutral. On agreed items with facts
neutral, preference + authority is 35% (28-43%), at the pre-registered falsifier line.

What stands is narrower. **When maintainers state a reason, it is mostly a checkable fact or a named general
value. First-person taste is a minority (about 16% of stated grounds, about 2% of all asks), and, with facts
set aside, taste and authority together are about a third of the discretionary grounds: a mixed result at
the registered lines.**

The result reaches neither the roughly 63% of asks that state no ground nor the scope layer (area-level
grounds 1.6%). It does not test the attention rival.
