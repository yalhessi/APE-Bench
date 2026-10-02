"""Design D1, `structured`: decide per declaration and concern, verify before filing.

The solo baseline decides once per PR. This design keeps its packet -- the PR, the PR model,
the diff, the hygiene layer's tools, the brief -- and changes the unit of decision: for every
declaration the PR leaves in place and every concern a maintainer raises, the reviewer records a
verdict with its reason, and files a finding for every `would_change`. Silence is not a verdict.
The contract is the arms' `target_verdicts` (`candidates.py`), built for work units, refused for
the whole-PR reviewer at `runner.py` and never run on a model that reaches anything, generalized
to the whole PR and to a concern axis (`docs/plans/2026-10-02-review-designs.md` §3).

Why the unit change: two reps of one configuration share 65% of their change targets and ask
different things at them; the flipping obligations are second and third asks at an object the
reviewer already attended, and a reviewer that files one ask per attended object draws which.
Deciding each (declaration, concern) on its own makes each ask its own decision.

**One entry per declaration, six fixed cells, each with its own reason.** The first contract let a
row decide several concerns at once; on the first gpt-5.2 test (2026-10-02, two PRs) every
declaration got one row over all six concerns with one shared reason, which is one decision per
object again -- the thing this design exists to break. So an entry now has a field per concern
(`proof`, `statement`, ...), each a verdict and its reason, and the schema itself refuses a
collapsed entry. Entries go through `record_ledger`, which the reviewer may call as it goes, one or
several declarations at a time, rather than inside the one submission: a whole ledger in one call
is 516 cells on 33294, about 130,000 characters, past gpt-5.2's 32,000-token output limit.
`submit_findings` may still carry entries, so a small PR can be reviewed in one call.

**Verification happens at submission, by the task, never at the reviewer's discretion.** Every
`edit` is compiled in the reviewed file with Mathlib's linters on (`WHOLE_FILE_OPTIONS`); every
`duplicate_of` and `rename_to` is looked up (`lookup_declaration`, the `declaration_search`
answer; `naming_census`, the `naming_norm` answer). A change the tools contradict is recorded as
refuted and not filed; a change the tools cannot check is filed as advisory and marked
unverified. An edit the reviewer already compiled with `lean_verify_edit` in the same attempt is
not compiled again: that result is this one (`edit_key`; 79 of 92 submitted edits in D1's first
Claude dev rep had been). This is refutation by fact only -- an edit that does not compile, a duplicate that
does not exist, a rename onto a name the library already has. Nothing ranks or withholds a
change the tools do not contradict (the selection ruling of 2026-09-22 stands), and nothing here
can touch a docstring-wording ask, since no tool contradicts a wording: the docs family's control
emission is read separately, and no value filter is added for it (ensemble-union reading,
2026-10-02).

**What is inherited and what is not.** The prompts are the solo's (`solo_user_template`, the
brief named by the config) rendered without the prose `notes` line, plus this design's contract
appended; the `review_notes` knob the hygiene config carries is honoured as the ledger, which is
the same account in structured form. The submission tool is this module's own: the base's
`submit_findings` is not registered. The result is the solo's plus the ledger and the refuted
list, which the runner writes to `ledgers.jsonl` for the critic stage (`structured_critic.py`)
and for the reading. Downstream of the result nothing changes: findings carry the solo's keys,
are anchored by path and line, and are stamped with the unlabelled pair the solo's v2 contract
stamps, so the review channel reads this design exactly as it reads the baseline. The design's
concern travels as the candidate's `concern_label` (`arm_responses.jsonl`,
`candidates_discovered.jsonl`), never as the gating `concern_family`. It does NOT reach
`findings.jsonl`: `merge.finding_from_candidate` builds `concern_tags` from the candidate's tags
and family only, and adding the label there would move every arm finding's sealed id. A reading
by concern takes it from `ledgers.jsonl`, whose findings carry `declaration` and `concern`
(corrected 2026-10-02; the D1 commit, 64ad99a0, said it reached `concern_tags`).
"""

import asyncio
import json
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, get_args

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import EvaluationResult, register_task

from .base import WHOLE_FILE_OPTIONS, edit_key
from .candidates import UNSTATED_VERDICT
from .solo import (
    SoloReviewConfig, SoloReviewData, SoloReviewResult, SoloReviewTask, solo_context_block,
    solo_system_prompt, solo_user_template,
)

#: `v5` spelling, like every task type here: a recorded identity, not a class name.
STRUCTURED_TASK_TYPE = "lean_pr_review_v5_structured"

