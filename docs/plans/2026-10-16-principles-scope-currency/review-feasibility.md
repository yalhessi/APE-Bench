# Feasibility and discrimination review of `2026-10-16-principles-scope-currency.md` (2026-10-16)

Reviewer brief: does the data each test needs exist and join, what does each test cost, and does each
possible outcome tell the project what to change. Every number below was read off the disk in this
review (commands in §0); nothing was run against a model.

## 0. The data, verified

**Census → PR, path, date, author.** `conventions-census-v1/reader_A/labels_b*.jsonl` (1,833 rows,
cids `v0000..`) join on `cid` to
`adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl` (2,306 rows): `pr` (1,833),
`author` (1,833), `month` (1,833), `path` (1,610; the 223 without one are `issue_comment` and `review`
rows, i.e. PR-level), `line` (1,610), `kind`, `stratum`, `ai`, `event_id`. So PR, path and author are
present for every cid; the **date is month-level only** in that file. Day-level `at` comes from
`analysis/probes.py::extract_feedback` over a probe-set spec with
`feedback: {draw: val1000-2025-06-2026-03-v1}`: it renumbers the same events `v0000..` in the same
order (checked on the 60 rows of
`probes/convention-detectors-2026-10-06/stage5/feedback.json`: 60 of 60 `cid → event_id` identical to
`events.jsonl`) and reads `created_at`/`submitted_at` from the PR store, `data/pull_requests/pr/<n>/`,
which holds all 759 PRs the events come from. The base commit per PR is
`inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json` → `accepted[].base_sha`
(973 episodes, 842 distinct bases). Reader B labelled the same 1,833 cids against its own codebook
(407 entries); `crossmap.json` maps A↔B entries (`same` / `a_broader` / `b_broader`).

The 269 rows of `labels_y*.jsonl` (cids `w0000..`) are the **out-of-window** set (2024 and 2026-04+),
joined through `adjudications/design-comparison-outside-v1/packet_manifest_window.json` (`cid → pr,
event_id, month, path`; 256 of 349 rows have a path; no author, no day; both recoverable from the
store by `event_id`). They are outside 2025-06..2026-03 by construction, so they serve test 2 and not
test 5's window shift. The 801 same-window outside asks (`o`-cids, `packet_manifest.json`) are not
census-labelled.

**Per-place probe** (`probes/conventions-places-2026-10-09/items.json`, `outputs.jsonl`): 1,431
(entry, place) pairs on 13 PRs — 591 exact (42 asked, **549 unasked-exact**) and 840 decoy; two
samples per exact pair, one per decoy. Unasked-exact: 1,098 samples, 332 "departs" (30%); **209 pairs
with at least one "departs", 123 with both** — the plan's "about 150" sits between the two; say which.
They concentrate: 27 entries, of which P369 (27), P100 (24) and P041 (23) hold 74 of 209; 185 are
segment places, 24 the PR-level place. The 13 PRs are val-small12 (8) and post-cutoff (5), all with
reviewed workspaces. The model was DeepSeek-V4.1-Flash, one turn, no tools (prompts ~2.9k tokens,
answers ~9.6k); the prompts are gitignored but `places.py build` rebuilds them to the digests in
`prompts.sha256`.

**Deprecation stream.** `results/pr_review_v5/naming_testbed/` holds the rename testbed's results
(`dev_a1/a2`, `heldout_a1`, `primary_a1`: 129 held-out records and 381 controls, items with `pr`,
`pr_date`, `old`, `new`, `module`). The "2,987 deprecations" is `summary.population.late_deprecations`,
a count at `L = b72c0345` (2026-03-04), **not a stored list**, and the module that produced it
(`analysis/naming_testbed.py`) is deleted from the tree (history: `d95406cf`). The stream itself is
derivable from the Mathlib clone: `git grep -ohE 'since := "YYYY-MM' <commit> -- Mathlib`. At `L` the
`since` months run 2025-08..2026-03 (415, 438, 709, 454, 748, 582, 218, 51); at `E = 36a2b22f`
(2025-11-21) they run 2025-04..2025-11 (157, 1137, 385, 430, 704, 442, 667, 189). Deprecations are
deleted after about six months, so **one snapshot covers seven months; the union of E and L covers
2025-04..2026-03**, with a file and a date per entry (the PR by `git log -S` or blame).

