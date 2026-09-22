# What the specialists' gold-site silences actually are (2026-09-21)

The free diagnostic that `docs/todo/specialist-abstention-interventions.md` called step 0, run as
an instrument rather than by hand. It answers the question the replay diagnostic left open:
41 of 45 gold-site silences reproduce from an identical prefix, so they are readings of a contract
rather than sampling noise — **readings of what?**

Conclusion first. **Of 58 distinct silent sessions at gold sites, 54 are not repairable by any
contract, prompt or tool change**: 37 are an arm correctly quiet about somebody else's concern, and
17 are the right arm considering the maintainer's ask and declining it on stated grounds. The three
mechanisms the interventions were costed against total **four sessions**, and the largest of them —
the one this session's own plan promoted to the first paid condition — is **one session on one PR**.
No condition in that plan clears its gate, and the ~$5.46 they were priced at is not worth spending.

## Method

`report silences --run pr5_A_lead_heldout12_v2_rep1 --replay <the null replay>` joins, per (gold
obligation, silent arm): the maintainer's `claim`, gold's `concern_labels` and `blocking_force`, the
arm's own brief and `expected_concerns`, the sentence it wrote in `abstention_detail`, what its
retrieval returned, whether it filed elsewhere in the same unit, and whether re-deciding from its
recorded prefix reproduced the silence. 76 cells over 22 counted obligations and 58 distinct
sessions; a session silent at two obligations is two cells.

Each of the 20 obligations went to one reader, which sees the ask once and every arm that went quiet
at it. Every label that would fund spending then went to a second reader told to refute it, with the
conservative label as its default. Both are models (`task:` rows in the store), not people: a human
row outranks them by design, and the seven cells the two disagreed on are recorded as contested
rather than averaged.

**The abstention reason was not used.** Replay swaps it on 17 of 45 sessions with the outcome
unchanged, so it labels nothing; the labels are made from the sentence.

## The split

| | sessions | cells | |
|---|---|---|---|
| `off_concern` | **37** | 50 | the ask is outside this arm's remit; the silence is correct |
| `disagreement` | **17** | 19 | the right arm considered the ask and declined on stated grounds |
| `evidence_gap` | 2 | 2 | a named tool could not answer — both `naming_norm` |
| `decision_noise` | 2 | 2 | the same prefix files in some replay samples |
| `fix_required` | **1** | 2 | had the maintainer's answer, blocked by the compiling-edit rule |
| `knowledge_gap` | 1 | 1 | did not know the thing the maintainer knew |
| `advisory_suppressed` | **0** | 0 | |
| `cross_unit` | **0** | 0 | |

The adversary did most of the work at the top of that table: it overturned **7 of the 13** labels it
was shown, taking `fix_required` from 6 sessions to 1 and `knowledge_gap` from 3 to 1, almost always
to `disagreement`. Its instruction was to default to refuting, so **the repairable counts are a lower
bound** — a less adversarial reading of the same texts gives up to 6 `fix_required`. What it refused
was the inference from "the arm tried an edit and it did not compile" to "the arm had the
maintainer's answer": on PR 33145 both arms that looked like `fix_required` had set out to improve a
proof they judged non-canonical, not to make the rename the maintainer asked for.

## What each intervention's gate did

The plan gated every paid condition on this read. All four fail, and three fail at zero.

| Condition | Gate | Found | |
|---|---|---|---|
| A `ask_without_fix` | ≥ 3 `fix_required` | **1 session, 1 PR** | do not run |
| B `advisory_licensed` | ≥ 3 `advisory_suppressed` | **0** | do not build |
| C out-of-scope channel | ≥ 3 `cross_unit` | **0** | do not build |
| E `naming_norm` behaviour | ≥ 3 `evidence_gap` on it | **2** | free code check first |

**A rests on PR 33149's axioms and one `duplication` session.** Its two cells are the same
invocation counted against the PR's two "remove the axioms" obligations. The arm found
`orthonormal_fourier` in `Analysis/Fourier/AddCircle.lean` — the library result that makes the
axiom unnecessary — and wrote that it "could not mechanically rewrite it to the PR's exact" form.
That is a real instance of the mechanism and it is one instance. The original todo's mechanism 1
was flagged as resting on one PR; its replacement rests on one session of the same PR.

**B and C are empty, and the reason is worth keeping.** The one site that motivated advisory
licensing — 33337's `naming` arm reading `emerging (21 vs 7)` and declining — is labelled
`decision_noise`, because the replay files the gold rename in 3 of 3 samples. The arm is not
suppressing an advisory finding; it produces it about 40–60% of the time from the identical prefix.
And no text among the 76 describes a defect the arm saw and could not anchor, so the out-of-scope
observation channel has no motivating site in this population at all.