#: The concern axis of the ledger: what maintainers raise, in the families the solo's brief
#: and the Claude reviewers' `notes.md` took a declaration through (plan §3.2).
Concern = Literal["proof", "statement", "library", "name", "docstring", "placement"]
CONCERNS: Tuple[str, ...] = get_args(Concern)

CONCERN_TEXT = {
    "proof": "the proof -- shorter, the idiomatic tactic, an existing lemma in place of a "
             "hand-written argument",
    "statement": "the statement and its generality -- hypotheses that are not needed, a special "
                 "case of something that holds generally, the form the library states such "
                 "things in",
    "library": "whether the library already has it, or has what it should reuse",
    "name": "the name, against the naming convention and the file's siblings",
    "docstring": "the docstring -- missing, wrong, or out of step with its siblings",
    "placement": "attributes and placement -- `simp`, `to_additive` and the like, the file and "
                 "section it sits in",
}

#: The concerns of a changed file as a whole, one ledger entry per changed file. Added after D1's
#: first Claude dev rep lost the one ask all three hygiene reps hit -- wrapping a line on 33305,
#: a PR that leaves no declaration in place and so had no cell at all
#: (`docs/todo/review-designs-file-cells.md`).
FileConcern = Literal["module_doc", "style", "organization"]
FILE_CONCERNS: Tuple[str, ...] = get_args(FileConcern)

FILE_CONCERN_TEXT = {
    "module_doc": "the module docstring and the file's comments -- missing, stale, or out of step "
                  "with what the file now declares",
    "style": "formatting and the linters -- line length, spacing, deprecated syntax, `set_option`s",
    "organization": "imports, sections and namespaces, and whether each declaration sits in the "
                    "right file and section",
}

#: Either kind of concern, as a finding names it.
AnyConcern = Literal["proof", "statement", "library", "name", "docstring", "placement",
                     "module_doc", "style", "organization"]
assert set(get_args(AnyConcern)) == set(CONCERNS) | set(FILE_CONCERNS)

LedgerVerdict = Literal["no_issue", "would_change", "cannot_determine"]

#: How many times a submission missing ledger cells, or carrying refuted changes, is handed back
#: before it is accepted as it stands. The arms' bound, for the arms' reason: an unbounded
#: refusal turns a review that answered most of its cells into a failed session, which is a
#: coverage gap, and a coverage gap is worse than a cell recorded `unstated`.
LEDGER_PRESSES = 3

#: What the task concluded about a filed change at submission.
VERIFIED, UNVERIFIED, REFUTED = "verified", "unverified", "refuted"


class Cell(BaseModel):
    """One (declaration, concern) cell. `reason` before `verdict`, the ordering
    `TargetVerdictSubmission` records as a choice: a frontier model writes tool arguments in
    order, and an identifier emitted ahead of its analysis cannot be retracted."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(description=(
        "What you checked under this concern and what you found. For `cannot_determine`, the "
        "evidence you needed and could not get."))
    verdict: LedgerVerdict


class DeclarationVerdicts(BaseModel):
    """One declaration's ledger entry: a cell per concern, in `CONCERNS` order (a test pins it)."""

    model_config = ConfigDict(extra="forbid")

    declaration: str = Field(description="A declaration from the list in the prompt, by name")
    proof: Cell
    statement: Cell
    library: Cell
    name: Cell
    docstring: Cell
    placement: Cell


class FileVerdicts(BaseModel):
    """One changed file's ledger entry: a cell per file concern, in `FILE_CONCERNS` order."""

    model_config = ConfigDict(extra="forbid")

    file: str = Field(description="A changed file from the list in the prompt, by path")
    module_doc: Cell
    style: Cell
    organization: Cell


class StructuredEdit(BaseModel):
    """An edit to the reviewed file, in `lean_verify_edit`'s two spellings."""

    model_config = ConfigDict(extra="forbid")

    declaration_name: Optional[str] = Field(default=None, description=(
        "Declaration mode: the declaration to replace whole"))
    new_declaration: Optional[str] = Field(default=None, description=(
        "Declaration mode: the full replacement, from its theorem/lemma/def keyword"))
    line_start: Optional[int] = Field(default=None, description="Line mode: first line (1-based)")
    line_end: Optional[int] = Field(default=None, description="Line mode: last line (inclusive)")
    replacement: Optional[str] = Field(default=None, description=(
        "Line mode: the text for that span; omit it to delete the span"))


