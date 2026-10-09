# The places test: does a convention's question, asked at every changed place, pick out where maintainers asked? (pre-registered 2026-10-09, before any call)

## Why this test, and why now

The user (2026-10-09), asked what investigation most moves a deployable reviewer past the solo one:
*"Okay let's start. It would be ideal if we can occupy the GPUs with deepseek runs."*

The ceiling analysis (`docs/research/ceiling-residual-2026-10.md`) puts most of the gap that a
deployable design can address in two places:
- instability across sessions;
- reviewers at the right place asking something else.

Asked alone at the place, one turn each, the convention's bare sentence writes the maintainer's change
for most of those asks (the ladder, `../conventions-ladder-2026-10-08/`, unmatched).

A **per-place engine** asks every convention's question at every place, and its answers are unioned
with the solo review. It removes the session's filing decision by construction. That decision is
where every ask-free delivery so far failed: stage F +0.03, stage G +0.00. The design is
architecture B of `docs/research/decompose-and-shrink-review-2026-10.md`.

Its one unmeasured property is whether the question **discriminates**. At asked places the bare
sentence says "departs" 79% of the time; at places no maintainer asked about, nobody knows. If it says
"departs" everywhere, the engine is a detector, a volume lever, as the detectors were. This test
measures that, and nothing else.

Nothing below has run.

## Units

The 14 probe PRs with in-census asks (stage L/D's two sets). Per PR:
- **The places:**
  - its **changed declaration segments**: each diff hunk split where a line opens a declaration or a
    top-level command, with a docstring or attribute kept with the declaration it leads, and a segment
    kept only if it holds an added or removed line (`places.py`, `segments`);
  - one place for **the PR as a whole**.
- **The conventions at each place:**
  - **exact**: the PR's exact census entries, the ones behind its maintainers' in-census asks
    (`briefs_exact.json`);
  - **decoy**: five of stage F's blind picks for the PR that sit behind no ask on it (seeded,
    `briefs_applicable.json`). Stage F has picks for ten of the 14 PRs.
