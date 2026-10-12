"""Design G, `filing_contract`: a cell closes as conforming only on evidence the task can verify.

The per-ask reading of P14 and D12 (`results/pr_review_v5/probes/ask-reading-2026-10-12/`) found the
free reviewer naming the maintainer's concern at most of its misses and clearing it -- on worth, a
corpus count, the file's siblings, a check it did not run or ran on the wrong variant, or nothing
stated -- and the same paragraph that ranks conventions over its judgement already in its packet
and routed around. Prose about grounds cannot reach an unstated ground; what moved this model's
filings in the record was always a change in what the submission may contain. So this design is
D1 `structured` (a disposition per declaration and concern, every subject answered) with the
submission changed (`docs/research/filing-decision-design-2026-10-12.md` §10, pre-registered in
`results/pr_review_v5/probes/filing-contract-2026-10-12/README.md`):

- **Three dispositions.** `conforms`; `candidate`, a change the author should make; `ask_author`, a
  question to the author (a check that could not be run, or that failed for want of something the
  author could supply).
- **`conforms` is refusable.** It is recorded only with an evidence item this task verifies: a
  `quote` of that subject's *own* reviewed code (a declaration's target and the doc-comment and
  attribute targets attached to it; a file's text; the PR's title and description), or a `check`
  (an edit compiled with `lean_verify_edit` in this session and found in its compile cache, or a
  declaration name the task looks up again and finds). A sibling's line is not the subject's code,
  and a count, a guess or the file's habit is not an evidence kind that can close a cell.
- **Nothing is withheld.** Every `candidate` and `ask_author` cell is filed; there is no finding
  budget; the contract states that it replaces the brief's instructions to predict only requests,
  to file only what the reviewer would insist on, and not to raise questions. A change the tools
  contradict is handed back as in D1 and then filed as a question carrying the tool's answer,
  never dropped.
- **Typed evidence and `would_clear_on`** ride on every filed cell: what the reviewer's case rests
  on, and the ground on which it would have left the cell out if it could. The ledger is stored
  (`ledgers.jsonl`), so a filing policy can be replayed over it without a reviewer run.
- **The questions the audit never asked** are written into the concerns (a mechanism that makes the
  declaration unnecessary; the shape a caller wants and what the proof uses; the library's current
  form, not the file's), and the PR itself is a subject (`description`, `scope`).

Everything else is D1's and the solo's: the brief, the packet, the tools, verification at
submission, the ledger presses, the findings' keys downstream.
"""

import asyncio
import json
import re
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, get_args

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import EvaluationResult, register_task

from .base import _strip_ws_prefix, edit_key
from .candidates import UNSTATED_VERDICT
from .solo import solo_context_block
from .structured import (
    CONCERNS, FILE_CONCERN_TEXT, FILE_CONCERNS, LEDGER_PRESSES, REFUTED, UNVERIFIED, VERIFIED,
    StructuredEdit, StructuredReviewConfig, StructuredReviewData, StructuredReviewResult,
    StructuredReviewTask, declarations_of,
)

FILING_TASK_TYPE = "lean_pr_review_v5_filing_contract"

#: D1's six concerns, each carrying the questions the per-ask reading found the audit never asks.
CONCERN_TEXT = {
    "proof": "the proof -- shorter, the idiomatic tactic, an existing lemma in place of a "
             "hand-written argument; and whether a tactic, an attribute or a generator would make "
             "this proof, or this declaration, unnecessary",
    "statement": "the statement and its generality -- hypotheses that are not needed, a special "
                 "case of something that holds generally, the form the library states such things "
                 "in; the shape a caller would want (an iff, a structure, an instance argument, "
                 "which side is the simpler one); and what the proof actually uses of each "
                 "hypothesis and constant",
    "library": "whether the library already has it, or has what it should reuse; and the "
               "library's current form for this kind of declaration -- its newest declarations "
               "and its deprecations, not only what this file does",
    "name": "the name, against the naming convention and the library's current names for such "
            "statements, not only this file's",
    "docstring": "the docstring -- missing, wrong, or out of step with what the declaration does",
    "placement": "attributes and placement -- `simp`, `to_additive`, generator attributes and the "
                 "like, the file and section it sits in; and what a new import costs the files "
                 "that import this one",
}
assert tuple(CONCERN_TEXT) == CONCERNS

