# The one reviewer table (2026-10-10)

The plan, the reading rule and every row's configuration are in
`docs/plans/2026-10-10-one-reviewer-table.md`, revised after the review round in
`docs/research/one-reviewer-table-review-2026-10.md`. This folder holds the scripts and the record.

## What runs where

| cell | script | where | started |
|---|---|---|---|
| fresh set's reviewed workspaces | `prebuild --reviewed` | Slurm 449292 | 04:31; 37 of 39 built by 10:19 (26083 and 35571 failed, below) |
| gpt-5.5 contract v2, P14 and D12, 3 reps | `run_gpt.sh` | Slurm 450109 | 10:45 |
| D12 re-judges on `elm_gpt_5_mini` | `rejudge_dev.sh` | shell | 10:49; done 11:06 |
| 19 blind selectors | `run_claude_batch.sh @selectors` | primary token | 10:50; done (audit: `audit_selectors.txt`) |
| DeepSeek: apt on P14's 4 PRs; D12 solo and apt | `run_ds41_gate.sh` | Slurm 450144, server 450145 | 11:05; server up 11:18 |
| Opus T1 and TA1 on P14 | `run_claude_pair.sh` | Slurm 450195 | 11:09 |

**The fresh set's two failed builds, to settle before its test.**
- **35571:** its round-1 reviewed state does not compile. `BrownianMotion.lean:22:13` reads
  "unexpected token 'section'; expected 'lemma'", so like 33057 it has no reviewed workspace and never
  will (`.claude/rules/mathlib-review.md`).
- **26083:** a module the diff does not change, `Mathlib.LinearAlgebra.Pi`, fails on the path between
  the changed modules. Before calling it a red state, compile the patched changed files against the
  base, as that rule says.
- **Either way the fresh-set runs** drop these PRs or accept the overlay. Which one is decided before
  its pre-registration.

## The Claude pair's transcript audit (read 2026-10-10, before any matching)

`audit_batch.py` over the 14 pair streams: 12 batches clean, and 5 flags in two batches.
- `pair_T1_1`: 30641 T1, 1 flag.
- `pair_T1_4`: 42184 T1, 4 flags.

All five are one benign pattern, the one stage F and the selectors recorded:
- the session writes a file inside its own packet (`$D/tmp/v1.py`, `$D/tmp/write.py`, or
  `findings.json` by heredoc);
- it runs the file with the project's Python by absolute path;
- it passes the resulting JSON to its own `$D/ptool lean_verify_edit`.

The Python binary is the only path outside the packet, and nothing outside the packet is read. The
finisher clears exactly these two (`FLAGS_READ=pair_T1_1,pair_T1_4`).

**The P14 matchers' audit.** Four post-cutoff matcher folders ran. One flag, in `b1/m1`: it built
its `matches.json` with its own `tmp/build.py`, run by the project's Python. That script opens only
its own folder's `R*_pr*.json` and writes `matches.json`; the other three did the same with the
system `python3`, which the audit does not flag. Read by hand, cleared, and unblinded with
`run_matching.sh ... merge`.

## Step 1, provisional: D12 issue recall for the rows on disk, all on `elm_gpt_5_mini`

Read 2026-10-10 from `audits/<slug>(.elm)/semantic_report.json`. These are not the table's cells: the
new D12 runs replace the gpt and DeepSeek rows.

| row | reps (of 23) | findings, 15 PRs |
|---|---|---|
| Opus 5.5, X route (2026-09-29) | 12, 11 | 119, 130 |
| Opus 5.5, project harness (contract v2, `claude_sub`) | 8, 7 | 99, 97 |
| Opus 5.5, hygiene (finding budget 40, write tools; not like-for-like) | 10, 9, 8 | 93, 103, 102 |
| gpt-5.5, contract v2 (OpenAI endpoint, 2026-10-01) | 3 | 39 |
| DeepSeek-V4.1-Flash, keepthink (plain server) | 8, 6, 9 | 60, 51, 54 |

So "DeepSeek near Claude on dev" holds against Opus under the project harness. Against the X route,
the Claude that P14 uses, Opus is ahead by 3 to 6 obligations, and files about twice as much.

