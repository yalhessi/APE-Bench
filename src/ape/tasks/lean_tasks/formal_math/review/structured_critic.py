"""Design D2, `structured_critic`: structured disagreement on D1's ledger.

A second session with D1's packet and tools is handed D1's ledger for the PR and told to take
each `no_issue` (and `cannot_determine`, and `unstated`) cell and argue the opposite with
evidence -- a compile, a lookup, a sibling in the file, the area's census -- or concede it
explicitly; and to take each `would_change` and confirm or refute it the same way. Its
`overturn` positions carry findings, which go through D1's verification unchanged
(`StructuredReviewTask._verify_all`), and the design's output is the union of the two stages:
D1's filed findings carried as they were, each labelled with the critic's position on it, plus
the critic's filed findings, labelled as the critic's. The critic never removes a finding; the
tools do (`docs/plans/2026-10-02-review-designs.md` §4).

Why: 60% of the residual misses are `attempted_concluded_fine`
(results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30), and Adversarial Review's
measured result is that a critic adds only when disagreement is prompted explicitly; the naive
second pass converges on false consensus.

**A chained stage, not a nested one.** The plan's first choice was to nest the critic inside
D1's per-PR task through `run_subtasks`, so one run and one cap covered a PR. That shape puts a
20-40 minute critic session inside a blocked MCP tool call of the parent's Claude Code session,
which no run here has exercised on the subscription; a failure there would surface in the first
paid rep, after D1's stage had already been paid for. The plan's fallback is built instead:
`reads_stage` tells the runner this design reads a finished run's `ledgers.jsonl` (named with
`--of <structured run>`, through `StageInput`, which hashes what it consumed and refuses a run
whose manifest says it did not cover its PRs), and each per-PR task is handed its episode's
row. Two run plans, two caps, and provenance from the stage-input machinery that already
exists. Whether nesting works on the subscription stays an open question, and nothing here
prevents a nested variant later: the union, the rebuttal contract and the verification are the
same code either way.

**The union key.** The critic may file only at a cell it overturns, and a cell D1 filed at is
confirmed, refuted or left undecided, never overturned -- so within the ledger a (declaration,
concern) cell holds the ask of at most one stage, and the two stages' findings never collide at
a cell. A change to a file as a whole (its `declaration` is the file's path) has no cell; two
file-level findings at one (path, concern, line) fold into one, carrying both stages. The
ensemble-union reading (2026-10-02) found that an exact-ask key folds 6 of 381 findings while a
paraphrase of one ask at one site survives as several, which is why the fold here is by site and
concern and never by the ask's wording.
"""

import json
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import EvaluationResult, register_task

from .candidates import UNSTATED_VERDICT
from .structured import (
    CONCERNS, LEDGER_PRESSES, REFUTED, VERIFIED, Concern, StructuredFinding, StructuredReviewConfig,
    StructuredReviewData, StructuredReviewResult, StructuredReviewTask, resolve_declaration,
)

CRITIC_TASK_TYPE = "lean_pr_review_v5_structured_critic"

STAGE_1, STAGE_2 = "structured", "critic"

#: What the critic may say about a cell, by what the first stage said.
#: `overturn` and `concede` answer a cell the first stage did not file at; `confirm`, `refute`
#: and `undecided` answer a cell it did. A position is a label on the finding, never a gate.
Position = Literal["overturn", "concede", "confirm", "refute", "undecided"]
POSITIONS_FOR_FILED = ("confirm", "refute", "undecided")
POSITIONS_FOR_UNFILED = ("overturn", "concede")


class Rebuttal(BaseModel):
    """The critic's position on one declaration under one or more concerns, with its evidence.
    `reason` before `position`, for the reason the ledger row puts it there."""

    model_config = ConfigDict(extra="forbid")

    declaration: str = Field(description="A declaration from the first stage's ledger, by name")
    concerns: List[Concern] = Field(min_length=1, description=(
        "The concern(s) this position covers. An `overturn` covers exactly one and has a finding."))
    reason: str = Field(description=(
        "The evidence: what you compiled, looked up, read in the file or counted, and what it "
        "showed. For `concede`, what settled it; for `undecided`, what you could not get."))
    position: Position