PRConcern = Literal["description", "scope"]
PR_CONCERNS: Tuple[str, ...] = get_args(PRConcern)
PR_CONCERN_TEXT = {
    "description": "whether the PR's description says what it does and why, and the plan when the "
                   "change is a step of a larger one",
    "scope": "whether the PR is one thing, and whether it finishes its change at the analogous "
             "places (the siblings, the dual, the other files that should follow)",
}
#: The PR as a subject: one entry, named this.
PR_SUBJECT = "PR"

AnyConcern = Literal["proof", "statement", "library", "name", "docstring", "placement",
                     "module_doc", "style", "organization", "description", "scope"]
assert set(get_args(AnyConcern)) == set(CONCERNS) | set(FILE_CONCERNS) | set(PR_CONCERNS)

Disposition = Literal["conforms", "candidate", "ask_author"]
#: The dispositions that file a finding.
FILING = ("candidate", "ask_author")
EvidenceKind = Literal["check", "quote", "convention", "form", "construction", "analogue", "own"]
#: The kinds that can close a cell as conforming, each verified by the task.
CLOSING_KINDS = ("quote", "check")
ClearGround = Literal["nothing", "worth", "maintainers_might_not_ask", "file_or_siblings",
                      "corpus_or_tool_count", "brief_or_budget", "change_may_be_wrong", "other"]

#: A quote must carry this much text to identify a line, and a convention sentence this much.
MIN_QUOTE_CHARS = 12
MIN_CONVENTION_CHARS = 30


class EvidenceEdit(StructuredEdit):
    """An edit the reviewer compiled with `lean_verify_edit`, exactly as it gave it."""

    path: str = Field(description="The reviewed file the edit was compiled in")


class Evidence(BaseModel):
    """One piece of what a disposition rests on."""

    model_config = ConfigDict(extra="forbid")

    kind: EvidenceKind = Field(description=(
        "`quote`: a line of this subject's own reviewed code; `check`: an edit you compiled with "
        "lean_verify_edit in this session, or a declaration you looked up; `convention`: a "
        "convention's sentence from the section in the prompt; `form`: a declaration or "
        "deprecation that shows the library's current form; `construction`: Lean text you built "
        "and what it did; `analogue`: a library declaration you compared against; `own`: your "
        "reasoning"))
    text: str = Field(description=(
        "For `quote`: the code, verbatim. For `convention`: the sentence, verbatim. Otherwise: "
        "what you checked, built, compared or reasoned, and what it showed."))
    edit: Optional[EvidenceEdit] = Field(default=None, description=(
        "For a `check` that is a compile: the edit, exactly as you gave it to lean_verify_edit"))
    lookup: Optional[str] = Field(default=None, description=(
        "For a `check` that is a lookup: the declaration name; it is looked up again"))


class Cell(BaseModel):
    """One (subject, concern) cell. `reason` first, as in D1."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(description="What you checked under this concern and what you found.")
    disposition: Disposition
    evidence: List[Evidence] = Field(default_factory=list, description=(
        "What the disposition rests on. A `conforms` needs a `quote` of this subject's own code "
        "showing it already has the form, or a `check`; a `candidate` or `ask_author` lists what "
        "its case rests on."))
    would_clear_on: Optional[ClearGround] = Field(default=None, description=(
        "For a `candidate` or `ask_author`: the ground on which you would have left it out of the "
        "review if that were allowed; `nothing` if none."))


class DeclarationEntry(BaseModel):
    """One declaration's entry: a cell per concern, in `CONCERNS` order."""

    model_config = ConfigDict(extra="forbid")

    declaration: str = Field(description="A declaration from the list in the prompt, by name")
    proof: Cell
    statement: Cell
    library: Cell
    name: Cell
    docstring: Cell
    placement: Cell


