"""
Shared base for PR-review tasks.

All review tasks — the holistic acceptability pass and the focused discovery
checkers (duplication, generality, …) — share the same workspace materialization
(merge-base snapshot + δ₀ applied, read-only), the same `submit_findings`
contract, and the same externally-scored result. They differ only in their
prompt (and tool defaults). This base owns the shared machinery; subclasses set
`task_type` and implement `_get_prompts`.

Findings carry an optional `evidence` field — the verified artifact behind a
finding (the existing declaration a dup checker found; the stronger statement a
generality checker proved). This is the proof-carrying-review hook and is scored
externally (D1/D2/D3 in src/datasets/pr_review_v2); the task never scores.
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

from .prompt import DEFAULT_PROMPT_VERSION

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
    "code_references",
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


class BasePRReviewTask(BaseLeanTask):
    """Shared, read-only, externally-scored review task. Not registered; subclass
    it, set `task_type`, and implement `_get_prompts`."""

    #: A review task has no scratch file. The thing worth compiling is the reviewed file in
    #: `target/`, which is read-only for the agent but not blocked from the compiler — review
    #: sets `read_only_path_patterns` and leaves `blocked_path_patterns` empty. Opting in here
    #: lets `lean_verify` read it, without changing proof_engineering, whose task genuinely
    #: does require a self-contained snippet.
    lean_verify_allows_target = True

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
        if has("file_read"):
            parts.append("read files")
        if has("content_search"):
            parts.append("grep the repo (content_search)")
        if has("lean_retrieve"):
            parts.append("semantic library search (lean_retrieve)")
        if has("lean_verify"):
            parts.append("compile/verify Lean code (lean_verify)")
        if has("get_lean_goal"):
            parts.append("inspect goals")
        if any(has(t) for t in ("code_hover", "code_goto", "code_references")):
            parts.append("navigate declarations (hover/goto/references)")
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
        # Force a submission: agents that conclude "nothing to flag" sometimes end with a text-only
        # reply and never call submit_findings, which the harness records as an empty failure rather
        # than a clean review. Make the empty-review path explicit and mandatory.
        mandate = (
            f"\n\nYou MUST finish by calling `{submit_tool_name}` exactly once — even if you find "
            "nothing. If there is nothing to change, call it with an empty `findings` list and "
            "`merge_ready_as_is: true`. A text-only reply does not count and fails the task."
        )
        return base + mandate + self._precedent_block()

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
            from ape.toolkits.code.lean.lean_parser import extract_proof_blocks
            try:
                decls = extract_proof_blocks(src)
            except Exception as exc:  # noqa: BLE001
                return None, f"could not parse {norm} to locate `{declaration_name}`: {exc}"
            matches = [d for d in decls if declaration_name in (d.name, d.fullname)
                       or (d.fullname and d.fullname.endswith("." + declaration_name))]
            if not matches:
                return None, f"declaration `{declaration_name}` not found in {norm}"
            if len(matches) > 1:
                opts = ", ".join(sorted({m.fullname or m.name or "?" for m in matches}))
                return None, f"`{declaration_name}` is ambiguous in {norm}; use the full name (one of: {opts})"
            d = matches[0]
            # Replace from the keyword by default, which preserves any attributes and
            # modifiers already in the file. When the replacement supplies its own, replace
            # from the start of that decoration instead — otherwise the two concatenate into
            # `@[simp] @[simp] theorem …`, which fails to parse and reads to the agent as a
            # mysterious syntax error in code it did not write.
            start = d.header_span[0]
            if _supplies_own_prefix(new_declaration):
                start = _declaration_prefix_start(src, d.header_span[0])
            edited = src[:start] + str(new_declaration).rstrip() + "\n\n" + src[d.body_span[1]:]
            return edited, ""

        lines = src.split("\n")
        if line_start is None or line_end is None or replacement is None:
            return src, ""  # compile the file unedited
        if not (isinstance(line_start, int) and isinstance(line_end, int)
                and 1 <= line_start <= line_end <= len(lines)):
            return None, f"line span {line_start}-{line_end} out of range for {norm} ({len(lines)} lines)"
        edited = lines[: line_start - 1] + str(replacement).split("\n") + lines[line_end:]
        return "\n".join(edited), ""

    @staticmethod
    def _error_key(item: Dict[str, Any]) -> str:
        """Identify an error by its text, not its position.

        Line numbers move when the file is edited, so position cannot be part of the key —
        the same pre-existing error would look new merely because the edit shifted it.
        """

        return str((item or {}).get("data") or "").strip()

    async def _baseline_errors(self, path: Optional[str]) -> set:
        """Errors the reviewed file already has, compiled once per attempt and cached.

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
        code, err = self._edited_file_code(path)
        if code is None:
            cache[key] = set()
            return cache[key]
        from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

        lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
        try:
            baseline = await lean_tool.execute(code=code, max_messages=50)
        except Exception:  # noqa: BLE001
            cache[key] = set()
            return cache[key]
        cache[key] = {
            self._error_key(item) for item in (baseline.get("errors") or [])
        }
        return cache[key]

    async def _attribute_errors(self, path: Optional[str], result: Dict[str, Any]) -> Dict[str, Any]:
        """Split a compile result into errors this edit introduced and errors already present."""

        errors = list(result.get("errors") or [])
        if not errors:
            return result
        baseline = await self._baseline_errors(path)
        introduced = [item for item in errors if self._error_key(item) not in baseline]
        pre_existing = [item for item in errors if self._error_key(item) in baseline]
        enriched = dict(result)
        enriched["errors_introduced_by_your_edit"] = introduced
        enriched["errors_already_in_the_file"] = pre_existing
        if pre_existing and not introduced:
            enriched["note"] = (
                "Your edit introduced no new errors — every error listed was already present "
                "in the reviewed file before it. The file does not compile as it stands."
            )
        elif pre_existing:
            enriched["note"] = (
                f"{len(introduced)} error(s) came from your edit; {len(pre_existing)} were "
                "already in the file. Fix only the former."
            )
        return enriched

    def _register_lean_verify_edit(self, mcp) -> None:
        """Register the lean_verify_edit exploration tool — available to EVERY review task (the
        holistic agent and the verified checkers), so any reviewer can test that a proposed edit
        compiles in context before reporting it."""
        from typing import Annotated

        @mcp.tool(
            description=(
                "Test an in-file edit, recompiling the WHOLE file and returning the compile result. "
                "Use it to confirm a change you want to suggest actually compiles in context. Two "
                "ways to specify the edit: PREFERRED — `declaration_name` + `new_declaration` "
                "replaces that whole declaration (robust for match/structured proofs; no line "
                "counting). You may include the declaration's `@[...]` attributes and "
                "modifiers or omit them; either way they are not duplicated. Or "
                "`line_start`/`line_end` + `replacement` to splice a line span. Your edit may "
                "reference the PR's own new declarations. Omit all edit args to check whether "
                "the file compiles as-is. Errors come back split into "
                "`errors_introduced_by_your_edit` and `errors_already_in_the_file` — fix only "
                "the former; line numbers refer to the whole spliced file, so use `code_line` "
                "to locate them."
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
                description="Line mode: exact Lean text to substitute for that span")] = None,
            max_messages: Annotated[int, Field(description="Max compile messages to return")] = 20,
        ) -> Dict[str, Any]:
            code, err = self._edited_file_code(
                path, line_start, line_end, replacement,
                declaration_name=declaration_name, new_declaration=new_declaration)
            if code is None:
                return {"success": False, "error": err}
            from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider
            lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
            try:
                result = await lean_tool.execute(code=code, max_messages=max_messages)
            except Exception as exc:  # noqa: BLE001
                return {"success": False, "error": f"verify raised: {exc}"}
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
            # Say which of the two things just happened. The as-is mode is deliberate and
            # stays, but its result was indistinguishable from a verified edit: both come
            # back `{"success": true, ... "Lean verification completed successfully"}`, and
            # the reviewed file compiles by construction, so an as-is call always succeeds.
            # On smoke4 that was 13 of 100 calls — a `family_design` invocation on PR 33117
            # made one, read the success, and submitted nothing. Neither the agent nor
            # anyone reading the transcript afterwards could tell it had verified nothing.
            if isinstance(result, dict):
                result["mode"] = "verified_edit" if edited_only else "as_is_compile_check"
                if not edited_only:
                    result["note"] = (
                        "No edit was applied — this is the unmodified reviewed file's "
                        "compile status, which is green by construction and is NOT evidence "
                        "for any change you are considering. To check a change, pass "
                        "`declaration_name` + `new_declaration`."
                    )
            return result

    async def register_task_tools(self, mcp) -> None:
        from typing import Annotated

        self._register_lean_verify_edit(mcp)

        @mcp.tool(
            description=(
                "Submit your final review findings for this PR. Call this exactly once when done. "
                "This records the review and ends the conversation. A text-only response is INVALID."
            )
        )
        async def submit_findings(
            findings: Annotated[List[Dict[str, Any]], Field(
                description=(
                    "List of findings (<= budget). Each: {path?, line_start?, line_end?, "
                    "severity: 'blocking'|'advisory', claim, suggested_fix?, evidence?}. "
                    "`evidence` is the verified artifact backing the finding (the existing "
                    "declaration's name for a duplicate; the stronger statement for a generality "
                    "issue). Empty list = nothing to change."
                )
            )] = [],
            merge_ready_as_is: Annotated[Optional[bool], Field(
                description="True if a maintainer would merge without requesting changes."
            )] = None,
            confidence: Annotated[Optional[float], Field(description="0.0-1.0")] = None,
            message: Annotated[str, Field(description="Optional summary of the review.", default="")] = "",
        ) -> Dict[str, Any]:
            self.logger.info("submit_findings: %d findings, merge_ready=%s", len(findings or []), merge_ready_as_is)
            try:
                normalized = self._normalize_findings(findings or [])
                # A verdict-less submission is still a valid review: infer it from the findings
                # (empty => nothing to change => merge-ready) so it is not recorded as an empty failure.
                if merge_ready_as_is is None:
                    merge_ready_as_is = len(normalized) == 0
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

    def _normalize_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Coerce raw tool input into the PredictionRecord finding shape; drop empties,
        clamp severity, enforce the budget, keep optional evidence."""
        budget = self.config.task_config.finding_budget
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
