"""Decision-turn replay: change what an arm decides without re-running what it investigated.

Every change aimed at the submission decision -- abstention wording, the bar, field order,
confidence elicitation -- used to be tested with a whole rep, which re-samples the
investigation as well. A decision change then competes with investigation variance it did not
cause, read through a judge that splits its own vote on ~11% of pairs. Forcing the decision
alone moved issue recall 0.20 -> 0.50 on the same PRs, so the decision is where this system's
findings go missing, and it deserves an instrument that holds everything else still
(`docs/todo/replay-decision-turn.md`).

**What is held fixed.** A recorded arm session is cut just before its first
`submit_candidates` call. Everything the arm read up to that point -- system prompt, tool
definitions, prompt, every tool call and result -- is replayed to the model as recorded; the
provider API is stateless Chat Completions here, so the session file is exactly what was sent.
The task is rebuilt from the run's own `arm_pool.jsonl` payload, so the submission validates
against the same `change_ids`, subjects and entity maps.

**Why the first submission, not the last.** ~9% of arm sessions on the held-out reps had their
first submission refused (26 / 31 / 28 of 321 / 316 / 322) and then repaired it. The task counts
refusals on the instance (`_mute_abstentions`, `_forced_presses`), and a replayed task starts at
zero -- so only a prefix containing no submission is consistent with the live contract. The
repair turns are part of the decision stage and are re-sampled with it.

**What is not held fixed**, and a reader must not forget: tool *behaviour* is today's code, not
the recorded run's (the tool definitions shown are the recorded ones; `tool_drift` names any
whose live registration differs); a decision that calls a tool again sees a fresh attempt
workspace, not the recorded one's scratch state; and a replayed decision sits on an
investigation shaped by the old contract, so it measures the decision and never an
investigation a new contract would have caused.

**What a condition may change** is exactly one of: a prompt substring, the tool schema (field
order, required-ness, descriptions), a closing instruction appended before the decision, or the
abstention contract. The null condition changes nothing, and its disagreement with the recorded
decision is the noise floor every other condition is read against.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes

SUBMIT_TOOL = "submit_candidates"
NULL_CONDITION = "null"


class ReplayRefused(ValueError):
    """A session or condition that cannot be replayed as asked, refused before any spend."""


# --- the condition -------------------------------------------------------------------------


class PromptReplacement(BaseModel):
    """Replace one exact substring of the recorded system prompt or user prompt."""

    model_config = ConfigDict(extra="forbid")

    #: `system` is the system node; `user` is the first user node, which is the arm's prompt.
    node: Literal["system", "user"]
    #: Must occur exactly once in that node's text. A substring that is absent means the
    #: condition was written against a different prompt; one that repeats means it is ambiguous.
    old: str = Field(min_length=1)
    new: str


class ToolSchemaEdit(BaseModel):
    """One change to a recorded tool's JSON schema."""

    model_config = ConfigDict(extra="forbid")

    tool: str = SUBMIT_TOOL
    #: `/`-separated path from the tool's `parameters` to the object schema edited. `""` is the
    #: call's own arguments (`candidates`, `abstention_reason`, `abstention_detail`);
    #: `properties/candidates/items` is one candidate -- the definitions the scaffold lists
    #: come from fastmcp with `$defs` already inlined, so the path is the one the model sees.
    at: str = ""
    #: Properties to put first, in this order; the rest follow in their recorded order.
    property_order: Optional[List[str]] = None
    #: Replaces the schema's `required` list.
    required: Optional[List[str]] = None
    descriptions: Dict[str, str] = Field(default_factory=dict)


class ReplayCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    #: Goes into the run name, which the replay refuses to launch without.
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    prompt_replacements: List[PromptReplacement] = Field(default_factory=list)
    tool_schema_edits: List[ToolSchemaEdit] = Field(default_factory=list)
    #: A user message appended after the last tool result, before the model decides.
    closing_instruction: Optional[str] = None
    #: The abstention contract: stamped on the task payload the way `forbid_abstention` is on a
    #: generation run, when set.
    forbid_abstention: Optional[bool] = None

    @property
    def changes_nothing(self) -> bool:
        return not (self.prompt_replacements or self.tool_schema_edits
                    or self.closing_instruction or self.forbid_abstention is not None)

    def sha256(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    def assert_named_honestly(self) -> None:
        """`null` changes nothing, and nothing else is allowed to.

        A null replay that changed something would be read as the noise floor; a condition
        that changes nothing under another name would be read as an effect of no change.
        """

        if (self.name == NULL_CONDITION) != self.changes_nothing:
            raise ReplayRefused(
                f"condition {self.name!r} "
                + ("is named null but changes something" if self.name == NULL_CONDITION
                   else "changes nothing; name it `null`, which is what it is"))


class DecisionReplaySpec(BaseModel):
    """What a replay task starts from. Carried in the task data, so inside the task's identity."""

    model_config = ConfigDict(extra="forbid")

    source_run: str
    source_invocation_id: str
    source_session: str
    source_session_sha256: str
    #: The condition-applied prefix, written by the pipeline and verified by the task.
    prefix_path: str
    prefix_sha256: str
    #: Index, in the source session, of the assistant node that made the first submission.
    decision_node_index: int
    prefix_assistant_turns: int
    condition: str
    condition_sha256: str
    #: `tool name -> tool_definition_sha256` as recorded, before any condition. The task
    #: compares today's registration against it and records the difference as `tool_drift`.
    recorded_tool_sha256: Dict[str, str]


# --- sessions ------------------------------------------------------------------------------


def tool_definition_sha256(tool: Dict[str, Any]) -> str:
    """Order-preserving, unlike `canonical_json_bytes`: property order is part of what the model
    is shown, and it is the one thing a field-order condition changes."""

    return sha256_bytes(json.dumps(tool, ensure_ascii=False, separators=(",", ":")).encode())


def prefix_bytes(rows: List[Dict[str, Any]]) -> bytes:
    """A prefix file, one node per line, in the session file's own encoding.

    Not `jsonl_bytes`: it sorts keys, which would reorder every tool schema's properties -- so
    the null replay would not show the model what it was shown, and a field-order condition
    would be erased on write. Read back with `io.jsonl_rows`, which preserves order.
    """

    return b"".join(json.dumps(row, ensure_ascii=False).encode("utf-8") + b"\n" for row in rows)


def _blocks(node: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
    message = node.get("message") or {}
    return [block for block in (message.get("content") or [])
            if isinstance(block, dict) and block.get("type") == kind]


def decision_index(nodes: List[Dict[str, Any]]) -> Optional[int]:
    """The assistant node that made the session's first `submit_candidates` call."""

    for index, node in enumerate(nodes):
        if node.get("type") == "assistant" and any(
                block.get("name") == SUBMIT_TOOL for block in _blocks(node, "tool_use")):
            return index
    return None


def decision_prefix(nodes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Everything before the first submission, refused unless every tool call was answered.

    The conversation manager would otherwise drop an unanswered trailing call on resume, and
    the replay would silently start from an earlier point than the one it reports.
    """

    index = decision_index(nodes)
    if index is None:
        raise ReplayRefused(f"the session never called {SUBMIT_TOOL}")
    prefix = nodes[:index]
    pending = set()
    for node in prefix:
        pending.update(block.get("id") for block in _blocks(node, "tool_use"))
        pending.difference_update(block.get("tool_use_id")
                                  for block in _blocks(node, "tool_result"))
    if pending:
        raise ReplayRefused(f"the prefix ends with unanswered tool calls {sorted(pending)}")
    return copy.deepcopy(prefix), index


def _replace_once(rows: List[Dict[str, Any]], replacement: PromptReplacement) -> None:
    target = next((row for row in rows if row.get("type") == replacement.node
                   and _blocks(row, "text")), None)
    if target is None:
        raise ReplayRefused(f"the prefix has no {replacement.node} prompt to edit")
    blocks = _blocks(target, "text")
    count = sum((block.get("text") or "").count(replacement.old) for block in blocks)
    if count != 1:
        raise ReplayRefused(
            f"{replacement.node} prompt contains {replacement.old[:60]!r} {count} times; "
            "a replacement must match exactly once")
    for block in blocks:
        if replacement.old in (block.get("text") or ""):
            block["text"] = block["text"].replace(replacement.old, replacement.new)


def _edit_tool_schema(tools: List[Dict[str, Any]], edit: ToolSchemaEdit) -> None:
    tool = next((item for item in tools
                 if (item.get("function") or {}).get("name") == edit.tool), None)
    if tool is None:
        raise ReplayRefused(f"no recorded tool named {edit.tool!r}")
    schema = tool["function"].get("parameters") or {}
    for segment in [part for part in edit.at.split("/") if part]:
        if not isinstance(schema, dict) or segment not in schema:
            raise ReplayRefused(f"{edit.tool} schema has no {edit.at!r}")
        schema = schema[segment]
    properties = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(properties, dict):
        raise ReplayRefused(f"{edit.tool} schema at {edit.at!r} is not an object schema")

    def known(names, what):
        unknown = [name for name in names if name not in properties]
        if unknown:
            raise ReplayRefused(f"{what} names properties {edit.tool} does not have: {unknown}")

    if edit.property_order is not None:
        known(edit.property_order, "property_order")
        if len(set(edit.property_order)) != len(edit.property_order):
            raise ReplayRefused("property_order repeats a property")
        ordered = {name: properties[name] for name in edit.property_order}
        ordered.update((name, value) for name, value in properties.items()
                       if name not in ordered)
        schema["properties"] = properties = ordered
    if edit.required is not None:
        known(edit.required, "required")
        schema["required"] = list(edit.required)
    known(edit.descriptions, "descriptions")
    for name, text in edit.descriptions.items():
        properties[name]["description"] = text


def _user_text_node(after: Dict[str, Any], text: str) -> Dict[str, Any]:
    """A user message built by the session model itself, so it validates on load."""

    from ape.llm_clients.models import ContentBlock, ConversationMessage, ConversationNode

    return ConversationNode(
        parentUuid=after.get("uuid"), cwd=after.get("cwd"), sessionId=after["sessionId"],
        type="user",
        message=ConversationMessage(role="user", content=[ContentBlock.text_block(text)]),
    ).model_dump(mode="json")


def apply_condition(prefix: List[Dict[str, Any]],
                    condition: ReplayCondition) -> List[Dict[str, Any]]:
    """The prefix a replay starts from. Refuses rather than applying a condition partially."""

    condition.assert_named_honestly()
    rows = copy.deepcopy(prefix)
    for replacement in condition.prompt_replacements:
        _replace_once(rows, replacement)
    if condition.tool_schema_edits:
        definitions = next((row for row in rows if row.get("type") == "tool_definitions"), None)
        if definitions is None:
            raise ReplayRefused("the prefix records no tool definitions to edit")
        for edit in condition.tool_schema_edits:
            _edit_tool_schema(definitions["message"]["tools"], edit)
    if condition.closing_instruction:
        rows.append(_user_text_node(rows[-1], condition.closing_instruction))
    return rows


def recorded_tools(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    definitions = next((row for row in rows if row.get("type") == "tool_definitions"), None)
    return list((definitions or {}).get("message", {}).get("tools") or [])


# --- what was decided ----------------------------------------------------------------------


def submission_summary(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """One `submit_candidates` call, reduced to the levels a replay is compared at.

    `argument_order` and `candidate_field_order` are the model's emission order, read off the
    call arguments -- a field-order condition is only effective if the model follows it, and
    the accepted result cannot say, because validation re-serialises it in schema order.
    """

    candidates = [item for item in (arguments.get("candidates") or []) if isinstance(item, dict)]
    return {
        "filed": bool(candidates),
        "abstention_reason": None if candidates else arguments.get("abstention_reason"),
        "anchors": sorted({str(item.get("primary_change_id")) for item in candidates}),
        "candidate_keys": sorted({
            "|".join(str(item.get(key)) for key in
                     ("primary_change_id", "concern_family", "issue_kind"))
            for item in candidates}),
        "model_confidence": [item.get("model_confidence") for item in candidates],
        "argument_order": list(arguments),
        "candidate_field_order": [list(item) for item in candidates],
    }


def accepted_summary(result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The submission the task accepted, from its result. None when nothing was accepted."""

    if not result or not result.get("success"):
        return None
    candidates = result.get("candidates") or []
    summary = submission_summary({
        "candidates": candidates,
        "abstention_reason": (result.get("abstention") or {}).get("reason"),
    })
    for key in ("argument_order", "candidate_field_order"):
        summary.pop(key)
    return summary


def decision_record(nodes: List[Dict[str, Any]], start: int) -> Dict[str, Any]:
    """Every submission from `start` on, whether it was accepted, and what was said when not.

    Tool output is read from `result_content`; a transcript's `tool_result.content` is always
    null (`.claude/rules/mathlib-review.md`).
    """

    results: Dict[str, Any] = {}
    for node in nodes[start:]:
        for block in _blocks(node, "tool_result"):
            results[block.get("tool_use_id")] = block.get("result_content")
    calls = []
    for node in nodes[start:]:
        if node.get("type") != "assistant":
            continue
        for block in _blocks(node, "tool_use"):
            if block.get("name") != SUBMIT_TOOL:
                continue
            outcome: Dict[str, Any] = {}
            try:
                outcome = (json.loads(results.get(block.get("id")) or "{}")
                           .get("evaluation_result") or {})
            except (TypeError, ValueError, AttributeError):
                pass
            calls.append({
                "arguments": block.get("input") or {},
                "accepted": outcome.get("success"),
                "message": outcome.get("message"),
            })
    return {
        "turns": sum(1 for node in nodes[start:] if node.get("type") == "assistant"),
        "submissions": len(calls),
        "refusals": [call["message"] for call in calls if call["accepted"] is False],
        "first": submission_summary(calls[0]["arguments"]) if calls else None,
    }
