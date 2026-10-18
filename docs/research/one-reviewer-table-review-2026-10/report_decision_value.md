**Adversarial review of `docs/plans/2026-10-10-one-reviewer-table.md`: decision value and statistical adequacy.** I worked read-only. The figures below are mine, computed from committed match tables and audits; nothing spent.

1. **The table cannot explain the disagreement it was commissioned for.**
   (a) P14 and D12 differ in their PRs, their scorer (blind matchers against judge v9 with change-id pairing) and their gold unit. The rule says "report the disagreement, do not choose" (l.83). DeepSeek ≈ gpt is not an artifact of the ten PRs. It holds on all 14 and in each sub-set: validation DX 5-6 vs GB 4 of 25, post-cutoff 3-4 vs 3,3 of 14. On D12 the reps are 8,6,9 vs 3. So the likely result is the same disagreement, with no way to say why.
   (c) Blocks.
   (d) One blind-matcher seal over D12's 23 obligations and its sessions, so one scorer spans both sets. About 0.3-0.5M tokens, far less than X3.

2. **"DeepSeek near Claude on dev" comes from the project-harness Claude, and the plan drops that row.**
   (a) Choosing brief X (l.40) makes the disagreement vanish by definition, not by data.
   (b) Hygiene has 9,9,7 on disk (`hygiene-layer` 938ff65e). Against DeepSeek it is +0.7 of 23, PR-bootstrap [−3.3,+5.7]. beating-solo l.71 cites only 7,7.
   (c) Distorts.
   (d) Add hygiene as a D12-only row, re-judged on ELM for pennies. Label each Claude row with its harness.

3. **The rep-range rule ignores PR clustering.**
   (a) Reps are nearly deterministic per PR: DX reps are identical on 8 of 10 PRs, and X1/X2 differ on 2 of 39 asks. So the ranges are narrow, and non-overlap can fire on one PR's worth of difference.
   (b) AP−DX: ranges 10-12 vs 5-6, which the rule calls ordered. But the PR-bootstrap is [+0.02,+0.39], and dropping PR 34091 alone takes +0.18 to +0.10. D12 X−DeepSeek: ranges separate if X3 ≥ 10, yet the PR-bootstrap is [−1.3,+8.7] of 23. The noise bands (l.77-78) leave out PR sampling, the largest term.
   (c) Distorts.
   (d) Also require that a paired PR-cluster bootstrap on the same seal excludes 0 on both matchers, plus a leave-one-PR-out range. State the minimum detectable difference now: about 0.18 on P14 and about 5 of 23 on D12. On that rule, DeepSeek vs gpt on P14 (about 1 ask apart) cannot be answered by construction.

4. **No decision depends on the gpt row.**
   (b) gpt was slated to be parked: after-structure's last step reads "one gpt-5.5 xhigh run, then park gpt". DeepSeek is already ≥ gpt on both benchmarks. The fill costs about £70, 18% of what ELM has left. The defect row at l.13 overstates: D12's gpt rep already ran contract v2, and ELM parity was measured (`elm-parity-2026-10-05`).
   (c) Distorts the spend.
   (d) Run gpt on P14 only, three reps (about $42). On D12, keep rep 1 re-judged.

5. **The comparator is wrong.**
   (b) §4(a) and §0 (l.176) set the comparator as DX_i∪DX_j, paired by rep. From the AP seal: AP_i∪DX_i reaches 10,13,13 against DX_i∪DX_j 5-7 of 33.
   (c) Distorts.
   (d) Add the derived rows DX∪DX and AP∪DX to every cell. They cost nothing.

6. **The cell that tests "beats solo" is missing.**
   (a) DeepSeek + AP (0.34) ≈ Claude X (0.36), and Opus is already in AP's loop as the selector. Whether conventions beat the best solo reviewer, or only lift DeepSeek to Claude's level, needs Claude with AP's delivery. Stage A (sentences, no precedence) gave only +0.03, and l.51 excludes the cell.
   (c) Distorts the decision.
   (d) Spend X3's budget on one Claude + AP rep on P14 (14 sessions), marked as one rep.

7. **X3 buys almost nothing.**
   (b) X1/X2 agree on 37 of 39 asks and score 11, 11 on D12. X3 costs 2.6 windows, competing with the fresh set's 40 selectors (about 1.2 windows).
   (c) Distorts.
   (d) Cut it. Report Claude at two reps with the agreement stated.

8. **"AP off the ten PRs" is mostly arithmetic.**
   (b) P14's other four PRs add 6 in-census asks, of which DX already reaches about 3.3. The ten PRs' gain is +5.7 of 22 on validation against +0.3 of 11 post-cutoff, although the selector's picks held the right convention at similar rates (15/22 and 7/11).
   (c) Minor; pooling the sets hides this.
   (d) Report validation and post-cutoff separately, and call the four-PR extension a harm check.

9. **AP on D12 cannot be read as specified.**
   (b) Dev's census share was never measured (steelman step 1). The expected gain, +1 to +3, sits inside the noise. Running 12 PRs instead of 15 drops the three controls that §4(d) needs.
   (c) Distorts.
   (d) First label dev's obligations against the census (about 0.1M tokens) and state the expectation. Run all 15 PRs.

10. **An early stop leaves nothing readable.**
    (b) Reading waits for every cell (l.72), and the P14 seal waits for X3 (l.61-62), the step the plan itself says to cut first.
    (c) Distorts.
    (d) Re-judge the D12 runs already on disk first. Seal P14 without X3.

11. **The fresh set should get the paid capacity.**
    (a) The in-sample paid cells (gpt, X3) answer questions the runs on disk nearly answer already. With 34 PRs, the fresh set roughly halves the PR-level interval.
    (c) Distorts.
    (d) Start its builds now. Spend the Claude and ELM budget on its selectors and a Claude reference rep. Note it is validation-window, where AP's gain sits, so it tests overfitting to these PRs, not the validation/post-cutoff split.

12. **Measures.**
    (a) In-census asks are exactly where AP acts. Recall tracks volume (0.09-0.12 hits per finding for every reviewer), yet the rule never uses findings per PR.
    (c) Minor.
    (d) Headline all asks for reviewer ordering. Report yield and added-findings yield. Compare the 12-session seal's reading of the AP-seal sessions against the AP seal, tolerance 0.06.

**Recommended minimal version**
1. Free first: re-judge D12's on-disk runs (X, hygiene, gpt) on ELM; add the derived rows DX∪DX and AP∪DX; add paired PR-cluster bootstraps; split P14 into validation and post-cutoff.
2. Add hygiene as a D12 Claude row, and label each row's harness.
3. Before running AP on D12, label dev's census share and state the expected result.
4. DeepSeek + AP: selectors, then three reps on P14's 4 PRs and all 15 D12 PRs.
5. gpt contract v2, three reps on P14 only; D12 keeps rep 1.
6. One P14 seal with no X3; one matcher seal over D12, so a single scorer spans both sets.
7. Ordering requires both non-overlapping rep ranges and a PR-bootstrap that excludes 0; state the minimum detectable differences before collecting.
8. Instead of X3: one Claude + AP rep on P14. Start the fresh-set builds now; it gets the remaining Claude and ELM capacity.

My scratch scripts are `/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/592272bf-2a21-4fd7-84f0-c3c437872216/scratchpad/power.py` and `dev.py`. Nothing in the repo was changed or committed.