CRITIC_CONTRACT = """

---

## The first stage's ledger, and your task

A first reviewer decided this PR per declaration and concern. Its ledger and the changes it \
filed follow. Your task is structured disagreement: take every cell it left without a change -- \
`no_issue`, `cannot_determine`, `unstated` -- and argue the opposite with evidence (a compile, a \
lookup, a sibling in the file, the area's census), or concede it explicitly; take every \
`would_change` and try to refute it the same way, or confirm it. Agreement is not the aim; a \
concession and a confirmation are legal only with the evidence that settled them.

The concerns:
{concerns}

{ledger}

When you have finished, call `{submit_tool_name}` once with:

- `rebuttals`: rows that together give every cell above a position. For a cell without a change: \
`overturn` (you would request a change there -- exactly one concern per such row, and a finding \
for it) or `concede` (the first stage was right; say what settled it). For a `would_change` cell: \
`confirm`, `refute` or `undecided`, each with the evidence. Silence is not a position: a cell \
without a row is asked for again.
- `findings`: one per `overturn`, in the first stage's shape -- `declaration`, `concern`, `path`, \
`line_start`, `claim`, `suggested_fix`, `severity`, and the change as `edit`, `duplicate_of` or \
`rename_to` where it is one. A change to a file as a whole names the file's path as its \
`declaration` and needs no row.

At submission, this task -- not you -- compiles every `edit` with Mathlib's linters on and looks \
up every `duplicate_of` and `rename_to`, exactly as it did for the first stage: a change the \
tools contradict is handed back to you, then recorded as refuted and not filed; a change they \
cannot check is filed as advisory and marked unverified. Your `refute` on a first-stage change is \
recorded as your position on it; it removes nothing. Nothing ranks or withholds a change the \
tools do not contradict."""


class StructuredCriticConfig(StructuredReviewConfig):
    """D1's config; the critic stage varies nothing of the packet."""


class StructuredCriticData(StructuredReviewData):
    task_type: str = CRITIC_TASK_TYPE
    #: The first stage's row for this episode from its run's `ledgers.jsonl`: `run_name`,
    #: `ledger` (one cell per declaration and concern), `findings` (what it filed, as it
    #: recorded them) and `refuted`.
    stage: Dict[str, Any] = Field(default_factory=dict)


class StructuredCriticResult(StructuredReviewResult):
    design: str = "structured_critic"
    stage_run: str = ""
    #: One row per cell: the first stage's verdict and the critic's position with its reason.
    rebuttals: List[Dict[str, Any]] = Field(default_factory=list)


def union_key(finding: Dict[str, Any], paths) -> Tuple:
    """Where a finding sits for the union: its cell, or for a file-level change its line."""

    declaration, concern = finding.get("declaration"), finding.get("concern")
    if declaration in paths:
        anchor = finding.get("anchor") or {}
        return ("file", declaration, concern, anchor.get("line_start"))
    return ("cell", declaration, concern)


