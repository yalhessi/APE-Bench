"""The task every Mathlib review runs on, whatever generation scheduled it.

`BasePRReviewTask` and its config/data/result carry the parts of reviewing that do not vary:
the workspace, the tool grant, `lean_verify_edit` and the edit-confinement rules around it,
the submission plumbing, and the statement gate. A generation adds what it decides -- which
sites to look at, what question to ask, what counts as a warrant -- by subclassing.

It lived in `pr_review_v2` and was inherited from there by v4's candidate and opportunity
tasks and by v5's lead, which made "v4 is frozen and imported as a library" untrue in the most
consequential possible place: a v5-only observation about `lean_verify_edit` changed the tool
contract for every v2 checker and every v4 arm, and this session did exactly that. A base
class three generations inherit is not part of any one of them.

It sits here, beside the generations, rather than in `src/mathlib_review/`. A review task is a
`BaseLeanTask`, and `ape/tasks/__init__.py` imports every task package eagerly, so a task base
outside that tree cannot import `ape.tasks.base` without a cycle -- the framework's layout is
telling you where task classes go. `src/mathlib_review/` holds the parts that are not tasks.

`VerifiedPRReviewTask` sits on top for the tasks whose claims a compile settles.
"""

import asyncio
import json
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from pydantic import ConfigDict, Field

from ape.tasks.base import BaseTaskConfig, BaseTaskResult, EvaluationResult
from ape.tasks.lean_tasks.base import BaseLeanTaskData, BaseLeanTask

#: Default prompt version for a review task that does not name one.
#:
#: Carried here rather than imported from `pr_review_v2.prompt`, which was this module's only
#: dependency on the generation it used to live in. The prompt *texts* stay with v2's task,
#: which is the only thing that resolves this name into a pair of prompts; what the base needs
#: is a default to stamp on a config, and a subclass that renders its own prompts (every v4 and
#: v5 task does) never resolves it at all.
DEFAULT_PROMPT_VERSION = "acceptability_v2"

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


# Read-only toolset by default: no file_write/file_edit (the agent reviews, it
# does not fix). The list is the harness ablation knob — drop lean_verify for the
# no-compile rung, etc. lean_retrieve is intentionally NOT here: it needs a
# per-commit retrieval index that the workspace build does not produce, and
# without it the tool silently returns empty results (guard warning in `setup`).
DEFAULT_REVIEW_TOOLS = [
    "file_read",
    "content_search",  # grep over the repo — the cheap "retrieval substitute"
    "lean_verify",
    "get_lean_goal",
    "code_hover",
    "code_goto",
]


class BasePRReviewConfig(BaseTaskConfig):
    """Configuration shared by all PR-review tasks."""

    finding_budget: int = Field(default=10, description="Max findings the agent may submit")
    enabled_tools: Optional[List[str]] = Field(default_factory=lambda: list(DEFAULT_REVIEW_TOOLS))
    prompt_version: str = Field(
        default=DEFAULT_PROMPT_VERSION,
        description="Prompt framing/version; interpreted by each task's _get_prompts "
        "(holistic: acceptability_v2|mergeready_v1; checkers use their own).",
    )
    lean_verify_print_axioms: bool = False
    # Stage-2 Mode A priming (docs/research/precedent-retrieval-design.md §4/§7). Orthogonal to the
    # checker: any review task (golf/idiom/dup/gen/holistic) primes when precedent_file is set and is
    # byte-identical to its pre-priming baseline when it is None — so primed vs unprimed is a clean
    # ablation over the SAME code path, not a forked checker.
    precedent_file: Optional[Path] = Field(
        default=None,
        description="Precomputed precedents-by-PR JSONL (precedent_prime.py). None => unprimed baseline.",
    )
    precedent_top_k: int = Field(default=6, description="How many precedents to inject when primed.")
    require_verification: bool = Field(
        default=True,
        description="Verified checkers only: if True (default), EVERY submitted finding must carry "
        "a compilable edit/snippet (all-or-nothing gate — golf/idiom semantics). If False, findings "
        "WITH edits are still compile-gated, but claim-only findings (naming/docs/style, or edits "
        "that would not compile) pass through marked verified=false instead of sinking the batch — "
        "required by apply-all instantiation, whose checklist mixes checkable and social concerns.",
    )

    def apply_to_scaffold_config(self, scaffold_config: "BaseScaffoldConfig") -> None:
        scaffold_config.tools_config.lean_verify.print_axioms = self.lean_verify_print_axioms


class BasePRReviewData(BaseLeanTaskData):
    """One data model for every review task. The reviewed state is materialized as
    target_workspace (pinned at the MERGE BASE) + δ₀ applied. `task_type` selects
    which review task runs (the runner sets it; default = holistic)."""

    task_type: str = Field(default="lean_pr_review_v2")

    #: Diagnostic only: refuse an empty submission instead of recording an abstention, so the
    #: arm must name its best candidate however weak. NOT a production setting — it inverts
    #: the contract that makes control PRs measurable. It exists to separate three
    #: explanations of the 76% `already_correct` rate that the abstention data alone cannot:
    #: a bar set too high (recall rises under duress), arms that cannot see what maintainers
    #: want (volume rises, recall flat), or arms with genuinely nothing to say (neither moves).
    #: Bounded by `_FORCED_SUBMISSION_ATTEMPTS` so a refusal loop cannot turn a job into a
    #: coverage gap — the failure d06a144 fixed for the ordinary path.
    forbid_abstention: bool = Field(default=False)

    #: A verdict on every review target instead of one abstention for the whole job:
    #: `issue` (backed by a candidate), `no_issue` or `cannot_determine`, each with its reason.
    #: Not forcing -- `no_issue` is a legal answer, so an empty candidate list stays as cheap as
    #: it was -- but no target can pass unexamined and no silence goes unexplained. The contract
    #: lives entirely in the `submit_candidates` tool, so the rendered prompt, and with it every
    #: prompt identity, is unchanged: a run with this on differs from one without in the
    #: submission tool and nothing else. `docs/plans/2026-09-23-work-enumeration.md`.
    target_verdicts: bool = Field(default=False)

    pr_number: int = Field(..., description="GitHub PR number")
    pr_title: str = Field(default="", description="PR title (model-visible, cleaned)")
    pr_description: str = Field(default="", description="PR description (model-visible, cleaned)")
    diff: str = Field(..., description="δ₀ — unified diff (merge base → h0)")
    changed_files: List[str] = Field(default_factory=list, description="Changed .lean file paths")
    snapshot_head_sha: Optional[str] = Field(
        default=None, description="h0 commit, for reference (materialization is base + δ₀)."
    )
    snapshot_base_sha: Optional[str] = Field(
        default=None, description="Merge-base commit (= target_workspace.commit_hash); patch marker."
    )

    @property
    def pr_diff(self) -> str:
        """Alias consumed by the reused legacy patched-workspace materialization."""
        return self.diff


class BasePRReviewResult(BaseTaskResult):
    """Result model: the submitted review, for external D1/D2/D3 scoring."""

    model_config = ConfigDict()

    pr_number: int
    merge_ready_as_is: Optional[bool] = None
    confidence: Optional[float] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    review_message: str = ""


