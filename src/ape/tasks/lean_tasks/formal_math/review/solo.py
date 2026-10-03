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

import json
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from pydantic import Field, model_validator

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
{severity_line}
- `concern_family` -- one of: `correctness`, `proof-golf`, `duplication`, `naming`, \
`generalization`, `documentation`, `style`, `scope`, `other`.
- `issue_kind` -- one of: `broken_build`, `correctness_policy`, `documentation_gap`, \
`duplicate_implementation`, `generalization_available`, `missed_canonical_api`, \
`naming_convention_violation`, `policy_violation`, `proof_simplification`, \
`scope_placement`, `style_norm_violation`.

Label a finding with what it actually is. The labels route it to the right check; they are not \
a guess at what the grader wants, and a wrong one is worse than the honest nearest fit.
{notes_line}"""


#: The two spellings of the severity line, chosen by `SoloReviewConfig.filing_bar`. "merge" is the
#: wording every run before 2026-09-30 saw. "request" is the filing-bar condition of
#: results/pr_review_v5/probes/filing-bar-2026-09-30: gpt-5.4 and gpt-5.5 verified the
#: maintainers' asks and withheld them as "not something a maintainer would require", and this
#: line, the submission mandate and the submit tool's `merge_ready_as_is` were the three places
#: the task framed a finding as a merge verdict.
SEVERITY_LINES = {
    "merge": "- `severity` -- `blocking` if a maintainer would withhold merge over it, else `advisory`.",
    "request": ("- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` "
                "for every other change you would request. Advisory findings count in full."),
}


#: `SoloReviewConfig.review_notes`: brief X's `notes.md`, which every Claude reviewer wrote and no
#: gpt condition was asked for (docs/todo/reviewer-model-gap.md, 2026-10-01), as a field of the
#: submission. Empty when the field is off, so every earlier prompt renders byte for byte.
NOTES_LINE = """
Also give `notes`: what you did, object by object, including what you checked and found nothing \
wrong with. Every changed object gets an entry, closed with what you concluded about it."""


#: `SoloReviewConfig.notes_form: per_object_family`: the account in the shape the Claude reviewers'
#: `notes.md` actually took -- declaration by declaration, each taken through the concerns that apply
#: to it and closed with a verdict. Under the per-object line, gpt's notes named 37% of the PR model's
#: changed declarations (Claude 73-78%) and mentioned naming on 50% of PRs and generality on 17%
#: (Claude 92-100% and 75-83%); results/pr_review_v5/probes/contract-2026-10-01/.
NOTES_LINE_FAMILY = """
Also give `notes`: your account of the review, with an entry for every changed declaration in the \
PR model (declarations of one family may share an entry). In each entry, say what you checked for \
that declaration under each concern that applies to it -- its proof, its statement and how general \
it is, whether the library already has it, its name, its docstring, its attributes and placement -- \
and close it with what you concluded, "nothing to ask" included."""

#: `SoloReviewConfig.user_prompt: v2`. What v1 says that the Claude reviewers' contract never did is
#: gone, and nothing is added (results/pr_review_v5/probes/contract-2026-10-01/README.md):
#: - the PR model comes before the diff, in Claude's reading order, not after the instructions;
#: - no "Investigate ... look for existing declarations that overlap, check whether a proof could be
#:   shorter" (two of the brief's eight families, from the first solo prompt, 28d40719);
#: - no `concern_family` / `issue_kind` lists: the task stamps the pair an imported Claude finding
#:   carries, since the candidate validator needs an `issue_kind` and the judge shows the family;
#: - no "at most N findings": the budget is enforced in code, and it never bound.
#: `{context_block}` is filled before `format` runs, with its braces escaped.
SOLO_USER_V2 = """\
# Pull request #{pr_number}

**Title:** {title}

**Description:**
{description}

**Changed files:**
{changed_files}

**Tools available:** {tool_summary}
{context_block}
---

## The diff

```diff
{diff}
```

---