## The D12 census share, and AP's expected effect there (written before any D12 AP session is read)

- **Census share.** Two blind readers labelled D12's 47 agreed asks against reader A's codebook,
  assign-only (`build_reader_folders.py <dir> configs/probe_sets/dev_medium_0_3_0.yaml`). Both
  transcripts audit clean, at 10 tool calls each.
  - **40 of 47 are in census** (either reader); 38 by both; the same primary entry on 37.
  - P14 has the same share: 39 of 46.
  - Labels: `conventions-ceiling-2026-10-04/readers_dev/`; per ask: `asks_dev_census.json`.
- **Retrieval.** The apt picks hold the entry of **29 of the 40** in-census asks (0.72). On the ten
  stage F PRs it was 22 of 33 (0.67).
- **Expectation, if the ten PRs' rates transfer.** On those PRs AP reached 0.50 of picked asks
  against solo's 0.20, and 0.03 of unpicked ones against 0.09. Applied to dev's split:
  0.72 × (+0.30) + 0.28 × (−0.06) ≈ **+0.20** of in-census reach on the matcher scorer.
  - On the judge's 23 obligations that is about +2 to +4.
  - It is inside D12's minimum detectable difference of about 5, so the judge alone cannot read it.
  - The matcher seal over the 47 asks is the instrument that can.

## Result (2026-10-10): the one reviewer table

Every cell read by the plan's rule (`read_table.py`; full output `table.txt`). P14 is one seal a set,
and D12's matcher scorer is one seal over its 47 agreed asks. Reach is per session, matcher 1, with
matcher 2 within 0.04 everywhere. Sessions a row are in brackets.

| reviewer | P14 all asks (46) | P14 in census (39) | D12 all asks (47) | D12 in census (40) | D12 judge, of 23 | findings a PR, P14 / D12 |
|---|---|---|---|---|---|---|
| gpt-5.5, contract v2 [3] | 0.24 | 0.21 | 0.28 | 0.26 | 2, 5, 5 | 1.8 / 3.3 |
| DeepSeek-V4.1-Flash, contract v2 [3] | 0.28 | 0.22 | 0.40 | 0.38 | 7, 6, 7 | 2.6 / 5.1 |
| DeepSeek, two solo reps unioned [3 pairs] | 0.32 | 0.26 | 0.43 | 0.41 | | |
| **DeepSeek + AP** [3] | **0.41** | **0.38** | **0.39** | **0.38** | 8, 6, 4 | 4.6 / 8.1 |
| Opus 5.5, project harness [2] | | | 0.52 | 0.50 | 8, 7 | — / 8.3 |
| Opus 5.5, X route, 2026-09-29 [2] | 0.47 | 0.46 | 0.62 | 0.56 | 12, 11 | 4.9 / 10.5 |
| Opus 5.5, X route, today (T) [1] | 0.48 | 0.46 | | | | 5.4 / — |
| **Opus 5.5 + AP, today (TA)** [1] | **0.67** | **0.69** | | | | 14.3 / — |

**Orderings that pass the rule** (reps apart, and the PR-bootstrap interval excludes 0 on both
matchers):
- **Claude (X route) over DeepSeek, on both benchmarks:** +0.19 on P14, +0.22 on D12 (matcher), and
  +4.8 obligations on the judge.
- **Opus over itself, by harness:** the X route beats the project harness on D12, +0.10 (matcher)
  and +4.0 (judge).
- **DeepSeek over gpt-5.5 on D12** (+0.12).
- **DeepSeek + AP over DeepSeek on P14's in-census asks** (+0.15, pooled).
- **Opus + AP over same-day Opus solo,** on each P14 set: +0.20 pooled, +0.20 on validation and
  +0.19 on post-cutoff.

**Read as indistinguishable:**
- DeepSeek against gpt-5.5 on P14 (+0.04), and on D12's judge (+2.7, interval [0.0, 5.7]).
- DeepSeek against Opus under the project harness on D12 (+0.12, reps apart, interval spans 0).
- Opus X route, 2026-09-29, against Opus X route today (−0.01).
- DeepSeek + AP against two DeepSeek reps unioned, on every benchmark.

