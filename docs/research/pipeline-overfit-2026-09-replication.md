# The arm-coverage audit, replicated on 1,000 validation PRs (2026-09-24)

The user, after reading `pipeline-overfit-2026-09.md`: *"Before we commit to this, let's generate a
much larger validation set and run the same analysis over it."* Seven of the 60-PR audit's claims
were pre-registered as R1-R7, with thresholds, in `docs/todo/pipeline-overfit-review.md` before any
label existed (`6bd9cc4`).

**The set.**
- **Sealed and drawn:** `val1000-2025-06-2026-03-v1`, seal `c311568d`, draw `af565b9`.
- **Frame:** the validation frame minus its 60 PRs, and so minus test's 60 too.
- **Size:** 850 main PRs in month quotas, plus 123 AI PRs. The AI stratum ran out 27 short of 150
  and completes as the seal allowed.
- **Feedback:** 759 of the 973 PRs have round-1 feedback, for 2,306 events and 1,833 asks.
- **Reviewers:** 80; the busiest wrote 8.5% of the events.

**The instrument.** Rubric v2: the audit's rubric plus a frozen codebook of the twelve families, and
`NEW` for anything outside them.
- **Readers:** two blind Claude readers per batch of about 150 comments.
- **Calibration on the audit's 144 comments:** each reader against the auditor's adjudication,
  κ 0.95 and 0.94.
- **Agreement here:** κ 0.97 on ask or not, 0.94 on family, 0.90 on primary arm, 0.85 on owned or
  unowned.
- **Contested:** 93 asks have a family the readers split on; they are counted as contested, not
  resolved.
- **Intervals:** from a bootstrap over PRs.
- **Where the data is:** `results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/`.
- **Caveat:** one model family reads both sides, so the agreement is an upper bound.

## The verdicts

| | claim (60-PR audit) | replicates if | 1,000 PRs | verdict |
|---|---|---|---|---|
| R1 | about a third of asks have no owning arm (30-34%) | unowned in [25%, 40%] | **21.4%** (18.9-24.2) | **fails: lower** |
| R2 | registration (F3) and PR-level (F12) asks exist and no arm owns them | each ≥ 5%, ≤ 10% owned | F3 **4.3%**, 14% owned; F12 6.3%, 1% owned | **fails on F3**, holds on F12 |
| R3 | naming is a small share (3%) | F8 ≤ 6% | **9.7%** (8.0-11.6) | **fails** |
| R4 | the remits name little explicitly (37%) | explicit ≤ 45% | 42.0% (38.7-45.3) | holds, narrowly |
| R5 | a PR-level unit is needed (14% PR-grain) | PR grain ≥ 8% | 9.3% (8.0-10.9) | holds |
| R6 | `api_reuse` owns nothing | ≤ 1% | **3.8%** (70 asks) | **fails** |
| R7 | the families cover the work | NEW ≤ 10% | 0.3% | holds |

Four of seven fail. As pre-registered, the failures are reported as failures, and the proposal
changes to follow the larger set (§4).

## 1. What the larger set says

| family | share of asks (95% CI) | PRs | owned by an arm | explicit fit | 60-PR share |
|---|---|---|---|---|---|
| F1 proof | **22.1%** (18.8-25.7) | 179 | 98% | 79% | 20.6% |
| F6 statement and API design | **14.3%** (12.3-16.5) | 171 | **39%** | 16% | 7.5% |
| F10 documentation | 12.4% (10.2-14.7) | 141 | 95% | 38% | 12.1% |
| F9 formatting | 11.8% (9.8-13.8) | 132 | 94% | 38% | 7.5% |
| F8 naming | **9.7%** (8.0-11.6) | 118 | 95% | 79% | 2.8% |
| F12 PR level | 6.3% (5.1-7.7) | 99 | **1%** | 0% | 14.0% |
| F5 redundancy | 4.3% (3.1-5.6) | 57 | 56% | 15% | 4.7% |
| F3 registration | 4.3% (3.2-5.5) | 57 | 14% | 6% | 9.3% |
| F7 generality | 3.4% (2.4-4.4) | 46 | 98% | 68% | 2.8% |
| F2 interface | 3.3% (2.4-4.3) | 46 | 85% | 26% | 11.2% |
| F11 meta-code correctness | 1.1% | 16 | 25% | 0% | 2.8% |
| F4 derive, don't restate | 0.9% | 15 | 63% | 31% | 4.7% |
| mathematical correctness | 0.6% | 11 | 100% | 91% | 0% |
| NEW | 0.3% | 3 | – | – | – |
| contested | 5.1% | 74 | – | – | – |