**Mathlib history.** `data/code_execute/repos/mathlib4/source` is a full clone: 31,660 commits,
2021-05-09 to 2026-05-14 (HEAD `28908c09b5`); `git log --format=%cs` works (9,357 commits in the
census window); the three base shas tried resolve. Built state: 1,277 `snapshots/*.snap` (75 of the
842 val1000 bases), 239 reviewed workspaces (39 val1000 bases). Tests 3 and 4 need only `git grep` /
`git show` at a sha, as the library reading did; **only test 6 needs a built workspace**, and the
41 never-reached asks' workspaces all exist (41 of 41), as do the 13 places-probe PRs'.

**Zulip store.** `data/zulip/corpus/zulip.sqlite3` (204 MB; `messages.jsonl`, `threads.jsonl`
beside it; `src/datasets/zulip/store.py::search` over FTS5): 180,162 messages, 12,033 threads,
46,082 refs, 2018-05-28 to **2026-07-30** (synced 2026-08-07), 8 streams (`mathlib4` 64k, `general`
41k, `lean4` 24k, `Is-there-code-for-X?` 23k, `nightly-testing` 15k, `PR-reviews` 8.5k,
`metaprogramming-/-tactics` 3k, `triage` 1.9k); 5.7k-9.9k messages a month across the window, 33,350
of them by maintainers (`sender_is_maintainer`). Dense enough for test 5.

**Library reading's partial rows** (`probes/library-knowledge-2026-10-13/readings/{A,B,C,D}.jsonl`):
19 rows with `determiner == library_partial`, **one reader per ask** (the four files split the 41,
not two readers each). Fields: `ask, pr, change, determiner, kind, artifact, commands,
findable_from_place, confidence, note`. Kinds: naming_pattern 7, file_pattern 5, tactic 4,
existing_declaration 2, attribute_or_generator 1; confidence medium 17, low 2. Sets: **11 dev (D12),
4 val-small12, 4 post-cutoff**; PRs 33145 (5), 33098 (3), 30641/42814/43167 (2 each), five singles.
The 41 asks' `asks.jsonl` carries `base`, `reviewed_head`, `workspace`, `path`, `comment`,
`code_at_comment`, `reached_by`.

**What the census can bear.** Asks per entry (reader A, val): 166 entries with 1, 79 with 2, 41 with
3, 28 with 4, 31 with 5-7, 29 with 8-15, 24 with 16+. 84 entries have ≥5 asks; of those, 49 have asks
in two or more top-level areas with ≥2 each, 35 at the second directory level. 53 entries have ≥8
asks; 41 of them have ≥3 asks on each side of the median month (2025-11). 74 reviewers wrote the
1,669 principled asks; the top five wrote 31%. 295 of 438 codebook entries carry **two** rationale
tags, unordered; `form` is `rule` (261, checkable without judgement) or `standard` (177, takes
judgement). Mathlib's `docs/` in the clone holds only the yaml overviews; the style and naming guides
are on disk as `docs/guides/{style-guidelines,naming-conventions,pr-review-guide}-official.md`.

**Readers and rates.** "Reader" in this project means a Claude subagent session on the subscription:
the census ran 17 reader runs at ~200k tokens each for 2,102 text-only labels (≈1.6k tokens a label,
2-3 five-hour windows for 3.4M). A git-verified reading (the library reading's batches were 9-11
asks per reader) is heavier; I take 20-25k tokens an ask as the estimate. The free reviewer is
DeepSeek-V4.1-Flash on `first` (Slurm, ~12 min to serve); the strong one is Opus 5.5 on the user's
own subscription token (asked, never assumed) or `elm_gpt_5.5` against the £500 ELM cap.

## 1. Per test: data, effort, what cannot be done as written

