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

## Result (2026-10-01): not a lever, as built

The run completed 15 of 15 sessions for $9.36 billed (Grc1: $8.90). No session was capped: the
maximum was 46 of 160 turns. There were no API retries and no refused submissions. The judge was
`configs/pr_review_v5_medium_heldout_judge.yaml`, as stated (audit
`results/pr_review_v5/audits/probe-dev-gpt52-Grc-contract-rep1`, $0.13).

| reviewer (dev held-out 12, judge v9) | issue recall | reachable (12) | findings | per PR | targets (of 432) | hits / finding | notes bullets per PR |
|---|---|---|---|---|---|---|---|
| Claude X1 / X2 | 0.478 / 0.478 | 0.583 / 0.583 | 90 / 97 | 7.5 / 8.1 | 76 / 83 | 0.122 / 0.113 | 33.5 / 23.5 |
| **gpt_5.2 carried, contract** | **0.130** | **0.167** | 42 | 3.5 | 40 | 0.071 | 8.5 |
| gpt_5.2 carried (Grc1) | 0.130 | 0.250 | 31 | 2.6 | 30 | 0.097 | - |
| gpt_5.2 off | 0.174 | 0.083 | 38 | 3.2 | 35 | 0.105 | - |

(`breadth.py` reproduces every column but the first two, which are the judge's `semantic_report.json`.)

**By the rule stated before the run, the contract as built is not a lever:** 3 obligations, the
same count as Grc1 and under the 4-obligation bar. The obligations themselves moved. Contract and
Grc1 both hit the two 33149 axiom asks. The contract gained the 33362 namespace move, which X2 also
reached. It lost the 33145 rename (`Dense.upperBounds_image`), which Grc1 filed.

**What the contract changed.** gpt said about a third more: 42 findings against 31, on 40 targets
against 30. It still reached about half of Claude's 76-83 targets, and the extra findings hit less
often (0.071 per finding, the lowest of any reviewer). The ledger was written for every session,
with a median of 8.5 bullets per PR against Claude's 23.5-33.5. It names each changed object and
closes each with a conclusion about the object's proof or docs. In the sessions read it does not
take an object through the concern families:
- 33145: eight findings, all proof golf or docstrings, with 14 compiles. The notes never mention
  names, and Grc1's naming finding (the maintainers' rename) is gone.
- 33421: on the lemma the maintainer asked to generalize, the notes say "searched for duplicates
  by name and didn't find any conflicts". That is `attempted_concluded_fine`, Phase 1's dominant
  mechanism.
- 33337: one finding, as before. The notes say the `coe_` rename "matches common naming", where
  the ask was `toLinearMap_`. The session made 13 tool calls against Grc1's 34.

Claude's notes do take objects through the families. They close with "concern families checked
with nothing to request", one line per family. That is the part of the contract this build did
not carry over.

**Untried, before anything is concluded about the contract.** This was one design, one run and
23 obligations (one obligation is 0.043, inside the judge's noise):
1. **A family-by-object ledger:** a required verdict per changed object for each concern family,
   as Claude's notes have. This build asked only for "an entry per object".
2. **The account as a file written during the session** rather than a field in the final call.
   Whether Claude wrote `notes.md` as it went or at the end has not been checked.
3. **gpt in a Claude Code-like harness** (codex scaffold; blocked, see `docs/todo/`).
4. **The contract on gpt-5.5**, the model that verifies most edits (`../filing-bar-2026-09-30/`).
5. **Removing the tools Claude lacked** (`lean_verify`, hover/goto), so the grants are identical
   rather than a superset.

So the four contract differences together, as built here, do not close the gap on this set. They
widen gpt's output somewhat without raising what it reaches.

## Is gpt a proof reviewer where Claude reviews broadly? (2026-10-01, no spend; `focus.py`)

The question was raised from the 33145 session read. One keyword classifier was applied to every
reviewer's findings, notes and the gold asks on the held-out 12. Tool calls were parsed from the
conversations, not regex-counted: a regex over the turn file counts each call twice, which put two
figures in the early read at double.

**By share, no.** Proof-related findings are 28-33% of Claude's, 16% of Grc1's, 21% of the contract
run's and 27-29% of gpt-5.5's and gpt-off's. Grc1 leans more on naming than Claude (23% against
16-18%), and the contract moved it away from naming (10%). **By count, Claude files about three times
as much in every family:** naming 14-17 against 4-7, proof 25-32 against 5-11, generality 15-21 against
1-5, API design 23-26 against 4-10. Claude is also better at proof asks: it hits both proof-golf asks
(33285), which gpt_5.2 misses in every condition. gpt-5.5 carried hits both too.

