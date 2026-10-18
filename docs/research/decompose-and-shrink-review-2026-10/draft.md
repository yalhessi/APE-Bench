# Draft under review (2026-10-09): decompose the PR, shrink the conventions per part, review the parts concurrently

## The user's direction, verbatim

2026-10-09, after the conventions results were walked through:

> "Clearly, choosing conventions without the asks is the most important question to address at this point."

> "We shouldn't jump into making any decisions or changes to the code yet. We should ideate and try to take in the full picture of the problem at the moment. It's worth remembering that we learned the conventions (in an adhoc way that we need to go back to and make more robust). In this reviewer, if being told which exact convention to follow gives us a clear advantage, we would be willing to tell the model to follow a number of conventions. We don't have to get the correct convention in top-1. It may be the case that identifying 5-10 conventions give us sufficiently good results if we can scrutinze other findings. It's seems like either way, it's useful to have a way to quickly and soundly shrink the number of conventions we are considering at a specific point. For example, conventions about proofs, etc. Or this may also be a good point to explore conventions about correctness, conventions about conciseness, etc. This does bring us back to decomposing the review problem into multiple review subproblems, which hasn't been tested with Opus or DS. I guess the point here is it's clear we don't have to consider all 400 conventions at a given point, we can use syntacic information to shrink that number significantly. I'm not sure how much we can push the idea of shrinking the conventions (even using cheaper semantic model calls) and then firing concnurrent reviews with the remanining conventions"

> "A clear issue at the moment is that moving from the solo reviewer to shrinking conventions means going back to workunits that have a focus, which means it's critical to come up with a way to enumerate workunits to cover all the work associated with a PR. So question 1) how do we decompose the entire PR into parts such that we can focus on only a subset of conventions in each part 2) can we choose a correct subset given a partial PR"

## The idea, as sketched (to be attacked, not built)

1. **Decompose** each PR into parts: work units such as a declaration, a family of declarations, a proof, the imports, the docs, the PR as a whole. Together they must cover all the review work in the PR.
2. **Shrink** the census's ~400 conventions per part:
   - by syntax: what changed, which Lean constructs, the area;
   - by groupings: family (proof, statement/API, naming, docs, PR-level...) or rationale (conciseness, consistency, discoverability, correctness...);
   - then by a cheap semantic model call or retrieval from census examples;
   - down to about 5-10 conventions per part.
3. **Review** each part concurrently, with its 5-10 conventions delivered as DP delivers (two maintainer examples each, plus the precedence paragraph).
4. **Scrutinise** the filings that are not maintainer asks afterwards. Validity (is the departure real, does the fix compile) can be checked; demand (would a maintainer raise it) is not yet predictable.
5. **Make the census robust for this use.** Today an entry is a sentence with rationale and form. This use needs each entry's situation: where it applies, syntactically and semantically.

## Facts in hand (verify what you rely on)

- **Probe results** (39 in-census asks on 14 PRs, stage L/D sets; per-session reach):
  - Unbriefed: Claude 0.46-0.49; DeepSeek 0.22 (three reps).
  - Exact conventions (built from the PR's own asks, 1-5 a PR, all true): Claude 0.74, DeepSeek 0.44, gpt-5.5 +0.22.
  - DP (exact + two census examples each + precedence): DeepSeek 0.64 over three reps.
  - Disposition paragraph on exact, gpt-5.5 (stage W): 0.43 → 0.62.
- **Ask-free deliveries:**
  - Stage F: 25 picked from the diff by a blind Opus selector, sentences only, on Claude: +0.03. The right entry was in the 25 for 22 of 33 asks, in the first 10 for 15, in the first 5 for 6.
  - Stage G: pinpointed rules, half decoys, verify-and-drop lead, on Claude: +0.00. The right convention was at the right place for 21 asks, and it was verified and overridden.
  - Detectors: 0-1 of 13 alone; under the disposition paragraph 5 of 13, with 13 of 14 unasked facts filed.
  - Stage H: maintainers raise a convention at 1 in 20 to 1 in 400 of the places it applies; models predict which places get raised at AUC 0.56-0.64.
- **The ladder** (2026-10-08, one turn at the ask's own place, DeepSeek, unmatched, provisional unblinded look):
  - At the place, the bare sentence writes the maintainer's change for 6 of DP's 7 gains.
  - DP's examples sometimes made the model judge "conforms" where the bare sentence said "departs".
  - At asked places, the bare sentence said "departs" in 93 of 117 answers. No unasked place was tested.
- **The census:** 1,833 val1000 asks, ~400 principles, not saturated (one new per ten asks).
  - Coverage: top 10 = 22% of asks, top 50 = 55%, 286 entries with three asks or fewer.
  - Families: proof 406 asks / 89 entries; statement/API 264 / 92; formatting 220 / 65; naming 169 / 36; docs 155 / 64; PR-level 122 / 38; registration 80 / 28; redundancy 80 / 25; generality 70 / 14; interface 61 / 24; derive 19 / 8; meta-code 15 / 12.
  - Rationales by asks: readability 488, consistency 475, compactness 466, discoverability 427, maintainability 416, generality 133, process 128, automation 121, performance 63, mathematics 35, correctness 34.
  - Form: rule 841 / standard 828.
  - About 45% of asks carry a suggestion block.
- **Work-unit record:**
  - `docs/plans/2026-09-23-work-enumeration.md` set out to enumerate maintainer questions from the corpus, ask each at every place it applies, and force a verdict per target, with no generalist and no lead. It ran on gpt-5.2 with reasoning off; its corpus-derived question list was never built. The census is that list now.
  - On the held-out 12, 91% of obligations were located by the pipeline and 57% correctly asked; 8 of the 10 never hit were located and asked about the wrong thing.
  - Forcing verdicts took the arms from 0.20 to 0.50 (one rep). Solo owned naming, scope and generalisation, "judgements that need the whole file".
  - `docs/todo/batching-work-units.md`: units are built from change targets and packed. After the repack, 3 of 42 anchored obligations span more than one unit and 32 of 38 request groups sit wholly inside one. For 12 of the 15 multi-declaration asks, the arm sees every target and still cannot say them together (coordinated emission).
  - On validation, 15 of 107 round-1 asks (14%) are PR-grain.
  - The specialist arms and the family division were tested on gpt-5.2, mostly with reasoning off and on defective tools; never on Opus or DeepSeek with convention-scoped sub-reviews.
