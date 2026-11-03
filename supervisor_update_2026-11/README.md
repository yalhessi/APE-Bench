# Supervisor update for 4 November 2026

Fresh copy of [the October update](../supervisor_update_2026-10/slides.md), prepared on
3 November. The October Markdown, HTML and PDF are preserved. The separate
[living research overview](../docs/project-research-overview.md) is also unchanged.

- [Revised meeting version](meeting-v2.md): 18 main slides plus six backups;
  [HTML](meeting-v2.html) and [PDF](meeting-v2.pdf). The main talk includes the theoretical
  frame and comparison with previous work, then separates research questions, monthly
  experiments and open questions for discussion.
- [Current structure and timing](meeting-structure.md): the four parts, the research
  questions, and the studies mapped to them; designed for 15–20 minutes before discussion.
- [Earlier restructuring options](presentation-options.md), preserved for comparison.
- [First meeting prototype](meeting-draft.md), also preserved;
  [HTML](meeting-draft.html) and [PDF](meeting-draft.pdf).
- [Slide source and speaker notes](slides.md)
- [HTML presentation](slides.html)
- [PDF](slides.pdf)
- [Evidence register](evidence.md)

The detailed reference updates experiments and lessons, especially conventions. It includes completed
experiments through 26 October and the 27 October assessment, checked against the current local
records, including experiment branches. It retains the earlier task formulation. The revised
meeting version above incorporates the later theoretical qualifications and places the
prior-work comparison before the project questions and monthly studies.

The detailed reference has 37 slides: 33 main slides and four backups. Its shorter path uses slides
1, 7–8, 13, 16, 18–23 and 25–33; the earlier formalization and literature remain available for
discussion. Slides 14–16 report the historical baseline experiments, rather than new November
measurements. Speaker notes give qualifications; the evidence register maps each new claim to
its record and revision.

The empirical additions cover:

- The GPT disposition positive omitted from the earlier summary, under exact convention supply.
- Corrections to the “5% of applicable places” claim: rule validity, scope, attention and survival.
- Conditional preparation on two PRs: more sources, unchanged historical recovery.
- The compact/full knowledge-bank comparison: 54 final reviews, failed primary advancement rule.
- The focused follow-up: 72 sessions separating alternative generation from the decision to ask.
- Exploratory requests outside the historical reference, with usefulness still to be judged.

The latest comparisons are small development studies. Historical ask recovery, a compiled
alternative and a useful request are separate measurements. The knowledge-bank and preparation
usefulness panels remain unlabeled in the inspected records; this deck does not claim an overall
usefulness comparison is complete. The source-bank and focused results are branch-local; see
the evidence register before moving or removing those worktrees.

Render from the repository root with a local Marp CLI and Chrome:

```bash
marp supervisor_update_2026-11/meeting-v2.md --html -o supervisor_update_2026-11/meeting-v2.html
marp supervisor_update_2026-11/meeting-v2.md --html --pdf --allow-local-files \
  -o supervisor_update_2026-11/meeting-v2.pdf
```

These commands only render local documents. No generation, semantic matching or judging is
needed to build the presentation. Relative links in the HTML open local source documents;
the PDF is the portable presentation, while the Markdown and evidence register carry the
full research trail.

Use `slides.md` in the same commands to regenerate the detailed reference.

Reference validation: Marp rendered both formats; the PDF has 37 pages. Chrome checks found no
slide overflow or footer overlap, and the main new result slides were visually inspected.
All 47 local Markdown links resolve in this checkout. The bank's reported counts and
primary misses were checked against both saved matcher tables, and the original October
source is byte-identical to its committed version. The source documents are versioned;
HTML and PDF are generated local exports, as in the October update.