| Test | Data present | Effort (session hours; model work) | Not doable as written → smallest change |
|---|---|---|---|
| 1 Principles well-defined | **Yes.** Codebook (438 entries, 11 tags); the three official guides on disk. | 3-4 h to write 11 statements; 2 reader passes × 100 entries, text-only, ≈0.4M tokens; +1 control pass (below) ≈0.2M. Claude readers. | "Agreement with the codebook's tag" is undefined for the 295 two-tag entries and "several equally" is the codebook's own state for 67% of entries. Change: score a hit as "in the entry's tag set", and report ties and no-fit as separate categories against the 20%. |
| 2 Scope-dependent instantiations | **Yes, after one script.** cid → area needs `events.jsonl` (1,610 paths; 223 PR-level rows take the PR's `files.jsonl`); month suffices for the period split; reviewer is in `author`. | 0.5 day for the join script (serves 2, 3, 5); 2 reader passes over the 438 one-line entries to list pairs, ≈0.3M tokens; splits are a script. | The ask counts: a pair's two entries both need ≥3 asks per side to call a separation, and only 84 entries have ≥5 asks at all. Change: enumerate pairs, then report how many are *testable* at that floor before any separation share; add the reviewer axis (see §2). |
| 3 Ask = scope's established form | **Partly.** 19 partial rows exist (single reader, 11 of 19 dev asks, bases and workspaces present). The 21 census asks have base sha, path, line, author on disk; the *asked form* and the *PR's form* are not recorded anywhere and must be read off each comment. | ~1 day. 40 asks × 2 readers × ~25k (git-verified: directory, area, library, `--since 90 days`) ≈ 2.0M tokens. Claude readers; no build needed (`git grep` at the sha). | "Count the asked form" presumes a grep-countable form; it holds for naming/file-pattern/tactic/attribute kinds (16 of the 19) and not for `existing_declaration`, generality or process asks. Change: draw the 21 from `form: rule` entries or from `standard` entries with a nameable surface form, and record `countable: yes/no` plus the raw counts, with a floor of n ≥ 5 occurrences for "dominant". |
| 4 Silence has negative evidence | **Yes.** 549 unasked pairs with verdicts and the model's CHANGE/WHY; bases in the two draws; PR history in the store (`timeline`, `review_threads`, `commits`, later rounds). | ~1 day. (40 + 33 calibration pairs) × 2 readers × ~20k ≈ 2.9M tokens; plus a store script for "raised later / fixed anyway / present at merge" (no model). | "Sample 40 by principle" cannot be done evenly: the departs pool is 27 entries on 13 PRs and three entries hold 35%. Change: stratify by entry with a cap of 3 per entry, and split PR-level places (24) from segments (185). The pool size must be fixed as 123 (both samples) or 209 (either). |
| 5 Conventions change over the window | **Partly.** Dates: month-level now, day-level via `extract_feedback`. Deprecations: derivable from two snapshots (E ∪ L covers 2025-04..2026-03), not from `naming_testbed/`. Zulip: present and dense to 2026-07. Automation introduction commits: `git log -S/--grep` with dates. | 0.5 day for the computable part (first-ask dates per entry, deprecation union, automation commits). The "shift in the asked form" is **not computable from the labels**: a census label is at entry level and records no form. Reading the forms: 53 entries × 8 sampled asks = 424 asks × 2 readers × ~1.5k ≈ 1.3M tokens. | The entry-level label hides within-entry shifts and the fixed vocabulary hides shifts that appear as *new* entries. Change: (a) read forms on a per-entry sample as costed; (b) add the computable signal "entries whose first ask falls after 2025-12 with ≥3 asks" as a second kind of shift; (c) rebuild the deprecation stream from the two snapshots rather than citing the testbed. |
| 6 A model executes the reasoning | **Partly.** 30 asks: the 41 never-reached have workspaces (22 dev, 12 val, 7 post-cutoff; 18 overlap the ladder's 39). The 15 `scope_form` non-asks exist only after test 4. Tool access to the base = the solo scaffold or a `claude -p`/DeepSeek session with the workspace, not the ladder's one-turn form. | With tools, a "prompt" is a session: 45 cases × DeepSeek ($0, ~3 min each, server up) + 45 × strong model (subscription: ~40-80k processed tokens each, ≈2-4M, about a quarter to half of a five-hour window; or ELM gpt-5.5 ≈ $0.3-0.8 billed each, $15-40). Blind readers: 45 × 2 × ~5k ≈ 0.5M. Triple that for the three-arm version in §2. | The plan's single arm cannot separate the layers from memory: DeepSeek's and Claude's training cover Mathlib and Zulip for the 2025 PRs (the ladder README flags it). Change: three arms per case — place only; place + principle statement; place + principle + scope search — and prefer the 7 post-cutoff asks and val asks over the 22 dev asks (one reviewer's set, in-sample for every design). |

Two notes that apply to every test. **"Two independent readers" are two sessions of one model**, so
reader–reader agreement is a floor on the statements' legibility to that model, not two witnesses;
report it as such. And the plan's "under a million tokens" for tests 1, 3, 4 together is about a
fifth of the estimate above (≈5.3M); the census rate (1.6k a label) only holds for text-only labels,
and tests 3 and 4 are git-verified readings.

## 2. Outcome → action, per test

**Test 1.**
- κ ≥ 0.6 and ≤ 20% no-fit/ties → proceed. *Weak evidence as written:* two sessions of one model
  reading one set of statements will agree on most well-written text whatever the statements
  say about maintainers. Add the **names-only control**: a third pass given the 11 tag names and no
  statements. If it agrees with the two statement-readers as well as they agree with each other,
  the statements add nothing and test 1 has validated the tag names, not the principles.
- κ < 0.6 → "revise the statements". *Non-discriminating:* the same κ arises from (a) poor
  statements, (b) a tag set that is not a partition — `consistency` is defined as "matches how the
  library does it, whatever the reason", so it overlaps every other tag by construction, and 67% of
  entries already carry two tags — and (c) a 100-item sample (κ's interval is about ±0.12). Split:
  report κ with `consistency` merged into the other tag of each two-tag entry; report ties separately
  from no-fit; and widen to 150 entries if the first κ lands within 0.1 of the bar.
- The "Then" (run tests 3, 4, 6 on conventions alone) follows only for cause (a). Under (b) the fix is
  to the tag set, which the plan's guard forbids revising during test 3 — write the amendment before
  test 3 starts.

**Test 2.**
- ≥ 10 incompatible pairs, most separated by area → scope is a layer; resolution level from where
  the separation appears. *Confound:* an area is reviewed by few maintainers (74 reviewers, top five
  31%), so "separated by area" and "separated by reviewer" are the same observation. Record the
  reviewer per ask and report the pairs that separate **within one reviewer's asks** — those are
  scope; the rest are undetermined.
- < 10 pairs → "scope does no work, a flat list suffices". *Non-discriminating:* the census merged
  near-duplicates into one entry (`revised: true` marks entries broadened while reading), so an
  entry may already hold both forms under an "or"/"unless" clause, and the reader finds no pair
  because the codebook pre-empted it. Split: count entries whose text contains an alternation or
  exception clause, and take the crossmap's `a_broader`/`b_broader` A↔B relations as candidate
  pairs (reader B split what A merged). If those are plentiful, the result is "the codebook hides
  the pairs", not "there are none".
- > half co-occur in one area and period → "two designs coexist, maintainers accept both".
  *Non-discriminating:* with 2 asks a side, co-occurrence is noise; with two reviewers it is a
  reviewer split, which is not acceptance. Require ≥ 3 asks per side per entry before a pair counts
  as co-occurring, and report the reviewer split beside it. Expect few testable pairs: the floor
  leaves 84 candidate entries, 49 with asks in two areas.
- The date-separation → test 5 handoff follows as written, at the same floor.

**Test 3.**
- Same-scope dominant ≥ 75% → scope resolution is the mechanism. *Non-discriminating with a flat
  list:* if the asked form dominates the whole library, it also dominates every directory, and a
  flat convention predicts the same ask. The informative cell is **same-scope dominant and
  library-not-dominant**. Report the 2×2 (dominant in scope × dominant in library), not the margin;
  the plan's claim lives in one cell of it.
- "Dominant only wider" → a resolution rule. Follows, provided the wider count is not carried by
  one large file or one author's recent batch; record the top contributing files.
- "Dominant only in recent code" → currency (test 5). *Confound:* a directory written in the last
  90 days has every form "recent". Control: is the PR's form also present in the recent slice? Only
  "asked form recent and PR's form not" is currency.
- "Dominant nowhere" → a design decision. *Non-discriminating:* also produced by an uncountable form
  (`existing_declaration`, generality, process), a wrong grep pattern, or a scope with fewer than 5
  occurrences. The `countable` flag and the n ≥ 5 floor separate these; "nowhere" is only read on
  countable asks with enough occurrences.
- The stop rule's "under 50%" uses this test's margin; use the countable subset, or a flat-list
  success will be scored as the picture's failure (or the reverse).
- Also stratify dev (11 of 19 partial rows) against val/post: the dev set is one reviewer's 30 of
  52 comments, and a same-scope result there is one reviewer's habit.

**Test 4.**
- `unraised` ≥ 40% → gold is loose, silence is attention. *Non-discriminating in the other
  direction:* the reader knows every pair is unasked (they were selected for it), and the label set
  invites explaining the silence; a low `unraised` share can be deference, not evidence. Fix by
  **blinding with the 33 asked pairs where the model also said "departs"**, mixed into the batch
  unlabelled: the share of real asks the reader calls `trigger_absent` or `scope_form` is its
  rationalisation rate, and the unasked result is read only after that rate is known (under
  ~15% says the reading is believable; higher and the test cannot read silence).
- `scope_form` + `exception` dominate → negative evidence is reconstructible. Follows, if the
  calibration above passes.
- `history` vs `unraised`: both are "nothing in the code says why". Split by the store, not by a
  reader: for each pair, was the same thing raised in a later round, fixed by the author in a later
  commit without a comment, or still present at merge? Add `raised_later` and `fixed_anyway` as
  labels computed from `review_threads`/`commits`/the merge diff; "present at merge" is the only
  state that supports `unraised` as acceptance-by-silence.
- The 24 PR-level "departs" pairs are mostly process-type entries; read them as their own bucket or
  the segment result is diluted.
- The stop rule's 40% is on a 40-pair sample at one reader's reading: ±15pp. Either reader over 40%
  trips it; with two readers at that variance a false stop is likely. Require both, or read 60.

**Test 5.**
- < 5% of eligible entries shift → no currency layer. *Non-discriminating with power:* the labels do
  not record the form, and at 8 asks split 4/4 only a near-total shift is detectable even after the
  form reading. Report the detectable effect size per entry beside the shift count, and add the
  computable "new entry after 2025-12 with ≥ 3 asks" signal, which the fixed vocabulary otherwise
  hides. A "no shift" result on these two signals together is readable; on the first alone it is
  not.
- Shifts exist, none with a repository signal first → "Zulip only". *Non-discriminating:* a
  deprecation is a maintainer's act and often sits in the same PR as the first ask in the new form,
  so "signal precedes ask" is trivially true or trivially false depending on the tie rule. Require
  the signal's PR ≠ the ask's PR and signal date < first-ask date by at least a day; record the
  Zulip thread date from the FTS store for each shift so the two signals are compared on the same
  footing (the store runs to 2026-07-30 and is dense, so absence of a Zulip signal is informative).
- Shifts with a repository signal first → the norm store's maturity is measurable from snapshots.
  Follows, if the deprecation stream is rebuilt from E ∪ L; the testbed figure cannot be cited for
  it.

**Test 6.**
- ≥ 70% derive the asked form → the layers suffice. *Non-discriminating with memory:* the models
  may know the convention (val PRs predate both cutoffs; the ladder README flags DeepSeek's
  memory), and the sentence being hidden does not hide the training data. The three-arm design
  (place only / + principle / + scope search) reads the increments: arm 1 is memory and general
  skill, arm 2 − arm 1 the principle layer, arm 3 − arm 2 the scope layer. Without arm 1 a pass says
  nothing about the layers; prefer the 7 post-cutoff and 12 val asks, and report the 22 dev asks
  apart.
- ≥ 70% "conforms" on the `scope_form` non-asks → *non-discriminating as written:* these pairs were
  selected because DeepSeek said "departs" on them, so the test is whether a new prompt flips its
  own verdict, which a more conservative prompt also does. Add decoy non-asks whose right answer is
  "departs" (asked pairs the model called departs); a prompt that says conforms on both has learned
  caution, not scope.
- "Which step failed" per case → follows only from the transcript's tool calls and what each
  returned (`cli report tools` / the CLAUDE.md rule), not from the final answer; budget the reading
  for it.

## 3. Order, and the total

1. **The join script first** (half a day, no model): cid → PR, path, area, day-level date, author,
   base sha, for the 1,833 + 269 census asks; the deprecation union over E and L; first-ask date per
   entry. Three tests read from it and nothing else in the plan can start without it.
2. **Test 2's pair enumeration and test 5's computable part** (one day together, ≈0.3M tokens).
   They say whether scope and currency have enough asks behind them to be measured at all — the
   floor of ≥3 asks a side will leave few testable pairs, and knowing that number first stops a
   reading programme from being sized for a layer the census cannot see.
3. **Test 1's statements** written in the same day, before any reading (the plan's guard), with the
   names-only control (≈0.6M).
4. **Test 4 with the calibration mix** (one day, ≈2.9M), before test 3: it drives the stop rule, its
   calibration decides whether silence can be read at all, and it produces test 6's non-asks.
5. **Test 3** on the 19 + 21, countable subset flagged, 2×2 reported (one day, ≈2.0M).
6. **Test 5's form reading** only if step 2 found ≥ 10 entries with a detectable effect size (half a
   day, ≈1.3M).
7. **Test 6**, three arms, only if 3 and 4 hold (one day; DeepSeek $0, strong model ≈2-4M
   subscription tokens per arm or $15-40 on ELM per arm; readers ≈0.5-1.5M).

Total: about **5-6 session days**; **≈8-9M reader tokens** (≈ 40 subagent runs; at the census rate,
3-4 five-hour windows, shared with interactive use); cash **$0** if the strong model runs on the
subscription (the user's call, asked before) or **$45-120** on ELM for the three-arm test 6. No paid
review run, no build: tests 3 and 4 work at a sha, and every workspace test 6 needs is already built.