**The unowned fifth is three families.** The 393 unowned asks are:

| family | unowned asks |
|---|---|
| statement and API design (F6) | 122 |
| PR level (F12) | 111 |
| registration (F3) | 62 |
| redundancy (F5) | 30 |
| everything else | 68 |

API design is now the largest gap. It is twice the 60-PR share, and only 16% of its asks fit an
arm explicitly.

**What the 60 PRs got wrong, and why.** Sixty PRs carried 107 asks, and a few PRs weighed heavily:
- Two PRs carried 6 of the 12 binder asks (F2), which is why interface came out at 11% there
  against 3% here.
- Registration asks sat on 6 PRs (9.3% there, 4.3% here).
- Naming happened to be light: 3 asks. At scale it is 9.7% and well owned: the `naming` arm fits
  140 of 178 explicitly.
- `api_reuse` owns 70 asks (3.8%). The 60-PR "owns nothing" was a small sample.

The audit said counts at 60 PRs were not rates; this is what that caveat looked like in practice.

**What holds.**
- The division still names only 42% of review work explicitly.
- A PR-level unit is still needed: 9.3% of asks are PR-grain, and 99% of PR-level asks are unowned.
- The codebook covers the work: 6 NEW asks in 1,833. Two of them recur and are worth a family:
  - simplifying or speeding up tactic and linter code (5 asks, the same question from both
    readers);
  - build-performance cost (2).

**AI-generated PRs look different** (205 asks on 83 PRs, against 1,628 on 559):

| | AI PRs | other PRs |
|---|---|---|
| PR-level asks | **16.1%** | 5.1% |
| meta-code asks | 4.9% | 0.6% |
| documentation asks | 16.1% | 12.0% |
| proof asks | 17.6% | 22.7% |
| naming asks | 5.4% | 10.3% |
| unowned asks | 24.9% | 21.0% |

The project's eventual target raises exactly the family no arm owns. Being wanted, described and
coordinated is the first question maintainers ask of an AI PR.

**Month to month (exploratory, not pre-registered).**
- The unowned share runs from 10.7% (June 2025) to 29.1% (January 2026), mostly 19-28% from July
  on.
- API design stays at 11-18% throughout.
- Naming drifts down, from 13.6% to 7.5%.
- Nothing here is a trend claim at these counts.

## 2. The dev set, placed against both

The dev set is 16 PRs, 48 asks, one reviewer on 58% of its comments. Against 1,000 PRs:

| family | dev | 60 PRs | 1,000 PRs |
|---|---|---|---|
| naming | 29% | 2.8% | 9.7% |
| API design | 8% | 7.5% | 14.3% |
| registration | 0% | 9.3% | 4.3% |
| PR level | 8% | 14.0% | 6.3% |

Naming is overweighted by 3× on dev, not 10×. API design is underweighted on dev by about half.
The audit's headline, that the pipeline was shaped by a set unlike review work, stands; its size was
overstated by the 60-PR sample in the direction of the families it happened to over-sample.

## 3. The settings at scale (the audit's Part 3, not pre-registered)

**How it was computed.**
- The audit's gold-free features were rebuilt for val1000 with the tree's own functions: the
  release build, `enumerate_invocations`, `build_components` and `plan_coverage`.