class StructuredFinding(BaseModel):
    """One change the reviewer would request, at one declaration under one concern."""

    model_config = ConfigDict(extra="forbid")

    declaration: str = Field(description=(
        "The declaration this change is about, from the list in the prompt; or a changed file's "
        "path for a change to the file as a whole, under a file concern"))
    concern: AnyConcern
    path: str = Field(description="The reviewed file, e.g. Mathlib/.../X.lean")
    line_start: int = Field(description="The line of the declaration the claim is about")
    claim: str = Field(description="Name the declaration and say what is wrong with it")
    suggested_fix: str = Field(description="What to do instead")
    severity: Literal["blocking", "advisory"] = Field(default="advisory", description=(
        "`blocking` if the change is needed for correctness or policy; `advisory` for every "
        "other change you would request. Advisory findings count in full."))
    line_end: Optional[int] = None
    edit: Optional[StructuredEdit] = Field(default=None, description=(
        "The change as an edit to the reviewed file, when it is one; compiled at submission"))
    duplicate_of: Optional[str] = Field(default=None, description=(
        "When the library already has this: the existing declaration's name; looked up at "
        "submission"))
    rename_to: Optional[str] = Field(default=None, description=(
        "When the change is a rename: the new name; looked up at submission"))


#: Appended to the solo's user prompt. `{declarations}` and `{submit_tool_name}` are filled by
#: the task; there are no other braces, so the solo template's `format` never sees this text.
STRUCTURED_CONTRACT = """

---

## The ledger

This review decides per declaration and per concern, and files the changes it decides on.

Declarations in this PR, as it leaves them -- every one needs a verdict under every concern:
{declarations}

The concerns of a declaration:
{concerns}

Files this PR changes -- every one needs a verdict under every file concern:
{files}

The concerns of a file as a whole:
{file_concerns}

Record the ledger with `{record_tool_name}`, as you go: one entry per declaration (`entries`) and \
one per changed file (`files`), one or several per call, and a later entry for a declaration or a \
file replaces the earlier one. An entry has a field per concern, each with its own `reason` and \
`verdict`: `no_issue` (you checked and have nothing to ask -- say what you checked under that \
concern), `would_change` (a change you would request; it needs a finding), or `cannot_determine` \
(what you needed and could not get). Each concern is its own decision: say what you checked for \
that concern, not for the declaration or the file.

When you have reviewed the PR, call `{submit_tool_name}` once with:

- `findings`: one per `would_change`, naming its `declaration` and `concern`, with `path` and \
`line_start` (the declaration's line in the reviewed file), `claim`, `suggested_fix` and \
`severity`. Where the change is an edit to the reviewed file, give it as `edit` \
(`declaration_name` + `new_declaration`, or `line_start`/`line_end` + `replacement`); where it \
says the library already has something, give that name as `duplicate_of`; where it is a rename, \
give the new name as `rename_to`. A change to a file as a whole -- its module doc, its \
formatting, its imports or sections -- names the file's path as its `declaration` and one of the \
file concerns, and sits on that file's `would_change` cell.
- `ledger` and `files`: any entries not yet recorded (optional; the whole ledger may go here on a \
small PR).

A declaration or a file without an entry is asked for again: silence is not a verdict.

At submission, this task -- not you -- compiles every `edit` in the reviewed file with Mathlib's \
linters on and looks up every `duplicate_of` and `rename_to`. A change the tools contradict (an \
edit that does not compile, a duplicate that does not exist, a rename onto a name the library \
already has) is handed back to you with the tool's answer, to correct, to resubmit without the \
edit or the name, or to drop; after that it is recorded as refuted and not filed. A change the \
tools cannot check is filed as advisory and marked unverified. Nothing ranks or withholds a \
change the tools do not contradict."""


class StructuredReviewConfig(SoloReviewConfig):
    """The solo's config. `review_notes: true`, which the hygiene baseline carries, is honoured
    as the ledger: the account per declaration and concern, structured rather than prose."""


class StructuredReviewData(SoloReviewData):
    task_type: str = STRUCTURED_TASK_TYPE
    #: The declarations the ledger covers: every `declaration` target of the change graph that
    #: the PR leaves in place (`reviewed_code` non-empty), as the PR model lists them, in its
    #: order. Built by `design_payload` from the release, never by the reviewer, so the
    #: completeness check has a fixed denominator.
    declarations: List[Dict[str, Any]] = Field(default_factory=list)


class StructuredReviewResult(SoloReviewResult):
    design: str = "structured"
    #: One row per (declaration, concern): `verdict`, `reason`, and for a `would_change` the
    #: `outcome` the submission gave it (`verified`, `unverified`, `refuted`).
    ledger: List[Dict[str, Any]] = Field(default_factory=list)
    #: Changes the tools contradicted, with the tool's answer. Not findings.
    refuted: List[Dict[str, Any]] = Field(default_factory=list)


