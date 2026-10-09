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
