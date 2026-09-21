# Improving the specialist arms, given that their silence is stable

**Status** — open, written 2026-09-21 from the replay diagnostic; **step 0 is free**
**Cost** — $0 to diagnose; $2.60 per contract condition; $5.82–$13.95 for a whole-task replay
**Owner question** — the arms are silent at 41 of 45 gold sites *every time*; which of the three
mechanisms behind that silence is worth paying to fix?

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
