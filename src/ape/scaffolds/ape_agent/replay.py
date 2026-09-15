"""Session replay: run any recorded task again from a point inside its conversation.

A replay is not a kind of task. It is the same task -- same task type, same payload, same tools
executing, same submission contract -- whose conversation starts from a recorded prefix instead
of from its prompt. So it travels the way `execution_limits` does: a reserved task-data key,
`session_replay`, read at the runtime boundary (`scaffolds/runner.py::main_from_params`) and
honoured by this scaffold's conversation manager. Its results are ordinary results of the
replayed task type, so everything that reads that task type reads a replay unchanged.

What a family supplies is only what is specific to it: which recorded attempts to replay, and
where to cut. `cut_before_tool_call` covers the common case -- a review arm's first
`submit_candidates`, a proof task's `submit_result`.

**What is held fixed.** Everything before the cut is replayed as recorded. The OpenAI provider
here is stateless Chat Completions, so a session file is exactly the messages the model was
sent. The model is shown the *recorded* tool definitions, with at most the change a condition
makes; calls still execute against today's registration, and any registered tool whose
definition differs from the recording is written down as `tool_drift`.

**What is not.** Tool behaviour is today's code. A call made after the cut sees a fresh attempt
workspace, not the recorded one's scratch state. And the recorded prefix was shaped by the old
contract, so a replay measures what is decided from it, never an investigation a changed
contract would have caused.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

#: The task-data key a replay travels under. Absent on every task that is not a replay.
SESSION_REPLAY_KEY = "session_replay"
#: Written beside the session file in a replayed attempt: what it started from, what drifted.
REPLAY_RECORD_FILENAME = "session_replay.json"
NULL_CONDITION = "null"


class ReplayRefused(ValueError):
    """A session or condition that cannot be replayed as asked, refused before any spend."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# --- the directive -------------------------------------------------------------------------


class SessionReplay(BaseModel):
    """Start this task's conversation from a sealed prefix file."""

    model_config = ConfigDict(extra="forbid")

    prefix_path: str
    prefix_sha256: str
    #: `tool name -> tool_definition_sha256` as recorded, before any condition, so today's
    #: registration can be compared with what the recorded session was produced under.
    recorded_tool_sha256: Dict[str, str]
    #: Where the prefix came from: run, attempt, session file and its hash, cut point, condition.
    #: Provenance for readers; nothing in the replay path acts on it.
    source: Dict[str, Any] = Field(default_factory=dict)


def load_prefix(replay: SessionReplay) -> List[Dict[str, Any]]:
    """The prefix nodes, refused if the file is not the one the directive names.

    Read by splitting on "\\n" only: session text keeps U+2028 and friends verbatim, and
    `splitlines()` cuts a record in half on them.
    """

    content = Path(replay.prefix_path).read_bytes()
    if _sha256(content) != replay.prefix_sha256:
        raise ReplayRefused(
            f"replay prefix {replay.prefix_path} does not match its recorded sha256; the "
            "replay would start from a conversation other than the one it names")
    return [json.loads(line) for line in content.decode("utf-8").split("\n") if line.strip()]


# --- the condition -------------------------------------------------------------------------


class PromptReplacement(BaseModel):
    """Replace one exact substring of the recorded system prompt or first user prompt."""

    model_config = ConfigDict(extra="forbid")

    node: Literal["system", "user"]
    #: Must occur exactly once. Absent means the condition was written against another prompt;
    #: repeated means it is ambiguous.
    old: str = Field(min_length=1)
    new: str


class ToolSchemaEdit(BaseModel):
    """One change to a recorded tool's JSON schema, as the model is shown it."""

    model_config = ConfigDict(extra="forbid")

    tool: str
    #: `/`-separated path from the tool's `parameters` to the object schema edited; `""` is the
    #: call's own arguments. fastmcp inlines `$defs`, so a nested model is reached through
    #: `properties/<field>/items` or `properties/<field>` -- the path the model sees.
    at: str = ""
    #: Properties to put first, in this order; the rest follow in their recorded order.
    property_order: Optional[List[str]] = None
    #: Replaces the schema's `required` list.
    required: Optional[List[str]] = None
    descriptions: Dict[str, str] = Field(default_factory=dict)