**The difference is how much is done per object, across every family:**

| per session, median | Claude X1 / X2 | gpt Grc1 | gpt contract |
|---|---|---|---|
| tool calls (all) | 58 / 57 | 39 | 32 |
| candidate edits compiled (`lean_verify_edit`) | 9.5 / 11.5 | 3.5 | 1.5 (+4 `lean_verify` snippets) |
| library lookups (`declaration_search` + `file_search` + `naming_norm`) | 17 / 19.5 | 3.5 | 1.5 |
| file reads + greps | 14.5 / 16 | 19.5 | 16.5 |

| PRs whose notes mention the family | naming | generality | duplication | API design | placement |
|---|---|---|---|---|---|
| Claude X1 / X2 | 100% / 92% | 83% / 75% | 92% / 75% | 92% / 92% | 92% / 92% |
| gpt contract | 50% | 17% | 50% | 58% | 50% |

gpt reads and greps as much as Claude. It compiles a third as many candidate edits and looks the
library up a fifth as often, and it stops: no gpt session came near its caps (max 46 of 160 turns).
The notes instruction was the same text for both. Claude's is "what you did, object by object,
including what you checked and found nothing wrong with", and gpt got that plus "every changed
object gets an entry". Under it, Claude's notes take objects through the families and gpt's do not.

**Differences between the two contracts that remain after this build.** All are untested:
- gpt only, in the user prompt: "Investigate ... open the files, look for existing declarations that
  overlap, check whether a proof could be shorter" (it names two activities); the finding schema
  with path and line, the `concern_family` and `issue_kind` taxonomies, and "Label a finding with
  what it actually is"; "at most 20 findings"; "You MUST finish ... a text-only reply ... fails the
  task"; and the order PR, diff, instructions, then the PR model. Claude read pr, model, diff.
- gpt only, in the system prompt: the workspace and `<environment>` sections (scratch and target).
- Output: gpt makes one final call. Claude writes `findings.json` and `notes.md` as files, so it can
  rewrite them and read them while it works.
- Tools: gpt also holds `lean_verify` (snippet compiles, 3-4 a session), `get_lean_goal` and
  hover/goto, called natively. Claude held the `ptool` set, called through a shell script after one
  `ptool describe`.
- Harness: Claude ran as a Claude Code subagent under that harness's own system prompt and the
  probe's session prompt, uncapped. gpt runs in the `ape_agent` loop with turn and cost caps, none
  of which bound.
- Model: `claude-opus-5-5` against gpt_5.2 at high effort with reasoning carried. Dev is inside
  Claude's training window; the post-cutoff test found in-window reach is not mainly recall.

**What these runs cannot separate.** The same notes instruction produced a family-by-object pass in
one reviewer and not the other. That points at the model or the harness rather than the brief's
text, but no run here holds everything but the model fixed. The design that does is the swap: a
Claude session given gpt's rendered contract-condition prompt verbatim (system and user), the same
tools, and a `submit_findings`-shaped output, judged the same way. Claude near 0.48 would mean the
remaining gap is model or harness. Claude near 0.13 would mean it is in the prompt text gpt still
gets. It costs Claude-session time, not API spend.