- They cover 970 of the 973 PRs. The other three reorder an import block, which the inventory
  builder refused. That is fixed in `e0c22f9`, after these numbers were computed.
- No model was called. Review text was read for one count only, marked below.
- The per-stratum features are in `knob_features.json`, next to the labels. The structure build
  itself (release files for 970 PRs) is not kept: it rebuilds from the draw and the store.

| | dev (16) | 60 PRs | val1000 (970) | of which AI (123) |
|---|---|---|---|---|
| units per PR, median / max | 5.5 / 15 | 3 / 66 | 3 / 76 | 3 / 52 |
| PRs over 15 units | 0 | 7 (12%) | 41 (4.2%) | 12 (9.8%) |
| packer-cliff PRs, and their share of units | 0 | 3, 32% | 2, 2.9% | 0 |
| whitespace-only `modified` declarations | 0 of 124 | 120 of 344 | 102 of 3,517 (2.9%) | 8 of 238 |
| units holding only those | 0 | 85 (20%) | 32 (0.8%) | 8 (1.1%) |
| removed declarations, on how many PRs | 13, 4 | 92, 14 | 912, 205 (21%) | 77 |
| targets on Tactic, Linter, test or script paths | 0 | 90 | 1,114 (5.7%) | 344 (14.3%) |
| proposals the lead sees, median / max | – / 143 | – / 649 | 20 / 500 | 20 / 159 |
| PRs over the 184-proposal agenda `lead_cost_cap` was sized for | 0 | 6 | 15 (1.5%) | 0 |
| PRs at the required-row cap | 4 (25%) | 12 (20%) | 160 (16.5%) | 16 (13%) |

**The audit's ranked knobs, at scale.**

1. **The packer charge is real but rare.**
   - Two PRs of 970 have a shared hunk over the 24,000-char budget: 27250 (29,918 chars) and
     32245 (33,740).
   - They hold 123 units, 2.9% of the set. At 60 PRs the figure was 32%, because three of the 60
     were such PRs.
   - The two are the largest and fourth-largest PRs in the set: 76 units for 89 targets, and 47
     for 60. So the cliff produces the tail that the size knobs then meet.
   - Worth fixing, by charging for rendered text, but no longer first.
2. **Whitespace-only edits are small.**
   - 2.9% of modified declarations, and 32 units (0.8%).
   - The 60-PR figure came from two sweep PRs (26718, 33716).
   - A filter is cheap and correct, and little rides on it.
3. **The flat lead limits meet a tail of 1.5%.**
   - 15 PRs exceed the 184-proposal agenda. The median is 20 and the p90 70.
   - For those 15, the audit's untested question is still open: does a lead stopped at its cap lose
     its PR's arm output (`runner.py:541-542`)?
4. **The lifecycle rule holds, and at scale it is the largest knob.**
   - **The proof arms under both lifecycles.** Eligible on 2,087 main units, against 938 under v4's
     modified-only rule (2.2×). On AI PRs, 155 units against 38 (4.1×).
     - 60 PRs: 2.4×, and 26× on AI.
     - Whether the widening is right is a gold question, so it is a large scheduling choice that
       nothing has measured.
   - **No arm is eligible on a removed declaration,** and 21% of PRs remove one (912 declarations
     on 205 PRs). That is where reviewers ask for a deprecated alias.
     - 44 asks on 26 PRs mention deprecation, and reader A gives 26 of them no owner. This is the
       one count that read review text.
     - Of reader A's 34 unowned redundancy (F5) asks, 28 mention deprecation, renaming or removal.
       That is a keyword match, not a re-read.
     - So §1's fourth unowned block, redundancy's 30 asks, is mostly this knob.
