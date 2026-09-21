# Improving the specialist arms, given that their silence is stable

**Status** — **closed 2026-09-21, unfunded.** Step 0 ran (free) and none of the three mechanisms
clears its gate: labelling all 58 silent gold-site sessions gives **0** advisory-suppressed, **0**
cross-unit and **1** blocked-by-the-compiling-edit-rule, against **37** wrong-arm-correctly-quiet
and **17** right-arm-disagrees. Result: `docs/research/specialist-silences-2026-09.md`. Plan and
instrument: `docs/plans/2026-09-21-specialist-silences.md`. The routing half moved to
[routing-remit-and-silence.md](routing-remit-and-silence.md); what is left of this one is the
judgement residue, which no contract change reaches
**Cost** — $0 spent. The conditions were built and priced ($2.66 gold-site + $0.07 control, cached)
and are not worth running on this population
**Owner question** — *answered*: none of them, on the evidence available. The arms are silent at
41 of 45 gold sites every time because they were mostly the wrong arms, and where they were the
right arm they mostly disagreed.

## Motivating result

`docs/research/decision-replay-gold-abstentions-2026-09.md`: the 45 specialist invocations at
required-gold sites that abstained in `pr5_A_lead_heldout12_v2_rep1`, replayed 3× at the
first-submission cut for $1.97. **41 of 45 abstained in every sample.** So re-rolling the
decision — forcing, a looser bar by exhortation, confidence elicitation, more reps — can reach
at most 4 of them, and a full rep costs $7.26 to try.

**This does not rule out changing what the arm is told or shown**: that is a different prefix,
and replay prices it at $2.60 against the null already on disk. Reading the 125 abstention texts
that run produced (`already_correct` 70, `could_not_establish` 53, `below_my_bar` 1,
`belongs_to_another_concern` 1) separates three mechanisms, which want three different fixes.

**1. Seen, and not expressible at this grain.** The `correctness` prompt does list "`sorry`,
`admit`, or an axiom the repository does not accept"
(`review/focused_prompts.py:495`). On PR 33149 the arm *saw* it — "extensive use of axioms" —
and abstained `belongs_to_another_concern` **5/5**. Its work unit is one declaration
(`Vorticity`), and `submit_candidates` enforces `change_ids ⊆ unit` with `primary_subject`
equality, so a file-level defect has no anchor it may legally use. The `docs` arm on the same PR
filed about those same axioms 5/5 — its unit's subject *is* the file. The observation was
captured five times in free text and discarded: `abstention_detail` reaches no finding.

**2. Advisory verdicts become silence.** `naming_norm`'s own description says `emerging` means
"advisory at most" (`review/context_tools.py:567-569`), and `severity: advisory` exists in
`CandidateSubmission`. The `naming` arm on 33337 still concluded "emerging (`toLinearMap_` 21 vs
`coe_` 7) … so I'm not requesting a rename" — while 2 of 5 replays filed the gold rename. The
licensing exists in the tool and does not reach the decision.

**3. Evidence the tools cannot produce** (43% of abstention samples). The texts name it
precisely: `correctness` "could not validate … without access to the merge-base file contents";
`naming` gets `insufficient_evidence`; `family_design` wanted an edit spanning two declarations
and did not attempt it — `patch_set` has never been submitted in 1,660 recorded candidates and
would raise TypeError on first use (`batching-work-units.md`).

## What would close it

**Step 0, free, and first.** Pair each of the 45 gold asks with its four statements (the
recorded one plus three replays) and label each site: unexpressible-at-this-grain /
advisory-suppressed / evidence-gap / genuine disagreement. Everything below is sized by that
split. The rule applies: read the stage's *inputs* before touching its prompt.

**Then, cheapest first — each one replay condition against the null already on disk
(`pr5_replay_null_first_submit_candidates_goldabstain45_v2_rep1`), $2.60 and minutes each:**

1. **An out-of-scope observation channel.** A submission may carry "my target is fine; the file
   has X" as something `finalize` retains, instead of it dying in `abstention_detail`. Aimed at
   mechanism 1, needs no re-investigation, and the 5/5 stability of the axioms abstention makes
   it a clean test: the condition should convert that silence into a recorded observation.