class FileEntry(BaseModel):
    """One changed file's entry: a cell per file concern."""

    model_config = ConfigDict(extra="forbid")

    file: str = Field(description="A changed file from the list in the prompt, by path")
    module_doc: Cell
    style: Cell
    organization: Cell


class PREntry(BaseModel):
    """The PR's own entry."""

    model_config = ConfigDict(extra="forbid")

    pr: Literal["PR"] = PR_SUBJECT
    description: Cell
    scope: Cell


class FilingFinding(BaseModel):
    """One filed cell: a change the author should make, or a question to the author."""

    model_config = ConfigDict(extra="forbid")

    declaration: str = Field(description=(
        "The subject: a listed declaration, a changed file's path, or `PR`"))
    concern: AnyConcern
    path: str = Field(description=(
        "The reviewed file, e.g. Mathlib/.../X.lean; for the PR, its main changed file"))
    line_start: int = Field(description="The line the finding is about")
    claim: str = Field(description=(
        "For a change: name the declaration and say what is wrong. For a question: the question "
        "to the author."))
    suggested_fix: str = Field(description=(
        "The change to make; for a question, the change the question is about"))
    severity: Literal["blocking", "advisory"] = "advisory"
    line_end: Optional[int] = None
    edit: Optional[StructuredEdit] = Field(default=None, description=(
        "The change as an edit to the reviewed file, when it is one; compiled at submission"))
    duplicate_of: Optional[str] = Field(default=None, description=(
        "When the library already has this: the existing declaration's name"))
    rename_to: Optional[str] = Field(default=None, description="When the change is a rename: the new name")


#: Appended to the solo's user prompt. Placeholders are filled by the task; no other braces.
FILING_CONTRACT = """

---

## The review contract

For this review, this contract replaces the brief's instructions to predict only the changes a \
maintainer would request, to emit a finding only for a change you would actually request, and \
not to report questions or what was checked. Nothing is left out here: every concern of every \
subject ends in a disposition, and every `candidate` and `ask_author` is filed.

Declarations in this PR, as it leaves them -- each needs a disposition under every concern:
{declarations}

The concerns of a declaration:
{concerns}

Files this PR changes -- each needs a disposition under every file concern:
{files}

The concerns of a file as a whole:
{file_concerns}

The PR itself is a subject, named `PR`, with two concerns:
{pr_concerns}

**Dispositions.** Each cell has a `reason`, a `disposition`, its `evidence` and, unless it \
conforms, `would_clear_on`:
- `conforms`: the code already has the form this concern calls for. It is recorded **only with \
evidence this task verifies**: a `quote` -- a line of this subject's own reviewed code, verbatim, \
that shows it already has the form (a line of another declaration is not this subject's code) -- \
or a `check` -- an edit you compiled with `lean_verify_edit` in this session, given exactly as you \
gave it, or a declaration name you looked up, which is looked up again. A `conforms` without one is \
refused, and the whole call with it.
- `candidate`: a change the author should make. File it.
- `ask_author`: a question to the author -- a check you could not run, or one that failed for want \
of something the author could supply. File it, with the check and what it returned.

That this file or its siblings do it the same way, that a count over the library is high, that the \
change is minor or a matter of taste, that a maintainer might not insist on it, or that you did not \
check it are not evidence that a cell conforms. If one of them is why you would leave a cell out, \
the cell is a `candidate` or an `ask_author`, and `would_clear_on` names that ground: `worth`, \
`maintainers_might_not_ask`, `file_or_siblings`, `corpus_or_tool_count`, `brief_or_budget`, \
`change_may_be_wrong`, `other`, or `nothing`.

Record entries with `{record_tool_name}` as you go -- `entries` for declarations, `files` for files, \
`pr` for the PR -- one or several per call; a later entry for a subject replaces the earlier one.

When you have reviewed the PR, call `{submit_tool_name}` once with `findings`: one per `candidate` \
or `ask_author` cell, naming its subject as `declaration` (a declaration, a file's path, or `PR`) \
and its `concern`, with `path`, `line_start`, `claim` (for a question, the question itself), \
`suggested_fix` (for a question, the change it asks about) and, where the change is an edit, \
`edit`; a duplicate, `duplicate_of`; a rename, `rename_to`. Entries not yet recorded may go in the \
same call. A subject without an entry is asked for again.

At submission this task compiles every `edit` in the reviewed file and looks up every \
`duplicate_of` and `rename_to`. A change the tools contradict is handed back to you with the tool's \
answer, to correct or to resubmit; after that it is filed as a question to the author carrying the \
tool's answer. Nothing is withheld, and there is no limit on the number of findings."""


