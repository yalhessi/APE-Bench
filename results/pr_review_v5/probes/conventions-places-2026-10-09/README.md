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
