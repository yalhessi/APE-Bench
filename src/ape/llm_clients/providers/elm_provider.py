"""Edinburgh ELM provider.

ELM (https://elm.edina.ac.uk) is the University of Edinburgh's OpenAI-compatible gateway. It
fronts both the OpenAI suite and a set of locally hosted open-weight models behind one key,
speaking plain `/v1/chat/completions` with `Authorization: Bearer`.

Measured against the live endpoint on 2026-09-22, so the payload needs no adjusting:

* `max_completion_tokens` is accepted by every model, and `max_tokens` is *rejected* by the
  OpenAI ones ("not supported with this model"). `OpenAIProvider` already sends the former.
* `stream_options: {"include_usage": true}` is honoured by every model, and streamed
  responses carry a `usage` block -- so billed cost stays real rather than silently zero.
* `temperature` other than 1.0 is accepted.
* `prompt_tokens_details` comes back `null` for the locally hosted models. `parse_usage`
  already treats that as "no cache accounting" rather than crashing.

Two real differences, both properties of how ELM runs each backend rather than of the wire
format, both recorded per model in `MODEL_MAPPINGS`:

* tool calling -- see `supports_tools`;
* reasoning -- see `reasoning_efforts` and `LLMConfig.reasoning_effort`. `elm_qwen_3.5`
  reasons by default and `elm_mistral_small_4` does not, so there is no single "ELM
  default", and the difference is ~100x in completion tokens (4 against 451 on one
  arithmetic prompt) and ~23x in latency (0.5s against 11.5s). A token ceiling calibrated
  under one setting means nothing under the other.

The parameter is `reasoning_effort`. A payload carrying `reasoning: null` returns HTTP 200,
leaves reasoning ON and reports nothing -- measured, not assumed.
"""

import json
from typing import Any, Dict, List, Optional

from ..config import MODEL_MAPPINGS, ProviderError
from .openai_provider import OpenAIProvider


#: Sentinel: distinguishes "leave this argument alone" from a repair that yields None.
_UNREPAIRED = object()