class FilingContractConfig(StructuredReviewConfig):
    """D1's config. The finding budget is not enforced: nothing is withheld."""


class FilingContractData(StructuredReviewData):
    task_type: str = FILING_TASK_TYPE


class FilingContractResult(StructuredReviewResult):
    design: str = "filing_contract"
    #: How many `conforms` cells were refused for want of verified evidence, over the session.
    conforms_refused: int = 0
    #: Changes the tools contradicted that were filed as questions after the presses.
    contradicted_filed_as_questions: List[Dict[str, Any]] = Field(default_factory=list)


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def own_code_of(graph) -> Dict[str, str]:
    """Declaration name -> its own reviewed code: the declaration target's, and every doc-comment
    and attribute target attached to it."""

    by_change = {target.change_id: target for target in graph.targets}
    own: Dict[str, List[str]] = {}
    for target in graph.targets:
        if target.kind == "declaration" and target.declaration_name and (target.reviewed_code or "").strip():
            own.setdefault(target.declaration_name, []).append(target.reviewed_code)
    for target in graph.targets:
        anchor = by_change.get(target.attached_to or "")
        if anchor is not None and anchor.declaration_name and (target.reviewed_code or "").strip():
            own.setdefault(anchor.declaration_name, []).append(target.reviewed_code)
    return {name: "\n".join(parts) for name, parts in own.items()}


