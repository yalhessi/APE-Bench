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

---

## Result (2026-09-29): not mainly recall, on both matchers

The run, in order, each step committed before the next:
- the draw, release and build rows (`ea3f7d3`);
- the 20 sessions (`2ace505`);
- then the asks were extracted, labelled by two readers (`readers/`) and matched by two matchers
  (`match/`);
- `unblind.py` applies the rule above.

**The asks.** Six of the ten PRs drew round-1 feedback, 17 comments in all. The other four (41271,
41280, 41314, 42238) are controls.
- The readers agree on `is_ask` and family for all 17 and on grain for 16. They agree on 16 asks.
- The post-cutoff mix is naming 4, interface 3, statement design 2, generality 2, derivation 2, and
  layout, documentation and PR level one each.
- It holds no proof and no registration asks. The in-window reference is proof 7, interface 5,
  registration 2 and documentation 2.

| | matcher 1 | matcher 2 |
|---|---|---|
| in-window per-session reach (16 asks × 4 sessions) | 28/64 = 0.44 | 38/64 = 0.59 |
| post-cutoff per-session reach (16 asks × 2 sessions) | 15/32 = 0.47 | 15/32 = 0.47 |
| `r = post / in` | **1.07** | **0.79** |
| reading (`r ≥ 0.6` on both) | **not mainly recall** | **not mainly recall** |

- **The restricted `r`** (proof, interface and registration only) is not computed: the post-cutoff set
  holds 3 such asks, under the pre-set 8.
- **The families both sets hold:**
  - interface: 12/20 in-window against 4/6 post-cutoff;
  - documentation: 8/8 against 2/2.
- **Post-cutoff reach by family:**
  - layout 2/2 and documentation 2/2;
  - interface 4/6;
  - derivation 2/4 and generality 2/4;
  - naming 3/8;
  - statement design 0/4 and PR level 0/2.
- **Stability:** of the 8 post-cutoff asks either session reached, both sessions reached 7.
- **Controls:** findings per session on the four no-feedback PRs are 1/1, 3/4, 3/2 and 2/0 (mean
  2.0), against a mean of 4.1 on the six PRs with asks.

**Matching is reproducible.** These matchers re-judged the construction demonstration's in-window
cells and agree with that probe's matchers on reached-or-not in 64 of 64. Labels differ in one cell
(matcher 1) and two cells (matcher 2), each between partial and no. The two new matchers agree on all
32 post-cutoff cells. So the in-window totals here equal the first matching's (28 and 38) because the
matching is stable, not by construction. Their one systematic disagreement is again 32875's golf asks:
whether a different tactic that closes the goal reaches a `simpa` ask.

**What it means, at probe altitude** (6 PRs with asks, 16 asks, 2 sessions, 2 matchers):
1. **Claude's reach on in-window PRs is not mainly recall.** On PRs created after its cutoff, the same
   reviewer with the same brief, packet and tools reaches asks at 79-107% of its in-window rate. The
   five asks the pipeline missed and Claude reached are therefore more likely capability or harness
   than memory. This is the confound `docs/todo/reviewer-model-gap.md` named.
2. **The mix differs, and that limits the comparison.** The post-cutoff asks are naming and design,
   the in-window ones proof and interface. Where the families overlap (interface, documentation), the
   rates agree. A family-matched comparison needs more post-cutoff proof asks than 6 PRs supplied.
3. **Where the reviewer is weak on unseen PRs is where the record says it is:** statement design
   (0/4), PR level (0/2) and naming (3/8). Mechanical and local asks were reached.

**Designs not yet tried:** a larger post-cutoff draw, family-matched to the in-window reference; the
pipeline's model on this set (test (b)), where neither model can have seen the PRs.

## Deviations during the run, recorded

- **Four sessions were aborted by the API rate limit** (41930 X1/X2 and 43167 X1/X2), after 10-15
  tool calls and before any finding. They were rerun from a clean packet, and their partial call logs
  are kept in scratch.
- **Reviewed workspaces for seven PRs were built while earlier sessions ran.** Each PR's sessions
  launched only after its own reviewed workspace existed.
- **One base restore collided with its own build's completion** and marked the workspace failed. It
  was rebuilt and restored after the build had exited.
- **Leak audit** (`audit_transcripts.txt`): 593 tool calls in 24 transcripts, with 2 flags, both
  benign. After extraction, no tool result in any session contains a phrase from its own PR's
  round-1 comments. The only phrase found anywhere is a generic Mathlib docs URL, cited by a comment on
  42184 and seen in other PRs' sessions.
- **The matchers** read only their own folders.
