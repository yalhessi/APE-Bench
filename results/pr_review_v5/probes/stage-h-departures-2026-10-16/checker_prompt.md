# Step 4 checker brief (identical for every PR; `{PR}` and `{ITEMS}` filled per PR)

You are running a convention's own check at specific places in a Mathlib (Lean 4) pull request, with the
project's tools, for a research study. You decide nothing by taste: the compiler or the search decides.

Working directory (run every command from here): /research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading
Before any command: `export PYTHONPATH=$PWD:$PWD/src ELAN_HOME=/research/projects/proofedit/ya475/.elan`.

Your places: the packets `/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/stageh_packets_blind/<item>.md`
for items {ITEMS}, all on PR {PR}. Each packet gives the rule (sentence, trigger, **check**, exception), two
maintainer comments under it, the place (file, declaration) and the PR's code around it.

Tools, on PR {PR}'s reviewed workspace (the PR's code as reviewed, compiled against its own changes):
```
ape/bin/python -m src.mathlib_review.review.cli tool <name> --episodes inputs/probes/stage-h-v1/input/episodes.jsonl \
  --pr {PR} --workdir /tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/a142d916-dd29-4521-a449-00e1db067b18/scratchpad/check_{PR} \
  --run-config configs/pr_review_v5_stage_h_v1_build.yaml --arguments '<JSON>'
```
`<name>` is `file_read`, `lean_verify_edit`, `declaration_search` or `content_search`; run
`... tool describe ...` once to see their arguments. `lean_verify_edit` with `path`, `declaration_name` and
`new_declaration` compiles the whole file with that declaration replaced; its `outcome` is `compiled`,
`compile_errors` (an answer about the code), or `timeout`/`environment_failure` (no answer).
File paths in tool arguments start with `target/`, e.g. `target/Mathlib/LinearAlgebra/LinearPMap.lean`.

For each place, do what the rule's **check** says, and nothing else:
- **compile rules** (P005, P010, P018, P040): read the declaration (`file_read`), write at most six candidate
  edits that the check describes (P005: the goal closed by one finishing tactic, with hints; P010: the hypothesis
  deleted or the class weakened, one at a time; P018: the consecutive steps merged into one call; P040: the block
  as one term), compile each with `lean_verify_edit`. `departs` if a candidate the check describes compiles with
  no error introduced; `conforms` if none does.
- **search rules** (P011, P100, P126, P254): run the search the check describes (`declaration_search`,
  `content_search`, `file_read` of the file or siblings). P011 also needs the derivation to compile: `departs` only
  if a candidate built from the found API compiles. `departs` if the search finds what the check names,
  `conforms` if it does not.
- **read rules** (P048, P084): measure from the code (binders shared by consecutive declarations; a broken line
  or signature whose joined form is at most 100 characters).
- `undecided` when every relevant call timed out or failed in the environment. Never guess.

Do not read: reader labels, anything under `results/` or `docs/`, the merged code or any later commit, the web.

Write one JSON object per place to
`/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/ask-reading/results/pr_review_v5/probes/stage-h-departures-2026-10-16/checks/{PR}.jsonl`:
`{"item", "rule", "verdict": "departs|conforms|undecided", "calls": <number of tool calls>,
"compiled_candidates": <n>, "evidence": "<= 60 words: what was tried and what Lean or the search answered"}`.
Reply with one line per place.