class FilingContractTask(StructuredReviewTask):
    task_type = FILING_TASK_TYPE
    data_class = FilingContractData
    task_config_class = FilingContractConfig
    task_result_class = FilingContractResult
    design_version = "filing_contract/1"

    CELL_VALUE = "disposition"
    RECORD_TOOL = "record_ledger"

    # --- the design hooks ---------------------------------------------------------------------

    @classmethod
    def design_payload(cls, *, episode, graph, dataset, stage) -> Dict[str, Any]:
        payload = super().design_payload(episode=episode, graph=graph, dataset=dataset, stage=stage)
        own = own_code_of(graph)
        payload["declarations"] = [{**row, "own_code": own.get(row["name"], "")}
                                   for row in payload["declarations"]]
        return payload

    @classmethod
    def describe_design_payload(cls, payload: Dict[str, Any]) -> str:
        count = len(payload.get("declarations") or [])
        files = len(payload.get("changed_files") or [])
        cells = count * len(CONCERNS) + files * len(FILE_CONCERNS) + len(PR_CONCERNS)
        return (f"{count} declaration(s) x {len(CONCERNS)} + {files} file(s) x {len(FILE_CONCERNS)} "
                f"+ the PR x {len(PR_CONCERNS)} = {cells} cells")

    def _finding_budget(self) -> int:
        # Nothing is withheld: no budget, here or in the base's normalisation.
        return 0

    # --- subjects -----------------------------------------------------------------------------

    def _subjects(self) -> List[Tuple[str, str, Tuple[str, ...]]]:
        return super()._subjects() + [(PR_SUBJECT, "pr", PR_CONCERNS)]

    def _resolve_subject(self, given: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
        if (given or "").strip() in (PR_SUBJECT, "pr", "the PR"):
            return (PR_SUBJECT, "pr", PR_CONCERNS)
        return super()._resolve_subject(given)

    def contract_text(self) -> str:
        declarations = "\n".join(
            f"- `{row['name']}` ({row['kind']}, `{row['path']}`)" for row in self.data.declarations
        ) or "- (none: this PR leaves no declaration in place)"
        concerns = "\n".join(f"- `{name}`: {CONCERN_TEXT[name]}." for name in CONCERNS)
        files = "\n".join(f"- `{path}`" for path in self.data.changed_files or []) or "- (none)"
        file_concerns = "\n".join(f"- `{name}`: {FILE_CONCERN_TEXT[name]}." for name in FILE_CONCERNS)
        pr_concerns = "\n".join(f"- `{name}`: {PR_CONCERN_TEXT[name]}." for name in PR_CONCERNS)
        return FILING_CONTRACT.format(
            declarations=declarations, concerns=concerns, files=files, file_concerns=file_concerns,
            pr_concerns=pr_concerns,
            record_tool_name=f"{self.config.mcp_server_name}{self.RECORD_TOOL}",
            submit_tool_name=f"{self.config.mcp_server_name}submit_findings")

    # --- evidence -----------------------------------------------------------------------------

    def _own_text(self, subject: str, kind: str) -> str:
        """The text a `quote` for this subject must come from."""
        if kind == "pr":
            return f"{self.data.pr_title}\n{self.data.pr_description}"
        if kind == "file":
            root = self.target_workspace.path if self.target_workspace else None
            if root is None:
                return ""
            from pathlib import Path
            path = Path(root) / (_strip_ws_prefix(subject) or "")
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                return ""
        row = next((row for row in self.data.declarations if row["name"] == subject), None)
        return (row or {}).get("own_code", "")

    def _context_text(self) -> str:
        if not hasattr(self, "_context_cache"):
            try:
                self._context_cache = solo_context_block(self.config.task_config, self.data.pr_number) or ""
            except Exception:  # noqa: BLE001
                self._context_cache = ""
        return self._context_cache

    async def _verify_evidence(self, item: Evidence, subject: str, kind: str) -> bool:
        """Whether this task can confirm the evidence item. Only `quote` and `check` can close a
        cell; `convention` is checked against the delivered section, for the record only."""

        if item.kind == "quote":
            quote = _normalize_space(item.text)
            return (len(quote.replace(" ", "")) >= MIN_QUOTE_CHARS
                    and quote in _normalize_space(self._own_text(subject, kind)))
        if item.kind == "check":
            if item.edit is not None:
                edit = item.edit
                found = self._edit_compiles().get(edit_key(
                    edit.path, edit.line_start, edit.line_end, edit.replacement,
                    edit.declaration_name, edit.new_declaration))
                return bool(found) and found.get("outcome") in ("compiled", "compile_errors")
            if (item.lookup or "").strip():
                from . import context_tools

                answer = await context_tools.lookup_declaration(self, item.lookup.strip(), trace=False)
                return bool(answer.get("success")) and bool(answer.get("count"))
            return False
        if item.kind == "convention":
            sentence = _normalize_space(item.text)
            return len(sentence) >= MIN_CONVENTION_CHARS and sentence in _normalize_space(self._context_text())
        return False

    # --- recording the ledger -----------------------------------------------------------------

    async def _record_entries_async(self, entries) -> Tuple[List[str], List[str]]:
        """`(recorded subjects, problems)`. All or nothing, as in D1; a `conforms` without
        verified closing evidence is a problem."""

        staged: Dict[str, Dict[str, Dict[str, Any]]] = {}
        problems: List[str] = []
        refused = 0
        for entry in entries:
            if isinstance(entry, PREntry):
                given, expected = PR_SUBJECT, "pr"
            elif isinstance(entry, FileEntry):
                given, expected = entry.file, "file"
            else:
                given, expected = entry.declaration, "declaration"
            subject = self._resolve_subject(given)
            if subject is None or subject[1] != expected:
                problems.append(f"{given!r} is not one of this PR's listed "
                                f"{ {'file': 'changed files', 'pr': 'subjects'}.get(expected, 'declarations') }")
                continue
            name, kind, concerns = subject
            if name in staged:
                problems.append(f"{name} has two entries in one call")
                continue
            cells = {}
            for concern in concerns:
                cell: Cell = getattr(entry, concern)
                if not cell.reason.strip():
                    problems.append(f"({name}, {concern}) has an empty reason")
                evidence = []
                for item in cell.evidence:
                    verified = await self._verify_evidence(item, name, kind)
                    evidence.append({**item.model_dump(mode="json", exclude_none=True), "verified": verified})
                if cell.disposition == "conforms" and not any(
                        row["verified"] and row["kind"] in CLOSING_KINDS for row in evidence):
                    refused += 1
                    problems.append(
                        f"({name}, {concern}) is `conforms` without verified evidence: give a `quote` "
                        f"of this {kind}'s own reviewed code that shows it already has the form, or a "
                        "`check` (an edit you compiled with lean_verify_edit in this session, exactly "
                        "as you gave it, or a declaration you looked up); otherwise it is a "
                        "`candidate` or an `ask_author`")
                cells[concern] = {
                    "disposition": cell.disposition, "reason": cell.reason.strip(),
                    "evidence": evidence,
                    "would_clear_on": (cell.would_clear_on or "unstated") if cell.disposition in FILING else None,
                }
            staged[name] = cells
        self._conforms_refused = getattr(self, "_conforms_refused", 0) + refused
        if problems:
            return [], problems
        self._recorded().update(staged)
        self._persist_progress()
        return list(staged), []

    async def _record_reply_async(self, entries) -> Dict[str, Any]:
        recorded, problems = await self._record_entries_async(entries)
        if problems:
            return {"success": False, "outcome": "invalid_request", "error": (
                "Nothing recorded: " + "; ".join(problems) + ". Fix and call again.")}
        names = [subject[0] for subject in self._subjects()]
        remaining = [name for name in names if name not in self._recorded()]
        return {"success": True, "recorded": recorded,
                "progress": f"{len(names) - len(remaining)} of {len(names)} subjects recorded",
                "remaining": remaining[:20] + ([f"... and {len(remaining) - 20} more"]
                                               if len(remaining) > 20 else [])}

    # --- the submission -----------------------------------------------------------------------

    async def register_task_tools(self, mcp) -> None:
        from .context_tools import register_context_tools

        self._register_lean_verify_edit(mcp)
        register_context_tools(self, mcp)

        @mcp.tool(description=(
            "Record entries: for each declaration, each changed file and the PR, a disposition "
            "with its reason and evidence under every one of its concerns. Call it as you go; a "
            "later entry replaces the earlier one. Returns what is still to record."))
        async def record_ledger(
            entries: Annotated[List[DeclarationEntry], Field(description=(
                "One entry per declaration, each with all six concern cells."))] = [],
            files: Annotated[List[FileEntry], Field(description=(
                "One entry per changed file, each with its three file-concern cells."))] = [],
            pr: Annotated[List[PREntry], Field(description=(
                "The PR's entry, with its two cells (at most one)."))] = [],
        ) -> Dict[str, Any]:
            return await self._record_reply_async(list(entries) + list(files) + list(pr))

        @mcp.tool(description=(
            "Submit your review of this PR: one finding per `candidate` or `ask_author` cell, and "
            "any entries not yet recorded. Call it once, when you have finished: it records the "
            "review and ends the session."))
        async def submit_findings(
            findings: Annotated[List[FilingFinding], Field(description=(
                "One per `candidate` or `ask_author` cell, naming its subject and concern; [] "
                "when no cell files."))] = [],
            ledger: Annotated[List[DeclarationEntry], Field(description=(
                "Declaration entries not yet recorded; [] when all are."))] = [],
            files: Annotated[List[FileEntry], Field(description=(
                "File entries not yet recorded; [] when all are."))] = [],
            pr: Annotated[List[PREntry], Field(description=(
                "The PR's entry, if not yet recorded; [] when it is."))] = [],
            confidence: Annotated[Optional[float], Field(description="0.0-1.0")] = None,
            message: Annotated[str, Field(description="Optional summary of the review.")] = "",
        ) -> Dict[str, Any]:
            return await self._submit(findings, list(ledger) + list(files) + list(pr), confidence, message)

    def _check_ledger(self, findings: List[FilingFinding],
                      ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """D1's check with `candidate` and `ask_author` as the filing dispositions."""

        recorded = self._recorded()
        problems: List[str] = []
        filed: Dict[Tuple[str, str], int] = {}
        for index, finding in enumerate(findings):
            subject = self._resolve_subject(finding.declaration)
            if subject is None:
                problems.append(f"finding {index} names {finding.declaration!r}, which is not a "
                                "listed declaration, a changed file's path, or `PR`")
                continue
            name, kind, concerns = subject
            if finding.concern not in concerns:
                problems.append(f"finding {index} is about the {kind} {name} under "
                                f"{finding.concern!r}, which is not one of its concerns {list(concerns)}")
                continue
            cell = (recorded.get(name) or {}).get(finding.concern)
            if cell is None or cell["disposition"] not in FILING:
                problems.append(f"finding {index} is about ({name}, {finding.concern}), whose "
                                f"disposition is {cell['disposition'] if cell else 'unrecorded'!r}, "
                                "not `candidate` or `ask_author`")
            filed[(name, finding.concern)] = filed.get((name, finding.concern), 0) + 1
        for name, cells in recorded.items():
            for concern, cell in cells.items():
                if cell["disposition"] in FILING and (name, concern) not in filed:
                    problems.append(f"({name}, {concern}) is a `{cell['disposition']}` with no finding")
        if problems:
            return None, "The ledger is inconsistent: " + "; ".join(problems) + ". Fix and resubmit."
        missing = [name for name, _kind, _concerns in self._subjects() if name not in recorded]
        if missing:
            self._ledger_presses = getattr(self, "_ledger_presses", 0) + 1
            if self._ledger_presses <= LEDGER_PRESSES:
                shown = ", ".join(missing[:12])
                more = f" and {len(missing) - 12} more" if len(missing) > 12 else ""
                return None, (
                    "Every declaration, every changed file and the PR need an entry, a disposition "
                    f"under each of their concerns, before the review is submitted. Not recorded: "
                    f"{shown}{more}. Record them with {self.RECORD_TOOL}, or pass them here. "
                    f"(attempt {self._ledger_presses} of {LEDGER_PRESSES})")
        cells = []
        for name, kind, concerns in self._subjects():
            for concern in concerns:
                cell = (recorded.get(name) or {}).get(concern)
                cells.append({"declaration": name, "kind": kind, "concern": concern,
                              "disposition": cell["disposition"] if cell else UNSTATED_VERDICT,
                              "reason": cell["reason"] if cell else "",
                              "evidence": cell["evidence"] if cell else [],
                              "would_clear_on": cell["would_clear_on"] if cell else None})
        return cells, None

    def _filed_finding(self, finding, outcome: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        row = super()._filed_finding(finding, outcome, evidence)
        if outcome == REFUTED:
            # Filed as a question after the presses: the change did not check.
            answer = "; ".join(str(item.get("answer")) for item in evidence)[:600]
            row["suggested_fix"] = (f"{finding.suggested_fix} [Question to the author: the task's "
                                    f"check of this change did not pass ({answer}).]")
            row["severity"] = "advisory"
            row["verified"] = False
            row["verification"] = "contradicted_asked"
        return row

    async def _submit(self, findings: List[FilingFinding], entries,
                      confidence: Optional[float], message: str) -> Dict[str, Any]:
        if entries:
            _recorded, problems = await self._record_entries_async(entries)
            if problems:
                return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=(
                    "Nothing recorded: " + "; ".join(problems) + ". Fix and resubmit.")),
                    "message": "Invalid ledger"}
        cells, refusal = self._check_ledger(findings)
        if refusal is not None:
            return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=refusal),
                    "message": "Invalid ledger"}

        verified = await self._verify_all(findings)
        contradicted = [(finding, evidence) for finding, (outcome, evidence) in zip(findings, verified)
                        if outcome == REFUTED]
        if contradicted:
            self._refutation_presses = getattr(self, "_refutation_presses", 0) + 1
            if self._refutation_presses <= LEDGER_PRESSES:
                lines = [f"- ({finding.declaration}, {finding.concern}) {finding.claim[:80]!r}: "
                         + "; ".join(str(item.get("answer")) for item in evidence)
                         for finding, evidence in contradicted]
                return {"evaluation_result": EvaluationResult(success=False, score=0.0, message=(
                    f"{len(contradicted)} change(s) are contradicted by the tools:\n" + "\n".join(lines)
                    + "\nCorrect the edit or the name, or resubmit the finding without it; keep every "
                    f"other finding. After attempt {LEDGER_PRESSES} a contradicted change is filed "
                    "as a question to the author carrying the tool's answer. "
                    f"(attempt {self._refutation_presses} of {LEDGER_PRESSES})")),
                    "message": "Contradicted changes"}

        filed_raw, asked = [], []
        outcome_by_cell: Dict[Tuple[str, str], str] = {}
        for finding, (outcome, evidence) in zip(findings, verified):
            subject = self._resolve_subject(finding.declaration)
            key = (subject[0] if subject else finding.declaration, finding.concern)
            outcome_by_cell.setdefault(key, outcome)
            if outcome == REFUTED:
                asked.append({**finding.model_dump(mode="json"), "evidence": evidence})
            filed_raw.append(self._filed_finding(finding, outcome, evidence))
        for cell in cells:
            if cell["disposition"] in FILING:
                cell["outcome"] = outcome_by_cell.get((cell["declaration"], cell["concern"]))
        try:
            normalized = self._normalize_findings(filed_raw)
            result = self.create_result(
                success=True, score=1.0, pr_number=self.data.pr_number, merge_ready_as_is=None,
                confidence=confidence, findings=normalized, review_message=message or "",
                ledger=cells, refuted=[], conforms_refused=getattr(self, "_conforms_refused", 0),
                contradicted_filed_as_questions=asked)
        except Exception:  # noqa: BLE001
            import traceback

            self.logger.error("submit_findings (filing_contract) failed: %s", traceback.format_exc())
            return {"evaluation_result": EvaluationResult(success=False, score=0.0,
                                                          message=traceback.format_exc()),
                    "message": "Submit failed"}
        self.logger.info("submit_findings (filing_contract): %d cells, %d filed, %d asked after "
                         "contradiction, %d conforms refused over the session", len(cells),
                         len(normalized), len(asked), getattr(self, "_conforms_refused", 0))
        if self.termination_callback:
            try:
                await self.termination_callback(result)
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to trigger termination: %s", exc)
        return {
            "evaluation_result": EvaluationResult(success=True, score=1.0, message=(
                f"Review recorded: {len(cells)} cells, {len(normalized)} findings filed.")),
            "message": "Review submitted",
        }


register_task(FILING_TASK_TYPE, FilingContractTask)