2. **Advisory licensing.** Tell the arm that an `emerging` verdict warrants an advisory
   candidate and that only `insufficient_evidence` warrants silence. This is §D2 of
   `docs/research/pr-review-v5-principled-design.md` (norm store with maturity; emerging norms
   license advisory findings only) — written, never built, and the open contract question in
   `dead-ends.md`'s retracted naming-arm entry.

**Then the tool work, indicated by mechanism 3 and priced before spending:** merge-base file
access for `correctness`/`duplication`, a `patch_set` that works, and the norm store's coverage
(`evidence-tiers-and-traces.md`, `specialist-arm-contents.md`). Each needs a **whole-task**
replay to see whether the silence moves, because new evidence has to enter the investigation:
`--cut turn=1` on the same 45 sessions is **$5.82 cached / $13.95 uncached** at 3 samples,
measured by preflight.

**Do not** spend on more reps, forcing (it also inverts the control-PR property that makes
precision measurable), or "be less conservative" prompt nudges. The 41/45 stability is the
argument against all three.

## Evidence

- `results/pr_review_v5/runs/pr5_replay_null_first_submit_candidates_goldabstain45_v2_rep1/`
  (135 samples, all prefix-verified) and the case study beside it (`…_case4b_…`).
- `review/focused_prompts.py:495`; `review/context_tools.py:567-569`;
  `review/candidates.py` (`change_ids ⊆ unit`, `primary_subject` equality, `severity`).
- Related todos: `specialist-arm-contents.md` (what the arms contain),
  `evidence-tiers-and-traces.md` (collectors that can only say `inconclusive`),
  `batching-work-units.md` (unit grain and `patch_set`), `replay-decision-turn.md` (the
  instrument and its remaining condition).

## Risk

- Mechanism 1 rests on **one PR**: 33149's axioms, five samples, plus the `docs` contrast. The
  grain explanation is a hypothesis, and step 0 is what tells us how many of the 41 it covers.
- All of it is one source rep with gold-based (in-sample) selection and no judge: these are
  statements about what arms *say*, not about recall.
- An out-of-scope channel and an advisory tier both **increase volume**, and ~90% of what the
  system emits is already unadjudicated (`README.md`, "Adjudicating findings that are not
  maintainer obligations"). Control-PR emission is the guard to watch: 0–1 per run historically,
  and a condition that raises it is not an improvement.

## Corrections, 2026-09-21 (read these before costing anything above)

Written the same day, from a join of the 45 sessions to their gold asks and a read of the 43 that
appear as silent cells in `report buckets`. The diagnostic is untouched; the *interventions* it
motivated needed five changes, and the plan
(`docs/plans/2026-09-21-specialist-silences.md`) is ordered by them rather than by this file.

1. **Most of the population is the wrong arm, correctly silent.** Only **11 of 43** silent cells sit
   at an obligation whose gold `concern_labels` intersect the arm's own `expected_concerns` (mapped
   through `CONCERN_ALIASES`). The other 32 are `duplication` at a rename, `naming` at "factor out a
   lemma", four arms at a docstring ask. "41 of 45 stable" is true and mostly means this. The miss
   there is **routing**, not the contract — bounded by the fanout entry in `dead-ends.md`, measured
   by `on_concern_arm_scheduled`, and split out as its own todo.
2. **The dominant on-concern blocker is not in the three mechanisms.** About **9 of 43** texts say
   they could not produce, or were refused, a *compiling edit*: `candidates.py:420-424` refuses a
   candidate in a checkable family (`correctness`, `proof-golf`, `duplication`, `generalization`)
   with `proposed_edit: null`, and the supplements say "report ONLY verified edits" / "If nothing you
   attempted compiled, submit nothing". 33149's ask was "replace the axiomatized Parseval with the
   existing one"; the arm found the existing lemma and could not say so without a patch the
   maintainer never supplied either. This is now the first paid condition (`ask_without_fix`).
