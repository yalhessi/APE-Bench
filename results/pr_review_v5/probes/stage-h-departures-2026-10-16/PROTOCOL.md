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

## Step 2, pre-registered (2026-10-16, after step 1, before any place is read)

Step 1: 100 of the 145 located unasked places merge unchanged; the baseline was too small to read. Step 2
asks how many of the flagged places are departures at all.

**Items.** 60 of the 145 located unasked places, seeded (20261018), at most 8 a rule, plus the 6 asked
places as blind calibration (66), shuffled under opaque ids (`step2_items.jsonl`). **Packets** (scratch:
they quote census asks): the rule as the codebook states it and as stage G wrote it (trigger, check,
exception; `conventions-ceiling-2026-10-04/rules.json`), two census asks under the rule from PRs outside
the 16 (seeded) as the maintainers' own statement of it, the place's code at the round-1 head
(`census_mined.json`), its file and declaration, and the base commit for git lookups. Never the merged code.

**Labels.** `departs` (a maintainer holding the rule as stated and as the asks show would ask here),
`conforms` (the rule's situation occurs and the code already does what the rule asks, or its check would
fail), `excluded` (outside the rule as held), `needs_tools` (only a compile or a search the reader cannot do
would decide it), `unclear`. Two readers, independent.

**Calibration.** A reader labelling fewer than 5 of the 6 asked places `departs` is reported, and only the
items both readers agree on are read.

**Reading rule.** Over the sampled unasked places labelled `departs`, `conforms` or `excluded`:
- `departs` ≤ 25%: the 5%'s denominator was mostly conforming or excluded places; the ask rate per real
  departure, 6 / (6 + d̂ · 199), is at least about four times the 2.9%;
- `departs` ≥ 60%: most flagged places are departures nobody asked about; the demand reading stands for
  these rules;
- between: mixed. `needs_tools` is reported by rule and check kind (compile, lookup, read): it is the share
  a reading cannot settle and a tool-using reviewer would have to.

## Step 3, pre-registered (2026-10-16, after the adversarial review, before any re-read label): the same places without the note

The adversarial review (`review2-departures.md`) found step 2's packets carried the pinpointer's note, and every
departure both readers agreed on was one the note named. Step 3 re-reads **the same 66 places with the note
removed** and nothing else changed (same rule text, same two maintainer asks, same code excerpt, same base),
under new ids and a new order (seed 20261019, `step3_items.jsonl`), by two new readers, same labels.

**Note types, coded before any re-read label** (`note_types.jsonl`): `names_fix` (the note names a concrete
alternative, a contrasting precedent or a measured length) 28, `hedged` 13, `neutral` 25. **Calibration**: the
7 asked places, the original 6 and H008 (asked via "similar below" on another place; review2), 4 with a
`names_fix` note and 3 with a `neutral` one.

**Reading rule, fixed now.**
1. **Does departure track the note when the note is gone?** The share of `departs` among decided labels at
   `neutral`-note places, against step 2's (1 of 42 pooled):
   - 20% or more: the notes suppressed departures where they were silent; step 2 under-read neutral places;
   - 5% or less while `names_fix` places stay at 50% or more: readers find departures where the pinpointer did,
     unaided; the note was informative rather than the reading's source.
2. **Does the rule-kind split survive?** Departs share on layout rules (P084, P048) minus on substantive rules
   (search and compile kinds), both readers pooled: 30 points or more, it survives; 15 or less, it collapses.
3. **Calibration** by note type: departs on the 4 `names_fix` and the 3 `neutral` asked places, per reader; a
   reader under 5 of 7 is reported, and its labels are read only where both agree.

## Step 4, pre-registered (2026-10-16, before any check runs): each rule's own check, run with tools

Step 3 left one confound: readers without Lean judged the substantive rules, whose checks are a compile or a
search. Step 4 runs the rule's own check at the same 66 places in each PR's reviewed workspace (base snapshots
built by `build/base_build_rows.jsonl`, reviewed workspaces by `release.prebuild --reviewed` on
`configs/pr_review_v5_stage_h_v1_build.yaml`, release `inputs/probes/stage-h-v1`), PR by PR as workspaces
become ready.

