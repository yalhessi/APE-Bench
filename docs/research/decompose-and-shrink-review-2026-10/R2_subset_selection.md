# R2 — Q2, subset selection from a partial PR (final report as returned, markdown layout normalised; 134k subagent tokens, 53 tool calls, 7.8 min)

**1. Verdict.** Syntax shrinks the census, but neither to 5-10 nor soundly. Part kind (proof / declaration statement / docs / commands / imports / PR) cuts ~400 entries to 134 (proof parts) or 234 (declaration parts), and leaks: 19-25% of asks fall outside their entry's usual part kind. Getting to 5-10 is a ranking problem, and every cheap ranker on disk is weak: part-conditioned frequency puts the right entry in the top 10 for 0.36 of asks (census, leave-PR-out) and 0.22 (other years); lexical retrieval 0.26; the best on record is stage F's Opus selector, 0.45 at 10, per PR. A third to a half of asks depend on information outside the part, so a part-local selector cannot pick them at all. And "sound plus 5-10" contradicts itself: a sound filter keeps every convention whose situation occurs (tens of entries); cutting to 5-10 means predicting demand, which failed (stage H, AUC 0.56-0.64).

**2. Objections to step 2, ranked**

1. **"Sound" and "5-10" are incompatible.** In stage G only 52 rules fired 19.6 times per PR on average (5-30), up to 20 rules at one place, a mean of 1.4-7.5 per place (read); maintainers raise 1 in 20 to 1 in 400 of flagged places (read). Over all 438 entries a sound set per part is likely 10-50 (inferred). *Refuted if* a blind "does the situation occur?" pass over all 438 at real parts returns ≤ 10 per part and keeps the asked entry.
2. **Part kind is a weak, leaky filter** (computed from reader A's 1,669 principled val1000 asks joined to hunks and `situated_asks.json`; the classifier is my heuristic). Entries ever seen per part kind: proof 134, declaration (non-proof) 234, PR 94, docs 65, commands 40, imports 6. Of the 41 entries with ≥ 10 asks, only 8 have ≥ 90% of their asks in one part kind; maintainers often anchor a whole-declaration ask on the header line. On the 39 probe asks a filter learnt from census occurrence drops the right entry outright for 8 (some may be my classifier's errors). *Refuted if* a better part labeller (enclosing declaration plus elaboration) brings leakage under 5%.
3. **A third to a half of asks need context outside the part.** The facet pilot (155 asks, one reader, reweighted by family): references to a specific library declaration 8%, siblings 4%, module graph 3%, process 12%, author intent 6.5% — 33% (read). My reading of the 39 probe asks: 18 need siblings, the file, the old version or the PR's purpose (P100, P254, P201, P048, P105, P098, P369, P329, P041, P185) (inferred); 5 of DP's 7 gains on DeepSeek are among them (p0000, p0007, v0029, v0062, v0063). PR-grain asks are 12% overall but 21% on AI-generated PRs (48 of 233), the eventual target. *Refuted if* parts carry sibling, file, old-version and PR context and the selector still ranks these entries well.
4. **Family and rationale groupings are not sound.** Proof parts: proof-family entries hold 67% of their asks, the top two families 80%; declaration parts: the top two families hold only 44%. Rationale says why a convention exists, not where it applies; "correctness" covers 34 asks (2%); "consistency" (475 asks) is by definition about something outside the part.
5. **Retrieval was not what made the exact brief work.** Stage F: with the right entry in the brief for 22 asks, Claude reached 12; stage G: right rule at the right place verified and overridden (9 of 21, the unbriefed level) (read). A better shrink addresses the stage that already worked well enough.

**3. Best answer to Q2**

(a) **Decompose with context.** Each part carries its before/after code, its sibling and neighbouring declaration names, the file's `variable`/section context, and the PR text. One PR-level part holds the 94 PR-grain entries, rankable from the PR's text.

(b) **Hard syntactic gates only for token-triggered entries** — imports, `theorem`, `variable`/section, attributes, `@`/named arguments, primes in names, docstring prose: about 40 entries confined to one part kind. Of stage G's 52 triggers I read 32 as decidable from the part's text, 11 as needing a file, library or sibling lookup, 4 as semantic within the part, 5 as PR-level. Elsewhere part kind is a ranking feature, never a filter.

(c) **A model ranks per part over all 438**, each with trigger / applies_to / not_when fields (stage G wrote them for 52; all 438 would need them), selecting on situation, not conformance. Expected recall@10:

| ranker | recall@10 | status |
|---|---|---|
| part-conditioned frequency | 0.36 val1000, 0.22 other years | computed |
| family known in advance (oracle) | 0.55 | computed |
| stage F, Opus per PR | 0.45 at 10, 0.67 at 25 | read |
| stage G, right rule guaranteed in a 52-pool | 0.85 in a candidate, 0.64 at the place | read |
| per-part model ranker, all 438 | 0.5-0.65 at 10, 0.7-0.8 at 25 | inferred, untested |

(d) **The ceiling.** 14% of principled asks sit under an entry seen on no other PR; 8.9% of asks have no principle; on other years 15% of principled asks fall under entries absent from val1000; the census is not saturated (one ask in ten brings a new principle). So the shrink's recall over all asks is at most about 0.75. **It cannot select:** library-scope against file-scope choices (30458); migrations in progress (32875's `grind`); "keep the old proof" (minimal diff); PR theme (more golf on a golf PR); reviewer preference (one maintainer wrote 30 of dev's 52 round-1 comments).

**4. Reject outright**
- Family or rationale as a filter (§2.4).
- Lexical or kNN retrieval over census hunks: computed 0.16-0.26 at 10, below the frequency prior; consistent with "Facet-keyed review join" (facets fit 4-8%) and "Surface proxies"; Mode A's dense retrieval found precedents (hit@5 49%) but priming did not move recall (13 vs 11).
- A demand cut ("would a maintainer raise it here") as the 5-10 criterion: stage H (AUC 0.56-0.64) and artifact-only selectors (0.62); no new run without a new signal (the reviewer, the PR's theme, the file's regularity).
- A fixed common list: the top 50 hold the entry of 16 of 33 probe asks, and the gains sat in the tail.

**5. Cheapest settling measurement: an offline selection bench, no review run.** *Units:* the other-years held-out set, 248 principled asks reader A labelled (entries not written from val1000 asks; exclude or count as misses the asks under the 29 entries those batches created), plus the 39 probe asks; report the AI-generated stratum separately. *Input:* the part (enclosing declaration, before/after), the PR text and diff, the 438 sentences (with situation fields if written). *Output:* a ranked top 10, plus the count the selector judges "applies" at that part (the size of a sound set). *Baselines (computed, free):* frequency 0.22 at 10 on other years, 10 of 39 on the probe asks; stage F 0.45 at 10. **Threshold, fixed now:** recall@10 ≥ 0.60 on the 287 units (~±6pp) → Q2 answered yes, a review run on step 3 justified; ≤ 0.45 → per-part selection does not beat a per-PR selector, step 2 is retrieval-limited, step 3 not run; between → partial. *Also read:* the median "applies" count per part; over 15 rules out a sound 5-10. *Cost:* ~290 single-turn calls at ~20-25k tokens (~7M processed), 1-2 h of DeepSeek on `first`, $0; on Claude about a third of a five-hour window on the user's account, which needs the user's go-ahead.

**Unproven:** whether 10 ranked entries per part under DP's precedence recover DP's gain; only a review run answers that, after this bench passes.

Read-only; scripts in the R2 scratch directory; nothing committed.