- **An asked pair** is an (entry, place) where an in-census ask filed under that entry has its
  commented line in that segment (matched by the line's text), or, for a comment on the PR, the PR
  place.
  - 42 asked pairs, among 1,431 pairs in all: 591 exact, 840 decoy.
  - v0016 (a file-level comment with no hunk) is unplaced.
  - The places per PR run from 4 to 43.

## The question

Each prompt is the ladder's head with the place set to the segment:
- the PR's text (`probes.pr_markdown`) and its whole diff;
- the place: the segment's file and lines, or "the pull request as a whole".

Then the ladder's U form, the bare sentence judged, with a confidence line added:

```
VERDICT: departs | conforms
CONFIDENCE: <0-100: how likely it is that the code at this place departs from this convention>
CHANGE: ...
WHY: ...
```

- **The call:** DeepSeek-V4.1-Flash on `first` (`serve_ds41.sbatch` defaults), one turn, no tools,
  `reasoning_effort: high`, `max_tokens` 65536. The ladder lost 66 of 585 answers to its 32768.
- **Samples:** two for exact pairs, one for decoy pairs. That is 2,022 calls, asked pairs first, then
  exact, then decoys, so a run cut short keeps the core.
- **The prompts** are 1.8k-10.4k characters. They are uncommitted (`.gitignore`); `items.json` and
  `prompts.sha256` hold their digests, and `places.py build` rebuilds them.

## Reading rule, fixed before any call (`places.py read`)

**The measures:**
- the "departs" rate (share of samples) over asked, unasked-exact and decoy pairs;
- the AUC of the mean stated confidence, asked pairs against decoy pairs, and asked against
  unasked-exact;
- the capped engine: per PR, every pair ranked by confidence, and the share of the 42 asked pairs in
  the top 5, 10 and 20;
- the volume: projected filings per PR if stage F's 25 picks are asked at every place unscoped
  (decoy rate × places × 25), for orientation only.

**The readings:**

| reading | when |
|---|---|
| **the engine discriminates**: build the deployable version (scoping by M1, stage F's picks or a ranker, one end-to-end run unioned with solo DeepSeek, matched blind) | AUC asked vs decoy ≥ 0.75 **and** (decoy departs rate ≤ 0.10 **or** capped at 10 keeps ≥ 0.50 of asked pairs) |
| **the engine is a detector**: drop this form (a `docs/dead-ends.md` entry), and the residual goes to architecture A's test (DP with decoys, M4) | decoy departs rate ≥ 0.40 **or** AUC asked vs decoy ≤ 0.60 |
| between | read the per-entry table and the segments that drew departs; no build before that |

**Also read:**
- **Asked vs unasked-exact.** The secondary discrimination. It is confounded by design: a convention
  in play on a PR often applies at neighbouring segments too, such as P048's repeated `{D : ℤ}` in
  four signatures, so an unasked-exact "departs" may be a real departure that nobody asked about.
- Per exact entry: the asked against unasked departs rates.
- The asked pairs' departs rate against the ladder's 93 of 117.
- Unparsed and truncated answers per group.

**Matched later, not in the rule.** Whether the asked pairs' `CHANGE` is the maintainer's, by blind
matchers on the primary subscription after its reset. The rule above reads only verdicts and
confidences, which are mechanical.

## Limits, stated before

- **In-sample on the probe set,** and the exact entries were chosen from the asks.
- **Decoys are stage F's picks:** situations the selector thought occur, so they are a hard
  negative, not a random one.
- **Unasked does not mean wrong.** Maintainers raise 1 in 20 to 1 in 400 of the places a convention's
  situation occurs (stage H). This measures how much the engine would file, not how much of that is
  invalid.
- **One turn, no tools,** as in the ladder.
- **Memory:** census merges predate DeepSeek-V4.1's release.

## How it runs, and what it costs

- **The job:** `run_places.sh` is one Slurm job on `first`. It starts the server, runs
  `probe_correct` and `probe_carry`, then `places.py run` with 48 at a time, and releases the node.
- **Time:** at the ladder's rate it is about four to seven hours, inside one server's eight. A cut-off
  resumes on rerun.
- **Money:** $0 for generation. No subscription tokens before the matching above.

## Also read, added during the run (2026-10-09 ~08:40), before any reading

**Why.** Prompted by the code-review systems survey, revisited the same morning
(`docs/research/code-review-systems-survey-2026-09.md`, "Revisited 2026-10-09"): deployed per-rule
checkers manage precision per rule, and use agreement across passes as confidence.

**What had been seen before this was written.** A format check of the first 112 answers, mostly
asked pairs: finish reasons, the presence of a verdict and a confidence, and the counts of verdicts.
No group was compared.

**Neither reading below is part of the rule above.** Both are in-sample, and each is reported as a
bound.

1. **Agreement as confidence.** For exact pairs, the two samples are counted as both, one or neither
   saying `departs`. The asked share is reported in each bucket, beside the stated confidence's AUC.
2. **Per-rule policies, simulated.**
   - A per-entry confidence threshold, set leaving the PR out.
   - The suppression of entries whose non-asked departs rate on the other PRs exceeds 0.5, 0.3 and
     0.1.
   - For each policy: asked pairs kept, and filings per PR.

## Also read, added during the run (2026-10-09 ~09:15), before any reading

These come from the third adversarial round's measurement reviewer
(`docs/research/deployable-reviewer-review-2026-10/`). They are not part of the rule, and they are
read before the rule's verdict is used.

- **Within-PR AUC,** pooled over the PRs that have both asked and decoy pairs. In the record, a
  pooled AUC has been one PR before: 0.749 fell to 0.511 without 33145. Here 32875 holds 9 of the 42
  asked pairs.
- **The leave-one-PR-out range** of the asked-vs-decoy AUC.
- **The AUC on sample 1 only,** for asked and exact pairs alike, because asked pairs average two
  samples and decoys have one.
- **Asked pairs kept on asks that DX misses** (reached in at most 1 of its 3 reps): what the engine
  would add over solo.
- **The cap reading is optimistic,** and this is said whatever it reads. It ranks against 5 decoys a
  PR, where a deployment would rank against 25 picks plus the gates. Three PRs with asked pairs
  (26755, 36822, 43192) have no decoys at all.

## Running note (2026-10-09 ~09:30): an interim verdict count was seen by a reviewer

**What happened.** The third adversarial round's mechanics reviewer read interim rows of
`outputs.jsonl` for throughput. Its report also states an interim unasked-exact `departs` rate of
about 0.29, from rows written before about 09:10. That is a verdict count, though not the
pre-registered asked-against-decoy reading.

**What it means for the reading.** The orchestrating session has not read any group's verdicts. The
rule, its thresholds and the readings declared above were all fixed before the report arrived. The
note is here so the reading can be judged knowing it.

## Result (2026-10-09): by the rule as written, the detector band. The rule's key measure failed; the verdict discriminates moderately, at about 7% precision

**How it ran.**
- **Answers:** all 2,022, 07:44 to 11:16 (`e5d10631`). Four stopped at 65,536 tokens, and six are
  unparsed.
- **Readings:** `places.py read` gives the rule's readings. `read_more.py` gives the readings declared
  during the run, plus two scores added after the reading, labelled as such.

**The rule's measures.**

| | asked (42) | unasked exact (549) | decoy (836 parsed) |
|---|---|---|---|
| `departs` rate | **0.70** | 0.30 | 0.28 |

- **AUC of the stated CONFIDENCE:** asked against decoy **0.348**; asked against unasked 0.474.
- **The capped engine:** a cap of 10 a PR by confidence keeps 2 of 42 asked pairs.
- **Projected unscoped filings from stage F's 25:** median 67.5 a PR.

**By the rule as written: the detector band** (AUC asked against decoy ≤ 0.60). Decoy `departs`
(0.28) does not reach the band's other trigger, 0.40.

**The rule's AUC measured the wrong thing.**
- **The model gave its confidence in its own verdict, not the probability of a departure the prompt
  asked for.**
  - `departs` answers: mean confidence 90.5, median 95.
  - `conforms` answers: mean 89.9, median 95.
- **So a confident `conforms` ranks above a hesitant `departs`.** The stated number carries no
  information about departure, and the AUC criterion and the capped reading rest on it.
- **This is a failure of the elicitation, recorded as such.** The pre-registered verdict stands as
  written. It is not re-read.

**Readings declared before the reading** (`read_more.py`):

| | stated confidence | `departs` rate as the score *(added after)* | signed confidence *(added after)* |
|---|---|---|---|
| pooled AUC, asked vs decoy | 0.348 | 0.729 | 0.775 |
| pooled AUC, asked vs unasked | 0.474 | 0.732 | 0.777 |
| within-PR AUC (10 PRs) | 0.351 | 0.678 | 0.716 |
| leave-one-PR-out range | 0.333-0.376 | 0.687-0.752 | 0.744-0.801 |
| sample 1 only, vs decoy | 0.394 | 0.729 | 0.771 |

Signed confidence is CONFIDENCE for a `departs` answer and 100 − CONFIDENCE for a `conforms` one.

- **Agreement as confidence.** For exact pairs with two samples, the asked share by the number of
  samples saying `departs`:

  | samples saying `departs` | pairs | asked | asked share |
  |---|---|---|---|
  | 2 of 2 | 149 | 26 | 0.174 |
  | 1 of 2 | 93 | 7 | 0.075 |
  | 0 of 2 | 349 | 9 | 0.026 |

  It is monotone, about 7× from 0 of 2 to 2 of 2.
- **Asked pairs on asks DX misses:** 35 of the 42, with a `departs` rate there of 0.70, the same as
  over all asked pairs.
- **Per-rule suppression, simulated leave-PR-out.** The share of asked departs kept, against filings
  a PR over this test's pairs:

  | cut | asked departs kept | filings a PR |
  |---|---|---|
  | none | 29.5 of 29.5 | 33.2 |
  | 0.5 | 24.5 | 28.1 |
  | 0.3 | 24.0 | 24.0 |
  | 0.1 | 22.5 (0.76) | 18.7 |

- **Precision:** 0.068 of all `departs` filings sit at an asked pair. The base rate is 42 of 1,431
  pairs, 2.9%.

**What it means, at this altitude** (one model, one turn, the exact entries plus five decoys a PR, in
sample).
- **The verdict at a place discriminates moderately.**
  - It says `departs` at 0.70 of the places maintainers asked about, against 0.28-0.30 elsewhere.
  - Verdict-based AUCs are 0.68-0.78, above stage H's deciders (0.56-0.64), though those answered a
    different question.
  - Within a PR it holds on 7 of the 10 PRs.
- **It reaches what solo misses:** 35 of the 42 asked pairs are on asks DX misses, at the same 0.70.
- **But uncapped it files at about a quarter to a third of all (place, convention) pairs, so about 7%
  of its filings are asks.**
  - That is the territory of stage H's finding that maintainers raise 1 in 20 to 1 in 400 of the
    places a convention's situation occurs. Many of the unasked departures may be real, and nobody has
    adjudicated whether they would be welcome.
- **Two volume levers measure as real, in sample:** two-sample agreement, and per-rule suppression
  left out by PR. Together they could halve volume while keeping about three quarters of the asked
  departs. Both are selection under the 2026-09-22 ruling, so they are measured here as operating
  points, not proposed.
- **The decision this hands the user.**
  - Read as written, the rule says drop this form, and go to DP with decoys (M4).
  - Read with its failed measure set aside, the engine is a moderately discriminating, high-volume
    generator whose value turns on whether its unasked departures are welcome. That is the open
    adjudication (`docs/todo/adjudication-rubric.md`).

## Also read, added after the reading: a simulated deployable engine against solo run twice (`simulate_engine.py`)

**The setup.** An in-sample estimate from measured parts, not a run. The ten stage F PRs and their 33
in-census asks, with three parts:
- **selection:** stage F's 25 blind picks a PR, chosen without the asks;
- **the check:** the ladder's blind bare-sentence cells at the ask's place, counting an ask only if its
  entry is among the picks;
- **volume:** this test's decoy `departs` rate × places × 25.

**In-census reach, matcher 1 / matcher 2:**

| solo DX, one rep | solo run twice, unioned | the engine alone | the engine ∪ one solo rep |
|---|---|---|---|
| 0.162 / 0.141 | 0.192 / 0.152 | 0.485 / 0.485 | **0.552 / 0.552** |

**The volume:** filings a PR at a median of 68, ranging from 25 (42184) to 490 (30458, 43 places).
Solo DX files about 2.6.

**So the engine as specified would roughly triple recall on these PRs, at about 25 times the
filings.** That is the trade the round's remaining measurements and the user's selection ruling
decide.
