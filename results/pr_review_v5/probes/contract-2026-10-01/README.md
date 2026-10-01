# The contract condition: gpt_5.2 under the Claude reviewers' contract (pre-registered 2026-10-01, before its run)

## Why this condition

On the dev held-out 12 gold (judge v9, 23 obligations), hits per finding are about the same for
every reviewer, Claude included (0.08-0.12). What differs is how much each says, and about how
many objects:

| reviewer | findings per PR | change targets with a finding (of 432) | issue recall |
|---|---|---|---|
| Claude X1 / X2 | 7.5 / 8.1 | 76 / 83 | 0.478 / 0.478 |
| gpt_5.2 off / carried (Grc1) | 3.2 / 2.6 | 35 / 30 | 0.174 / 0.130 |
| gpt-5.5 / gpt-5.4 carried | 2.8 / 2.1 | 32 / 25 | 0.130 / 0.087 |

The inputs are identical: the full diff, the PR text, and the pass-0 model in every gpt prompt.
The tools work. Every gpt condition shares a contract that the Claude packet does not
(`docs/todo/reviewer-model-gap.md`, "Why every gpt condition looks alike", a394f572):

1. **No object-by-object account.** Brief X required `notes.md`, "what you did, object by object,
   including what you checked and found nothing wrong with" (median 22 object entries a PR).
   Brief G is X without its output section. gpt's only output is the final `submit_findings`.
2. **A merge verdict in the submission.** The severity line and the mandate speak of withholding
   merge, and the tool has `merge_ready_as_is`. Claude's `findings.json` had neither.
3. **The `ape_agent` batch preamble**: every response MUST include tool calls, "TEXT ALONE ...
   accomplishes NOTHING", batch ALL tool calls, submit only when "COMPLETED and VALIDATED".
   Claude ran under none of it.
4. **No `file_search`.** The 30 dev Claude sessions called it 396 times through `cli tool`.

The filing bar alone (2) did not move validation reach (`../filing-bar-2026-09-30/`), and it
widened gpt-5.5's targets from 20 to 37 at the same 0.20. Breadth without the per-object pass did
not help there. The untried design is the whole contract.

## The condition (built 2026-10-01, no other change)

`configs/pr_review_v5_dev_medium_gpt52_Grc_contract.yaml` extends Grc1's config
(`pr_review_v5_dev_medium_gpt52_Grc.yaml`: gpt_5.2, high effort, Responses, reasoning carried,
brief G, the pass-0 model, the five context tools Claude held, $13.40 / 16.08M a session) and sets:

| switch | built in | what the model sees |
|---|---|---|
| `review_notes: true` | 7a004d71 | `submit_findings` requires `notes`; a blank one is refused and the session goes on. The user prompt asks for an entry per changed object, closed with its conclusion. |
| `filing_bar: request` | b446f552 | the severity line without "withhold merge"; no `merge_ready_as_is` |
| `batch_preamble: plain` | 35525862 | three sentences: tools are how you read, search, compile and check; the submission tool ends the session; call it once, when finished |
| `file_search` granted | a074ea65 (first test of the tool; a plain file name now finds the file) | `find files by name (file_search)` in the tool summary |
| `max_turns: 160` | | so a longer pass cannot be cut off (Grc1: median 18 turns, max 45) |

Tool negatives were also made unambiguous before this run, for every condition from here on.
`lean_verify` / `lean_verify_edit` now say compiled, compile errors, timeout or environment failure
(6b2cf137). `naming_norm` says `conforms`, `population_too_small` or `no_dominant_prefix` (973b978c).
content_search and the Lean code tools mark a bad request (d2c1d98c). Grc1 ran before these fixes,
so the comparison also carries them. They change what a tool says on its negatives, not what it
finds.

Run: `probe_dev_gpt52_Grc_contract_rep1`, the 15 dev PRs (the held-out 12 judged). Grc1 billed
$8.90 on these PRs. Expected $15-30, since the pass is longer. Ceiling $201.50.

## Reading rule (stated before the run)

Judged with `configs/pr_review_v5_medium_heldout_judge.yaml` (23 obligations, 12 reachable), against
Grc1's 0.130 (3 obligations):
- **The contract is a lever** if issue recall ≥ 0.26 (6 obligations, double Grc1).
- **Not a lever, as built** if issue recall ≤ 0.174 (4 obligations, the top of the four gpt
  conditions' spread).
- 5 obligations (0.217): undecided; replicate before reading.

Read beside it, so a move can be attributed:
- findings per PR, change targets with a finding (of 432), obligations hit per finding;
- `notes` entries per PR against Claude's median 22;
- turns, billed cost, capped sessions, refused-notes submissions, `file_search` calls.

A rise in recall that comes with targets near Claude's (76-83) and hits per finding near 0.1 is
the breadth mechanism. A rise without more targets is something else, and is read as such.

**If it moves:** two more repetitions, then the validation probe match against the Phase 0 seal's
reviewers, then ablation of the four switches. **If it does not:** this is one built design, and the
untried ones are recorded before anything is concluded. They include the account as a running file
rather than a final field, gpt in a Claude Code-like harness (codex, blocked: `docs/todo/`), and
the tools Claude lacked (`lean_verify`, hover/goto) removed.

**Altitude.** One run, 23 obligations; the judge's self-agreement is about 90%, so one obligation
(0.043) is inside the noise. Dev is inside Claude's training window; the read here is gpt against
gpt conditions on the same set and gold, with Claude as a level.