**AP on DeepSeek, per set** (all asks, AP − DX):

| P14 validation (8 PRs) | P14 post-cutoff (6 PRs) | D12 (12 PRs) |
|---|---|---|
| +0.20 (interval touches 0 on matcher 1) | 0.00 | −0.01 (judge −0.7) |

The expectation written before D12 was read was about +0.20 of in-census reach. It was not met: the
picks held the entry of 29 of 40 in-census asks, and DeepSeek's reach did not move.

**Reading, provisional:**
1. **The question behind the table resolves.**
   - On P14 DeepSeek sits with gpt-5.5 (the same configuration now: +0.04).
   - On D12 it sits above gpt and level with Opus under the project harness.
   - Opus on the X route, the Claude of the probe tables, is ahead of DeepSeek on both benchmarks.
   - The Opus harness gap (+0.10, +4 obligations) is as large as DeepSeek against gpt. Part of
     "Claude against the rest" is the harness, not the model.
2. **AP's DeepSeek gain is confined to validation small12.** Those are the 8 PRs that stages C to AP
   were designed and read on. On the 6 post-cutoff PRs and the 12 dev PRs it is zero, at more volume
   (yield 0.30 → 0.19 on dev).
   - The likeliest readings are in-sample fit to those PRs, or chance on 8 PRs.
   - The fresh set is validation-window and untouched, so it tells fit to the PRs from a window
     effect.
   - Untried for DeepSeek:
     - the selector's `where` delivered with each sentence;
     - fewer picks (top 10);
     - the per-place engine;
     - examples drawn from the PR's own family;
     - a delivery without the precedence paragraph's licence wording.
3. **Opus + AP is the one cell where ask-free conventions lifted the best solo reviewer,** on both
   P14 sets.
   - It is one session a PR, on P14 only, and files 2.6 times as much (yield 0.29 → 0.15).
   - A second rep on P14 and a D12 run come before anything is built on it: about 29 sessions, about
     0.75 of a five-hour window at the measured 2.5 points a session.

## Inspection (2026-10-11): before any further run, is the table valid, and how should it be read?

The user, reading the Result:
- every row scores higher on D12 than on P14 except DeepSeek + AP, which on D12 is below its own
  solo;
- the Opus picture misses two cells.

These were checked by the main session and an independent auditor, and the numbers were reproduced.
The scripts are `inspect_*.py` here and their outputs `inspect_*.txt`.

1. **Delivery is sound.** Every AP session's record holds its own PR's conventions section, byte for
   byte (39 of 39); no solo session holds one. One D12 PR, 33149, hits the 20-finding cap under AP
   in two reps of three; no P14 run does.
2. **Matching is stable** (`inspect_cross_seal`).
   - The same sessions read under the older seals and the table's differ by 0 to 2 asks a session.
   - The losses fall on every row alike (v0065 and v0066 on 30641), and no session gains.
   - So harness-blind inputs and 13-session seals did not penalise AP.
3. **"D12 is easier" is mostly ask weighting** (`inspect_weighting`).
   - One reviewer wrote 29 of D12's 47 asks. D12 has 2.5 effective authors against P14's 9.3, and its
     repeated suggestions are counted as separate asks.
   - Weighting each (PR, author, family) group as one ask, P14 → D12 reads:

     | row | P14 → D12 |
     |---|---|
     | DX | 0.35 → 0.30 |
     | gpt | 0.28 → 0.21 |
     | AP | 0.42 → 0.29 |
     | X | 0.47 → 0.52 |
     | OP | — → 0.40 |

   - Under that weighting only Claude does better on D12, and AP is no longer the exception.
   - This lens is post hoc. The plan headlines raw reach, and both are reported from here on.
