# Compare four ways to review the same PR

25 November 2026. The reference is the maintainer's feedback in the first review round at the reviewed head. The four agent strategies share a model, scaffold, brief, code and Lean tools. The difference is how evidence from prior PRs reaches the reviewer.

| Strategy | Additional input |
|---|---|
| Solo | No prior PR search or supplied convention list. |
| Search earlier comments | The reviewer can call `precedent_search` with code. It gets earlier inline comments and their code hunks. |
| Use automatically selected conventions | A separate selector sees the incoming PR and the convention catalogue. The reviewer gets the selected sentences in catalogue order. |
| Use exact conventions | An offline reader uses the target's historical requests to identify entries in the same catalogue. The reviewer gets only the selected sentences in the same format. |

The last two rows here use the list as their only source of PR history. October gave both rows an additional search tool. The original selector could choose up to 25 conventions. The exact list contained the conventions behind recorded requests. An applicable convention that the maintainer never raised can be absent from this list.

## What we can reproduce from October

We imported both original sets of blind judgments through APE. Every ask-by-review result matched the archived tables. Each count below is the number of expert requests reached. The two ordinary columns are separate review samples. The two validation rows are separate readings of the same submissions.

| Saved reading | Expert requests | Ordinary 1 | Ordinary 2 | Selected | Exact |
|---|---:|---:|---:|---:|---:|
| Six validation PRs, reader 1 | 27 | 12 | 10 | 11 | 18 |
| Same six PRs, reader 2 | 27 | 11 | 9 | 10 | 17 |
| Four later PRs, both readers | 11 | 3 | 3 | 4 | 7 |