## The two findings worth keeping

**1. `naming_norm` is a prefix oracle, and one gold ask is a suffix change.** Both `evidence_gap`
sessions name it. On PR 33421 the ask is to rename `round_eq'` to `round_eq_div`;
`naming_norm.leaf_prefix` takes the leaf's first token, so both names have the prefix `round` and
the tool's population cannot distinguish them. This is structural, not a threshold: no value of
`MIN_SUPPORT_RATIO` makes a prefix-counting oracle see a suffix convention. It is a different
limitation from the 0.80 bar already recorded in `specialist-arm-contents.md`, and it is free to
check further.

**2. The remaining in-remit gap is judgement, not plumbing.** 17 sessions are the right arm looking
at the maintainer's ask and saying no on stated grounds. Nothing in the contract, the tools or the
prompts reaches those: the arm did the work and reached a different conclusion. That is the honest
residue of "the specialists are too silent", and it is a capability and evidence question rather
than an engineering one.

## Caveats, and what is untried

- **Model labels, not human ones.** One reader and one adversary per cell. The store keeps both
  readings and 7 contested cells; a human pass outranks all of it and has not happened.
- **One source rep, one release, 12 PRs, 22 obligations, 58 sessions.** Counts of 0, 1 and 2 are not
  measurements of a rate. "Zero `cross_unit`" means this population contains none, not that the
  mechanism does not exist — the case study's 33149 `correctness` session, which saw the axioms from
  a declaration-grain unit, is exactly that mechanism and is *not* in this population.
- **The adversary was told to default to refuting**, so every repairable count is a lower bound.
- **Gold-site silences only.** A condition aimed at what arms *file*, at the generalist, or at the
  ~90% of output that is off-gold draws from a different population and is untouched by any of this.
- **The remit test is 80% concordant with gold's own concern labels** (53 of 66 cells where both
  apply). Where they disagree the hand read was preferred, and gold's labels are the noisier of the
  two: 33145's "generalize the supremum result" is labelled `duplication`.
- **Untried, and not ruled out by this:** the whole-task cut (`--cut turn=1`), which re-samples the
  investigation rather than the decision, and so could move a `disagreement`; any change to what the
  arms are *shown* rather than told; and the same read on the other two v2 reps, which is free and
  is the first thing that would make any of these counts a rate.

## What was built to get here, and what it cost

Nothing was spent. `report silences`, the `SilenceLabel` store, the replay's retention of the
abstention text, and the `control-abstentions` selector are on branch `specialist-silences`; the
labelling itself ran as a local fan-out over the 20 obligations.

The four conditions were preflighted and priced, and the prices stand if the population ever
justifies them: the gold-site population is 58 sessions at $2.66 cached / $6.81 uncached for three
samples, and the control population is 7 sessions at $0.07 / $0.34 — the guard no replay before this
one could measure, because every earlier selection drew only from PRs carrying gold.

## Correction, 2026-09-22: these labels do not carry across repetitions

The store keys a label `<invocation_id>|<obligation_id>`, and because a work unit is derived from
the release, the same key recurs in every repetition built on it. That was the argument for
labelling once: running `report silences` on reps 2 and 3 finds **59 of 73** and **57 of 66** cells
already carrying a label from rep1.

They should not be trusted. Comparing the 59 cells shared by rep1 and rep2:

| | |
|---|---|
| same `abstention_reason` | 43 of 59 (73%) |
| median similarity of the two `abstention_detail` texts | **0.16** |
| pairs above 0.9 similarity | **0** |
| pairs below 0.5 | 42 of 49 |

The same arm is silent at the same slot both times and says something almost entirely different
about why. One `style` cell reads "found a likely style issue … but `lean_verify_edit` … failed to
compile" in rep1 and "checked binder/line-break style … and found no violations" in rep2: those are
different mechanisms, and a label made by reading the first does not describe the second.

The distinction that survives is between two kinds of label. `off_concern` is a property of the
**ask and the arm's remit**, neither of which changes between repetitions, so it carries. Every
other label is a property of the **session**, and does not. That is the opposite of
`AdjudicationLabel`, where the key identifies a recurring *claim* and carrying is the whole point.

Consequence for the numbers above: they are rep1's, and replicating them means relabelling the
session-level cells on reps 2 and 3 rather than reading the carry-over. Consequence for the store:
`report silences` should mark a label whose `from_run` is not the run being reported, so a borrowed
one is visibly weaker than a fresh one.