3. **Mechanism 1's example is not in this population.** `wu:1c5956b9…#correctness` (the axioms) comes
   from the four-session case study; its unit carries no required gold change, and both "remove the
   axioms" obligations were COVERED in this rep by `docs`. No text among the 45 describes a defect
   seen outside its unit. The retention half is still real and free — `abstention_detail` is written
   to `arm_responses.jsonl` and **read by nothing**; `finalize.py` contains no occurrence of
   `abstention`, and `report._abstentions` keeps the reason and drops the text. The observation
   *channel* is deferred behind step 0.
4. **Advisory licensing is already in the arm prompt, so condition 2 as written restates it.**
   `NAMING_SYSTEM` (`focused_prompts.py:363-368`) says an `emerging` verdict should be said "as an
   ADVISORY suggestion", and `naming_norm` renders "Advisory at most". What is missing is downstream:
   `SUBMISSION_CONTRACT` (`render_focused.py:52-99`) names advisory only inside the JSON literal and
   closes with "a wrong finding costs this review far more than a silence does". Gold marks **17 of
   22** counted obligations `blocking_force: advisory`. The condition survives as a *contract and
   schema* change and is gated on step 0 finding ≥ 3 advisory-suppressed cells; today's count is 1,
   and its one example filed the gold rename 3/3 under replay, i.e. it is decision-limited.
5. **A whole-task replay cannot test the tool work this file prices at $5.82/$13.95.** `--cut turn=1`
   resumes from the *recorded* system prompt, user prompt and tool list
   (`conversation.py:470-507`; `:638-690` is bypassed, and a newly registered tool lands in
   `registered_not_shown` and is never shown). It exercises today's *implementation* of an
   already-granted tool. Merge-base file access and a working `patch_set` are a rep, not a replay; a
   `naming_norm` behaviour fix is replayable on the naming sessions.

Two smaller ones. **No replay so far could measure the guard this file names**: the 45-session
selection contains no control PR, so control-PR emission was unobservable. `v2_rep1` has 7 specialist
abstentions on 33304/33315, ~$0.35 to replay, and a `control-abstentions` selector is in the plan.
And because 17 of 45 abstention *labels* swap under replay, **step 0 labels from the detail texts,
not from the reason enum**; `replay_outcomes.jsonl` does not carry `abstention_detail` (fixed
forward), so the replayed texts are in the attempt session files under
`.claude/worktrees/decision-replay/.ape/runs/…`.

## Closed, 2026-09-21 — what step 0 returned

Full account in `docs/research/specialist-silences-2026-09.md`; the store is
`results/pr_review_v5/adjudications/silence_labels.jsonl` and the instrument is
`cli report silences`. Of **58** distinct silent sessions at gold sites:

| label | sessions | |
|---|---|---|
| `off_concern` | 37 | correct silence; a routing question, now its own todo |
| `disagreement` | 17 | the right arm declined the ask on stated grounds |
| `evidence_gap` | 2 | both `naming_norm` |
| `decision_noise` | 2 | includes 33337, which the replay files 3/3 |
| `fix_required` | **1** | one `duplication` session on 33149 |
| `knowledge_gap` | 1 | |
| `advisory_suppressed` / `cross_unit` | **0** / **0** | |

So mechanism 2 (advisory verdicts becoming silence) and mechanism 1 (seen and unfileable at this
grain) have **no instance in this population**, and mechanism 3 has two, both in one tool. The
mechanism this file's corrections added — the contract refusing a claim with no compiling edit —
has one, and it is PR 33149's axioms again.

An adversarial second reader overturned 7 of the 13 repairable labels it was shown, taking
`fix_required` from 6 sessions to 1; it was told to default to refuting, so **1 is a lower bound
and 6 is the ceiling**. Even at the ceiling this is one PR and two arms.

**What would reopen it.** The same read on `v2_rep2` and `v2_rep3` — free, and the only thing that
would turn any of these counts into a rate. A population drawn from somewhere other than gold-site
silences (what arms *file*, the generalist, the off-gold ~90%). Or a whole-task replay
(`--cut turn=1`), which re-samples the investigation and could move a `disagreement`, where a
decision-turn replay cannot.

**What is still live and is not this todo.** The judgement residue: 17 sessions where the right arm
looked at the maintainer's ask and said no. That is a capability and evidence question, and the
contract, the tools and the prompts do not reach it.