def submission_mandate(submit_tool_name: str, filing_bar: str = "merge",
                       review_notes: bool = False, plain: bool = False) -> str:
    """The closing instruction that forces a `submit_findings` call.

    Agents that conclude "nothing to flag" sometimes end with a text-only reply and never call
    the tool, which the harness records as an empty failure rather than a clean review, so the
    empty-review path is explicit and mandatory. Under the "request" filing bar the empty call
    carries no `merge_ready_as_is`, since that tool variant has no such field; with
    `review_notes` it still carries the notes, which the tool requires. `plain` (the solo task's
    `user_prompt: v2`) keeps the empty-review path and drops "MUST" and "fails the task", the same
    register as the batch preamble's "TEXT ALONE accomplishes NOTHING".
    """
    empty = ("call it with an empty `findings` list and `merge_ready_as_is: true`" if filing_bar == "merge"
             else "call it with an empty `findings` list and your `notes`" if review_notes
             else "call it with an empty `findings` list")
    if plain:
        return f"\n\nFinish by calling `{submit_tool_name}` once. If there is nothing to ask, {empty}."
    return (f"\n\nYou MUST finish by calling `{submit_tool_name}` exactly once — even if you find "
            f"nothing. If there is nothing to change, {empty}. A text-only reply does not count and "
            "fails the task.")


