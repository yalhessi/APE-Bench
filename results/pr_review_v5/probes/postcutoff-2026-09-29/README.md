# Post-cutoff probe: is a Claude reviewer's reach on in-window PRs recall? (2026-09-29)

Written before the draw was walked and before any ask was read. Test (a) of
`docs/todo/reviewer-model-gap.md`.

**The question.** Every Claude probe so far reviewed PRs created 2025-06..2026-03, inside the
reviewers' training window (knowledge cutoff June 2026). In the construction demonstration,
Claude with the pipeline generalist's brief reached 5-6 of 11 asks the pipeline missed. That reach
could be ability or recall. This probe runs the same reviewer, with the same brief, packet and tools,
on PRs created after the cutoff.

## The set

`probe-2026-07-08-v1` (sealed `1f429f1`, digest 9a6ebe64): 8 main PRs (4 per month, created 2026-07
and 2026-08) and 2 AI PRs, at most 40 change targets (main) or 60 (AI), one PR per author. The draw
follows `projections.frame walk`. The release is built outside `inputs/pr_review_v4/releases/`, so
the set stays out of `scored_pr_numbers()`. PRs with no round-1 feedback are controls.

## The condition

X, the construction demonstration's control, verbatim:
- `brief_X.md` (the generalist checklist brief);
- `pr.md`, `diff.patch`;
- the pass-0 model (`build_model.py`, from the release's input and derived files only);
- `./ptool`, the arms' tools against each PR's reviewed workspace, with every call logged by the
  wrapper.

Two sessions per PR, X1 and X2, Claude subagents (`claude-opus-5-5`), with the demonstration's rules:
- read only the packet;
- keep temporary files in the packet's `tmp/`;
- use no git, web or other path.

## Asks

- The round-1 feedback of the drawn PRs is extracted only after every reviewer has finished
  (`extract_draw_feedback.py`, as for the validation set).
- Two blind readers label each comment with `is_ask`, a family from the val1000 codebook, and a
  grain. The rubric is `arm-coverage-val1000-2025-06-2026-03-v1/reader_rubric_v2.md` with the owner
  fields dropped.
- Only asks both readers agree are asks enter.

## Matching

Two blind matchers use `construction-demo-2026-09-29/matcher_rubric.md`, generalised to the number
of reviewers per PR. Each matcher also re-judges the in-window reference in the same pass: the
construction demonstration's X1-X4 findings on 34091, 30458 and 32875, against their 16 asks. So the
ratio below is computed within one matcher, whose strictness applies to both sets. Reviewer labels
are shuffled per PR, findings are stripped to target, claim, requested change and severity, and
condition cues are redacted.

## Reading rule

Per matcher, **per-session reach** is the asks `reached`, summed over sessions, divided by
(agreed asks × sessions):
- `in` is per-session reach on the 16 in-window asks, over X1-X4;
- `post` is per-session reach on the post-cutoff agreed asks, over X1 and X2;
- `r = post / in`.

| on both matchers | reading |
|---|---|
| `r ≥ 0.6` | the in-window reach is **not mainly recall**: on unseen PRs Claude keeps at least 60% of it |
| `r < 0.4` | **recall inflates** the in-window reach |
| otherwise, or the matchers disagree | **inconclusive** at this size |

**Mix, stated before:** the in-window reference is 16 asks on 3 PRs:
- proof 7, interface 5, registration 2, documentation 2;
- its per-session reach is 0.44 (matcher 1) and 0.59 (matcher 2) as first matched.

The post-cutoff mix will differ. So the family table is reported beside `r`. If both sets hold at
least 8 agreed asks in proof, interface and registration, `r` restricted to those families is
reported as well.

**Also read, not in the rule:**
- findings per session on the control PRs;
- per-family reach;
- stability between X1 and X2;
- whether a finding reproduces a maintainer's specific suggestion: the same named lemma, tactic or
  form.

## Caveats stated before

- **n is small:** 8-10 PRs, two sessions, two matchers. The reading is directional.
- **Censoring:** 777 of the window's PRs were still open at the store's walk, so August's members
  lean to fast closers.
- **Store coverage:** the precedent and Zulip corpora may hold little after mid-2026, which changes
  what the context tools return. Tool calls are logged, and the amount of precedent and Zulip evidence
  is reported.
