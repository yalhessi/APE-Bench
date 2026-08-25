"""Load the distilled Mathlib review guidelines supplied to the guidelines agent.

The guidelines live in docs/guides as official docs (`*-official.md`) paired with
compact `*-reviewer.md` summaries. The distilled layer below — the review
`checklist.md` plus the four reviewer summaries it references — is small enough to
keep ALWAYS-ON in the system prompt. That is deliberate: the measured bottleneck is
not finding the code but the agent's flag/no-flag threshold, so the norms must be IN
CONTEXT at judgment time, not fetched on demand. The large `*-official.md` docs are
the depth layer (not injected; a future `read_guideline` tool can serve them).
"""

import functools

from ape.utils.project import PROJECT_ROOT

GUIDES_DIR = PROJECT_ROOT / "docs" / "guides"

# The distilled review layer the checklist itself defines (checklist.md §intro).
DISTILLED_GUIDES = [
    "checklist.md",
    "pr-review-guide-reviewer.md",
    "naming-conventions-reviewer.md",
    "documentation-style-reviewer.md",
    "style-guidelines-reviewer.md",
]


@functools.lru_cache(maxsize=1)
def load_distilled() -> str:
    """Concatenate the distilled guide files (each fenced by its filename)."""
    blocks = []
    for name in DISTILLED_GUIDES:
        path = GUIDES_DIR / name
        if path.exists():
            blocks.append(f"<<< {name} >>>\n{path.read_text().strip()}")
    if not blocks:
        raise FileNotFoundError(f"No distilled guideline files found under {GUIDES_DIR}")
    return "\n\n".join(blocks)


def guidelines_block() -> str:
    """The system-prompt section that supplies the community guidelines."""
    return (
        "# Mathlib community review guidelines\n\n"
        "Use the official Mathlib conventions below as the source of your review-quality "
        "judgments — not free-form preference. When a concern turns on naming, style, "
        "documentation, or what warrants a change request, these guidelines are authoritative: a "
        "deviation from them is a finding; conformance to them is not. Stay calibrated to them — "
        "do not invent stricter rules, and do not pad with nits the guidelines do not support.\n\n"
        + load_distilled()
    )
