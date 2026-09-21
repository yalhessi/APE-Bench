"""Session replay: run any recorded task again from a point inside its conversation.

A replay is not a kind of task. It is the same task -- same task type, same payload, same tools
executing, same submission contract -- whose conversation starts from a recorded prefix instead
of from its prompt. So it travels the way `execution_limits` does: a reserved task-data key,
`session_replay`, read at the runtime boundary (`scaffolds/runner.py::main_from_params`) and
honoured by this scaffold's conversation manager. Its results are ordinary results of the
replayed task type, so everything that reads that task type reads a replay unchanged.

Where a replay takes over is a parameter, never a policy in the code: `CutPoint` names any
point in the recording -- an assistant turn counted from either end, a raw node index, or
wherever a tool was called. A family supplies only what is specific to it: which recorded
attempts to replay, and how to read what came out.

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
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ToolCallCut(BaseModel):
    """A cut located by a tool call rather than by counting turns."""

    model_config = ConfigDict(extra="forbid")

    tool: str
    #: `first`, `last`, or a 1-based ordinal among this session's calls to the tool.
    occurrence: Union[Literal["first", "last"], int] = "first"


class CutPoint(BaseModel):
    """Where a replay takes over the conversation. Exactly one of the three spellings.

    Nothing about a cut is predetermined: a replay continues from any point in the recording.
    The three spellings answer the three ways one wants to say it.

    * `before_turn: k` -- the model regenerates assistant turn `k` onward, numbered as
      `record_turn` numbers them (1 = the first). Negative counts from the end, so `-1` is the
      last turn the recording took. `before_turn: 1` replays the whole task from its recorded
      prompt.
    * `at_node: i` -- the raw node index, for a cut a turn number cannot express. Negative
      counts from the end.
    * `before_tool_call: {tool, occurrence}` -- wherever the session first (or last, or nth)
      called a tool, which is how one names a decision without knowing which turn made it.

    A cut is refused rather than nudged if it lands inside a turn -- with tool calls whose
    results the prefix does not contain -- because the conversation manager drops an
    unanswered trailing call on resume, and the replay would then silently start earlier than
    the point it reports. That is why `at_node` is the last resort: one node index is not
    turn-aligned across recordings, and `at_node: 7` was mid-turn in 232 of 320 real arm
    sessions (3 more were shorter than 7 nodes), while `before_turn` and `before_tool_call`
    resolve in every session that is long enough.
    """

    model_config = ConfigDict(extra="forbid")

    #: Names the cut in run names, prefix files and outcome rows. Derived when absent.
    label: Optional[str] = Field(default=None, pattern=r"^[a-z0-9][a-z0-9_]*$")
    at_node: Optional[int] = None
    before_turn: Optional[int] = None
    before_tool_call: Optional[ToolCallCut] = None

    @model_validator(mode="after")
    def _exactly_one_spelling(self) -> "CutPoint":
        given = [name for name in ("at_node", "before_turn", "before_tool_call")
                 if getattr(self, name) is not None]
        if len(given) != 1:
            raise ValueError(
                "a cut is exactly one of at_node, before_turn, before_tool_call; "
                f"got {given or 'none'}")
        if self.before_turn == 0:
            raise ValueError("before_turn counts from 1 (and -1 is the last turn); 0 is not a turn")
        return self

    @property
    def name(self) -> str:
        if self.label:
            return self.label
        if self.at_node is not None:
            return f"node{self.at_node}" if self.at_node >= 0 else f"node_back{-self.at_node}"
        if self.before_turn is not None:
            return (f"turn{self.before_turn}" if self.before_turn > 0
                    else "last_turn" if self.before_turn == -1
                    else f"turn_back{-self.before_turn}")
        occurrence = self.before_tool_call.occurrence
        return f"{occurrence}_{self.before_tool_call.tool}" if isinstance(occurrence, str) \
            else f"{self.before_tool_call.tool}_{occurrence}"

    def resolve(self, nodes: List[Dict[str, Any]]) -> int:
        """The node index this cut means in one session, or `ReplayRefused`."""

        if self.at_node is not None:
            index = self.at_node if self.at_node >= 0 else len(nodes) + self.at_node
            if not 0 <= index <= len(nodes):
                raise ReplayRefused(
                    f"at_node {self.at_node} is outside a session of {len(nodes)} nodes")
            return index
        turns = [i for i, node in enumerate(nodes) if node.get("type") == "assistant"]
        if self.before_turn is not None:
            ordinal = self.before_turn - 1 if self.before_turn > 0 else self.before_turn
            try:
                return turns[ordinal]
            except IndexError:
                raise ReplayRefused(
                    f"before_turn {self.before_turn} needs more than the {len(turns)} "
                    "assistant turn(s) this session took") from None
        cut = self.before_tool_call
        calls = [i for i in turns
                 if any(block.get("name") == cut.tool for block in _blocks(nodes[i], "tool_use"))]
        if not calls:
            raise ReplayRefused(f"the session never called {cut.tool}")
        if cut.occurrence == "first":
            return calls[0]
        if cut.occurrence == "last":
            return calls[-1]
        try:
            return calls[cut.occurrence - 1]
        except IndexError:
            raise ReplayRefused(
                f"the session called {cut.tool} {len(calls)} time(s), "
                f"so occurrence {cut.occurrence} does not exist") from None


def parse_cut(text: str) -> CutPoint:
    """One command-line token as a cut: `turn=-1`, `node=7`, `tool=submit_candidates[:last|:N]`.

    A flag rather than a config override because overrides deep-*merge*: `--set dataset.cut=`
    leaves the config's spelling in place beside the new one, and a cut carrying two spellings
    is refused. A flag replaces the cut outright, which is what anyone typing it means.
    """

    kind, _, value = text.partition("=")
    if not value:
        raise ReplayRefused(
            f"a cut is `turn=<n>`, `node=<i>` or `tool=<name>[:first|:last|:<n>]`, not {text!r}")
    if kind == "turn":
        return CutPoint(before_turn=int(value))
    if kind == "node":
        return CutPoint(at_node=int(value))
    if kind == "tool":
        tool, _, occurrence = value.partition(":")
        if occurrence.isdigit():
            return CutPoint(before_tool_call=ToolCallCut(tool=tool, occurrence=int(occurrence)))
        return CutPoint(before_tool_call=ToolCallCut(
            tool=tool, occurrence=occurrence or "first"))
    raise ReplayRefused(f"unknown cut kind {kind!r}; expected turn, node or tool")


def cut_at_node(nodes: List[Dict[str, Any]],
                index: int) -> Tuple[List[Dict[str, Any]], int]:
    """`(prefix, index)`: the conversation up to `index`, refused if it is mid-turn.

    Every tool call in the prefix must have its result, or the manager would drop the trailing
    assistant node on resume and the replay would start before the point it reports.
    """

    prefix = nodes[:index]
    pending = set()
    for node in prefix:
        pending.update(block.get("id") for block in _blocks(node, "tool_use"))
        pending.difference_update(block.get("tool_use_id")
                                  for block in _blocks(node, "tool_result"))
    if pending:
        raise ReplayRefused(
            f"a cut at node {index} lands inside a turn: {len(pending)} tool call(s) have no "
            f"result in the prefix ({sorted(pending)[:3]})")
    return copy.deepcopy(prefix), index


def cut(nodes: List[Dict[str, Any]], point: CutPoint) -> Tuple[List[Dict[str, Any]], int]:
    """`(prefix, index)` for one cut point in one session."""

    return cut_at_node(nodes, point.resolve(nodes))


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
