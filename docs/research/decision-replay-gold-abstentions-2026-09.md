# Are the specialists' gold-site silences decisions or contracts? (2026-09-21)

The diagnostic that replaced the $37 null replay as this todo's closing condition. The 45
specialist invocations in `pr5_A_lead_heldout12_v2_rep1` whose work unit carries a **required
gold** change and that **abstained** — a maintainer asked for something there, an arm looked, and
it said nothing — replayed at the first-submission cut, 3 samples each, condition `null`.

Run `pr5_replay_null_first_submit_candidates_goldabstain45_v2_rep1`: 45 sessions, 135 samples,
**$1.97 billed / $6.35 nominal**, ~13 minutes, all 135 verified as started from their prefix.

## The split

| | sessions | |
|---|---|---|
| **stable abstention** — every sample abstained | **41 / 45** | no decision-stage change touches these |
| **decision-limited** — at least one sample filed | **4 / 45** | a bar, forcing or elicitation change could recover them |

At 3 samples the decision-limited count is a **lower bound**: a session that files one time in
five is caught about half the time. Read as "**at least 9%** of gold-site specialist silences are
decision noise", not "only 9%".

The four:

| session | recorded | replays |
|---|---|---|
| `wu:07d1ab9702ad80d61f40bbc9#style` | `could_not_establish` | filed **3/3** |
| `wu:1f9cf7865fe0948dfc6e47f8#naming` | `below_my_bar` | filed **3/3** (the gold rename; see the case study) |
| `wu:1031e8acbe2db1ea15d6a50e#style` | `already_correct` | filed 1/3 |
| `wu:730afd5b892a29885e89fd5c#generality` | `could_not_establish` | filed 1/3 |

Two of the four file in *every* replay, so the recorded abstention was the minority outcome at
its own prefix — the run we have under-reports what its own arms would say.

## What it means for where money goes

**Most gold-site silence is not sampling noise.** 41 of 45 sites are silent every time from an
identical prefix, across every arm: `correctness` 5/5 sessions stable, `duplication` 11,
`family_design` 6, `naming` 11. Anything that only re-rolls the decision — forcing, a lower bar,
confidence elicitation, more reps — can reach at most the 4, and a full rep costs $7.26 to move
them. The leverage is in what the arms are *told* and what they can *see*, not in how they are
sampled.

That is the opposite conclusion to the one the forcing experiment suggested on its own (issue
recall 0.20 → 0.50 under duress). Both can hold: forcing also changes what an arm files where it
had *something* to say, and 33337's naming site is exactly such a case. What this measurement
adds is the denominator — on the held-out set, such sites are a small minority of gold-site
silences.

## The second finding: the abstention label is not reproducible

**17 of 45 sessions** (38%) produced an abstention reason the recording did not, with the same
outcome. The common swap is `already_correct` ↔ `could_not_establish` — two different diagnoses
("the check applies and the code satisfies it" vs "I needed evidence my tools could not
produce"). This project reads those labels as evidence about *why* arms are silent, including in
the 76% `already_correct` figure that motivated the forcing experiment. At the decision turn,
better than a third of them are a coin flip.

## Operational

Two samples paused on the turn cap (8 turns after the cut) without submitting: the replayed arm
occasionally investigates rather than deciding. Both belonged to sessions whose other two
samples succeeded — and the orchestrator emits no task result for a task with any paused
sample, so reading outcomes through the execution index dropped **both whole sessions**,
successful samples included, and reported a clean rate over the remaining 43. Fixed by locating
tasks through the tasks this run scheduled; `collect_outcomes` now reports every scheduled
sample.

## Caveats

- One source rep, gold-based (in-sample) selection, submission-level comparison, no judge. A
  filed candidate here is an *ask at a gold site*, not a scored hit — whether it is what the
  maintainer wanted needs the judge or a hand read (done for the naming session; it matches).
- The floor is measured on abstaining specialists at gold sites. A condition aimed at filing
  behaviour, or at the generalist, needs its control drawn from that population instead.