class ReplayCondition(BaseModel):
    """Exactly what a replay changes. `null` changes nothing and is the noise floor."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    prompt_replacements: List[PromptReplacement] = Field(default_factory=list)
    tool_schema_edits: List[ToolSchemaEdit] = Field(default_factory=list)
    #: A user message appended after the last recorded node, before the model takes over.
    closing_instruction: Optional[str] = None
    #: Merged into the task payload: a change to the task's own contract rather than to what
    #: the model is shown (a review arm's `forbid_abstention`, say).
    task_data_overrides: Dict[str, Any] = Field(default_factory=dict)

    @property
    def changes_nothing(self) -> bool:
        return not (self.prompt_replacements or self.tool_schema_edits
                    or self.closing_instruction or self.task_data_overrides)

    def sha256(self) -> str:
        return _sha256(json.dumps(self.model_dump(mode="json"), sort_keys=True,
                                  ensure_ascii=False).encode())

    def assert_named_honestly(self) -> None:
        """`null` changes nothing, and nothing else may.

        A null replay that changed something would be read as the noise floor; a condition
        that changes nothing under another name would be read as the effect of a change.
        """

        if (self.name == NULL_CONDITION) != self.changes_nothing:
            raise ReplayRefused(
                f"condition {self.name!r} "
                + ("is named null but changes something" if self.name == NULL_CONDITION
                   else "changes nothing; name it `null`, which is what it is"))


# --- sessions ------------------------------------------------------------------------------


def tool_definition_sha256(tool: Dict[str, Any]) -> str:
    """Order-preserving: property order is part of what the model is shown, and it is the one
    thing a field-order condition changes."""

    return _sha256(json.dumps(tool, ensure_ascii=False, separators=(",", ":")).encode())


def prefix_bytes(rows: List[Dict[str, Any]]) -> bytes:
    """A prefix file in the session file's own encoding, one node per line.

    Never with sorted keys: that would reorder every tool schema's properties, so the null
    replay would not show the model what it was shown and a field-order condition would be
    erased on write.
    """

    return b"".join(json.dumps(row, ensure_ascii=False).encode("utf-8") + b"\n" for row in rows)


def _blocks(node: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
    content = (node.get("message") or {}).get("content") or []
    return [block for block in content if isinstance(block, dict) and block.get("type") == kind]


def recorded_tools(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    definitions = next((row for row in rows if row.get("type") == "tool_definitions"), None)
    return list(((definitions or {}).get("message") or {}).get("tools") or [])


def cut_before_tool_call(nodes: List[Dict[str, Any]],
                         tool_name: str) -> Tuple[List[Dict[str, Any]], int]:
    """`(prefix, index)`: everything before the first assistant node that calls `tool_name`.

    The first call, not the last: a task that refuses a submission typically counts refusals
    on its instance, and a replayed instance counts from zero, so only a prefix holding no
    call agrees with the live contract. Refused unless every tool call in the prefix was
    answered -- the manager drops an unanswered trailing call on resume, and the replay would
    silently start earlier than the point it reports.
    """

    index = next((i for i, node in enumerate(nodes) if node.get("type") == "assistant"
                  and any(b.get("name") == tool_name for b in _blocks(node, "tool_use"))), None)
    if index is None:
        raise ReplayRefused(f"the session never called {tool_name}")
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
    target = next((row for row in rows
                   if row.get("type") == replacement.node and _blocks(row, "text")), None)
    if target is None:
        raise ReplayRefused(f"the prefix has no {replacement.node} prompt to edit")
    blocks = _blocks(target, "text")
    count = sum((block.get("text") or "").count(replacement.old) for block in blocks)
    if count != 1:
        raise ReplayRefused(f"{replacement.node} prompt contains {replacement.old[:60]!r} "
                            f"{count} times; a replacement must match exactly once")
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
    """A user message built by the session model itself, so it validates when loaded."""

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


def replay_task_data(task_data: Dict[str, Any], prefix: List[Dict[str, Any]],
                     condition: ReplayCondition, prefix_path: Path,
                     source: Dict[str, Any]) -> Tuple[Dict[str, Any], bytes]:
    """`(payload, prefix bytes)`: the recorded task's own payload, started from `prefix`.

    The caller writes the bytes to `prefix_path` (immutably) before the task runs. The task
    type and task id are the recorded ones: this is the same task, run from a later point.
    """

    content = prefix_bytes(apply_condition(prefix, condition))
    replay = SessionReplay(
        prefix_path=str(prefix_path), prefix_sha256=_sha256(content),
        recorded_tool_sha256={tool["function"]["name"]: tool_definition_sha256(tool)
                              for tool in recorded_tools(prefix)},
        source={**source, "condition": condition.name, "condition_sha256": condition.sha256(),
                "prefix_assistant_turns": sum(1 for n in prefix if n.get("type") == "assistant"),
                "prefix_nodes": len(prefix)})
    payload = copy.deepcopy(task_data)
    payload.pop("global_index", None)  # recomputed from content
    payload.update(copy.deepcopy(condition.task_data_overrides))
    payload[SESSION_REPLAY_KEY] = replay.model_dump(mode="json")
    return payload, content


def tool_calls(nodes: List[Dict[str, Any]], start: int, tool_name: str) -> List[Dict[str, Any]]:
    """Every call to `tool_name` from `start` on, with whether its evaluation accepted it.

    Tool output is read from `result_content`; a transcript's `tool_result.content` is always
    null.
    """

    results = {block.get("tool_use_id"): block.get("result_content")
               for node in nodes[start:] for block in _blocks(node, "tool_result")}
    calls = []
    for node in nodes[start:]:
        if node.get("type") != "assistant":
            continue
        for block in _blocks(node, "tool_use"):
            if block.get("name") != tool_name:
                continue
            outcome: Dict[str, Any] = {}
            try:
                outcome = (json.loads(results.get(block.get("id")) or "{}")
                           .get("evaluation_result") or {})
            except (TypeError, ValueError, AttributeError):
                pass
            calls.append({"arguments": block.get("input") or {},
                          "accepted": outcome.get("success"), "message": outcome.get("message")})
    return calls
