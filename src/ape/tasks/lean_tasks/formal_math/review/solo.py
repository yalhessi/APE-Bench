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

**Known and deliberate: the `verified` channel is structurally empty for this condition.** The
base grant includes `lean_verify_edit` and the agent does use it -- 4 calls on the first clean
probe run -- but nothing captures those compiles as verification artifacts, so no finding here
can ever carry a `verified_compile` warrant. That is the generalist arm's situation exactly,
for the same reason, and it is why the comparison is read on the `review` channel: `published`
recall measures the evidence gate rather than either reviewer. Recorded here so it is a stated
limitation rather than a surprise found while reading a result.
"""

from typing import List, Optional, Tuple

from pydantic import Field

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

Then call `{submit_tool_name}` exactly once with at most {budget} findings. For each, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be \
located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if a maintainer would withhold merge over it, else `advisory`.
- `concern_family` -- one of: `correctness`, `proof-golf`, `duplication`, `naming`, \
`generalization`, `documentation`, `style`, `scope`, `other`.
- `issue_kind` -- one of: `broken_build`, `correctness_policy`, `documentation_gap`, \
`duplicate_implementation`, `generalization_available`, `missed_canonical_api`, \
`naming_convention_violation`, `policy_violation`, `proof_simplification`, \
`scope_placement`, `style_norm_violation`.

Label a finding with what it actually is. The labels route it to the right check; they are not \
a guess at what the grader wants, and a wrong one is worse than the honest nearest fit.
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

    #: The same grant the generalist arm gets, for the same reason. The generalist is the
    #: scheduled design's own control and is documented as keeping all four "because that is
    #: the point of a control"; this condition is a control too, so a narrower grant would
    #: make an information difference read as an architecture difference. Retrieval is
    #: effectively one tool in practice -- `declaration_search` is 83% of observed calls --
    #: but the asymmetry would be in the wrong direction and free to avoid.
    context_tools: List[str] = Field(default_factory=list)

    #: Gates every retrieval tool: the committer timestamp of `reviewed_head_sha`, which is
    #: gold-free. The tools raise `CutoffUnavailable` rather than answering without it -- "a
    #: read that could see the future is not allowed to happen at all" -- and that refusal is
    #: the whole temporal-isolation story for an agent that is otherwise unconstrained.
    retrieval_cutoff: Optional[str] = None

    #: What every context tool stamps its trace row with. An arm's is its `(unit, arm)` pair;
    #: a whole-PR review has one per episode, so it is minted from the episode.
    #:
    #: Required, not optional, and this is why: the tools read `task.data.invocation_id` while
    #: building the row, *before* the best-effort trace write can swallow anything. Without the
    #: field every retrieval call returned
    #: `'SoloReviewData' object has no attribute 'invocation_id'` to the agent. Measured on the
    #: first paid run: 3 of 3 calls failed that way -- two `declaration_search`, one
    #: `precedent_search` -- so the condition reviewed the PR with its retrieval grant revoked
    #: and nothing said so. A default would have restored exactly that silence.
    invocation_id: str

    #: Where those rows land. The retrieval record is not a nicety: the fairness invariant this
    #: comparison rests on is that every condition saw the same sources under the same gate,
    #: and the leak audit's temporal check is that every row carries a non-null `gate` and an
    #: `as_of` no later than the cutoff. Neither is checkable without the file.
    trace_path: Optional[str] = None


class SoloReviewResult(BasePRReviewResult):
    episode_id: str = ""
    #: On the result as well as the data, so the run's own tooling files this as one
    #: invocation. `analysis.trajectory.extract` reads `task_result.json` and classifies a
    #: top-level result by whether it carries an `invocation_id`; without it the whole-PR
    #: review was filed as a lead, and its transcript could be found but not attributed.
    invocation_id: str = ""


class SoloReviewTask(BasePRReviewTask):
    task_type = SOLO_TASK_TYPE
    data_class = SoloReviewData
    task_config_class = SoloReviewConfig
    task_result_class = SoloReviewResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return SOLO_SYSTEM, SOLO_USER

    async def register_task_tools(self, mcp) -> None:
        # The base grant first -- `lean_verify_edit` and `submit_findings` -- then exactly the
        # context tools this run granted. Order matters: `register_context_tools` deliberately
        # omits `lean_verify_edit` because the base registers it, and registering it twice
        # would shadow it.
        await super().register_task_tools(mcp)
        from .context_tools import register_context_tools

        register_context_tools(self, mcp)

    def create_result(self, **kwargs):
        # From `self.data`, never the model's self-report -- the same rule the arms follow, and
        # for the same reason: an identity the model can state is an identity it can get wrong.
        kwargs.setdefault("episode_id", self.data.episode_id)
        kwargs.setdefault("invocation_id", self.data.invocation_id)
        return super().create_result(**kwargs)


register_task(SOLO_TASK_TYPE, SoloReviewTask)