class BasePRReviewTask(BaseLeanTask):
    """Shared, read-only, externally-scored review task. Not registered; subclass
    it, set `task_type`, and implement `_get_prompts`."""

    #: A review task has no scratch file. The thing worth compiling is the reviewed file in
    #: `target/`, which is read-only for the agent but not blocked from the compiler — review
    #: sets `read_only_path_patterns` and leaves `blocked_path_patterns` empty. Opting in here
    #: lets `lean_verify` read it, without changing proof_engineering, whose task genuinely
    #: does require a self-contained snippet.
    lean_verify_allows_target = True

    #: `lean_verify` is the snippet probe here (`LeanVerifyToolsProvider._register_snippet_probe`):
    #: a review task has no scratch Lean file to compile, the reviewed file is compiled through
    #: `lean_verify_edit`, and under the general registration the two tools read as one
    #: ("verify ... correctness" with a `file_path`) while reviewers used this one for `#check`
    #: and `example` probes 55 times in 84 (2026-10-01).
    lean_verify_snippet_only = True

    data_class = BasePRReviewData
    task_config_class = BasePRReviewConfig
    task_result_class = BasePRReviewResult

    # --- prompt hook (subclasses implement) ---------------------------------
    def _get_prompts(self, version: str) -> Tuple[str, str]:
        """Return (system_prompt, user_template) for this task's framing."""
        raise NotImplementedError

    # --- workspace materialization ------------------------------------------
    @classmethod
    async def setup_attempt(
        cls, data, config, orchestrator_id, attempt_path=None, logger=None, progress_callback=None,
    ):
        """Reviewed state = merge-base snapshot + δ₀ applied, reusing the legacy
        task's proven patched-workspace overlay (needs only pr_diff/changed_files/
        target_workspace) rather than resolving a fork head commit."""
        attempt_path, scratch_workspace, target_workspace, reference_workspaces = (
            await super().setup_attempt(
                data, config, orchestrator_id, attempt_path, logger, progress_callback
            )
        )
        if target_workspace is not None and (data.diff or "").strip():
            from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask

            # A prebuilt reviewed workspace -- base + diff + changed modules rebuilt -- if one
            # exists for this (base, diff). Then there is nothing to patch, and a compile of any
            # changed file resolves the declarations the PR itself adds or renames. Without it,
            # the source-only overlay below is the environment in which 41 of 321 arm sessions
            # read a renamed sibling as `Unknown constant`; the fallback logs that at WARNING.
            reviewed = await ReviewPRCoreTask._maybe_setup_reviewed_target_workspace(
                data, target_workspace.path, logger=logger, progress_callback=progress_callback,
            )
            if reviewed is not None:
                target_workspace = reviewed
            else:
                target_workspace = await ReviewPRCoreTask._ensure_patched_target_workspace(
                    data=data, target_workspace=target_workspace,
                    logger=logger, progress_callback=progress_callback,
                )
        return attempt_path, scratch_workspace, target_workspace, reference_workspaces

    async def setup(self, termination_callback, orchestrator_id: str, attempt_path=None):
        """Materialize the reviewed PR state read-only — the agent inspects
        `target/` and the diff; it never edits."""
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if self.target_workspace and not self.target_workspace.read_only_path_patterns:
            self.target_workspace.read_only_path_patterns = ["**/*"]
        if self._lean_retrieve_enabled() and self._missing_retrieve_workspaces():
            self.logger.warning(
                "lean_retrieve is enabled but the retrieval index is missing for this commit — "
                "searches will silently return empty. Build it first "
                "(`python -m ape.toolkits.retrieve.lean.build`) or drop lean_retrieve."
            )
        return logger

    def _tool_summary(self) -> str:
        tools = self.config.task_config.enabled_tools or []
        has = lambda t: t in tools  # noqa: E731
        parts = []
        if getattr(self.config, "scaffold_type", "") == "claude_code":
            # Claude Code keeps its own file tools and APE's are not registered there, so the
            # line below named three tools the session did not have (`file_read`,
            # `content_search`, `file_search`), and a reviewer called `zulip_search` by its bare
            # name twice where the harness spells it `mcp__core__zulip_search` (2026-10-01).
            parts.append("read and search files with Read, Grep and Glob")
            parts.append("every other tool below is spelled `"
                         f"{self.config.mcp_server_name}<name>`")
        if has("file_read") and not parts:
            parts.append("read files")
        if has("content_search") and getattr(self.config, "scaffold_type", "") != "claude_code":
            parts.append("grep the repo (content_search)")
        if has("file_search") and getattr(self.config, "scaffold_type", "") != "claude_code":
            parts.append("find files by name (file_search)")
        if has("lean_retrieve"):
            parts.append("semantic library search (lean_retrieve)")
        if has("lean_verify"):
            parts.append("compile a snippet against the library (lean_verify)"
                         if getattr(self, "lean_verify_snippet_only", False)
                         else "compile/verify Lean code (lean_verify)")
        if has("get_lean_goal"):
            parts.append("inspect goals")
        if any(has(t) for t in ("code_hover", "code_goto")):
            # Not "references": `code_references` has no registration, so naming it here told
            # every task in every generation it had a capability it does not have.
            parts.append("navigate declarations (hover/goto)")
        return ", ".join(parts) if parts else "none (diff only)"

    async def create_user_prompt(self) -> str:
        _system, user_template = self._get_prompts(self.config.task_config.prompt_version)
        changed = "\n".join(f"  - `{p}`" for p in self.data.changed_files) or "  (none listed)"
        submit_tool_name = f"{self.config.mcp_server_name}submit_findings"
        base = user_template.format(
            pr_number=self.data.pr_number,
            title=self.data.pr_title,
            description=self.data.pr_description.strip() or "(no description provided)",
            diff=self.data.diff,
            changed_files=changed,
            tool_summary=self._tool_summary(),
            submit_tool_name=submit_tool_name,
            budget=self.config.task_config.finding_budget,
        )
        mandate = submission_mandate(submit_tool_name, self._filing_bar(), self._review_notes(),
                                     self._plain_contract())
        return base + mandate + self._precedent_block()

    def _filing_bar(self) -> str:
        """`task_config.filing_bar` where the task declares it (the solo task), else "merge"."""
        return getattr(self.config.task_config, "filing_bar", "merge")

    def _review_notes(self) -> bool:
        """`task_config.review_notes` where the task declares it (the solo task), else False."""
        return getattr(self.config.task_config, "review_notes", False)

    def _plain_contract(self) -> bool:
        """The solo task's `user_prompt: v2`: mandate and submit tool without the imperatives."""
        return getattr(self.config.task_config, "user_prompt", "v1") == "v2"

    def _precedent_block(self) -> str:
        """Stage-2 Mode A: append retrieved past-maintainer precedents for THIS PR, if primed.
        Returns "" (no-op) when unprimed, so the baseline prompt is unchanged."""
        cfg = self.config.task_config
        pf = getattr(cfg, "precedent_file", None)
        if not pf:
            return ""
        pf = Path(pf)
        if not pf.exists():
            self.logger.warning("precedent_file %s missing — running UNPRIMED", pf)
            return ""
        row = None
        for line in pf.read_text().splitlines():
            if line.strip() and json.loads(line).get("pr_number") == self.data.pr_number:
                row = json.loads(line)
                break
        precs = (row or {}).get("precedents") or []
        precs = precs[: max(0, getattr(cfg, "precedent_top_k", 6))]
        if not precs:
            return ""
        items = []
        for i, p in enumerate(precs, 1):
            body = (p.get("precedent_body") or "").strip()[:400]
            code = (p.get("precedent_code") or "").strip()[:600]
            items.append(
                f"{i}. On `{p.get('path')}`, a maintainer wrote:\n   \"{body}\"\n"
                f"   (regarding this code)\n   ```\n{code}\n   ```"
            )
        joined = "\n\n".join(items)
        return (
            "\n\n---\n## Precedent from past Mathlib maintainer reviews\n\n"
            "These are real comments maintainers made on *similar* code in earlier PRs, retrieved for "
            "this PR's changed declarations. Use them only as hints about what reviewers here tend to "
            "flag: apply a precedent's principle **only if it genuinely bears on this PR's code**, and "
            "do **not** invent a finding merely to match one. Ignore precedents that do not apply.\n\n"
            f"{joined}\n"
        )

    async def create_system_prompt(self) -> str:
        system, _user = self._get_prompts(self.config.task_config.prompt_version)
        return system

    # --- the shared submit_findings contract --------------------------------
    def _edited_file_code(
        self, path: Optional[str], line_start: Optional[int] = None, line_end: Optional[int] = None,
        replacement: Optional[str] = None, declaration_name: Optional[str] = None,
        new_declaration: Optional[str] = None,
    ) -> Tuple[Optional[str], str]:
        """Read the PATCHED reviewed file at `path` and return its content with the edit applied:

        - DECLARATION mode (`declaration_name` + `new_declaration`): parse the file, locate the
          named declaration, and replace it WHOLE with `new_declaration`. Robust for `match`/
          structured proofs (no line bookkeeping; the replacement is always a complete
          declaration, so it can't break the surrounding structure). Leading `@[...]` attributes
          before the keyword are preserved — give `new_declaration` from `theorem/lemma/def …`.
        - LINE mode (`line_start`/`line_end` + `replacement`): splice over that exact line span.
        - AS-IS (no edit): return the file unchanged (a plain compile check).

        Returns (code, "") or (None, error). Shared by the lean_verify_edit tool (all review tasks)
        and the verified submission gate; the compile runs via LeanVerifyToolsProvider.execute
        against target_workspace, so cross-file build (A) applies everywhere with no change here."""
        norm = _strip_ws_prefix(path)
        if not norm:
            return None, "no file path given"
        root = self.target_workspace.path if self.target_workspace else None
        if root is None:
            return None, "no reviewed workspace available to verify against"
        fp = Path(root) / norm
        if not fp.is_file():
            return None, f"reviewed file not found: {norm}"
        src = fp.read_text(encoding="utf-8")

        if declaration_name and new_declaration:
            return splice_declaration(src, declaration_name, new_declaration, label=norm)

        lines = src.split("\n")
        if line_start is None and line_end is None:
            if replacement is not None:
                return None, "`replacement` needs the span it replaces: give `line_start` and `line_end`"
            return src, ""  # compile the file unedited
        if not (isinstance(line_start, int) and isinstance(line_end, int)
                and 1 <= line_start <= line_end <= len(lines)):
            return None, f"line span {line_start}-{line_end} out of range for {norm} ({len(lines)} lines)"
        # No replacement for a span is a deletion. The model's way of saying "delete these lines"
        # was `"replacement": }`, malformed JSON that the CLI refused before the tool saw it, on
        # 7 calls in three dev runs (2026-10-01).
        edited = lines[: line_start - 1] + (str(replacement).split("\n") if replacement else []) + lines[line_end:]
        return "\n".join(edited), ""

    @staticmethod
    def _error_key(item: Dict[str, Any]) -> str:
        """Identify an error by its text, not its position.

        Line numbers move when the file is edited, so position cannot be part of the key —
        the same pre-existing error would look new merely because the edit shifted it.
        """

        return str((item or {}).get("data") or "").strip()

    async def _baseline_errors(self, path: Optional[str]) -> set:
        """Errors the reviewed file already has, compiled once per attempt and cached."""

        return (await self._baseline_diagnostics(path))["errors"]

    async def _baseline_diagnostics(self, path: Optional[str]) -> Dict[str, set]:
        """Errors and warnings the reviewed file already has, compiled once per attempt and cached.

        Cached because the unedited file does not change during an attempt, and a full-file
        compile is the expensive operation here — paying it once per file rather than once
        per exploratory edit is the difference between the split being free and it doubling
        the cost of verification.
        """

        cache = getattr(self, "_baseline_error_cache", None)
        if cache is None:
            cache = self._baseline_error_cache = {}
        key = _strip_ws_prefix(path)
        if key in cache:
            return cache[key]
        empty = {"errors": set(), "warnings": set()}
        code, err = self._edited_file_code(path)
        if code is None:
            cache[key] = empty
            return cache[key]
        from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

        lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
        try:
            baseline = await lean_tool.execute(code=code, max_messages=50, options=WHOLE_FILE_OPTIONS)
        except Exception:  # noqa: BLE001
            cache[key] = empty
            return cache[key]
        cache[key] = {
            "errors": {self._error_key(item) for item in (baseline.get("errors") or [])},
            "warnings": {self._error_key(item) for item in (baseline.get("warnings") or [])},
        }
        return cache[key]

    async def _attribute_errors(self, path: Optional[str], result: Dict[str, Any]) -> Dict[str, Any]:
        """Split a compile result into the errors and warnings this edit introduced and those
        already present."""

        errors = list(result.get("errors") or [])
        warnings = list(result.get("warnings") or [])
        if not errors and not warnings:
            return result
        baseline = await self._baseline_diagnostics(path)
        enriched = dict(result)
        if warnings:
            # Mathlib's linters run on the whole file (`WHOLE_FILE_OPTIONS`), so a long file
            # reports every pre-existing warning on every edit; only the edit's own are the
            # reviewer's business here, and the file's own are the as-is call's.
            enriched["warnings_introduced_by_your_edit"] = [
                item for item in warnings if self._error_key(item) not in baseline["warnings"]]
            enriched["warnings_already_in_the_file"] = len(warnings) - len(
                enriched["warnings_introduced_by_your_edit"])
            enriched.pop("warnings", None)
        if not errors:
            return enriched
        baseline = baseline["errors"]
        introduced = [item for item in errors if self._error_key(item) not in baseline]
        pre_existing = [item for item in errors if self._error_key(item) in baseline]
        enriched["errors_introduced_by_your_edit"] = introduced
        enriched["errors_already_in_the_file"] = pre_existing
        # The note states what was measured and nothing more. It used to end "The file does
        # not compile as it stands" -- a claim about the PR that this tool cannot make. On a
        # multi-file PR the compile resolves imports through the base commit's build products,
        # so a declaration the PR adds or renames in a *sibling* file is `Unknown constant` here
        # whatever the PR's real state; 41 of 321 arm sessions on the held-out run received
        # exactly that, and 16 findings asserted a build failure on PRs that all build. A
        # pre-existing error is a fact about this verification environment until the reviewed
        # state has been rebuilt; the environment says which it is (see `environment` below).
        if pre_existing and not introduced:
            enriched["note"] = (
                f"Your edit introduced no new errors. The {len(pre_existing)} error(s) listed were "
                "already present when the unedited file was compiled in this environment."
            )
        elif pre_existing:
            enriched["note"] = (
                f"{len(introduced)} error(s) came from your edit; {len(pre_existing)} were "
                "already present in the unedited file in this environment. Fix only the former."
            )
        if pre_existing:
            enriched["environment"] = self._verification_environment_note()
        return enriched

    def _verification_environment_note(self) -> str:
        """What the compile could and could not see, so a pre-existing error is read correctly.

        Two environments, told apart by the target's key. Against a *reviewed* workspace the
        PR's changed modules are rebuilt, so imports resolve the PR's own declarations and a
        pre-existing error is real -- rare on a PR that builds, and usually a file that cannot
        be checked standalone. Against a source-only overlay of the *base* commit, the PR's
        changes are visible in the file being compiled and invisible in every file it imports,
        so an error naming a declaration this PR adds or renames elsewhere is an artifact. The
        note names which, rather than leaving the model to infer a build failure.
        """

        from ape.toolkits.execute.lean.core.build_manager import is_reviewed_workspace_key

        commit = str(getattr(self.target_workspace, "commit_hash", "") or "")
        if is_reviewed_workspace_key(commit):
            return (
                "Verified against the reviewed workspace: this PR's changed modules, and the "
                "modules between them on the import graph, are rebuilt, so imports resolve the "
                "declarations this PR adds or renames. Modules the PR did not touch are as they "
                "were compiled at the merge-base; only a changed file has a fully rebuilt import "
                "closure. A pre-existing error in a changed file is genuine -- most often a file "
                "that cannot be checked on its own."
            )
        return (
            "Imports resolve against the base commit's build products, not the PR's. If an error "
            "names a declaration this PR introduces or renames in another file, it is an artifact "
            "of that -- not evidence the PR fails to build. This PR compiles."
        )

    def _register_lean_verify_edit(self, mcp) -> None:
        """Register the lean_verify_edit exploration tool — available to EVERY review task (the
        holistic agent and the verified checkers), so any reviewer can test that a proposed edit
        compiles in context before reporting it."""
        from typing import Annotated

        from ape.toolkits.execute.lean.tools import OUTCOME_NOTE

        @mcp.tool(
            description=(
                "Test an in-file edit, recompiling the WHOLE file and returning the compile result. "
                "Use it to confirm a change you want to suggest actually compiles in context. Two "
                "ways to specify the edit: PREFERRED — `declaration_name` + `new_declaration` "
                "replaces that whole declaration (robust for match/structured proofs; no line "
                "counting). You may include the declaration's `@[...]` attributes and "
                "modifiers or omit them; either way they are not duplicated. Or "
                "`line_start`/`line_end` + `replacement` to splice a line span, with no "
                "`replacement` to delete the span. Your edit may "
                "reference the PR's own new declarations. Omitting all edit args answers a "
                "DIFFERENT question — whether the file compiles as the PR leaves it — and "
                "returns `compiles` plus `errors_already_in_the_file`, with no `success` "
                "field, because nothing was verified: it tests none of the changes you are "
                "weighing. Errors come back split into "
                "`errors_introduced_by_your_edit` and `errors_already_in_the_file` — fix only "
                "the former; line numbers refer to the whole spliced file, so use `code_line` "
                "to locate them. Warnings are Mathlib's standard linters, as CI runs them, split "
                "the same way. " + OUTCOME_NOTE
            )
        )
        async def lean_verify_edit(
            path: Annotated[str, Field(description="Reviewed file path, e.g. Mathlib/.../X.lean")],
            declaration_name: Annotated[Optional[str], Field(
                description="Name of the declaration to replace whole (e.g. Subgroup.closure_pow_le)")] = None,
            new_declaration: Annotated[Optional[str], Field(
                description="Full replacement declaration (from its theorem/lemma/def keyword)")] = None,
            line_start: Annotated[Optional[int], Field(
                description="Line mode: first line of the span to replace (1-based)")] = None,
            line_end: Annotated[Optional[int], Field(
                description="Line mode: last line of the span (inclusive)")] = None,
            replacement: Annotated[Optional[str], Field(
                description="Line mode: exact Lean text to substitute for that span; omit it to delete the span")] = None,
            max_messages: Annotated[int, Field(description="Max compile messages to return")] = 20,
        ) -> Dict[str, Any]:
            code, err = self._edited_file_code(
                path, line_start, line_end, replacement,
                declaration_name=declaration_name, new_declaration=new_declaration)
            if code is None:
                return {"success": False, "outcome": "invalid_request", "error": err}
            from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider
            lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
            try:
                result = await lean_tool.execute(code=code, max_messages=max_messages,
                                                 options=WHOLE_FILE_OPTIONS)
            except Exception as exc:  # noqa: BLE001
                return {"success": False, "outcome": "tool_error", "error": f"verify raised: {exc}"}
            # Which of these errors are actually the caller's fault?
            #
            # Compiling the whole file means the report mixes three things: errors the edit
            # introduced, errors the file already had, and cascading noise from a splice that
            # damaged the surrounding structure. Without the split, an agent reads errors
            # about declarations it never touched and revises the wrong thing — which is what
            # happened repeatedly: a mangled splice produced `unexpected token 'open'` inside
            # a *neighbouring* declaration, and the agent kept editing its own.
            edited_only = bool(line_start or declaration_name or replacement or new_declaration)
            if edited_only:
                result = await self._attribute_errors(path, result)
                if isinstance(result, dict):
                    result["mode"] = "verified_edit"
                return result
            # Two different questions, and they must not come back in the same shape.
            #
            # "Does this file compile?" is legitimate and is the `correctness` arm's opening
            # move — a reviewed state that is red is the most serious thing a reviewer can
            # report (33057's gold obligation is exactly that). "Is my proposed change sound?"
            # is the other question, and only an edit can answer it.
            #
            # Spelling both `lean_verify_edit(path=...)` was survivable; returning both as
            # `{"success": true, ... "Lean verification completed successfully"}` was not. The
            # file compiles by construction in the ordinary case, so the no-edit call is a
            # guaranteed green that reads exactly like a discharged verification. A `note`
            # saying otherwise did not hold: all 86 no-edit calls in
            # `pr5_A_lead_heldout12_rep1` carried it, and the call was still the last act
            # before 33 of 82 empty submissions — 9 of 9 for `docs`, 10 of 19 for `naming`.
            # Text does not beat shape, so the shape changes here: this answers the status
            # question, in the vocabulary of the status question, and claims nothing else.
            #
            # `schema/evidence.py:88` already rules for the evidence layer that "we did not
            # check" and "we checked and found nothing" must not look alike. This is that rule
            # applied one layer up, where the artifacts are produced.
            if not isinstance(result, dict):
                return result
            errors = list(result.get("errors") or [])
            outcome = result.get("outcome")
            report = {
                "mode": "as_is_compile_check",
                "outcome": outcome,
                # From the outcome, not from an empty error list: a compile that never ran has no
                # errors either, and `not errors` reported it as `compiles: true`.
                "compiles": outcome == "compiled",
                # Every error is pre-existing by definition when no edit was applied, so this
                # needs no baseline compile — and it makes the `correctness` prompt's promise
                # of a split true for the first time, which it never was on this path.
                "errors_already_in_the_file": errors,
                "errors_introduced_by_your_edit": [],
                "warnings": result.get("warnings") or [],
                "environment": self._verification_environment_note(),
                "warrants": (
                    "The current state of the file as the PR leaves it, and nothing else. "
                    "This is NOT evidence for or against any change you are considering: no "
                    "edit was applied, so nothing you are weighing has been tested. To test "
                    "a change, call again with `declaration_name` + `new_declaration`."
                ),
            }
            if outcome not in ("compiled", "compile_errors"):
                # Did not finish or never ran: no verdict on the file, so say so in its words.
                report["compiles"] = None
                report["message"] = result.get("message")
                if result.get("diagnosis"):
                    report["diagnosis"] = result["diagnosis"]
            return report

    async def register_task_tools(self, mcp) -> None:
        from typing import Annotated

        self._register_lean_verify_edit(mcp)

        FINDINGS = Annotated[List[Dict[str, Any]], Field(
            description=(
                "List of findings (<= budget). Each: {path?, line_start?, line_end?, "
                "severity: 'blocking'|'advisory', claim, suggested_fix?, evidence?}. "
                "`evidence` is the verified artifact backing the finding (the existing "
                "declaration's name for a duplicate; the stronger statement for a generality "
                "issue). Empty list = nothing to change."
            )
        )]
        CONFIDENCE = Annotated[Optional[float], Field(description="0.0-1.0")]
        MESSAGE = Annotated[str, Field(description="Optional summary of the review.", default="")]
        DESCRIPTION = (
            "Submit your review of this PR. Call it once, when you have finished: it records the "
            "review and ends the session."
        ) if self._plain_contract() else (
            "Submit your final review findings for this PR. Call this exactly once when done. "
            "This records the review and ends the conversation. A text-only response is INVALID."
        )

        async def record(findings, merge_ready_as_is, confidence, message,
                         notes: Optional[str] = None) -> Dict[str, Any]:
            """Record a `submit_findings` call: normalise, build the result, fire termination.

            `notes` is None unless the task asks for the object-by-object account
            (`review_notes`); then a blank one is refused and the session goes on, since the
            account is what the condition exists to require.
            """
            self.logger.info("submit_findings: %d findings, merge_ready=%s", len(findings or []), merge_ready_as_is)
            if notes is not None and not notes.strip():
                return {
                    "success": False, "outcome": "invalid_request",
                    "error": ("Not recorded: `notes` is empty. Give your account of the review, "
                              "object by object, including what you checked and found nothing "
                              "wrong with, then call this tool again."),
                }
            budget = self.config.task_config.finding_budget
            if 0 < budget < len(findings or []):
                # Refused, not truncated. `_normalize_findings` used to cut the tail and warn in
                # the log, so a finding past the budget vanished with nothing said to the
                # reviewer: 2 and 4 findings on 33149 in two dev reps (2026-10-01). The reviewer
                # chooses what to drop.
                return {
                    "success": False, "outcome": "invalid_request",
                    "error": (f"Not recorded: {len(findings)} findings exceed this review's budget "
                              f"of {budget}. Call again with at most {budget}, keeping the changes "
                              "you would most insist on; mention the rest in `message`."),
                }
            extra = {} if notes is None else {"review_notes": notes}
            try:
                normalized = self._normalize_findings(findings or [])
                # A verdict-less submission is still a valid review: infer it from the findings
                # (empty => nothing to change => merge-ready) so it is not recorded as an empty failure.
                if merge_ready_as_is is None:
                    merge_ready_as_is = len(normalized) == 0
                result = self.create_result(
                    success=True, score=1.0, pr_number=self.data.pr_number,
                    merge_ready_as_is=merge_ready_as_is, confidence=confidence,
                    findings=normalized, review_message=message or "", **extra,
                )
                if self.termination_callback:
                    try:
                        await self.termination_callback(result)
                    except Exception as exc:  # noqa: BLE001
                        self.logger.warning("Failed to trigger termination: %s", exc)
                return {
                    "evaluation_result": EvaluationResult(
                        success=True, score=1.0,
                        message=f"Review recorded: {len(normalized)} findings, merge_ready={merge_ready_as_is}.",
                    ),
                    "message": "Review submitted",
                }
            except Exception:  # noqa: BLE001
                self.logger.error("submit_findings failed: %s", traceback.format_exc())
                return {
                    "evaluation_result": EvaluationResult(success=False, score=0.0, message=traceback.format_exc()),
                    "message": "Submit failed",
                }

        if self._review_notes():
            # The contract condition: the request bar, plus the object-by-object account the
            # Claude reviewers wrote as `notes.md` (brief X), here a required field of the one
            # call that ends the session. `SoloReviewConfig` refuses it under the merge bar.
            @mcp.tool(description=DESCRIPTION)
            async def submit_findings(
                notes: Annotated[str, Field(description=(
                    "What you did, object by object, including what you checked and found "
                    "nothing wrong with. Required, also when `findings` is empty."))],
                findings: FINDINGS = [],
                confidence: CONFIDENCE = None,
                message: MESSAGE = "",
            ) -> Dict[str, Any]:
                return await record(findings, None, confidence, message, notes=notes)
        elif self._filing_bar() == "request":
            # The filing-bar condition: no merge verdict anywhere in the submission, so the
            # reviewer is never asked whether a maintainer would merge, only what it would request.
            @mcp.tool(description=DESCRIPTION)
            async def submit_findings(
                findings: FINDINGS = [],
                confidence: CONFIDENCE = None,
                message: MESSAGE = "",
            ) -> Dict[str, Any]:
                return await record(findings, None, confidence, message)
        else:
            @mcp.tool(description=DESCRIPTION)
            async def submit_findings(
                findings: FINDINGS = [],
                merge_ready_as_is: Annotated[Optional[bool], Field(
                    description="True if a maintainer would merge without requesting changes."
                )] = None,
                confidence: CONFIDENCE = None,
                message: MESSAGE = "",
            ) -> Dict[str, Any]:
                return await record(findings, merge_ready_as_is, confidence, message)

    def _normalize_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Coerce raw tool input into the PredictionRecord finding shape; drop empties,
        clamp severity, enforce the budget, keep optional evidence."""
        budget = self.config.task_config.finding_budget
        if 0 < budget < len(findings) and self.logger:
            # Cut silently, a finding past the budget looks like one never filed.
            self.logger.warning("submit_findings: %d findings past the budget of %d not recorded",
                                len(findings) - budget, budget)
        out: List[Dict[str, Any]] = []
        for raw in findings[: budget if budget > 0 else len(findings)]:
            if not isinstance(raw, dict):
                continue
            claim = str(raw.get("claim") or "").strip()
            if not claim:
                continue
            path = raw.get("path") or None
            anchor = None
            if path:
                line_start = raw.get("line_start") if isinstance(raw.get("line_start"), int) else None
                line_end = raw.get("line_end") if isinstance(raw.get("line_end"), int) else line_start
                anchor = {"path": str(path), "line_start": line_start, "line_end": line_end}
            severity = str(raw.get("severity") or "").lower()
            if severity not in ("blocking", "advisory"):
                severity = "advisory"
            try:
                confidence = float(raw["confidence"]) if raw.get("confidence") is not None else None
                if confidence is not None:
                    confidence = min(max(confidence, 0.0), 1.0)
            except (TypeError, ValueError):
                confidence = None
            out.append({
                "anchor": anchor,
                "severity": severity,
                "claim": claim,
                # Carried through when the caller asked for them, absent otherwise. The
                # `solo` condition needs both because `candidates_from_response` refuses a
                # candidate with no `issue_kind` on any release rendered at
                # `candidate-prompt/12` or later -- which is all 225 work units of
                # dev-medium-0.3.0 -- so without them every finding it files would be
                # rejected and the run would read as a reviewer that found nothing.
                #
                # Deliberately not added to the tool's *description*: that string is
                # delivered verbatim to the v2 checkers, which are measured assets, and
                # changing what they are shown would make their next run incomparable to
                # their last for a reason unrelated to anything being tested. The schema is
                # already free-form, so a task that wants these asks for them in its own
                # prompt and they arrive here without a shared surface changing.
                "concern_family": (str(raw["concern_family"]) if raw.get("concern_family") else None),
                "issue_kind": (str(raw["issue_kind"]) if raw.get("issue_kind") else None),
                "suggested_fix": (str(raw["suggested_fix"]) if raw.get("suggested_fix") else None),
                "evidence": (str(raw["evidence"]) if raw.get("evidence") else None),
                "verified": raw.get("verified") if isinstance(raw.get("verified"), bool) else None,
                # per-finding P(maintainer would leave this comment) — the apply-all mode's ranking
                # signal; None for checkers that don't emit it.
                "confidence": confidence,
            })
        return out

    def create_result(self, success: bool, score: float, **kwargs) -> BasePRReviewResult:
        return self.task_result_class(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            **kwargs,
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        return True  # a submitted review always ends the task

    @classmethod
    def is_best_result(cls, result: "BaseTaskResult") -> bool:
        return bool(result.success)


# Concurrency cap for re-compiling finding evidence (each is a Lean compile).
_VERIFY_CONCURRENCY = 3

# Predicted paths are workspace-relative (target/Mathlib/…); the materialized reviewed
# tree is rooted at target_workspace.path with repo-relative paths (Mathlib/…).
_WS_PREFIX_RE = re.compile(r"^(?:target/|reference/[^/]+/|scratch/|a/|b/|\./|/)+")

#: `-D` options for compiling a whole reviewed Mathlib file: the standard linter set, as the
#: package build and CI apply it (`lakefile.lean`, `mathlibLeanOptions`, each name prefixed
#: `weak.` so that a file compiled outside the package accepts it). Without it a whole-file
#: compile reported `warnings: []` on a 101-character line the maintainers asked to wrap
#: (d0041; `transcript-inspection-2026-09-30`), and the one reviewer that found it compiled a
#: snippet with the linter switched on by hand. Checked 2026-10-01 in a reviewed workspace:
#: the long-line linter fires on a standalone compile with this option and not without it.
#: Snippet probes (`lean_verify`) do not get it: the header linter would flag every snippet.
WHOLE_FILE_OPTIONS = {"weak.linter.mathlibStandardSet": "true"}


def splice_declaration(
    src: str, declaration_name: str, new_declaration: str, *, label: str = "the file",
) -> Tuple[Optional[str], str]:
    """Replace one whole declaration in `src`, located by parsing rather than by text search.

    Returns `(edited, "")` or `(None, error)`. Public and shared, because there are two edit
    paths and they must mean the same thing by "declaration mode": the single-edit path
    (`_edited_file_code`) and the coordinated one (`patchset.apply`, which is handed this as a
    callable so it stays workspace-free). `patchset` used to do
    `text.replace(declaration_name, new_declaration, 1)` while its comment claimed to be doing
    this -- so an edit naming `Dense.continuous_sup` rewrote the first *mention* of that name,
    which on a real file is its own docstring, and then compiled the wreckage.

    An empty `new_declaration` deletes the declaration; `deletion` is 3 of the 11 obligation
    shapes that need a coordinated fix, and `PatchEdit.mode()` already admits it.
    """

    from ape.toolkits.code.lean.lean_parser import extract_proof_blocks

    try:
        decls = extract_proof_blocks(src)
    except Exception as exc:  # noqa: BLE001
        return None, f"could not parse {label} to locate `{declaration_name}`: {exc}"
    matches = [d for d in decls if declaration_name in (d.name, d.fullname)
               or (d.fullname and d.fullname.endswith("." + declaration_name))]
    if not matches:
        return None, f"declaration `{declaration_name}` not found in {label}"
    if len(matches) > 1:
        opts = ", ".join(sorted({m.fullname or m.name or "?" for m in matches}))
        return None, (f"`{declaration_name}` is ambiguous in {label}; use the full name "
                      f"(one of: {opts})")
    found = matches[0]
    # Replace from the keyword by default, which preserves any attributes and modifiers
    # already in the file. When the replacement supplies its own, replace from the start of
    # that decoration instead -- otherwise the two concatenate into `@[simp] @[simp] theorem
    # ...`, which fails to parse and reads to the agent as a mysterious syntax error in code
    # it did not write.
    start = found.header_span[0]
    if _supplies_own_prefix(new_declaration):
        start = _declaration_prefix_start(src, found.header_span[0])
    body = str(new_declaration).rstrip()
    if not body:
        # Deletion: drop the declaration and the blank line that separated it.
        return src[:start].rstrip("\n") + ("\n" if src[:start].strip() else "") + \
            src[found.body_span[1]:].lstrip("\n"), ""
    return src[:start] + body + "\n\n" + src[found.body_span[1]:], ""


def _strip_ws_prefix(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return _WS_PREFIX_RE.sub("", str(path).strip())


#: Modifiers that may precede a declaration keyword. `extract_proof_blocks` anchors
#: `header_span[0]` at the keyword itself, so anything in this set — and any `@[...]`
#: attribute block — sits in the *preserved prefix* when a declaration is replaced.
_DECL_MODIFIERS = (
    "private", "protected", "noncomputable", "public", "partial", "unsafe", "scoped",
    "local", "nonrec",
)


def _strip_decoration(segment: str) -> Optional[str]:
    """Consume leading `@[...]` blocks and modifier words; return what is left.

    Returns None when the segment contains something that is not decoration, which is the
    signal to leave the text alone.
    """

    rest = segment.strip()
    while rest:
        if rest.startswith("@["):
            depth, index = 0, 0
            for index, char in enumerate(rest):
                if char == "[":
                    depth += 1
                elif char == "]":
                    depth -= 1
                    if depth == 0:
                        break
            if depth != 0:
                return None
            rest = rest[index + 1:].lstrip()
            continue
        word = rest.split(None, 1)[0]
        if word in _DECL_MODIFIERS:
            rest = rest[len(word):].lstrip()
            continue
        break
    return rest


def _declaration_prefix_start(src: str, keyword_pos: int) -> int:
    """Start of the declaration's own attribute/modifier block.

    Handles decoration both on the keyword's own line (`@[simp] theorem foo …`, which is the
    common spelling in Mathlib and was the dominant real failure) and on the lines above it.
    Line-based above, character-based on the keyword's line — a character offset on an
    *earlier* line would let the splice swallow the newline ending a docstring, joining
    `/-- doc -/` onto the replacement.

    Anything it does not recognise makes it return `keyword_pos`, which is the original
    behaviour and always safe.
    """

    newline = src.rfind("\n", 0, keyword_pos)
    line_start = newline + 1 if newline != -1 else 0
    lead = src[line_start:keyword_pos]
    if lead.strip() and _strip_decoration(lead):
        # Something on this line is not decoration; do not reach past the keyword.
        return keyword_pos
    cursor = line_start if not lead.strip() else line_start

    while cursor > 0:
        previous_end = cursor - 1
        previous_newline = src.rfind("\n", 0, previous_end)
        previous_start = previous_newline + 1 if previous_newline != -1 else 0
        segment = src[previous_start:previous_end]
        if not segment.strip():
            break
        remainder = _strip_decoration(segment)
        if remainder is None or remainder:
            break
        cursor = previous_start
    return cursor


def _supplies_own_prefix(new_declaration: str) -> bool:
    """True when the replacement already carries its own attributes or modifiers.

    Agents supply them constantly — 32 of 58 `lean_verify_edit` failures on the rep4 smoke
    run were `unexpected token '@['`, `'noncomputable'` or `'public'`, all produced by
    splicing a self-decorated declaration after a prefix the file already had. Detecting it
    is strictly better than restating the contract in the tool description, which is what the
    contract already did.
    """

    head = (new_declaration or "").lstrip()
    if head.startswith("@["):
        return True
    first = head.split(None, 1)[0] if head.split() else ""
    return first in _DECL_MODIFIERS


class VerifiedPRReviewTask(BasePRReviewTask):
    """Review task that ENFORCES proof-carrying findings at submission.

    The verifiable checkers (golf / duplication / generality) subclass this. The
    agent's separate lean_verify calls are only a tool for its own exploration —
    they do not guarantee the *reported* finding holds. So submission itself runs
    the kernel: each finding must carry a `verification` Lean snippet, and the
    submit tool re-compiles every snippet via lean_verify. A finding is accepted
    ONLY if its snippet compiles; the result therefore contains only
    kernel-validated findings, with no agent claim to trust (judge-independent by
    construction). All-or-nothing, mirroring proof_engineering's submit: if any
    snippet fails the tool returns the compile errors and does NOT terminate, so
    the agent fixes or drops it and resubmits.
    """

    async def register_task_tools(self, mcp) -> None:
        from typing import Annotated

        self._register_lean_verify_edit(mcp)

        @mcp.tool(
            description=(
                "Submit your final findings. Each finding is VERIFIED by recompiling the PR file "
                "with your edit applied. PREFERRED: give `path` + `declaration_name` + "
                "`new_declaration` (the full replacement declaration) — submission replaces that "
                "whole declaration and recompiles; robust for match/structured proofs. Or give "
                "`path` + `line_start` + `line_end` + `replacement` to splice a line span. The "
                "finding is accepted only if the file still compiles; your rewrite MAY use the PR's "
                "own new declarations. Verify your edit first with lean_verify_edit. If any fails "
                "you'll get the errors back — fix or drop and resubmit. A text-only response is INVALID."
            )
        )
        async def submit_findings(
            findings: Annotated[List[Dict[str, Any]], Field(
                description=(
                    "List (<= budget). Each: {path, severity, claim, suggested_fix, and EITHER "
                    "(declaration_name + new_declaration) OR (line_start + line_end + replacement)}. "
                    "`new_declaration`/`replacement` is the verified Lean edit (recompiled on submit); "
                    "`suggested_fix` is the human-readable description. (Optional `verification`: a "
                    "self-contained snippet, used only when no in-file edit is given.)"
                )
            )] = [],
            merge_ready_as_is: Annotated[Optional[bool], Field(
                description="True if a maintainer would merge without requesting changes."
            )] = None,
            confidence: Annotated[Optional[float], Field(description="0.0-1.0")] = None,
            message: Annotated[str, Field(description="Optional summary.", default="")] = "",
        ) -> Dict[str, Any]:
            findings = findings or []
            self.logger.info("submit_findings (verified): %d candidate findings", len(findings))
            try:
                failures = await self._verify_findings(findings)
                if failures:
                    msg = self._format_verification_failures(failures, len(findings))
                    if not getattr(self.config.task_config, "require_verification", True):
                        msg += ("\nNote: only findings WITH edits are compile-gated here. For any "
                                "failing edit you cannot fix, REMOVE its edit fields "
                                "(declaration_name/new_declaration/replacement/verification) and "
                                "resubmit the finding claim-only with lower confidence — do not "
                                "drop the finding itself.")
                    return {
                        "evaluation_result": EvaluationResult(
                            success=False, score=0.0,
                            message=msg,
                        ),
                        "message": "Verification failed — fix or drop the listed findings and resubmit.",
                    }
                normalized = self._normalize_findings(self._mark_verified(findings))
                result = self.create_result(
                    success=True, score=1.0, pr_number=self.data.pr_number,
                    merge_ready_as_is=merge_ready_as_is, confidence=confidence,
                    findings=normalized, review_message=message or "",
                )
                if self.termination_callback:
                    try:
                        await self.termination_callback(result)
                    except Exception as exc:  # noqa: BLE001
                        self.logger.warning("Failed to trigger termination: %s", exc)
                return {
                    "evaluation_result": EvaluationResult(
                        success=True, score=1.0,
                        message=f"Review recorded: {len(normalized)} kernel-verified findings.",
                    ),
                    "message": "Review submitted",
                }
            except Exception:  # noqa: BLE001
                self.logger.error("submit_findings (verified) failed: %s", traceback.format_exc())
                return {
                    "evaluation_result": EvaluationResult(success=False, score=0.0, message=traceback.format_exc()),
                    "message": "Submit failed",
                }

    async def _verify_findings(self, findings: List[Dict[str, Any]]) -> List[Tuple[int, str, str]]:
        """Verify each finding by recompiling the PATCHED target file with the proposed
        edit spliced in (IN-FILE verification): the `suggested_fix` replaces lines
        [line_start, line_end] of the reviewed file and the whole file is recompiled.

        This is what lets a rewrite reference the PR's OWN new declarations — they are
        elaborated in-file, with the real local context (section variables, `open`s,
        notation, imports) — which a standalone snippet against the base-built oleans
        cannot do (the new decls aren't compiled). Falls back to a self-contained
        `verification` snippet when no in-file anchor is given (e.g. a brand-new
        self-contained claim). Returns failures (index, claim, error); empty = all
        kernel-verified.
        """
        from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

        lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
        sem = asyncio.Semaphore(_VERIFY_CONCURRENCY)

        require = getattr(getattr(self.config, "task_config", None), "require_verification", True)

        async def check_one(finding: Dict[str, Any]):
            code, err = self._build_verification_code(finding)
            if code is None:
                if not require:
                    # lax mode: claim-only finding — accepted unverified rather than failing
                    return {"success": True, "claim_only": True}
                return {"success": False, "errors": [{"data": err}]}
            async with sem:
                try:
                    return await lean_tool.execute(code=code)
                except Exception as exc:  # noqa: BLE001
                    return {"success": False, "errors": [{"data": f"verify raised: {exc}"}]}

        results = await asyncio.gather(*(check_one(f) for f in findings))
        failures: List[Tuple[int, str, str]] = []
        for i, (f, r) in enumerate(zip(findings, results)):
            if not (isinstance(r, dict) and r.get("success")):
                errs = "; ".join(e.get("data", "") for e in (r.get("errors") or [])) if isinstance(r, dict) else str(r)
                failures.append((i, str(f.get("claim") or "")[:80], errs[:400] or "did not compile"))
        return failures

    def _build_verification_code(self, finding: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """The Lean code to compile for one finding: the patched file with the named declaration
        replaced whole (`declaration_name` + `new_declaration`), or `replacement` spliced over
        [line_start, line_end], or a standalone `verification` snippet. (`suggested_fix` stays
        human-readable and is NOT used to verify.) Returns (code, "") or (None, error)."""
        dn, nd = finding.get("declaration_name"), finding.get("new_declaration")
        if finding.get("path") and dn and nd:
            return self._edited_file_code(finding.get("path"), declaration_name=dn, new_declaration=nd)
        ls, le = finding.get("line_start"), finding.get("line_end")
        replacement = finding.get("replacement")
        if finding.get("path") and isinstance(ls, int) and isinstance(le, int) and replacement:
            return self._edited_file_code(finding.get("path"), ls, le, replacement)
        snippet = str(finding.get("verification") or "")
        if snippet.strip():
            return snippet, ""
        return None, ("provide path + declaration_name + new_declaration (replace the whole "
                      "declaration — best for match/structured proofs), or path + line_start + "
                      "line_end + replacement, or a self-contained `verification` snippet")

    def _resolve_decl_lines(self, path: Optional[str], declaration_name: Optional[str]
                            ) -> Tuple[Optional[int], Optional[int]]:
        """Line span (1-based, inclusive) of the named declaration in the patched file, so a
        declaration-mode finding gets a line anchor the (line-anchored) evaluator can locate."""
        norm = _strip_ws_prefix(path)
        root = self.target_workspace.path if self.target_workspace else None
        if not (norm and root and declaration_name):
            return None, None
        fp = Path(root) / norm
        if not fp.is_file():
            return None, None
        src = fp.read_text(encoding="utf-8")
        from ape.toolkits.code.lean.lean_parser import extract_proof_blocks
        try:
            decls = extract_proof_blocks(src)
        except Exception:  # noqa: BLE001
            return None, None
        matches = [d for d in decls if declaration_name in (d.name, d.fullname)
                   or (d.fullname and d.fullname.endswith("." + declaration_name))]
        if len(matches) != 1:
            return None, None
        d = matches[0]
        ls = src[: d.header_span[0]].count("\n") + 1
        le = src[: d.body_span[1]].rstrip().count("\n") + 1
        return ls, max(ls, le)

    def _mark_verified(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Every accepted edit recompiled the file — flag those verified, record the verified edit
        as evidence, and for declaration-mode findings backfill the line anchor (from the located
        declaration) so the prediction is locatable by the evaluator. Claim-only findings (possible
        when require_verification=False) are marked verified=False: nothing was compiled for them."""
        out = []
        for f in findings:
            g = dict(f)
            if g.get("declaration_name") and g.get("path") and not isinstance(g.get("line_start"), int):
                ls, le = self._resolve_decl_lines(g.get("path"), g.get("declaration_name"))
                if ls is not None:
                    g["line_start"], g["line_end"] = ls, le
            has_edit = bool(
                (g.get("declaration_name") and g.get("new_declaration"))
                or (g.get("replacement") and isinstance(g.get("line_start"), int))
                or str(g.get("verification") or "").strip()
            )
            g["evidence"] = (f.get("new_declaration") or f.get("replacement")
                             or f.get("verification") or f.get("evidence"))
            g["verified"] = has_edit
            out.append(g)
        return out

    @staticmethod
    def _format_verification_failures(failures: List[Tuple[int, str, str]], total: int) -> str:
        lines = [f"Verification FAILED for {len(failures)}/{total} finding(s). Each finding is accepted "
                 "only if the reviewed file still compiles with your edit applied (new_declaration "
                 "replacing the named declaration, or replacement over the line span). Fix the edit "
                 "(or drop the finding) and resubmit ALL findings:"]
        for idx, claim, err in failures:
            lines.append(f"  [#{idx}] {claim!r}: {err}")
        return "\n".join(lines)