The ordinary reviewers called `precedent_search` on every one of the ten PRs, 18 calls in sample 1 and 15 in sample 2. The selected and exact reviewers called it 16 and 12 times. The four groups also used Zulip. These PRs were selected using earlier solo misses. We can reproduce the comparison of adding convention sentences to a search-enabled reviewer on these PRs. A new control is needed to measure the value of giving solo access to earlier PRs. [Study and selection](../conventions-ceiling-2026-10-04/README.md) · [Example ordinary search call](../postcutoff-2026-09-29/pr42184/X1/calls.jsonl#L26)

Run these Bash commands from this topic worktree. The first block reproduces the saved judgments locally. It creates two reports, one for each original set of PRs.

```bash
export PYTHONPATH="$PWD/src:$PWD"
cli=(ape/bin/python -m src.mathlib_review.review.cli)
archive=results/pr_review_v5/probes/conventions-ceiling-2026-10-04
work=.ape/review-reading-20261125
mkdir -p "$work"
for group in val post; do
  case "$group" in
    val) setfile=configs/probe_sets/val_small12.yaml ;;
    post) setfile=configs/probe_sets/postcutoff_2026_07_08_v1.yaml ;;
  esac
  plan="$work/original-$group"
  if [[ ! -f "$plan/matching_plan.json" ]]; then
    "${cli[@]}" probe match-plan --set "$setfile" --name "original-$group" --out "$plan" \
      --seal "$archive/blinding_F_${group}_SEALED.json" --sources "$archive/sources_F.json" --version 1-session
  fi
  if [[ ! -f "$plan/verdicts/import-original.jsonl" ]]; then
    "${cli[@]}" probe match-import --set "$setfile" --plan "$plan" --name original \
      --matches "$archive/match_F_$group/matches.1.json" "$archive/match_F_$group/matches.2.json"
  fi
  "${cli[@]}" report match --plan "$plan" --producer import-original
done
```

To obtain a fresh reading of exactly those saved review findings, run the next block in your authenticated Claude subscription shell. It uses the current task-based matcher. Keep its results with their own version. Both of these plans passed a local preflight.

```bash
set -e
for group in val post; do
  case "$group" in
    val) setfile=configs/probe_sets/val_small12.yaml ;;
    post) setfile=configs/probe_sets/postcutoff_2026_07_08_v1.yaml ;;
  esac
  plan="$work/reread-$group"
  name="reading_october_${group}_v2"
  if [[ ! -f "$plan/matching_plan.json" ]]; then
    "${cli[@]}" probe match-plan --set "$setfile" --name "$name" --out "$plan" \
      --seal "$archive/blinding_F_${group}_SEALED.json" --sources "$archive/sources_F.json" --version 2-task
  fi
  "${cli[@]}" match --plan "$plan" --config configs/match/ask_match_opus55_claude_sub.yaml \
    --run-name "$name" --execute
  "${cli[@]}" report match --plan "$plan" --producer "task-$name"
done
```

## Run a matched example on PR 42184

This example reconstructs the earlier setup for diagnosis. Its absolute workspace paths tell the reviewer which strategy it is running. Its shared prompt prescribes a checklist, and its direct search uses a different collection from the convention catalogue. The [input audit](design-audit.md) checks these details against a real transcript. The [shared-history decision](../../../../docs/adr/0001-shared-history-for-review-comparisons.md) applies to the new comparison.

This known case tests the wiring. It has a prepared workspace, two recorded expert requests, saved selector choices and saved exact labels. A fresh study needs its own target PRs, a catalogue derived from earlier sources and exact labels for those targets. Freeze that catalogue before selecting the automatic list. Keep the target discussion available only to the evaluator and the offline exact selector.

For evidence about incoming reviews, choose PRs before inspecting their expert feedback. Include quiet PRs and identifiable AI-assisted PRs. Give each design the same reviewed heads, model, scaffold, brief and reviewer budget. Record the work of the selector separately. Run independent samples of each design. Regrading the same sample measures variation in reading the review. A fresh reviewer sample measures variation in producing it.

The following commands reuse the saved choices and prepare the inputs. They make no reviewer calls.

```bash
export ELAN_HOME=/research/projects/proofedit/ya475/.elan
export PATH="$ELAN_HOME/bin:$PATH" PYTHONPATH="$PWD/src:$PWD"
cli=(ape/bin/python -m src.mathlib_review.review.cli)
work=.ape/review-reading-20261125
ape/bin/python - <<'PY'
from pathlib import Path
from src.mathlib_review.analysis import probes

archive = Path('results/pr_review_v5/probes/conventions-ceiling-2026-10-04')
book = Path('results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json')
spec = probes.load_probe_set(Path('configs/probe_sets/postcutoff_2026_07_08_v1.yaml'))
work = Path('.ape/review-reading-20261125')
work.mkdir(exist_ok=True)
for label, selection in [('solo', None), ('selected', 'applicable'), ('exact', 'exact')]:
    rules = probes.load_conventions(archive / f'briefs_{selection}.json', book) if selection else None
    text = probes.model_context(spec, [42184], rules)
    path = work / f'{label}.jsonl'
    if path.exists():
        assert path.read_text() == text, f'Existing input differs: {path}'
    else:
        path.write_text(text)
PY
```

The command below checks four plans. All four resolved the cutoff and the reviewed workspace in our local check. The Claude subscription credential was absent from that shell. Running `run_four --execute` in an authenticated Claude subscription shell reproduces these named diagnostic conditions. Keep each run's plan, task result including its findings and optional message, tool grants and trace, and final output. The generation names, source names, matching plan and matcher name in this example all refer to the first sample. An independent sample needs its own generation names, source mapping, matching plan and matcher run.

```bash
run_four() (
  set -e
  unset OPENAI_API_KEY ELM_API_KEY OPENAI_ELM_API_KEY ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL
  for arm in solo history selected exact; do
    context=$arm
    tools='["declaration_search"]'
    if [[ "$arm" == history ]]; then
      context=solo
      tools='["declaration_search","precedent_search"]'
    fi
    "${cli[@]}" run --config configs/pr_review_v5_probe_2026_07_08_v1_opus55_G_claude_sub.yaml \
      --run-name "reading_42184_${arm}_r1" --set 'dataset.pr_numbers=[42184]' \
      --set "dataset.solo_context_tools=$tools" --set "task_config.context_file=$work/$context.jsonl" \
      --set dataset.solo_token_cap=600000 --set execution.max_concurrency=1 "$@"
  done
)
run_four
```

This search returns excerpts. Reading a complete earlier PR, its changes and its discussion needs a separate reader or a prepared, read-only reference workspace. The present index gates on comment creation time. A retained text can have a later edit. Before drawing conclusions about historical access, use a version known to predate the reviewed head or omit the ambiguous record. [Search result format](../../../../src/ape/tasks/lean_tasks/formal_math/review/context_tools.py#L259) · [Search gates](../../../../src/mathlib_review/retrieval/precedent_index.py#L406)

## Evaluate all four submissions together

After the four successful review runs, use the same first-round raw asks for every submission. The existing matcher reads each submitted finding's target, claim, requested change and severity. It does not read the whole-review message. Save that message and the ordered comments for future evaluations of the full review. Check additional comments and reading burden separately. A comment the maintainer never made can still be useful.

The following commands prepare the comparison, run two blind readings in your authenticated shell, and print both results. A second evaluation can use the same source runs with a new plan and rubric. If only the arithmetic changes, reuse the saved verdicts.

```bash
set -e
ape/bin/python - <<'PY'
import json
from pathlib import Path

sources = {}
for arm in ('solo', 'history', 'selected', 'exact'):
    run = f'reading_42184_{arm}_r1'
    results = list((Path('.ape/runs') / run / 'tasks').glob('*/task_result.json'))
    if len(results) != 1:
        raise SystemExit(f'Expected one completed task for {run}')
    submitted = json.loads(results[0].read_text())
    if not submitted.get('success') or submitted.get('pr_number') != 42184:
        raise SystemExit(f'Incomplete or wrong PR in {run}')
    sources[arm] = {'kind': 'solo', 'run': run}
Path('.ape/review-reading-20261125/sources.json').write_text(json.dumps(sources, indent=2))
PY
plan="$work/match-four"
if [[ ! -f "$plan/matching_plan.json" ]]; then
  "${cli[@]}" probe match-plan --set configs/probe_sets/postcutoff_2026_07_08_v1.yaml \
    --name reading_42184_four --out "$plan" --sessions solo history selected exact --prs 42184 \
    --sources "$work/sources.json" --version 2-task --replicates 2
fi
"${cli[@]}" match --plan "$plan" --config configs/match/ask_match_opus55_claude_sub.yaml \
  --run-name reading_42184_four_match --execute
"${cli[@]}" report match --plan "$plan" --producer task-reading_42184_four_match
```