**Object coverage of the notes (2026-10-01).** This is the share of the PR model's changed
declarations (`## Objects`, commands excluded) that a session's notes name, in full or by leaf name.
The median over the held-out 12 is Claude X1 73%, X2 78%, gpt contract 37%. The gap is all on the
large PRs: 33117 (24 declarations) 71-75% against 25%, 33294 (20) 75% against 25%, 33321 (18) 83%
against 28%, 33421 (39) 64% against 46%. Below 14 declarations the coverage is the same. gpt
summarises by file ("reviewed new lemma X and new simp lemmas A, B, C, D ... no conflicts")
where Claude goes declaration by declaration. In gpt's prompt the object list comes last, after
the diff and the submission instructions. Claude read it second, before the diff. Untested as a cause.

## Contract v2 (pre-registered 2026-10-01, before its run)

This adds the prompt audit's changes to the contract condition: every item of gpt-only prompt text,
traced to its origin, either removed or made like Claude's, plus Claude's ledger. It is
`configs/pr_review_v5_dev_medium_gpt52_Grc_contract2.yaml`, which extends the contract config:

| item | origin | in v2 |
|---|---|---|
| "Investigate ... look for existing declarations that overlap, check whether a proof could be shorter" | first solo prompt, 28d40719 | dropped (`user_prompt: v2`) |
| the `concern_family` / `issue_kind` lists, "Label a finding" | candidate-validator plumbing, ee44dee3 | not asked; the imported-Claude pair (`other`, `style_norm_violation`) stamped on every finding, so both reach the judge alike |
| "at most 20 findings" | the lead's ceiling, 28d40719 | not shown; the cap stays in code (it never bound) and now warns when it truncates |
| "You MUST ... fails the task", "A text-only response is INVALID" | 2026-08-25 | the empty-review path kept, the threat dropped |
| the PR model after the diff and the instructions | the probe's append mechanism | before the diff; brief_G2.md reorders brief G's one sentence to match |
| the `<environment>` section ("rapid iteration and experimentation") | APE framework boilerplate | dropped (`workspace_environment: false`) |
| notes "an entry per object" | contract build, 7a004d71 | `notes_form: per_object_family`: an entry per changed declaration, each taken through the concerns that apply (proof, statement and generality, library duplicate, name, docstring, attributes and placement), closed with a verdict |

Kept: `path` and `line_start` (the anchoring pass keys on them), `filing_bar: request`, the plain
preamble, `file_search`, Grc1's model, effort, carry-over, tools and caps. Built in 59147706 and
eac39d40; the defaults render every earlier prompt byte for byte. `cli plan`: 15 of 15 reviewed
workspaces, worst case $201.00 under $201.50. The run is `probe_dev_gpt52_Grc_contract2_rep1`, and
about $10 is expected (the contract run billed $9.36).

**Reading rule, unchanged.** On the held-out 12 gold (23 obligations; Grc1 and the contract both
3): issue recall ≥ 0.26 (6 obligations) is a lever; ≤ 0.174 (4) is not, as built; 5 is undecided.

Read beside it, from `breadth.py` and `focus.py`:
- notes coverage of the PR model's declarations (contract 37%, Claude 73-78%) and notes family
  mentions (naming 50%, generality 17%; Claude 92-100% and 75-83%);
- findings, targets (40; Claude 76-83), hits per finding (0.071; Claude about 0.12);
- candidate edits compiled and library lookups per session (contract 1.5 and 1.5; Claude
  9.5-11.5 and 17-19.5).

