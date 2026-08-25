# PR Metadata Conventions For Split Plans

When proposing chunk titles and summaries:

- Make titles look like plausible standalone PR titles.
- Say what the chunk does, not just which files it touches.
- Summaries should explain the boundary: why these units belong together and why they are separated from neighboring units.
- If a chunk is preparatory, say what it is preparing for.
- If a chunk needs follow-up context, say that in the summary rather than overloading the title.

Good title patterns:
- `refactor: isolate prerequisite helper lemmas`
- `feat: add the main theorem statement and proof`
- `chore: normalize PR metadata and docs for the new API`