class ElmProvider(OpenAIProvider):
    """OpenAI Chat Completions against the ELM gateway."""

    #: Deliberately a class constant and not an environment variable. The endpoint changes
    #: what a run does, and `llm_config.base_url` is inside `scaffold_config_sha256` while an
    #: environment variable is inside nothing -- an invisible knob that redirects a run is
    #: exactly what the run plan exists to prevent. Override per run with `llm_config.base_url`.
    DEFAULT_BASE_URL = "https://elm.edina.ac.uk/api/v1/chat/completions"

    #: Master switch for the argument repair below. Flip to False to see the raw behaviour,
    #: or delete the block it guards once the gateway enforces tool schemas.
    REPAIR_STRINGIFIED_ARGUMENTS = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #: Schemas from the most recent request, so the repair below is schema-driven rather
        #: than a guess. Populated by `build_request_payload`, read by `postprocess_nodes`.
        self._tool_parameter_schemas: Dict[str, Dict[str, Any]] = {}
        #: How many arguments this provider has repaired. The number that says whether the
        #: workaround is still needed.
        self.repaired_argument_count = 0

    def build_request_payload(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """The OpenAI payload, refusing tools a backend cannot serve.

        ELM runs the open-weight models on a vLLM server started without
        `--enable-auto-tool-choice`, so passing `tools` to Llama 3.3 or EuroLLM returns a
        raw 400 (`"auto" tool choice requires --enable-auto-tool-choice ... to be set`) on
        the first call of every task. That is a fixed property of the deployment, recorded
        per model in `MODEL_MAPPINGS`, so it can be named here instead of being discovered
        once per run as a vLLM error message.
        """

        if tools and not self.supports_tools():
            raise ProviderError(
                f"{self.config.formal_model_name} is served by ELM without tool-calling "
                f"enabled, but {len(tools)} tool(s) were supplied. Agentic scaffolds need "
                f"tools: use a tool-capable model (the OpenAI models, or "
                f"Qwen/Qwen3.5-397B-A17B-FP8), or run a scaffold that sends none."
            )
        self._assert_reasoning_effort_is_real()
        self._remember_tool_schemas(tools)
        return super().build_request_payload(messages, tools=tools, stream=stream)

    def _assert_reasoning_effort_is_real(self) -> None:
        """Refuse an effort this model does not honour, before the first call.

        Two different wrong outcomes to head off, both measured 2026-09-22. `low` and
        `medium` are a raw 400 from the models that reason (`Unsupported reasoning effort
        'low' for model ...`), once per task, discovered on the first call of every run. And
        on the models that do NOT reason, every value returns 200 and changes nothing -- a
        knob the run plan records, the operator believes, and the endpoint ignores.

        A model with no measured row passes through unchecked: an untested model cannot be
        asserted to lack a reasoning mode, and refusing one would break every new model name.
        """

        effort = self.config.reasoning_effort
        if effort is None:
            return
        for entry in MODEL_MAPPINGS.values():
            if entry["model_name"] != self.config.formal_model_name:
                continue
            if "reasoning_efforts" not in entry:
                return
            supported = entry["reasoning_efforts"]
            if effort in supported:
                return
            raise ProviderError(
                f"reasoning_effort={effort!r} is not honoured by "
                f"{self.config.formal_model_name}: "
                + (f"ELM accepts only {sorted(supported)} for it."
                   if supported else
                   "it has no reasoning mode at all, and the gateway accepts every effort "
                   "value for it while changing nothing.")
                + " Measured on the live endpoint; re-measure before trusting it, since it "
                  "is a deployment setting ELM can change without notice."
            )
        return

    def supports_tools(self) -> bool:
        """Whether this model's ELM backend serves tool calls. Unknown models are assumed to."""

        for entry in MODEL_MAPPINGS.values():
            if entry["model_name"] == self.config.formal_model_name:
                return entry.get("supports_tools", True)
        return True

    # ======================================================================================
    # WORKAROUND: stringified tool arguments. Self-contained, and meant to be deleted.
    #
    # Measured 2026-09-22 against the live gateway, one tool, 8 trials, only `tool_choice`
    # varied:
    #
    #     tool_choice=auto      Qwen 0/8 schema-conformant, 6/8 stringified   gpt-5-mini 8/8
    #     tool_choice=required  Qwen 7/8                                      gpt-5-mini 8/8
    #     tool_choice=<named>   Qwen 8/8                                      gpt-5-mini 8/8
    #
    # vLLM applies guided decoding against a tool's JSON Schema only when a call is
    # compelled. Under `auto` -- which is what an agent sends -- nothing enforces the schema,
    # and the model writes the *text* of a list where an array is declared. This is an
    # enforcement gap in the serving stack, not a comprehension gap in the model: the same
    # model emits a conformant call the instant the constraint is applied.
    #
    # It is not a schema-quality problem, which was checked separately: typing `items` and
    # replacing Python `None` with JSON `null` in the description left it at 0/8 under
    # `auto`. Only removing the nesting (5/8) or compelling the call (7/8) helped.
    #
    # On one real run it was 64 of 79 tool-call failures; without them Qwen's failure rate is
    # 15/155, the same 10% gpt_5.2 shows on the same PR set.
    #
    # THE REAL FIXES, neither of which this is:
    #   * EDINA enabling guided decoding for tool calls under `auto` (asked for separately);
    #   * flattening nested tool parameters, done for `file_read` in the same commit.
    # `tool_choice: "required"` would also work and is deliberately NOT used here: it would
    # forbid a tool-free assistant turn for every model and stage, which is a larger and
    # longer-lived commitment than this.
    #
    # DELETE THIS BLOCK when the gateway enforces schemas. `repaired_argument_count` is how
    # you tell: when it stays 0 across a run, nothing here is load-bearing any more.
    # ======================================================================================

    def _remember_tool_schemas(self, tools: Optional[List[Dict[str, Any]]]) -> None:
        """Index this request's declared parameter schemas by tool name."""

        if not self.REPAIR_STRINGIFIED_ARGUMENTS or not tools:
            return
        for tool in tools:
            function = tool.get("function") or {}
            name = function.get("name")
            properties = (function.get("parameters") or {}).get("properties")
            if name and isinstance(properties, dict):
                self._tool_parameter_schemas[name] = properties

    @staticmethod
    def _declared_types(schema: Dict[str, Any]) -> set:
        """Every JSON type a parameter may take, flattening `anyOf`/`oneOf`."""

        types = set()
        declared = schema.get("type")
        if isinstance(declared, str):
            types.add(declared)
        elif isinstance(declared, list):
            types.update(t for t in declared if isinstance(t, str))
        for branch in (schema.get("anyOf") or []) + (schema.get("oneOf") or []):
            if isinstance(branch, dict):
                types |= ElmProvider._declared_types(branch)
        return types

    def postprocess_nodes(self, nodes: List):
        """Repair arguments the gateway let through unvalidated.

        Conservative by construction: a value is rewritten only when the schema says it is
        NOT a string, the model sent a string, and that string parses as JSON to exactly a
        type the schema allows. A parameter that may legitimately be a string is never
        touched, so a regex like `"[a-z]+"` or a Lean snippet is safe even if it happens to
        parse.
        """

        nodes = super().postprocess_nodes(nodes)
        if not self.REPAIR_STRINGIFIED_ARGUMENTS or not self._tool_parameter_schemas:
            return nodes

        for node in nodes:
            for block in getattr(getattr(node, "message", None), "content", None) or []:
                if getattr(block, "type", None) != "tool_use":
                    continue
                properties = self._tool_parameter_schemas.get(block.name)
                if not properties or not isinstance(block.input, dict):
                    continue
                for key, value in list(block.input.items()):
                    repaired = self._repair_value(properties.get(key), value)
                    if repaired is not _UNREPAIRED:
                        block.input[key] = repaired
                        self.repaired_argument_count += 1
                        self.logger.warning(
                            "repaired stringified argument %s.%s: %r -> %r "
                            "(the gateway does not enforce tool schemas under tool_choice=auto)",
                            block.name, key, value, repaired)
        return nodes

    def _repair_value(self, schema: Optional[Dict[str, Any]], value: Any) -> Any:
        """The repaired value, or `_UNREPAIRED` to leave it exactly as it arrived."""

        if not isinstance(schema, dict) or not isinstance(value, str):
            return _UNREPAIRED
        allowed = self._declared_types(schema)
        # A parameter that may be a string is ambiguous: leave it alone.
        if not allowed or "string" in allowed:
            return _UNREPAIRED
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            return _UNREPAIRED
        actual = {list: "array", dict: "object", bool: "boolean",
                  int: "integer", float: "number", type(None): "null"}.get(type(parsed))
        if actual is None or actual not in allowed:
            # `integer` also satisfies a `number` declaration.
            if not (actual == "integer" and "number" in allowed):
                return _UNREPAIRED
        return parsed