The two readings that matter:
- Coverage and family mentions near Claude's with recall still about 3 would mean the ledger was
  carried over and is not the lever. What remains is the model or the harness, and the swap
  (Claude under gpt's prompt) is the test that says which.
- Coverage still near 37% would mean gpt does not follow the ledger as written. That is a fact
  about the model under this instruction, not a test of the ledger.

One run, so provisional either way.

### Result (2026-10-01): the ledger was carried over, and it is not the lever

The run completed 15 of 15 sessions for $8.36 billed. No API retries, no budget truncations, no
capped session (max 41 of 160 turns). Judge v9 on the held-out 12, $0.08, audit
`probe-dev-gpt52-Grc-contract2-rep1`.

| reviewer | issue recall | reachable | findings | targets | hits / finding | notes cover declarations (median) | notes mention naming / generality | tool calls | edits compiled | library lookups |
|---|---|---|---|---|---|---|---|---|---|---|
| Claude X1 / X2 | 0.478 | 0.583 | 90 / 97 | 76 / 83 | 0.12 / 0.11 | 73% / 78% | 100% / 92%, 83% / 75% | 58 / 57 | 9.5 / 11.5 | 17 / 19.5 |
| **contract v2** | **0.087** | 0.167 | 34 | 34 | 0.059 | **73%** | **83%, 58%** | 30 | 2 (+1 snippet) | 2.5 |
| contract v1 | 0.130 | 0.167 | 42 | 40 | 0.071 | 37% | 50%, 17% | 32 | 1.5 (+4) | 1.5 |
| Grc1 | 0.130 | 0.250 | 31 | 30 | 0.097 | - | - | 39 | 3.5 (+3) | 3.5 |

**By the pre-registered rule, not a lever**: 2 obligations, the two 33149 axiom asks every gpt
run reaches. That is one fewer than v1 and Grc1, inside the noise.

**The first of the two pre-stated readings is the one that holds.** The ledger was carried over.
The notes now name as many of the PR model's declarations as Claude's do: 71-78% on the four
large PRs, against v1's 25-46%. They mention naming on 83% of PRs and generality on 58%. Recall
did not move. What remains, by the stated reading, is the model or the harness.

**What the ledger changed is what gpt writes, not what it does.** Tool calls did not rise (30 a
session, against Claude's 57-58), and neither did candidate edits compiled (2 against 9.5-11.5)
or library lookups (2.5 against 17-19.5). Claude's per-declaration entries are backed by a
compile or a search. gpt's v2 entries mostly assert a check from reading ("checked ...; nothing
to ask"). Where maintainers asked, the notes now show the decision outright:
- 33294: `isFundamentalSequence_of_isNormal`, which the maintainer asked to rename to dot
  notation: "just renamed/unprotected; no generality issues."
- 33285: `inf_comap_le_comap_add`, asked to golf to a direct lambda: "proof golfed to `simp` +
  `add_mem`; ... nothing to ask."
- 33421: `two_mul_fract_eq_one_iff_exists_int`, asked to generalize: "checked statement for
  correctness and usefulness ... No duplication found." The session asked to move it instead.

**Untried, and which question each answers:**
1. **The swap**: Claude given this prompt verbatim, same tools and output. It separates the model
   from the harness; the prompt is now as close to Claude's as these runs can make it.
2. **An evidence-backed ledger**: each "nothing to ask" names the call that checked it. This
   tests whether the missing investigation, not the missing account, is the lever. It is a forcing
   design beyond Claude's contract.
3. **v2 on gpt-5.5**, which verifies two to four times as many edits as gpt_5.2
   (`../filing-bar-2026-09-30/`).
4. **gpt in a Claude Code-like harness** (codex; blocked).

One run, 23 obligations: provisional.

## Contract v2 on gpt-5.5, and the swap (pre-registered 2026-10-01, before their runs)

Two runs, at the user's request, on the question contract v2 left open. The prompt is now as close
to Claude's as these runs can make it, and gpt_5.2 still files from reading rather than from
investigation. Is the remainder the model?

### gpt-5.5 under contract v2

`configs/pr_review_v5_dev_medium_gpt55_Grc_contract2.yaml` is contract v2 with only the model and
its caps changed, as the gpt-5.5 carried config changes them from Grc1 ($20 / 24M a session, 160
turns). The run is `probe_dev_gpt55_Grc_contract2_rep1`, on the 15 dev PRs. Expected about $18:
gpt-5.5 carried billed $18.42 here. gpt-5.5 compiles two to four times as many edits as gpt_5.2
did on validation. Under brief G it reached 0.130 on this gold, and it is the only gpt that hit
33285's two proof-golf asks.

Rule, on the held-out 12 gold (23 obligations): ≥ 0.26 (6) is a lever for this model; ≤ 0.174 (4)
is not; 5 is undecided. Read beside it: edits compiled and library lookups per session (gpt_5.2
v2: 2 and 2.5; Claude: 9.5-11.5 and 17-19.5), notes coverage, findings and targets.

### The swap: Claude under gpt's prompt

A Claude session (`claude-opus-5-5`, as X1 and X2) gets gpt's contract-v2 prompt verbatim. For each
PR the system and user messages are taken from that PR's session in
`probe_dev_gpt52_Grc_contract2_rep1`, so it is the text gpt read. The session runs through the probe
harness (`analysis/probes.py`) under the same rules and audit as X1 and X2. It writes the arguments
of `submit_findings` (`notes`, and findings with `path` and `line_start`) to `submission.json`.
`probe import` anchors those by `path` and line, as the solo runner anchors gpt's, and stamps the
same labels. Then the judge runs on the held-out 12. That is 12 PRs, one session each (`S1`).

What is held fixed against X1 and X2: the model, the probe harness and its rules, the tools (the
`ptool` set Claude held: five context tools, `lean_verify_edit` and the three file tools). What
changes: the prompt, from brief X and packet files to gpt's v2 messages. The one edit to gpt's
text is the user prompt's "Tools available" line. It names `lean_verify` and hover/goto, which
`ptool` does not provide, so it is rewritten to the `ptool` set. Against gpt, the model and the
harness change together, so this run can attribute the remainder to the prompt or not, but not
split model from harness.

Rule, against X1 / X2 (11 of 23 obligations each, 0.478):
- **≥ 0.35 (8 obligations): the prompt text is not what holds gpt back.** Claude reaches about its
  own level from gpt's prompt, so the remainder is the model, or the model with its harness.
- **≤ 0.217 (5): gpt's prompt accounts for most of the gap.** Something in the text still lowers a
  reviewer that reaches 0.48 from brief X.
- 6-7: partial.
Read beside it: Claude's tool calls, edits compiled, lookups and notes coverage under this prompt,
against its own under brief X.

One run each, so provisional.

### Result, gpt-5.5 under contract v2 (2026-10-01): it investigates like Claude, and files a third as much

The run completed 15 of 15 sessions for $19.52 billed: no retries, no truncations, max 40 of 160
turns. Judge v9, audit `probe-dev-gpt55-Grc-contract2-rep1`.

| (held-out 12) | issue recall | reachable | findings | targets | hits / finding | notes cover declarations | notes mention naming / generality | tool calls | edits compiled | library lookups |
|---|---|---|---|---|---|---|---|---|---|---|
| Claude X1 / X2 | 0.478 | 0.583 | 90 / 97 | 76 / 83 | 0.12 / 0.11 | 73% / 78% | 100% / 92%, 83% / 75% | 58 / 57 | 9.5 / 11.5 | 17 / 19.5 |
| **gpt-5.5, contract v2** | **0.130** | 0.250 | 30 | 29 | 0.100 | **82%** | **100%, 92%** | 41 | **9.5** (+3.5 snippets) | 6 |
| gpt_5.2, contract v2 | 0.087 | 0.167 | 34 | 34 | 0.059 | 73% | 83%, 58% | 30 | 2 (+1) | 2.5 |
| gpt-5.5 carried, brief G | 0.130 | 0.167 | 33 | 32 | 0.091 | - | - | | | |

**By the pre-registered rule, not a lever for this model**: 3 obligations (the two 33149 axiom
asks and one proof-golf ask), the same count as gpt-5.5 under brief G.

What gpt-5.5 under v2 now matches, or passes, in Claude's work: the declarations its notes cover,
the concerns they take each one through, and the candidate edits it compiles. What it does not
match: library lookups (6 against 17-19.5) and, above all, how much it files. That is 2.5
findings a PR against 7.5-8, at about Claude's hits per finding. So, on this model, the remaining
gap is not attention, the contract or investigation by compile. It is the decision to file, plus
library search. The model looks at what Claude looks at, compiles what Claude compiles, and
concludes "nothing to ask" two times in three where Claude asks.

One run, 23 obligations: provisional.

### Result, the swap (2026-10-01): Claude under gpt's prompt reaches its own level

There were 12 sessions (`claude-opus-5-5`), every transcript audited:
- seven were clean;
- five had flags, all adjudicated benign in `swap/audit.json`. Four were the venv's Python running
  the session's own `tmp/` scripts, which write tool arguments and the submission. One was an `ls`
  of the session's own `ptool` raw-output directory;
- the first 33294 attempt was stopped by the API's safety classifier after one call, and re-run
  unchanged.

`probe import` read 103 findings by `path` and line. 33149 had 28 past the 20 budget, as X1 and
X2 had there (30 and 33). It anchored 99 (3.9% lost; gpt 4.2%). Judge v9 on the held-out 12, audit
`probe-dev-claude-swap-S1`.

| (held-out 12) | issue recall | reachable | findings | targets | hits / finding | notes cover | notes: naming / generality | tool calls | edits compiled | library lookups |
|---|---|---|---|---|---|---|---|---|---|---|
| Claude X1 / X2, brief X | 0.478 | 0.583 | 90 / 97 | 76 / 83 | 0.12 / 0.11 | 73% / 78% | 100% / 92%, 83% / 75% | 58 / 57 | 9.5 / 11.5 | 17 / 19.5 |
| **Claude, gpt's v2 prompt** | **0.435** | **0.500** | 99 | 84 | 0.101 | 82% | 100%, 83% | **35** | **6** | **2.5** |
| gpt-5.5, the same prompt | 0.130 | 0.250 | 30 | 29 | 0.100 | 82% | 100%, 92% | 41 | 9.5 | 6 |
| gpt_5.2, the same prompt | 0.087 | 0.167 | 34 | 34 | 0.059 | 73% | 83%, 58% | 30 | 2 | 2.5 |

**By the pre-registered rule, the prompt text is not what holds gpt back.** That is 10
obligations against X's 11 (≥ 8), and the hits fall in the same families as X's (correctness 2,
duplication 2, proof-golf 2, style 2, docs 1, scope 1). Given the exact messages gpt read, Claude
files what it files under brief X: 99 findings on 84 targets.

**Nor is it investigation.** Under this prompt Claude did less than under brief X: 35 tool calls
against 57-58, 6 edits compiled against 9.5-11.5, 2.5 lookups against 17-19.5. That is less than
gpt-5.5 did under the same prompt. Yet it filed three times as much and reached three times the
asks, at the same hits per finding as gpt-5.5. Across these runs, the variable that moves recall
is how many changes the reviewer decides to ask for from what it has seen. Coverage, family
attention, compiles and lookups do not move it.

**What this does not separate:**
- **Model from harness.** Claude ran as a Claude Code subagent and gpt in the `ape_agent` loop.
- **Judgement from recall.** Dev is inside Claude's training window. Reaching its own level with
  a third of its usual lookups and two thirds of its compiles is what memory of these PRs would
  also produce. The post-cutoff measurement (2026-09-29: in-window reach 79-107% of its
  post-cutoff rate) argues against recall being most of it, but at probe altitude and with a
  different ask mix. The clean check is the swap on the post-cutoff set, scored by its blind
  matchers. There is no judge gold there.

One session per PR, 23 obligations: provisional.
