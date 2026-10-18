**Adversarial review: comparability and confounds in `docs/plans/2026-10-10-one-reviewer-table.md`**

**Findings**

1. **The Claude row and the ape rows run in different harnesses, and the harness alone moves Opus by about 4 of 23 on dev.**
   - (a) In the X route, Opus works as a Claude Code subagent. It has Bash, Claude Code's system prompt, and CLAUDE.md plus MEMORY.md in its context. gpt and DeepSeek run under ape_agent with a fixed tool set.
   - (b) The X1 transcript (`~/.claude/projects/…/029323d7…/subagents/agent-a0044c43a51a25eda.jsonl`) shows "Contents of …/CLAUDE.md" (~15.5k chars, CLI 2.1.284) and MEMORY.md injected. On dev, Opus scores 11 and 11 under X, against 7 and 7 under the project harness (audits `probe-dev-opus55-contract2-claude-sub-rep1/2`; with hygiene 9, 9, 7). That gap is bigger than the ±2 noise band.
   - (c) Distorts; blocks the claim "DeepSeek+AP ≈ Claude solo".
   - (d) Label the row "Opus, Claude Code X route". Add the existing `opus55_contract2_claude_sub` reps to D12, re-judged on ELM, as the like-for-like Claude row. No new generation needed.

2. **Different training windows confound every cross-model comparison.**
   - (a) Stage D read only within-model differences because "all three share the same memory" (README:892-894). This table reads differences between models. The val 8 PRs and dev 12 PRs fall inside Claude's training window (cutoff June 2026). DeepSeek-V4.1 was released 2026-09-10 with no public cutoff, so the post-cutoff 6 may be inside its window.
   - (c) Distorts "where DeepSeek sits".
   - (d) Report P14 per set (val and post) for every row, and state each model's cutoff against each set's dates in the table.

