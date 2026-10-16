# The 5% at its source: stage H's flagged places followed to merge (2026-10-16, before the script runs)

The second item of the queue the user set (2026-10-16; `docs/plans/2026-10-16-principles-scope-currency.md`):
the "maintainers raise a convention at 5% or less of the places it applies" figure was computed in stage H
(`probes/conventions-ceiling-2026-10-04`, Result 6) from 205 places a blind pinpointer flagged for ten rules on
16 census PRs, 6 of them at a round-1 ask (2.9%).

## Already answered?

- `docs/questions.md`, "Delivered as guarded rules pinpointed at places": the 2.9% itself, now read with the
  2026-10-16 correction.
- `docs/questions.md`, "Of the departures a detector finds at the reviewed head, how many are fixed by merge":
  for dot notation and primed names, unasked departures survive to merge at 98%; placement's sentence was
  misstated. This probe asks the same of the ten rules behind the 5%, which have no detector.
- `docs/todo/conventions-dossiers-exams.md` (narrowed; its drop rule met 2026-10-12) used stage H's figure
  as a motivating measurement; this probe re-reads that figure, it does not reopen the dossier line.
- Found before writing this, from `census_mined.json`: the pinpointer's status is `check` (the situation
  occurs, check it) at 176 places and `departs` at 29, the latter almost all on the two decoy rules; 5 of
  the 6 asked places carry `check`. So the 205 are places where a rule's situation occurs, not departures.

## Step 1 (deterministic; `follow.py`)

For each of the 205 places on a PR merged in the clone: the PR's file at the round-1 head, rebuilt as the
base file plus the round-1 diff (`data/pull_requests/pr/<n>/compares/<head>.json`), and the file at the
merged commit; the flagged declaration's text block in each, whitespace-normalised; outcome `unchanged`,
`changed`, `gone` (not declared at merge), `unlocated` (not found at the round-1 head). **Baseline:** every
other declaration the round-1 diff adds or modifies in the same files, classified the same way.

**Reading rule, fixed now.**
- Validity: the asked places on merged PRs are `changed` or `gone` in at least 4 of 5 (else the method
  cannot see what an ask does).
- The unasked places' changed-or-gone share against the baseline's:
  - within 10 points: being flagged does not predict a later change; nothing beyond round-1 asks touches
    these places more than any other code, and step 2 reads them;
  - 15 points or more above: flagged places are changed more than other code after round 1 (later
    rounds, the author); round-1 gold understates enforcement at these rules;
  - reported per rule and by status.

## Step 2 (pre-registered separately, after step 1)

A reading of the unasked places under each rule as maintainers state it, calibrated on the asked places and
on any unasked place step 1 shows changed toward the rule; written once step 1 says how much it must explain.