class StructuredCriticTask(StructuredReviewTask):
    task_type = CRITIC_TASK_TYPE
    data_class = StructuredCriticData
    task_config_class = StructuredCriticConfig
    task_result_class = StructuredCriticResult
    reads_stage = True

    # --- the design hooks ---------------------------------------------------------------------

    @classmethod
    def design_payload(cls, *, episode, graph, dataset, stage) -> Dict[str, Any]:
        payload = super().design_payload(episode=episode, graph=graph, dataset=dataset, stage=stage)
        if stage is None:
            raise ValueError(
                f"episode {episode.episode_id} has no first-stage ledger in the stage run "
                f"{getattr(dataset, 'stage_input_run', None)!r}; the critic has nothing to argue with")
        payload["stage"] = {
            "run_name": getattr(dataset, "stage_input_run", None) or "",
            "ledger": list(stage.get("ledger") or []),
            "findings": list(stage.get("findings") or []),
            "refuted": list(stage.get("refuted") or []),
        }
        return payload

    @classmethod
    def describe_design_payload(cls, payload: Dict[str, Any]) -> str:
        stage = payload.get("stage") or {}
        cells = stage.get("ledger") or []
        filed = sum(1 for cell in cells if cell.get("verdict") == "would_change")
        return (f"stage {stage.get('run_name') or '?'}: {len(cells)} cells, {filed} would_change, "
                f"{len(stage.get('findings') or [])} finding(s) filed, "
                f"{len(stage.get('refuted') or [])} refuted; "
                + super().describe_design_payload(payload))

    # --- prompts -----------------------------------------------------------------------------

    def _stage_cells(self) -> List[Dict[str, Any]]:
        return list((self.data.stage or {}).get("ledger") or [])

    def _stage_findings(self) -> List[Dict[str, Any]]:
        return list((self.data.stage or {}).get("findings") or [])

    def render_stage(self) -> str:
        """The first stage's ledger, declaration by declaration, with its filed changes."""

        by_declaration: Dict[str, List[Dict[str, Any]]] = {}
        for cell in self._stage_cells():
            by_declaration.setdefault(cell["declaration"], []).append(cell)
        findings_by_cell: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for finding in self._stage_findings():
            findings_by_cell.setdefault((finding.get("declaration"), finding.get("concern")), []).append(finding)
        lines = ["### The first stage's ledger", ""]
        for declaration, cells in by_declaration.items():
            lines.append(f"- `{declaration}`")
            for cell in cells:
                verdict = cell.get("verdict")
                line = f"  - {cell['concern']}: **{verdict}**"
                if cell.get("reason"):
                    line += f" -- {cell['reason']}"
                lines.append(line)
                for finding in findings_by_cell.get((declaration, cell["concern"]), []):
                    anchor = finding.get("anchor") or {}
                    lines.append(
                        f"    - filed ({finding.get('verification', 'unverified')}, "
                        f"{finding.get('severity', 'advisory')}) at `{anchor.get('path')}:"
                        f"{anchor.get('line_start')}`: {finding.get('claim', '')} -> "
                        f"{finding.get('suggested_fix', '')}")
        file_level = [f for f in self._stage_findings()
                      if f.get("declaration") in set(self.data.changed_files or [])]
        if file_level:
            lines += ["", "### Filed about a file as a whole", ""]
            for finding in file_level:
                anchor = finding.get("anchor") or {}
                lines.append(f"- `{anchor.get('path')}:{anchor.get('line_start')}` ({finding.get('concern')}): "
                             f"{finding.get('claim', '')} -> {finding.get('suggested_fix', '')}")
        refuted = (self.data.stage or {}).get("refuted") or []
        if refuted:
            lines += ["", "### Refuted at the first stage's submission (not filed)", ""]
            for row in refuted:
                answers = "; ".join(str(item.get("answer")) for item in (row.get("evidence") or []))
                lines.append(f"- `{row.get('declaration')}` ({row.get('concern')}): "
                             f"{row.get('claim', '')} -- {answers}")
        return "\n".join(lines)

    def contract_text(self) -> str:
        from .structured import CONCERN_TEXT

        concerns = "\n".join(f"- `{name}`: {CONCERN_TEXT[name]}." for name in CONCERNS)
        return CRITIC_CONTRACT.format(
            concerns=concerns, ledger=self.render_stage(),
            submit_tool_name=f"{self.config.mcp_server_name}submit_findings")

    # --- the submission -----------------------------------------------------------------------

    async def register_task_tools(self, mcp) -> None:
        from .context_tools import register_context_tools

        self._register_lean_verify_edit(mcp)
        register_context_tools(self, mcp)

        @mcp.tool(description=(
            "Submit your critique of the first stage's review: a position on every cell of its "
            "ledger, with evidence, and one finding per `overturn`. Call it once, when you have "
            "finished: it records the critique and ends the session."))
        async def submit_findings(
            rebuttals: Annotated[List[Rebuttal], Field(description=(
                "Rows that together give every cell of the first stage's ledger a position: "
                "`overturn` (exactly one concern, with a finding) or `concede` for a cell "
                "without a change; `confirm`, `refute` or `undecided` for a `would_change`."))],
            findings: Annotated[List[StructuredFinding], Field(description=(
                "One per `overturn` row, naming its declaration and concern; [] when nothing is "
                "overturned."))] = [],
            confidence: Annotated[Optional[float], Field(description="0.0-1.0")] = None,
            message: Annotated[str, Field(description="Optional summary of the critique.")] = "",
        ) -> Dict[str, Any]:
            return await self._submit_critique(rebuttals, findings, confidence, message)

    def _check_rebuttals(self, rebuttals: List[Rebuttal], findings: List[StructuredFinding],
                         ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """`(cells, None)` when the positions are a legal answer, `(None, refusal)` otherwise.

        One row per cell of the first stage's ledger, in its order, each carrying the first
        stage's verdict and the critic's position. A position must fit the verdict, an
        `overturn` must have a finding and a finding must sit on an `overturn`; missing cells are
        pressed `LEDGER_PRESSES` times and then recorded `UNSTATED_VERDICT`.
        """

        stage_cells = self._stage_cells()
        names = list(dict.fromkeys(cell["declaration"] for cell in stage_cells))
        verdict_of = {(cell["declaration"], cell["concern"]): cell for cell in stage_cells}
        paths = set(self.data.changed_files or [])
        positions: Dict[Tuple[str, str], Dict[str, Any]] = {}
        problems: List[str] = []
        for row in rebuttals:
            declaration = resolve_declaration(row.declaration, names)
            if declaration is None:
                problems.append(f"{row.declaration!r} is not in the first stage's ledger")
                continue
            if not row.reason.strip():
                problems.append(f"{declaration}'s row has an empty reason")
            if row.position == "overturn" and len(row.concerns) != 1:
                problems.append(f"{declaration}'s `overturn` must cover exactly one concern, not "
                                f"{list(row.concerns)}")
            for concern in row.concerns:
                cell = verdict_of.get((declaration, concern))
                if cell is None:
                    problems.append(f"({declaration}, {concern}) is not a cell of the ledger")
                    continue
                if (declaration, concern) in positions:
                    problems.append(f"({declaration}, {concern}) has more than one position")
                    continue
                legal = (POSITIONS_FOR_FILED if cell["verdict"] == "would_change"
                         else POSITIONS_FOR_UNFILED)
                if row.position not in legal:
                    problems.append(
                        f"({declaration}, {concern}) was {cell['verdict']!r}, so its position is "
                        f"one of {list(legal)}, not {row.position!r}")
                    continue
                positions[(declaration, concern)] = {
                    **cell, "position": row.position, "position_reason": row.reason.strip()}
        filed: Dict[Tuple[str, str], int] = {}
        for index, finding in enumerate(findings):
            if finding.declaration in paths:
                continue
            declaration = resolve_declaration(finding.declaration, names)
            if declaration is None:
                problems.append(f"finding {index} names {finding.declaration!r}, which is neither "
                                "a declaration of the ledger nor a changed file's path")
                continue
            row = positions.get((declaration, finding.concern))
            if row is None or row["position"] != "overturn":
                problems.append(f"finding {index} is about ({declaration}, {finding.concern}), "
                                f"whose position is {row['position'] if row else 'missing'!r}, "
                                "not `overturn`")
            filed[(declaration, finding.concern)] = filed.get((declaration, finding.concern), 0) + 1
        for key, row in positions.items():
            if row["position"] == "overturn" and key not in filed:
                problems.append(f"({key[0]}, {key[1]}) is an `overturn` with no finding")
        if problems:
            return None, "The rebuttals are inconsistent: " + "; ".join(problems) + ". Fix and resubmit."
        missing = [key for key in verdict_of if key not in positions]
        if missing:
            self._rebuttal_presses = getattr(self, "_rebuttal_presses", 0) + 1
            if self._rebuttal_presses <= LEDGER_PRESSES:
                shown = ", ".join(f"({name}, {concern})" for name, concern in missing[:12])
                more = f" and {len(missing) - 12} more" if len(missing) > 12 else ""
                return None, (
                    "Every cell of the first stage's ledger needs a position with its evidence. "
                    f"Missing: {shown}{more}. (attempt {self._rebuttal_presses} of {LEDGER_PRESSES})")
            for key in missing:
                positions[key] = {**verdict_of[key], "position": UNSTATED_VERDICT, "position_reason": ""}
        return [positions[(cell["declaration"], cell["concern"])] for cell in stage_cells], None

    async def _submit_critique(self, rebuttals: List[Rebuttal], findings: List[StructuredFinding],
                               confidence: Optional[float], message: str) -> Dict[str, Any]:
        cells, refusal = self._check_rebuttals(rebuttals, findings)
        if refusal is not None:
            return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=refusal),
                    "message": "Invalid rebuttals"}
        budget = self.config.task_config.finding_budget
        if 0 < budget < len(findings):
            return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=(
                f"Not recorded: {len(findings)} findings exceed this review's budget of {budget}. "
                f"Call again with at most {budget}; mention the rest in `message`.")),
                "message": "Over budget"}

        verified = await self._verify_all(findings)
        refuted = [(finding, evidence) for finding, (outcome, evidence) in zip(findings, verified)
                   if outcome == REFUTED]
        if refuted:
            self._refutation_presses = getattr(self, "_refutation_presses", 0) + 1
            if self._refutation_presses <= LEDGER_PRESSES:
                lines = [f"- ({finding.declaration}, {finding.concern}) {finding.claim[:80]!r}: "
                         + "; ".join(str(item.get("answer")) for item in evidence)
                         for finding, evidence in refuted]
                return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=(
                    f"{len(refuted)} change(s) are contradicted by the tools:\n" + "\n".join(lines)
                    + "\nCorrect the edit or the name, resubmit the finding without it (it is then "
                    "filed unverified), or drop it; keep every other row and finding. After "
                    f"attempt {LEDGER_PRESSES} the contradicted changes are recorded as refuted "
                    f"and not filed. (attempt {self._refutation_presses} of {LEDGER_PRESSES})")),
                    "message": "Refuted changes"}

        paths = set(self.data.changed_files or [])
        names = list(dict.fromkeys(cell["declaration"] for cell in cells))
        critic_raw, refuted_rows = [], []
        outcome_by_cell: Dict[Tuple[str, str], str] = {}
        for finding, (outcome, evidence) in zip(findings, verified):
            key = (resolve_declaration(finding.declaration, names) or finding.declaration,
                   finding.concern)
            rank = {VERIFIED: 2, "unverified": 1, REFUTED: 0}
            if rank[outcome] >= rank.get(outcome_by_cell.get(key, REFUTED), 0):
                outcome_by_cell[key] = outcome
            if outcome == REFUTED:
                refuted_rows.append({**finding.model_dump(mode="json"), "evidence": evidence})
            else:
                critic_raw.append(self._filed_finding(finding, outcome, evidence))
        position_of = {(cell["declaration"], cell["concern"]): cell["position"] for cell in cells}
        for cell in cells:
            if cell["position"] == "overturn":
                cell["outcome"] = outcome_by_cell.get((cell["declaration"], cell["concern"]))

        # The union: the first stage's findings as they were, each with the critic's position
        # on its cell; then the critic's, folded onto a first-stage finding only at a file-level
        # site (a cell holds one stage's ask by construction).
        union: Dict[Tuple, Dict[str, Any]] = {}
        for finding in self._stage_findings():
            row = dict(finding)
            position = position_of.get((row.get("declaration"), row.get("concern")))
            row["stage"] = STAGE_1
            row["stages"] = [STAGE_1]
            row["critic"] = position if row.get("declaration") not in paths else None
            row["agreed"] = position == "confirm" if position else None
            union[union_key(row, paths)] = row
        try:
            critic_rows = self._normalize_findings(critic_raw)
        except Exception:  # noqa: BLE001
            import traceback

            self.logger.error("submit_findings (critic) failed: %s", traceback.format_exc())
            return {"evaluation_result": EvaluationResult(success=False, score=0.0,
                                                          message=traceback.format_exc()),
                    "message": "Submit failed"}
        folded = 0
        for row in critic_rows:
            key = union_key(row, paths)
            if key in union:
                union[key]["stages"] = sorted(set(union[key]["stages"]) | {STAGE_2})
                union[key]["agreed"] = True
                folded += 1
                continue
            row["stage"] = STAGE_2
            row["stages"] = [STAGE_2]
            row["critic"] = "overturn"
            row["agreed"] = False
            union[key] = row
        findings_out = list(union.values())
        rebuttal_rows = [{"declaration": cell["declaration"], "concern": cell["concern"],
                          "verdict": cell["verdict"], "position": cell["position"],
                          "reason": cell["position_reason"]} for cell in cells]
        try:
            result = self.create_result(
                success=True, score=1.0, pr_number=self.data.pr_number, merge_ready_as_is=None,
                confidence=confidence, findings=findings_out, review_message=message or "",
                ledger=cells, refuted=refuted_rows, rebuttals=rebuttal_rows,
                stage_run=str((self.data.stage or {}).get("run_name") or ""))
        except Exception:  # noqa: BLE001
            import traceback

            self.logger.error("submit_findings (critic) failed: %s", traceback.format_exc())
            return {"evaluation_result": EvaluationResult(success=False, score=0.0,
                                                          message=traceback.format_exc()),
                    "message": "Submit failed"}
        counts = {}
        for cell in cells:
            counts[cell["position"]] = counts.get(cell["position"], 0) + 1
        self.logger.info("submit_findings (critic): %d cells %s; %d first-stage findings carried, "
                         "%d critic findings filed (%d folded), %d refuted",
                         len(cells), json.dumps(counts, sort_keys=True), len(self._stage_findings()),
                         len(critic_rows) - folded, folded, len(refuted_rows))
        if self.termination_callback:
            try:
                await self.termination_callback(result)
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to trigger termination: %s", exc)
        return {
            "evaluation_result": EvaluationResult(success=True, score=1.0, message=(
                f"Critique recorded: {len(cells)} cells, {len(findings_out)} findings in the union "
                f"({len(critic_rows) - folded} the critic's), {len(refuted_rows)} refuted.")),
            "message": "Critique submitted",
        }


register_task(CRITIC_TASK_TYPE, StructuredCriticTask)