5. **The required-row cap holds, and it binds on one PR in six:** 160 of 970 (60 PRs: 20%).
   - In those PRs, 724 of 1,484 units with an eligible specialist get a required one (49%).
   - In the 37 with more than 10 eligible units, the share is 29%.
   - The worst is 32245: 6 of 76.
   - Which units get the ten slots is decided by hash order.
6. **`naming_norm`'s bars:** not recomputed. They are owned by the naming branches.
7. **The intent keywords:** not recomputed. Their precision needs the PR descriptions read.

**AI PRs, structurally.**
- **Larger:** p90 14 units against 8, and 9.8% over 15 units against 3.4%.
- **More meta code:** three times the share on Tactic, Linter, test or script paths, 14.3% of
  targets against 4.5%.
- **More new code:** 610 added declarations to 238 modified, against 5,724 to 3,279 on main.
- **Where the knobs bind:**
  - Under the both-lifecycles rule, the proof arms reach four times the AI units v4's rule
    would.
  - The packer cliff and the 184-proposal tail are main-only.
  - The cap binds a little less often (13% against 17%).
- **Consistent with §1:** meta-code asks are 4.9% of AI asks and 0.6% of the rest, and only 25%
  of them have an owner.

Under the full ten-arm roster, 194 units (4.6%) have no eligible specialist. That is not
comparable with the audit's 21.6%, which was for the lean five-arm roster.

## 4. What changes in the proposal

The families-first re-division (`registry.FAMILY_DIVISION`, on `arm-division`) was cut to the
60-PR counts. At scale:

- **`design` becomes the main lever.** API design plus generality is 17.7% of asks, 325 on 203
  PRs, and 122 of its asks are the largest unowned block.
  - The per-job review of the four-PR run found `design` hurt more by a gate than by its question
    (`docs/research/family-division-fanout4-review-2026-09.md`).
  - Its gate is now fitted (`53161eb`).
- **`pr_level` is justified mainly for AI PRs:** 16% of their asks, 5% of the rest. It is worth
  scheduling where AI evidence exists, and it needs the PR-level verdict built in `53161eb`.
- **`interface` shrinks.** Binders are 3.3% and 85% owned already, by `style`. Registration is
  4.3% and mostly unowned: 62 asks, the third unowned block. Registration still has no owner, but
  a whole arm for binders and registration is not justified by these counts. Fold registration
  into `formatting`'s or `design`'s remit, or keep a small `interface` and measure it.
- **`naming` stays:** 9.7%, and the one arm whose remit fits most of its family explicitly.
- **`library_fit` keeps `api_reuse`'s work:** 70 asks, which the merge was right to keep.
- **Add meta-code quality to `correctness`,** or give it a small arm: simplify or speed up tactic
  and linter code, and is new behaviour tested. It is 1-5% overall and 5% of AI-PR asks.
- **The knob fixes re-rank (§3).** Two come first:
  - an arm eligible on removed and renamed declarations, asking whether the old name keeps a
    deprecated alias, for `library_fit` or `pr_level`;
  - a required-row cap that spreads its ten slots across units rather than taking them in hash
    order.

  The packer charge and the whitespace filter stay as cheap hygiene, at 3% and 1% of units.

The measurement the audit fixed still stands: current against re-divided on small12's asks. It
should now run with the three framework fixes on both sides (`eec8d3a`, `814ed69`, `db07c83`),
since they changed what every arm reads.

## Caveats

- **Model readers.** Two readers of one model family, calibrated against one human-free
  adjudication. A human sitting outranks all of it.
- **Round-1 asks, not gold.** No gold exists for this set, and the gold chain may score fewer
  PR-level asks.
- **The families are the auditor's construction.** They were fitted on 60 PRs and hold on 1,000
  (0.3% NEW); that is coverage, not proof they are the right cut.
- **§3 counts structure, not outcome.** It says where a knob binds, not what binding costs in
  recall.
- **The AI stratum is 83 PRs with feedback,** and one author dominates AI PRs in this window
  (`docs/todo/eval-set-selection.md`).