4. **AP's P14 gain is the discovery sample** (`inspect_per_ask`).
   - On the ten stage F PRs the AP cell is stage AP's own sessions, the result that motivated the
     table, scored again.
   - Every AP session collected fresh reads null against DX: P14's other four PRs −0.04, D12 −0.01.
   - Of AP's net +18 cells on P14, 9 are one suggestion repeated on three theorems of 34091 (v0106-108:
     DX 0 of 9, AP 9 of 9).
   - Group-weighted, pooled P14 AP − DX is +0.07 (matcher 1's interval spans 0); validation alone
     stays at about +0.17.
5. **The D12 expectation was miscalibrated.** On asks whose entry the selector picked, AP reaches
   about 0.5 everywhere (0.50, 0.52, 0.56). DX's reach on the same asks is 0.20 on the ten PRs but
   0.49 on D12, so there was little room to gain. Where room exists on D12 (14 picked asks DX never
   reaches), AP converts 5 of 42 cells, against 18 of 48 on the ten.
6. **Crowding out is small and the same on both benchmarks.** AP loses 4 cells on P14 and 6 on D12,
   one rep each, mostly proof and documentation asks. Only one loss is on 33149, where the cap binds.
7. **The D12 judge cannot read AP:** 8, 6, 4 are one-obligation flips, under a minimum detectable
   difference of 5.
8. **The Opus gaps are a design limit, not an artifact.**
   - Stage C chose the ten PRs as those where X missed an in-census ask, so X reaches 0.94 on the other
     four and there is no headroom there.
   - All 7 asks TA reaches and no solo Opus session does are on the ten. TA's post-cutoff gain is
     42184 and 42814, both among them.
   - So TA's +0.20 is measured only where solo Claude has room to miss. It is one session.
   - D12 is where Opus + AP can be tested off the ten: 15 sessions, with a same-day Opus solo beside
     them, 30 in all.
   - The Opus project harness on P14 bears only on harness against model, and that is already measured
     on D12: +0.10, 4 obligations.

**How the table reads after the inspection, provisionally:**
- The orderings are honest about these sessions.
- Claude is ahead of DeepSeek under every weighting.
- AP on DeepSeek moved only the sessions that discovered it; every fresh cell is null.
- Opus + AP is untested off the ten PRs.

## The dev pair: Opus + AP off the ten PRs (pre-registered 2026-10-11, before any session)

The inspection's deciding cell, run at the user's go-ahead (2026-10-11).
- **Sessions.** On the dev release's 15 PRs: T1 (Opus 5.5 solo, brief X, the X route) and TA1 (the
  same with `context_dev_apt.jsonl`'s section, byte for byte), one session each a PR, the same day.
  Run with `run_claude_pair.sh dev`.
  - T1's brief and model are byte-identical to the dev X1's.
  - The 3 control PRs run because a judge import needs all 15.
- **Scoring.**
  - **Matcher:** a new D12 seal (`blinding_D12b_SEALED.json`) holding all 15 sessions a PR (the
    table's 13 plus T1 and TA1), matched harness-blind in PR batches, so TA − T sits in one seal.
  - **Judge v9:** T1 and TA1 imported as runs (`cli probe import`) and judged on `elm_gpt_5_mini`.
- **Reading rule.**
  - **The comparison:** TA − T, raw and group-weighted (`inspect_weighting`), with the PR bootstrap
    and leave-one-PR-out range.
  - **One session a row**, so the bootstrap interval decides.
  - **Ordered on both matchers:** Opus + AP's gain holds off the ten PRs chosen for solo Claude's
    misses.
  - **Interval spans 0:** the P14 gain is read as confined to those ten.
  - **On P14 the gain was +0.20,** at 2.6 times the findings. TA's findings a PR and yield are
    reported beside it.
  - **Also read:** T − X (Claude across days on dev), and every table row again under the new seal, as
    a second check of seal stability.

**The dev pair's audit (2026-10-11, before matching).** All 30 sessions finished by 09:18. There
was one flag, in `pair_dev_T1_1` (33145 T1). The session wrote its own `findings.json` by heredoc,
assigned the project's Python path to a variable it never used, and checked the file with the
system `python3`. Nothing outside the packet was read. Cleared by name (`FLAGS_READ=pair_dev_T1_1`).
