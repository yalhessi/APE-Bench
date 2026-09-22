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

from typing import Any, Dict, List, Optional

from ..config import MODEL_MAPPINGS, ProviderError
from .openai_provider import OpenAIProvider


class ElmProvider(OpenAIProvider):
    """OpenAI Chat Completions against the ELM gateway."""

    #: Deliberately a class constant and not an environment variable. The endpoint changes
    #: what a run does, and `llm_config.base_url` is inside `scaffold_config_sha256` while an
    #: environment variable is inside nothing -- an invisible knob that redirects a run is
    #: exactly what the run plan exists to prevent. Override per run with `llm_config.base_url`.
    DEFAULT_BASE_URL = "https://elm.edina.ac.uk/api/v1/chat/completions"

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
