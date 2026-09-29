# The reviewer-model gap: is the binding constraint the model, not the coordination?

**Status** — open, 2026-09-29. Two cheap tests, below.
**Cost** — (a) free: Claude session time plus a few reviewed-workspace builds; (b) about $1 on
`gpt_5.2`.

**Motivating example.** `results/pr_review_v5/probes/construction-demo-2026-09-29/`. On three
validation small12 PRs (34091, 30458, 32875), Claude reviewers with the pipeline generalist's own
brief, the arms' tools and a pass-0 PR model reached **5-6 of 11** asks, stably across two
replicates and two blind matchers. The pipeline's lead run on `gpt_5.2` reached **none** of the 11.
The pipeline's whole-PR solo baseline (`val-small12-2026-09-25/match_solo`) holds the same tools and
has no work units and no pruning. It reached **none** of the five asks that every Claude reviewer
set reached:
- three instance-binder asks on 34091;
- two "does the old proof work?" asks on 30458.

The design-level interventions tried since September (facet brief, hard cells, PR-level job,
constructions) each moved Claude's reach little. The difference between Claude and `gpt_5.2` on
these asks is the whole distance.

**The causes this does not separate:**
- **recall:** every PR is inside Claude's training window (June 2026 cutoff);
- **the model:** `gpt_5.2` with reasoning off (`reasoning-in-the-arms.md`: 0 reasoning tokens in
  2,857 of 2,857 arm attempts) against Claude;
- **the harness:** `ape_agent` against a Claude agent with a shell;
- **the packet and brief:** X had the pass-0 model and the generalist checklist, while solo had the
  solo brief and no model.

## The two tests

1. **After the cutoff (free).**
   - Draw about five PRs created after 2026-06 from the PR store that hold round-1 asks of the
     binder, pre-PR-proof or golf kind, and build their reviewed workspaces.
   - Run the construction demonstration's X condition twice, with the same matchers.
   - If Claude reaches such asks at a similar rate, the gap is ability or harness, not recall.
2. **The pipeline's model on the same packet (~$1).**
   - Run `gpt_5.2` through `cli run` (the solo scaffold) on the three PRs, with the X brief and the
     pass-0 model as its prompt, reasoning off and then on.
   - If it reaches the binder and pre-PR-proof asks, the packet or brief matters.
   - If it does not, the model or the harness does.

**What would close it.** A small table of reach on the same asks, by model × brief/packet ×
window, with two runs a cell. The next generator change should then be decided by which factor
carries the gap. If it is the model, coordination designs should be measured on the model that will
run them, before any more are built.
