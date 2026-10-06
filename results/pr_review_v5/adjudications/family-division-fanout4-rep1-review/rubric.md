# Reviewing what each arm did in each unit — rubric

You are reviewing jobs from one run of an LLM code-review pipeline on four Mathlib pull requests
(33145, 33315, 33337, 33421; 33315 is a control PR where maintainers asked for nothing). Each job
is one specialist "arm" reviewing one work unit (a few declarations of one file). Your inputs:

- `dig/<arm>.md` — the dossier for each job of your arm(s): its targets, the gold obligations at
  those targets (what the maintainer actually asked, as extracted), its per-target verdicts with
  reasons, what it filed (claims, whether an edit came with it, whether it was published, and how
  a model judge voted against the gold, e.g. `7fef913e:2/3`), what the older ten-arm run's arms
  (V3) did on the same unit, and a compact transcript of its tool calls and results.
- `dig/pr_context.md` — each PR's gold obligations and the maintainers' actual round-1 comments.
- `dig/prompts.md` — exactly what each arm was told (system prompt, contract, shared checklist).
- `dig/where_the_code_is.md` — how to read the base and reviewed code to check a claim.

Gold is a LOWER BOUND: maintainers ask for a few things and leave many valid ones unsaid. A finding
absent from gold is not wrong for that reason. Judge each finding on the code: is it true, and
would a Mathlib maintainer plausibly ask for it? Check claims that matter against the code (read
the files; do not compile, do not run any model, do not edit anything).

For EVERY job, write one JSON object per line to your output file with these keys:

- `invocation_id`, `arm`, `pr`
- `track`: `"on_track"` (asked the right questions of these targets and its output is right),
  `"partly"` (right idea, wrong execution, or some good and some wrong output),
  `"off_track"` (asked the wrong question, or its output is mostly wrong or trivial), or
  `"correct_silence"` (nothing to ask here within its remit, and it said so with a sensible reason).
- `did`: what it actually did, at most 40 words.
- `findings_correct`, `findings_wrong`, `findings_trivial`: counts over what it filed (trivial =
  true but not something a maintainer would bother to ask).
- `missed_in_remit`: what a maintainer asked (gold or round-1 comment) at these targets that falls
  in this arm's remit and it did not ask; `""` if nothing.
- `failure_modes`: a NON-EXCLUSIVE list from: `contract_refusal` (the submission tool refused a
  correct ask), `concern_gate_mismatch` (the arm's concern/issue kind forced a check that does not
  fit what it found), `tool_misread` (misread a tool result, e.g. a moved declaration read as a
  duplicate), `wrong_question`, `remit_too_narrow`, `remit_ambiguous`, `shallow_investigation`,
  `false_claim`, `trivial_nit`, `target_grain_trap` (answered at target level a question that
  needed the PR or a group), `evidence_gap` (a tool it needed was missing or answered the wrong
  question), `over_filing`, `duplicate_of_other_arm`, `stopped_short` (had the answer in hand and
  did not file it), `good`. Add a short new tag if none fits and say what it means in the note.
- `what_went_wrong`: at most 60 words; `""` for a clean on_track or correct_silence job.
- `mitigation`: at most 60 words, concrete — the prompt sentence to add or remove, the tool or
  tool output to change, the contract or gate rule to change, or the scheduling change.
- `vs_v3`: at most 30 words — did the old arms on the same unit do better, worse, or the same, and
  why.
- `evidence`: one or two short quotes from the dossier that carry the judgement.

Read the notes before you count. Then write a summary file (path given) with:
1. per arm: counts of each `track` value and each failure mode;
2. what the arm is good at and bad at, with the two best and two worst jobs by invocation id;
3. the mitigations, ranked by how many jobs each would have fixed, each with the job ids;
4. anything about the contract, tools or scheduling that affects arms beyond yours.
Keep the summary under 900 words. Then reply with the summary's headline findings (under 250 words).
