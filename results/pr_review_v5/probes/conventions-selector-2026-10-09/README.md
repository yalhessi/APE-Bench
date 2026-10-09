# DeepSeek as the convention selector: can the reviewer's own model choose the conventions, without the asks, as well as Opus did? (pre-registered 2026-10-09, before any call)

**Why.** Stage AP (`../conventions-ceiling-2026-10-04/README.md`, Result AP) moved DeepSeek from 0.16
to 0.34 of in-census asks.
- **It used stage F's blind Opus picks** as the conventions.
- **Its gain sits where the picks were right:** 0.50 on the 22 asks whose entry was picked, against
  0.03 on the other 11.
- **So selection is now the lever,** and a fully self-hosted reviewer needs its own model to select.
  This measures that alone, before any review session.

The user (2026-10-09): *"You can pick... I want to have a clearer picture of how to improve on the
solo reviewer to get a better deployable reviewer."*

**The design.**
- **Inputs:** stage F's selector inputs, built by the same functions as
  `build_selector_folders.py`:
  - all 438 reader-A entries as `P### sentence`;
  - `probes.pr_markdown`, `probes.render_models` and the episode's diff;
  - stage F's rubric, its "What to select" and "How many" sections verbatim.
- **Changes from stage F,** because this is one turn: the inputs are inline, not files, and the answer
  is the JSON list itself (`selector.py`, `INTRO`, `OUTPUT`).
- **The PRs:** the 13 probe PRs with in-census asks (stage L/D's sets). Stage F's Opus picks exist for
  10 of them.
- **The call:** DeepSeek-V4.1-Flash on `first`, one turn, reasoning high, `max_tokens` 65536, three
  samples a PR, 39 calls.
- **The prompts** are 73k-111k characters. They are uncommitted (`.gitignore`), with digests in
  `items.json` and `prompts.sha256`.

**The measure.** For each in-census ask, whether its reader-1 entry is in its PR's list at the first
5, 10 and 25: recall@k, mean over samples, per PR set. Mechanical, no matchers.

**Reading rule, on the 10 stage F PRs (33 asks), against Opus's recall@25 of 0.67 and recall@10 of
0.45:**

| DeepSeek's mean recall@25 | reading |
|---|---|
| **≥ 0.60** | **DeepSeek can replace Opus as AP's selector**: the self-hosted AP is next |
| **≤ 0.45** | **it cannot,** at one turn; the union of samples, or Opus, stays |
| between | mixed; the union of the three samples decides |

**Also read:**
- recall@5 and @10;
- the union of the three samples' picks (up to 75 a PR) and its recall;
- the overlap with Opus's 25;
- the 13-PR figures;
- unparsed and truncated answers.

**Limits.** In-sample PRs, three samples, and the census was written by Claude. Recall of the entry is
necessary for AP's gain, not sufficient: application still decides, as Result AP's split shows.

**Cost.** About 39 calls, under an hour on `first` including the server's start. $0.

## Result (2026-10-09): DeepSeek in one turn selects well below Opus; the union of three samples comes near, with half again as many picks

**How it ran.** 39 answers, 13:03 to 13:30 (`3482bbc7`), read with `selector.py read`. Every answer
parsed, none truncated, and the median list held 25 entries.

| on the 10 stage F PRs (33 asks) | DeepSeek, three samples | mean | Opus (stage F) |
|---|---|---|---|
| recall@5 | 0.15, 0.06, 0.09 | 0.101 | 0.182 |
| recall@10 | 0.27, 0.24, 0.24 | 0.253 | 0.455 |
| **recall@25** | 0.45, 0.48, 0.36 | **0.434** | **0.667** |

- **The union of the three samples' picks,** a mean 38.5 a PR: recall 0.636.
- **Overlap with Opus's 25:** a mean of 12.8 entries a sample.
- **On all 13 probe PRs with in-census asks** (39 asks; the script's label says 14):
  - recall@25 0.46 (mean of samples);
  - union 0.667 at 36 picks a PR.

**By the rule: it cannot replace Opus at one turn** (0.434 ≤ 0.45). The rule leaves the union of
samples or Opus. The union reaches 0.64, near Opus's 0.67, but at about 38 picks a PR against 25: a
longer section, and stage F showed that length dilutes.

**What it means, at this altitude** (three samples, in-sample PRs).
- **A self-hosted AP needs a better selector than one DeepSeek turn.** The candidates, none tried:
  - the union of three samples, at the cost of a longer section;
  - a selector that reads one file or declaration at a time and unions its picks (open-code-review's
    pass per file);
  - two stages: DeepSeek proposes 50, then ranks them.
- **Opus stays the selector for AP's measured gain.** One Opus selector call a PR is deployable on the
  subscription route.