When you have reviewed the PR as the brief asks, call `{submit_tool_name}`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be \
located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
{severity_line}
{notes_line}"""


def solo_user_template(filing_bar: str = "merge", review_notes: bool = False,
                       user_prompt: str = "v1", notes_form: str = "per_object",
                       context_block: str = "") -> str:
    """The user template for this condition, before `format`.

    v1 is `SOLO_USER` with its severity line and, when the submission requires notes, the notes
    line; the PR model is appended after it by the task. v2 is `SOLO_USER_V2` with the PR model
    in place before the diff (`context_block`, braces escaped so `format` leaves Lean alone).
    """
    notes = "" if not review_notes else NOTES_LINE_FAMILY if notes_form == "per_object_family" else NOTES_LINE
    template = SOLO_USER if user_prompt == "v1" else SOLO_USER_V2.replace(
        "{context_block}", context_block.replace("{", "{{").replace("}", "}}"))
    return template.replace("{severity_line}", SEVERITY_LINES[filing_bar]).replace("{notes_line}", notes)


class SoloReviewConfig(BasePRReviewConfig):
    #: The lead's own per-PR published ceiling. A whole-PR reviewer has one call in which to
    #: say everything, so a budget tighter than the scheduled design's would be a handicap
    #: rather than a control.
    finding_budget: int = 20

    #: A brief in place of `SOLO_SYSTEM`, read from a file. Added 2026-09-29 so a probe's
    #: brief can run on the pipeline's own model through this task, with the brief kept beside
    #: the probe rather than in this module (`results/pr_review_v5/probes/gpt52-postcutoff-*`).
    #: The path is part of the scaffold config, so `scaffold_config_sha256` in the run plan
    #: changes with it; the file's content is pinned by the run plan's git commit.
    system_prompt_file: Optional[Path] = None

    #: Per-PR sections appended to the user prompt: JSONL rows
    #: `{"pr_number": N, "sections": [{"title": ..., "text": ...}]}`. How a probe hands the
    #: reviewer what its Claude conditions read from a packet (the pass-0 PR model). A PR the
    #: file does not hold is refused, not reviewed without its context.
    context_file: Optional[Path] = None

    #: How the task frames what a finding is. "merge": the severity line, the mandate and the
    #: submit tool speak of withholding merge and of `merge_ready_as_is` (every run before
    #: 2026-09-30). "request": a finding is a change the reviewer would request, `advisory` when
    #: not insisted on; the mandate and the tool carry no merge verdict. Only this task
    #: implements the field, so it lives here and not on the arms' base config.
    filing_bar: Literal["merge", "request"] = "merge"

    #: The submission requires `notes`, the object-by-object account brief X asked Claude for
    #: (`NOTES_LINE`), and a blank one is refused. Implemented for the request bar only: the
    #: merge bar's tool carries `merge_ready_as_is`, and a third variant of it would be a
    #: condition nothing has asked for.
    review_notes: bool = False

    #: What the notes are asked to cover: "per_object" (`NOTES_LINE`, the contract run of
    #: 2026-10-01) or "per_object_family" (`NOTES_LINE_FAMILY`). Needs `review_notes`.
    notes_form: Literal["per_object", "per_object_family"] = "per_object"

    #: "v1": `SOLO_USER`, every run before 2026-10-01. "v2": `SOLO_USER_V2` -- the PR model before the
    #: diff, no steering line, no label lists, no finding count -- with the mandate and the submit
    #: tool's description stated without "fails the task" / "INVALID", and the unlabelled pair stamped
    #: on every finding.
    user_prompt: Literal["v1", "v2"] = "v1"

    @model_validator(mode="after")
    def _named_files_exist(self) -> "SoloReviewConfig":
        """A named brief or context file that is not there is refused when the config is built,
        not when the first session opens it. `--set task_config.context_file=null` reached every
        session of iter_local397_unlock_D_rep1 as the path "null" (`parse_cli_args` spells the null
        value `None`) and the run sealed its plan; all 15 tasks then failed on their first prompt."""
        for name in ("system_prompt_file", "context_file"):
            path = getattr(self, name)
            if path is not None and not Path(path).is_file():
                raise ValueError(f"{name} {str(path)!r} is not a file (to unset it, --set {name}=None)")
        return self

    @model_validator(mode="after")
    def _notes_need_the_request_bar(self) -> "SoloReviewConfig":
        if self.review_notes and self.filing_bar != "request":
            raise ValueError("review_notes is implemented for filing_bar: request only")
        if self.notes_form != "per_object" and not self.review_notes:
            raise ValueError("notes_form needs review_notes: true")
        return self


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
    #: The reviewer's object-by-object account, when `review_notes` asked for one; "" otherwise.
    review_notes: str = ""


def solo_system_prompt(config: SoloReviewConfig) -> str:
    """`SOLO_SYSTEM`, or the brief `config.system_prompt_file` names -- never a silent default
    when a file was named and is missing."""

    if config.system_prompt_file is None:
        return SOLO_SYSTEM
    path = Path(config.system_prompt_file)
    if not path.is_file():
        raise FileNotFoundError(f"system_prompt_file {path} does not exist")
    return path.read_text(encoding="utf-8")


def solo_context_block(config: SoloReviewConfig, pr_number: int) -> str:
    """The sections `config.context_file` holds for this PR, or "" when no file is set."""

    if config.context_file is None:
        return ""
    path = Path(config.context_file)
    with path.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    row = next((item for item in rows if item.get("pr_number") == pr_number), None)
    if row is None:
        raise KeyError(f"context_file {path} holds no row for PR {pr_number}")
    sections = "\n\n".join(f"## {item['title']}\n\n{item['text'].rstrip()}"
                             for item in row["sections"])
    return "\n\n---\n\n" + sections + "\n"


class SoloReviewTask(BasePRReviewTask):
    task_type = SOLO_TASK_TYPE
    data_class = SoloReviewData
    task_config_class = SoloReviewConfig
    task_result_class = SoloReviewResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        config = self.config.task_config
        return (solo_system_prompt(config),
                solo_user_template(config.filing_bar, config.review_notes, config.user_prompt,
                                   config.notes_form,
                                   solo_context_block(config, self.data.pr_number)
                                   if config.user_prompt == "v2" else ""))

    async def create_user_prompt(self) -> str:
        # v1 appends the PR model after the instructions; v2 has already placed it before the diff.
        prompt = await super().create_user_prompt()
        if self.config.task_config.user_prompt == "v1":
            prompt += solo_context_block(self.config.task_config, self.data.pr_number)
        return prompt

    def _normalize_findings(self, findings):
        normalized = super()._normalize_findings(findings)
        if self.config.task_config.user_prompt == "v2":
            # Not asked for, so not the model's: the pair an imported Claude finding carries.
            from src.mathlib_review.analysis.probes import IMPORT_ISSUE_KIND, UNLABELLED_FAMILY

            for finding in normalized:
                finding["concern_family"], finding["issue_kind"] = UNLABELLED_FAMILY, IMPORT_ISSUE_KIND
        return normalized

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