def declarations_of(graph) -> List[Dict[str, Any]]:
    """The PR model's declarations, from the change graph, in the PR model's order."""

    rows = []
    for target in sorted(graph.targets, key=lambda item: (item.path, item.change_id)):
        if target.kind != "declaration" or not target.declaration_name:
            continue
        if not (target.reviewed_code or "").strip():
            continue  # removed by the PR: nothing the PR leaves in place to decide on
        rows.append({
            "name": target.declaration_name, "kind": target.declaration_kind or target.kind,
            "path": target.path, "change_id": target.change_id,
        })
    return rows


def resolve_declaration(given: str, names: List[str]) -> Optional[str]:
    """The listed declaration `given` names: itself, or the unique one it is a dotted suffix of."""

    given = (given or "").strip()
    if given in names:
        return given
    matches = [name for name in names if name.endswith("." + given)]
    return matches[0] if len(matches) == 1 else None


class StructuredReviewTask(SoloReviewTask):
    task_type = STRUCTURED_TASK_TYPE
    data_class = StructuredReviewData
    task_config_class = StructuredReviewConfig
    task_result_class = StructuredReviewResult
    #: 1: multi-concern rows (the first gpt-5.2 test only); 2: one entry per declaration with six
    #: fixed cells, through `record_ledger` (c3f24639; every dev rep up to 2026-10-02 noon);
    #: 3: plus one entry per changed file with three file-concern cells.
    design_version = "structured/3"

    # --- the design hooks ---------------------------------------------------------------------

    @classmethod
    def design_payload(cls, *, episode, graph, dataset, stage) -> Dict[str, Any]:
        if graph is None:
            raise ValueError(
                f"episode {episode.episode_id} has no change graph in the release, so its "
                "declarations cannot be enumerated for the ledger")
        return {"declarations": declarations_of(graph)}

    @classmethod
    def describe_design_payload(cls, payload: Dict[str, Any]) -> str:
        count = len(payload.get("declarations") or [])
        files = len(payload.get("changed_files") or [])
        cells = count * len(CONCERNS) + files * len(FILE_CONCERNS)
        return (f"{count} declaration(s) x {len(CONCERNS)} concerns + {files} file(s) x "
                f"{len(FILE_CONCERNS)} = {cells} ledger cells")

    # --- prompts -----------------------------------------------------------------------------

    def _review_notes(self) -> bool:
        # The account is the ledger, so the mandate and the template carry no `notes`.
        return False

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        config = self.config.task_config
        return (solo_system_prompt(config),
                solo_user_template(config.filing_bar, False, config.user_prompt, config.notes_form,
                                   solo_context_block(config, self.data.pr_number)
                                   if config.user_prompt == "v2" else ""))

    def _declaration_names(self) -> List[str]:
        return [row["name"] for row in self.data.declarations]

    def _subjects(self) -> List[Tuple[str, str, Tuple[str, ...]]]:
        """`(name, kind, concerns)` for every subject of the ledger, in its order: the PR's
        declarations, then its changed files."""
        return ([(name, "declaration", CONCERNS) for name in self._declaration_names()]
                + [(path, "file", FILE_CONCERNS) for path in (self.data.changed_files or [])])

    def _resolve_subject(self, given: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
        """The subject `given` names: a changed file by its path (any `target/` prefix dropped),
        else a declaration by its full name or a unique dotted suffix."""
        from .base import _strip_ws_prefix

        subjects = self._subjects()
        path = _strip_ws_prefix(given)
        for subject in subjects:
            if subject[1] == "file" and subject[0] == path:
                return subject
        declarations = [subject[0] for subject in subjects if subject[1] == "declaration"]
        name = resolve_declaration(given, declarations)
        return next((subject for subject in subjects if subject[1] == "declaration"
                     and subject[0] == name), None) if name else None

    def contract_text(self) -> str:
        declarations = "\n".join(
            f"- `{row['name']}` ({row['kind']}, `{row['path']}`)" for row in self.data.declarations
        ) or "- (none: this PR leaves no declaration in place)"
        concerns = "\n".join(f"- `{name}`: {CONCERN_TEXT[name]}." for name in CONCERNS)
        files = "\n".join(f"- `{path}`" for path in self.data.changed_files or []) or "- (none)"
        file_concerns = "\n".join(f"- `{name}`: {FILE_CONCERN_TEXT[name]}." for name in FILE_CONCERNS)
        return STRUCTURED_CONTRACT.format(
            declarations=declarations, concerns=concerns, files=files, file_concerns=file_concerns,
            record_tool_name=f"{self.config.mcp_server_name}{self.RECORD_TOOL}",
            submit_tool_name=f"{self.config.mcp_server_name}submit_findings")

    async def create_user_prompt(self) -> str:
        return await super().create_user_prompt() + self.contract_text()

    # --- recording the ledger -----------------------------------------------------------------

    #: What a cell holds and what the tool that records it is called. The critic stage records
    #: positions through the same machinery (`structured_critic.py`).
    CELL_VALUE = "verdict"
    RECORD_TOOL = "record_ledger"

    def _recorded(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """subject (a declaration's name or a file's path) -> concern -> {CELL_VALUE, reason}, for
        every entry recorded so far."""
        if not hasattr(self, "_recorded_cells"):
            self._recorded_cells = {}
        return self._recorded_cells

    def _cell_problem(self, declaration: str, concern: str, value: str) -> Optional[str]:
        """A reason this cell's value is not legal here, or None. Every verdict is legal in D1."""
        return None

    def _record_entries(self, entries) -> Tuple[List[str], List[str]]:
        """`(recorded declarations, problems)`. All or nothing: a call with any problem records
        none of its entries, so a half-applied call cannot leave the ledger in a state the
        reviewer did not write."""

        staged: Dict[str, Dict[str, Dict[str, str]]] = {}
        problems: List[str] = []
        for entry in entries:
            given = getattr(entry, "file", None) or getattr(entry, "declaration", None)
            subject = self._resolve_subject(given)
            expected = "file" if hasattr(entry, "file") else "declaration"
            if subject is None or subject[1] != expected:
                problems.append(f"{given!r} is not one of this PR's listed "
                                f"{'changed files' if expected == 'file' else 'declarations'}")
                continue
            declaration, _kind, concerns = subject
            if declaration in staged:
                problems.append(f"{declaration} has two entries in one call")
                continue
            cells = {}
            for concern in concerns:
                cell = getattr(entry, concern)
                value = getattr(cell, self.CELL_VALUE)
                if not cell.reason.strip():
                    problems.append(f"({declaration}, {concern}) has an empty reason")
                problem = self._cell_problem(declaration, concern, value)
                if problem:
                    problems.append(problem)
                cells[concern] = {self.CELL_VALUE: value, "reason": cell.reason.strip()}
            staged[declaration] = cells
        if problems:
            return [], problems
        self._recorded().update(staged)
        self._persist_progress()
        return list(staged), []

    def _persist_progress(self) -> None:
        """The ledger so far, beside the attempt's logs: forensic, and the only place a session
        that ends without submitting leaves what it had decided."""
        attempt = getattr(self, "attempt_path", None)
        if attempt is None:
            return
        try:
            (attempt / "ledger_progress.json").write_text(
                json.dumps(self._recorded(), indent=1, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def _record_reply(self, entries) -> Dict[str, Any]:
        recorded, problems = self._record_entries(entries)
        if problems:
            return {"success": False, "outcome": "invalid_request", "error": (
                "Nothing recorded: " + "; ".join(problems) + ". Fix and call again.")}
        names = [subject[0] for subject in self._subjects()]
        remaining = [name for name in names if name not in self._recorded()]
        return {"success": True, "recorded": recorded,
                "progress": f"{len(names) - len(remaining)} of {len(names)} declarations and files recorded",
                "remaining": remaining[:20] + ([f"... and {len(remaining) - 20} more"]
                                               if len(remaining) > 20 else [])}

    # --- the submission -----------------------------------------------------------------------

    async def register_task_tools(self, mcp) -> None:
        from .context_tools import register_context_tools

        # The base grant's `lean_verify_edit`, then the context tools, then this design's own
        # tools -- never the base's `submit_findings`, which is why the base's
        # `register_task_tools` is not called.
        self._register_lean_verify_edit(mcp)
        register_context_tools(self, mcp)

        @mcp.tool(description=(
            "Record ledger entries: for each declaration, and for each changed file, a verdict and "
            "its reason under every one of its concerns. Call it as you go, with one or several; a "
            "later entry replaces the earlier one. Returns what is still to record."))
        async def record_ledger(
            entries: Annotated[List[DeclarationVerdicts], Field(description=(
                "One entry per declaration, each with all six concern cells."))] = [],
            files: Annotated[List[FileVerdicts], Field(description=(
                "One entry per changed file, each with its three file-concern cells."))] = [],
        ) -> Dict[str, Any]:
            return self._record_reply(list(entries) + list(files))

        @mcp.tool(description=(
            "Submit your review of this PR: one finding per `would_change` cell of the ledger, "
            "and any ledger entries not yet recorded. Call it once, when you have finished: it "
            "records the review and ends the session."))
        async def submit_findings(
            findings: Annotated[List[StructuredFinding], Field(description=(
                "One per `would_change` cell, naming its declaration and concern; [] when no cell "
                "is a `would_change`."))] = [],
            ledger: Annotated[List[DeclarationVerdicts], Field(description=(
                "Declaration entries not yet recorded with record_ledger; [] when all are."))] = [],
            files: Annotated[List[FileVerdicts], Field(description=(
                "File entries not yet recorded with record_ledger; [] when all are."))] = [],
            confidence: Annotated[Optional[float], Field(description="0.0-1.0")] = None,
            message: Annotated[str, Field(description="Optional summary of the review.")] = "",
        ) -> Dict[str, Any]:
            return await self._submit(findings, list(ledger) + list(files), confidence, message)

    def _check_ledger(self, findings: List[StructuredFinding],
                      ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """`(cells, None)` when the recorded ledger is a legal answer, `(None, refusal)` otherwise.

        One cell per (subject, concern), from the recorded entries, subjects being the PR's
        declarations and its changed files. Every `would_change` cell has a finding and every
        finding sits on a `would_change` cell of its subject, under a concern that subject has; a
        contradiction is refused like any other contract violation. A subject with no entry is
        asked for `LEDGER_PRESSES` times and then recorded `UNSTATED_VERDICT` under every concern,
        so "never answered" cannot read as `no_issue`.
        """

        recorded = self._recorded()
        problems: List[str] = []
        filed: Dict[Tuple[str, str], int] = {}
        for index, finding in enumerate(findings):
            subject = self._resolve_subject(finding.declaration)
            if subject is None:
                problems.append(f"finding {index} names {finding.declaration!r}, which is neither "
                                "a listed declaration nor a changed file's path")
                continue
            declaration, kind, concerns = subject
            if finding.concern not in concerns:
                problems.append(f"finding {index} is about the {kind} {declaration} under "
                                f"{finding.concern!r}, which is not one of its concerns {list(concerns)}")
                continue
            cell = (recorded.get(declaration) or {}).get(finding.concern)
            if cell is None or cell["verdict"] != "would_change":
                problems.append(f"finding {index} is about ({declaration}, {finding.concern}), "
                                f"whose verdict is {cell['verdict'] if cell else 'unrecorded'!r}, "
                                "not `would_change`")
            filed[(declaration, finding.concern)] = filed.get((declaration, finding.concern), 0) + 1
        for declaration, cells in recorded.items():
            for concern, cell in cells.items():
                if cell["verdict"] == "would_change" and (declaration, concern) not in filed:
                    problems.append(f"({declaration}, {concern}) is a `would_change` with no finding")
        if problems:
            return None, "The ledger is inconsistent: " + "; ".join(problems) + ". Fix and resubmit."
        missing = [name for name, _kind, _concerns in self._subjects() if name not in recorded]
        if missing:
            self._ledger_presses = getattr(self, "_ledger_presses", 0) + 1
            if self._ledger_presses <= LEDGER_PRESSES:
                shown = ", ".join(missing[:12])
                more = f" and {len(missing) - 12} more" if len(missing) > 12 else ""
                return None, (
                    "Every declaration and every changed file needs a ledger entry, a verdict with "
                    f"its reason under each of its concerns, before the review is submitted. Not "
                    f"recorded: {shown}{more}. Record them with {self.RECORD_TOOL}, or pass them as "
                    f"`ledger` and `files` here. (attempt {self._ledger_presses} of {LEDGER_PRESSES})")
        cells = []
        for name, kind, concerns in self._subjects():
            for concern in concerns:
                cell = (recorded.get(name) or {}).get(concern)
                cells.append({"declaration": name, "kind": kind, "concern": concern,
                              "verdict": cell["verdict"] if cell else UNSTATED_VERDICT,
                              "reason": cell["reason"] if cell else ""})
        return cells, None

    # --- verification -------------------------------------------------------------------------

    async def _compile_edit(self, finding: StructuredFinding) -> Tuple[str, Dict[str, Any]]:
        """`(outcome, evidence)` for the finding's edit, compiled in the reviewed file."""

        edit = finding.edit
        code, error = self._edited_file_code(
            finding.path, edit.line_start, edit.line_end, edit.replacement,
            declaration_name=edit.declaration_name, new_declaration=edit.new_declaration)
        if code is None:
            return REFUTED, {"check": "compile", "answer": f"the edit could not be applied: {error}"}
        # The same edit, compiled by the reviewer's own `lean_verify_edit` in this attempt, in
        # this workspace, with the same options: its result is this compile's result. Only a
        # finished compile is reused; one that timed out is compiled again.
        reused = self._edit_compiles().get(edit_key(
            finding.path, edit.line_start, edit.line_end, edit.replacement,
            edit.declaration_name, edit.new_declaration))
        if reused is not None and reused.get("outcome") in ("compiled", "compile_errors"):
            result = reused
        else:
            reused = None
            from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

            lean_tool = LeanVerifyToolsProvider(task=self, config=self.config, logger=self.logger)
            try:
                result = await lean_tool.execute(code=code, max_messages=20, options=WHOLE_FILE_OPTIONS)
            except Exception as exc:  # noqa: BLE001
                return UNVERIFIED, {"check": "compile", "answer": f"the compile raised: {exc}"}
            if not isinstance(result, dict) or result.get("outcome") not in ("compiled", "compile_errors"):
                return UNVERIFIED, {"check": "compile", "answer": (
                    "the compile did not finish: "
                    + str((result or {}).get("message") if isinstance(result, dict) else result))}
            result = await self._attribute_errors(finding.path, result)
        introduced = result.get("errors_introduced_by_your_edit")
        if introduced is None:
            introduced = result.get("errors") or []
        source = {"reused": "the same edit, compiled by lean_verify_edit in this session"} if reused else {}
        if introduced:
            first = str((introduced[0] or {}).get("data") or introduced[0])[:400]
            return REFUTED, {"check": "compile", **source, "answer": (
                f"the edit introduces {len(introduced)} error(s); the first: {first}")}
        return VERIFIED, {
            "check": "compile", **source, "answer": "the reviewed file compiles with the edit applied",
            "warnings_introduced": len(result.get("warnings_introduced_by_your_edit") or []),
        }

    async def _lookup_duplicate(self, finding: StructuredFinding) -> Tuple[str, Dict[str, Any]]:
        from .context_tools import lookup_declaration

        answer = await lookup_declaration(self, finding.duplicate_of, trace=False)
        if not answer.get("success"):
            return UNVERIFIED, {"check": "duplicate_of", "answer": answer.get("error")}
        if not answer.get("count"):
            return REFUTED, {"check": "duplicate_of", "answer": (
                f"no declaration of {finding.duplicate_of!r} exists at the base commit or in the "
                "files this PR changes")}
        return VERIFIED, {"check": "duplicate_of", "answer": answer.get("results")}

    async def _lookup_rename(self, finding: StructuredFinding) -> Tuple[str, Dict[str, Any]]:
        from .context_tools import lookup_declaration, naming_census

        answer = await lookup_declaration(self, finding.rename_to, trace=False)
        if answer.get("success") and answer.get("declared_before_this_pr"):
            return REFUTED, {"check": "rename_to", "answer": (
                f"{finding.rename_to!r} is already declared at the base commit: "
                + str(answer.get("results")))}
        census = await naming_census(self, finding.declaration, trace=False)
        return UNVERIFIED, {
            "check": "rename_to",
            "answer": "the new name clashes with nothing the library declares",
            "naming_norm": (census.get("results") if census.get("success") else census.get("error")),
            "naming_norm_verdict": census.get("verdict"),
        }

    async def _verify_finding(self, finding: StructuredFinding) -> Tuple[str, List[Dict[str, Any]]]:
        """`(outcome, evidence)`: refuted if any check contradicts the change, verified if any
        check confirms it and none contradicts, unverified otherwise."""

        checks = []
        if finding.edit is not None:
            checks.append(await self._compile_edit(finding))
        if finding.duplicate_of:
            checks.append(await self._lookup_duplicate(finding))
        if finding.rename_to:
            checks.append(await self._lookup_rename(finding))
        outcomes = [outcome for outcome, _ in checks]
        outcome = (REFUTED if REFUTED in outcomes else VERIFIED if VERIFIED in outcomes
                   else UNVERIFIED)
        return outcome, [evidence for _, evidence in checks]

    async def _verify_all(self, findings: List[StructuredFinding],
                          ) -> List[Tuple[str, List[Dict[str, Any]]]]:
        semaphore = asyncio.Semaphore(3)

        async def one(finding):
            async with semaphore:
                return await self._verify_finding(finding)

        return list(await asyncio.gather(*(one(finding) for finding in findings)))

    # --- recording ----------------------------------------------------------------------------

    def _filed_finding(self, finding: StructuredFinding, outcome: str,
                       evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """The solo's free-form finding shape, which the base normalizes and the runner anchors.
        An unverified change is filed as advisory (plan §3.3)."""

        return {
            "path": finding.path, "line_start": finding.line_start,
            "line_end": finding.line_end or finding.line_start,
            "severity": finding.severity if outcome == VERIFIED else "advisory",
            "claim": finding.claim, "suggested_fix": finding.suggested_fix,
            "evidence": json.dumps(evidence, ensure_ascii=False) if evidence else None,
            "verified": outcome == VERIFIED,
            # The subject as the ledger names it, so a `target/`-prefixed path or a dotted suffix
            # meets its cell again in the critic stage.
            "declaration": (self._resolve_subject(finding.declaration) or (finding.declaration,))[0],
            "concern": finding.concern,
            "verification": outcome,
        }

    def _normalize_findings(self, findings):
        normalized = super()._normalize_findings(findings)
        # The base keeps a fixed key set; this design's own keys ride beside it. Every raw
        # finding has a non-empty claim (the typed model), so the two lists align.
        for raw, row in zip(findings, normalized):
            row["declaration"] = raw.get("declaration")
            row["concern"] = raw.get("concern")
            row["concern_label"] = raw.get("concern")
            row["verification"] = raw.get("verification")
        return normalized

    async def _submit(self, findings: List[StructuredFinding], entries,
                      confidence: Optional[float], message: str) -> Dict[str, Any]:
        if entries:
            _recorded, problems = self._record_entries(entries)
            if problems:
                return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=(
                    "Nothing recorded: " + "; ".join(problems) + ". Fix and resubmit.")),
                    "message": "Invalid ledger"}
        cells, refusal = self._check_ledger(findings)
        if refusal is not None:
            return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=refusal),
                    "message": "Invalid ledger"}
        budget = self.config.task_config.finding_budget
        if 0 < budget < len(findings):
            return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=(
                f"Not recorded: {len(findings)} findings exceed this review's budget of {budget}. "
                f"Call again with at most {budget}, keeping the changes you would most insist "
                "on; mention the rest in `message`.")), "message": "Over budget"}

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
                    "filed unverified), or drop it; keep every other finding. After "
                    f"attempt {LEDGER_PRESSES} the contradicted changes are recorded as refuted "
                    f"and not filed. (attempt {self._refutation_presses} of {LEDGER_PRESSES})")),
                    "message": "Refuted changes"}

        filed_raw, refuted_rows = [], []
        outcome_by_cell: Dict[Tuple[str, str], str] = {}
        for finding, (outcome, evidence) in zip(findings, verified):
            subject = self._resolve_subject(finding.declaration)
            key = (subject[0] if subject else finding.declaration, finding.concern)
            # The cell's outcome: the strongest filed state wins over a refuted sibling.
            rank = {VERIFIED: 2, UNVERIFIED: 1, REFUTED: 0}
            if rank[outcome] >= rank.get(outcome_by_cell.get(key, REFUTED), 0):
                outcome_by_cell[key] = outcome
            if outcome == REFUTED:
                refuted_rows.append({**finding.model_dump(mode="json"), "evidence": evidence})
            else:
                filed_raw.append(self._filed_finding(finding, outcome, evidence))
        for cell in cells:
            if cell["verdict"] == "would_change":
                cell["outcome"] = outcome_by_cell.get((cell["declaration"], cell["concern"]))
        try:
            normalized = self._normalize_findings(filed_raw)
            result = self.create_result(
                success=True, score=1.0, pr_number=self.data.pr_number, merge_ready_as_is=None,
                confidence=confidence, findings=normalized, review_message=message or "",
                ledger=cells, refuted=refuted_rows)
        except Exception:  # noqa: BLE001
            import traceback

            self.logger.error("submit_findings (structured) failed: %s", traceback.format_exc())
            return {"evaluation_result": EvaluationResult(success=False, score=0.0,
                                                          message=traceback.format_exc()),
                    "message": "Submit failed"}
        self.logger.info("submit_findings (structured): %d cells, %d filed (%d verified), %d refuted",
                         len(cells), len(normalized), sum(1 for row in normalized if row["verified"]),
                         len(refuted_rows))
        if self.termination_callback:
            try:
                await self.termination_callback(result)
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to trigger termination: %s", exc)
        return {
            "evaluation_result": EvaluationResult(success=True, score=1.0, message=(
                f"Review recorded: {len(cells)} ledger cells, {len(normalized)} findings filed, "
                f"{len(refuted_rows)} refuted.")),
            "message": "Review submitted",
        }


register_task(STRUCTURED_TASK_TYPE, StructuredReviewTask)
