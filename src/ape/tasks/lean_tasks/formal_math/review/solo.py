"""The whole-PR reviewer: one agent, the entire diff, no work units and no arms.

This is the floor the scheduled design has never been measured against.
`docs/research/step-by-step.md:24` named it Step 5 -- "run plain Claude Code/Codex ... purpose
is not leaderboard numbers but instrument validation" -- and :28 warned against skipping it.
It was skipped.

**It subclasses `BasePRReviewTask` directly, not the candidate task.** That is the whole
point: `LeanPRReviewV4CandidateTask` exists to enforce the work-unit submission contract --
`change_ids` drawn from the unit, subject equality, entity membership -- and a reviewer given
the whole PR was never handed that vocabulary. It says what a maintainer would say, at a path
and a line, and the anchoring pass resolves that onto change targets afterwards. Inheriting
the contract here would smuggle the decomposition into the condition that exists to do without
it.

**It is scaffold-agnostic, and that is load-bearing.** The same task runs under `ape_agent`
and under `claude_code`, so those two conditions send byte-identical prompt text through the
same submission contract and the same anchoring pass, and differ only in the agentic harness.
That restores the byte-identity invariant (commit 43e9d88) for the harness comparison, which
a whole-PR-vs-work-unit comparison cannot have. The alternative -- reusing the v2 holistic
task for the `ape_agent` cell -- would have confounded harness with prompt and contract, which
is the confound that cell exists to remove.

No submission tool is defined here. `BasePRReviewTask` already registers `submit_findings`
with exactly the free-form shape this condition wants -- `{path, line_start, line_end,
severity, claim, suggested_fix, evidence}` -- and `create_user_prompt` already names it.
"""

from typing import Tuple

from ape.tasks.base import register_task

from .base import (
    BasePRReviewConfig,
    BasePRReviewData,
    BasePRReviewResult,
    BasePRReviewTask,
)

#: Keeps the `v5` spelling for the same reason every other task type does: a task type is a
#: recorded identity, not a class name. See this package's `__init__` docstring.
SOLO_TASK_TYPE = "lean_pr_review_v5_solo"

SOLO_RENDERER_VERSION = "v5-solo-prompt/1"

SOLO_SYSTEM = """\
You are reviewing a pull request to Mathlib, the Lean 4 mathematics library, as one of its \
maintainers would.

The question is not whether the code compiles. It does -- it is a real PR that already builds. \
The question is whether a maintainer would merge it as it stands, and if not, what specifically \
they would ask the author to change.

What maintainers actually raise, in rough order of frequency: a proof that could be shorter or \
use the idiomatic tactic; a declaration that duplicates or should reuse something already in \
the library; a statement that could be more general at no cost; a name that does not follow \
the naming convention; a missing or inadequate docstring; a design that should be factored \
differently, or a family of lemmas that should be one mechanism.

How to review well:

- **Read the code, do not skim the diff.** The tools let you open any file in the repository at \
this commit. A duplicate or a reusable lemma is only findable by looking.
- **Be specific and indexical.** "Consider adding documentation" is not a review comment. \
"`foo_bar` has no docstring, and the three lemmas around it do" is. Name the declaration, say \
what is wrong with it, and say what to do instead.
- **Anchor every finding.** Give the file path and the line, and name the declaration in your \
claim. A finding nobody can locate cannot be acted on.
- **Do not pad.** A maintainer who asks for nothing is a normal outcome and a correct one. \
Findings you do not believe cost more than the ones you omit.
"""

SOLO_USER = """\
# Pull request #{pr_number}

**Title:** {title}

**Description:**
{description}

**Changed files:**
{changed_files}

**Tools available:** {tool_summary}

---

## The diff

```diff
{diff}
```

---

Review this PR. Investigate what you need to before deciding -- open the files, look for \
existing declarations that overlap, check whether a proof could be shorter.

Then call `{submit_tool_name}` exactly once with at most {budget} findings. For each, give \
`path` and `line_start` so the finding can be located, a `claim` naming the declaration and \
stating what is wrong, and a `suggested_fix` saying what to do instead.
"""


class SoloReviewConfig(BasePRReviewConfig):
    #: The lead's own per-PR published ceiling. A whole-PR reviewer has one call in which to
    #: say everything, so a budget tighter than the scheduled design's would be a handicap
    #: rather than a control.
    finding_budget: int = 20


class SoloReviewData(BasePRReviewData):
    task_type: str = SOLO_TASK_TYPE
    #: The run's episode, carried so `reviewed_workspaces` can resolve which workspace
    #: reviewed which episode. `BasePRReviewData` is keyed by PR; the evidence collectors are
    #: keyed by episode, and a whole-PR task is the only review task that would otherwise
    #: carry no episode at all.
    episode_id: str


class SoloReviewResult(BasePRReviewResult):
    episode_id: str = ""


class SoloReviewTask(BasePRReviewTask):
    task_type = SOLO_TASK_TYPE
    data_class = SoloReviewData
    task_config_class = SoloReviewConfig
    task_result_class = SoloReviewResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return SOLO_SYSTEM, SOLO_USER

    def create_result(self, **kwargs):
        # From `self.data`, never the model's self-report -- the same rule the arms follow, and
        # for the same reason: an identity the model can state is an identity it can get wrong.
        kwargs.setdefault("episode_id", self.data.episode_id)
        return super().create_result(**kwargs)


register_task(SOLO_TASK_TYPE, SoloReviewTask)
