# Instructions handed to each reader run (one run = one reader, one batch)

You are `READER` (reader_A or reader_B) in a pre-registered labelling study of Mathlib pull-request
review comments, working on batch `BATCH`. Work only from the three input files below and write
only the two output files named below. `CENSUS` is
`/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-nature/results/pr_review_v5/adjudications/conventions-census-v1`
and `BATCHES` is
`/tmp/claude-1905243447/-research-projects-proofedit-ya475-APE-Bench/70b1c0e2-a390-4acc-945e-cf9fe0e9a3b5/scratchpad/census/batches`.

Read, in this order, with the Read tool:

1. The rubric: `CENSUS/reader_rubric_census_v1.md`. Follow it exactly; it defines what a
   principle is, the grain, the codebook protocol, the output keys and the vocabularies.
2. Your codebook: `CENSUS/READER/codebook.json`, a JSON list of the entries you created on earlier
   batches (empty on the first). Read all of it and hold it in mind: the rubric says to prefer an
   existing entry whenever its sentence covers the ask as written, and to create a new entry only
   when none does.
3. The batch: `BATCHES/batch_BATCH.md`, up to 125 asks. It is about 130 KB; read all of it, in
   several Read calls with offset and limit if needed.

Then, following the rubric, for EVERY ask in the batch in order: assign an existing entry, or
broaden one of your own entries (set `"revised": true`), or create a new entry with the next
consecutive id after the last existing one, or label it none with a `none_reason`. Ids stay
consecutive with no gaps; never change, merge, split or delete an existing entry.

Write, with the Write tool:

- `CENSUS/READER/labels_BATCH.jsonl`: one JSON object per line per ask, in batch order, with
  exactly the keys `cid, principle_id, second_principle_id, none_reason, new, confidence, note`.
  Every ask of the batch present exactly once.
- `CENSUS/READER/codebook.json`: the full codebook, every existing entry unchanged (except a
  broadened sentence with `revised` true) plus the new ones, each with keys `id, principle,
  rationale` (a list of one or two values from the rubric's table), `form` (`rule` or
  `standard`), `revised` (boolean).

Constraints: do not open any other file or directory (nothing under the other reader's directory,
no earlier labels file, nothing else in the repository); do not run git; do not search the web or
the repository; do not look anything up. After writing, run one short Python check with Bash that
reads only the two files you wrote and the batch file, and verifies: every cid of the batch present
exactly once and in order; every `principle_id` an id in the codebook or `none`; every
`second_principle_id` an id in the codebook or `""`; `none_reason` is `specific` or `unreadable`
exactly when `principle_id` is `none` and `""` otherwise; ids consecutive from P001; every
rationale value from the rubric's list. Fix any error and re-check.

Reply only with: the number of asks labelled, the number labelled none by reason, the number
assigned to an existing entry, the number of new entries, the final codebook size, and each new
entry's id and sentence on one line each.