3. **X3 is not a third rep of X1/X2.**
   - (a) Every X1/X2 session ran on 2026-09-29: `calls.jsonl` stamps run 06:55-17:50 EDT, on 2.1.284. That was before `5e215ffe` (2026-09-30), which fixed `declaration_search`'s false "already exists" results. X3 would run on 2.1.285, headless, with today's tools and today's CLAUDE.md (22k chars). The route control covered only 2 PRs and 7 asks (README:374-385).
   - (a') The label `X3` already exists, finished, on 30458 and 32875 (X4 on 34091 too), in `construction-demo-2026-09-29`. `run_claude_batch.sh` stops on "a finished session".
   - (a'') On D12, `import_probe_session` refuses any session missing a PR from the spec's 15 (`probes.py:1255-1257`), so 12 sessions cannot be imported.
   - (c) Distorts the Claude row. Cutting step 4 leaves only two reps, both on the old tools.
   - (d) Give the new sessions a fresh label and run them on all 14 P14 PRs and all 15 dev PRs. Report them beside X1/X2, not pooled with them.

4. **DeepSeek's D12 solo reps and the planned D12 AP reps ran on different servers.**
   - (a) The keepthink reps 1-3 used a plain server: DSpark off (local-ds41 README:249), with backend flags passed by hand. Since `8538502a`, DSpark is the default, so AP would run with it. Only one DSpark rep exists (6 of 23). Server flags are not recorded in any run plan.
   - (c) Distorts AP − solo on D12.
   - (d) Run 3 new solo D12 reps in the same server job as the AP reps. It is free, about 35 min a rep.

5. **All three AP reps share one selector draw.**
   - (a) There is one Opus selector a PR (`selectors/pr*.json`), so the reps vary only the reviewer. Selector variance is large: DeepSeek as selector reads 0.43 mean against 0.64 for the union of its samples.
   - (c) Distorts. The "rep ranges do not overlap" rule will overstate how sure an AP ordering is.
   - (d) State in the reading rule that AP's range is conditional on a single pick set.

6. **The AP-extension tooling cannot do what the plan says.**
   - (a) `context_ap.sha256` holds whole-file digests, so it cannot check that a 14-row file keeps the ten PRs' rows.
   - `build_context.py ap` rewrites `context_*_ap.jsonl`, `examples_ap.json` and `context_ap.sha256` in place. That overwrites the record of what the existing AP runs saw.
   - `run_ds41.sh` accepts only `base|exact|prec|ap` (so `ap4` exits 2), and it sets `pr_numbers` from every row in the context file.
   - The probe-PR assertion lists only the val and post PRs, not dev.
   - (c) Minor, but it corrupts provenance.
   - (d) Add a new level with its own files and digests. Compare the ten rows by per-row hash. Add the dev PRs to the assertion. Check that the dev model sections are byte-equal to `model-gap-dev-medium-0.3.0/model_context.jsonl`.

7. **Matchers can tell the harnesses apart.**
   - (a) `repo_target` strips only workspace prefixes. Claude targets read as prose ("module_doc in Mathlib/…/Upcrossing.lean (section …)"); ape targets are `path:line`.
   - `_REDACT` removes only "pass N" and "cNN". AP findings say "the convention requires…" in 7 of 25 findings (`iter_ds41_conv_val_ap_rep1`), against 2 of 28 in base.
   - `_claude` does not apply the 20-finding cap. The P14 maximum is 13 today, so it does not bind yet.
   - (c) Minor, can distort.
   - (d) Render Claude targets through `resolve_target`, redact convention phrasing, and apply the 20-finding cut in `_claude`.

8. **The 12-session seal is larger than any seal matched so far.**
   - (a) The largest so far is D23_val: 8 PRs × 8 sessions, 251 findings, about 181k tokens a matcher (README:1198). The new val seal is 8 × 12, adding Claude and gpt sessions, which file more findings. That is roughly 400 findings, so a matcher may compact partway through.
   - (c) Distorts consistency within the seal.
   - (d) Keep one seal, but give each matcher instance batches of PRs, with all 12 sessions of a PR together.

9. **Judge fork: confirmed.**
   - (a) X1, X2 and `gpt55_contract2_rep1` were judged on `gpt_5_mini` (identity 0711a6c0). The DeepSeek reps were judged on `elm_gpt_5_mini` (6238bc81). Re-judging moved Opus's contract-v2 rep1 from 7 to 8. The X dev sessions ran on 2026-09-29, not 2026-10-01 as the plan says.
   - (c) The re-judge the plan already includes is required.
   - (d) Re-read X's "11, 11" only after the re-judge.

10. **Smaller asymmetries.**
    - Effort is xhigh for Claude and high for the other two; state it in the table.
    - The ELM gpt configs add `openai_responses_reasoning_summary: auto`, marked "unverified on review sessions". The new config should pin it and state both reasoning lines.
    - Caps differ (gpt 20.00 / 24M, DeepSeek 13.40 / 16.08M) but do not bind: the largest sessions used 3.35M and 5.74M tokens.

**Verified as correct**

- **DeepSeek's P14 and D12 runs share one configuration.** The `config.json` files differ only in context file, PR list, concurrency (12 vs 15) and paths. The dev reps have the same `scaffold_config_sha256`. Between 0c3da787 and eaaf37f1, `src` changes only in `analysis/probes.py` and `review/cli.py`.
- **The reviewers saw the same PR model.** `context_val_base.jsonl` is byte-identical to `model-gap-val-small12/model_context.jsonl` (a5ef1b85). Every X packet's `model.md` equals the matching ape context row on all four sets.
- **gpt contract v2 matches DeepSeek's setup apart from the model.** It differs only in model, API and caps: same G2 brief, user prompt v2, `request` filing bar, `per_object_family` notes and tools, and reasoning `high` for both.
- **Census disjointness holds.** None of the 16 dev PRs is among val1000's 759, outside_window's 300 or outside_years' 129.
- **The numbers on disk match the plan.** Dev: X 11 and 11, DeepSeek 8, 6, 9, gpt 3. Across seals, X reads 0.27-0.39 on the ten PRs (`read_common.py` reproduces it).
- **The D12 Claude import applies the 20-finding cap.** X1: 139 raw findings, 129 after the cut.
- **Blinding mechanics are as described.** Labels are shuffled per PR, and matchers see only target, claim, requested change and severity.

Everything was read-only: nothing was edited or committed, and no LLM was called. The one script I wrote was a config-diff helper in the scratchpad.
