"""
Idiomaticity / canonicality checker (`lean_pr_review_idiom`).

A focused review task for a V2 sub-family the golf checker structurally misses:
proofs that are correct AND readable but are not written the *canonical, idiomatic*
way — a manual monotonicity `calc`/`rw` chain that should be `grw`/`gcongr`, an
explicit rewrite sequence that `simp`/`simp_all` handles, a bespoke arithmetic
argument that is `omega`/`grind`, or a re-derivation that should reuse the canonical
existing lemma. Characterisation of the missed maintainer golfs found this is where
they cluster: ~10/11 missed V2 golfs are "use the stronger tactic / canonical lemma",
on proofs that read fine — so the signal is *idiomaticity*, ORTHOGONAL to length
(golf) and to clarity (the proof is legible).

Like golf, the claim is a checkable proposition: write the idiomatic version and
confirm it compiles. This subclasses VerifiedPRReviewTask, so every submitted finding
carries a `verification` snippet that the kernel re-compiles — the idiomatic proof
provably closes the same goal, by construction.

The deliberate difference from golf: this is NOT about minimizing lines. An idiomatic
rewrite may be the same length; flag it when a maintainer would say "use X here", and
do NOT flag a proof that is already canonical just to shave tokens.
"""

from typing import List, Tuple

from ape.tasks.base import register_task

from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewConfig, VerifiedPRReviewTask

# The prompt text now lives in `review.focused_prompts` so the v4 focused arm can
# reuse it without a code edge into this frozen generation. Re-exported here under the
# original names: they are this module's public surface and the config default below.
from ape.tasks.lean_tasks.formal_math.review.focused_prompts import IDIOM_TOOLS, IDIOM_SYSTEM, IDIOM_USER  # noqa: F401


class LeanPRReviewIdiomConfig(BasePRReviewConfig):
    """Idiom-checker config: verify + search heavy tool defaults."""

    enabled_tools: List[str] = list(IDIOM_TOOLS)


class LeanPRReviewIdiomTask(VerifiedPRReviewTask):
    """Focused V2 idiomaticity/canonicality checker — orthogonal to golf (length)."""

    task_type = "lean_pr_review_idiom"
    task_config_class = LeanPRReviewIdiomConfig

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return IDIOM_SYSTEM, IDIOM_USER


register_task("lean_pr_review_idiom", LeanPRReviewIdiomTask)