**The checker.** One agent per PR, given the note-free packets (`stageh_packets_blind`) and the project's tools
through `cli tool` (`lean_verify_edit`, `declaration_search`, `content_search`, `file_read`) on that PR's reviewed
workspace; it never sees reader labels, notes or merged code. Per place it does exactly what the rule's `check`
says and records every call:
- **compile rules** (P005 finishing tactic, P010 drop or weaken a hypothesis, P018 merge consecutive steps,
  P040 a term for a short block): at most six candidate edits a place, each compiled; `departs` if one the
  check describes compiles (and, for P010, the hypothesis is removed or weakened), `conforms` if none does;
- **search rules** (P011 existing API, P100 siblings' variant, P126 the file's spelling, P254 siblings' names):
  the search the check describes, at the base or in the PR's own files; `departs` if it finds what the check
  names (for P011, a derivation that compiles), `conforms` if it does not;
- **read rules** (P048, P084): measured from the code (shared binders; joined line lengths ≤ 100);
- `undecided` when a call times out or the environment fails; never a guess.

**Reading rule, fixed now.** On the open substantive places, against the note-free readers (step 3):
- the share of reader-`conforms` places where the check finds a departure: **30% or more**, readers' substantive
  "conforms" was largely not checking, and the substantive departure share is the check's; **10% or less**,
  readers' "conforms" holds and the split stands as step 3 measured it; between, mixed;
- the substantive departure share by the checks alone, and by rule; the 7 asked places as calibration
  (the check should find each departure: at least 5 of 7);
- reported as each PR finishes; the reading is made on all PRs whose workspaces build, with the unbuilt named.

### Step 4 amendment (2026-10-16, after 7 of 14 PRs are checked, 38 of 66 places; before any audit label)

**Why.** Two committed rows depart only under a reading looser than the rule's literal `check`. On K045 the
checker merged `intro` then `cases` into `rintro`, which is not among P018's four combined forms (a `rw` list,
`rwa`, `by_contra!`, one `calc` step), and the checker said so. On K031, `use 1; simp` is two calls where P005
asks for one finishing tactic. The checkers were told to do what the check says. But a capable checker
generalises the check to the principle behind it, and that is a different measurement: the rule as stage G
wrote it, or the principle it instantiates. Re-labelling those rows myself, after seeing the scores, would be
choosing the reading that suits.

**The audit.** After the last PR is checked, one auditor agent reads every check row: the item, the rule's
`trigger` and `check` text from `conventions-ceiling-2026-10-04/rules.json`, and the row's verdict and evidence.
It sees no reader label, no note, no `asked` flag and no score. Per row it writes `audit.jsonl`
`{"item", "reading": "literal|looser|incomplete", "why"}`:
- `departs` row: `literal` if the compiled or found candidate is a form the check names and does what the
  check asks; `looser` if it departs only under a broader reading (another combining form, two calls where
  one is asked, a judgement the check leaves open).
- `conforms` row: `literal` if the check was done as described; `incomplete` if a form the check names was
  not tried.

**Reading.**
- The strict reading counts `looser` as `conforms`; `incomplete` stays `conforms` and is counted. The
  checker's own verdicts are the second reading.
- Both are reported against the 30% and 10% lines. If the two readings fall on different sides of a line,
  the result is stated as depending on the reading, with the rows that decide it listed.
- The `looser` rows are reported on their own as departures from the principle beyond the rule as written.
  That bears on the plan's question of how far a rule is an instance of something broader.

**Descriptive field, added before the audit runs (after PR 35140, 53 of 66 places checked).** On K001 and
K062 the only finishing call that compiled is a hinted `aesop` longer than the proof it replaces. The rule's
literal check is met, but the result is not one a maintainer would want; P005's check, unlike P040's, has no
"reads no worse" clause. The auditor also records, per `departs` row, `"longer": true|false|null`: whether
the departing candidate is longer, in characters, than the code it replaces (null where there is no
candidate, as for search and read rules). It is reported as a count beside each reading and changes no
verdict. Judging which literal departures a maintainer would want is the open question, not something to
settle after seeing the data.
