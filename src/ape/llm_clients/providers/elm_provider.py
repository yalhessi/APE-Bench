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

The one real difference is tool calling, which is a property of how ELM runs each backend
rather than of the wire format -- see `supports_tools` in `MODEL_MAPPINGS`.
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
        return super().build_request_payload(messages, tools=tools, stream=stream)

    def supports_tools(self) -> bool:
        """Whether this model's ELM backend serves tool calls. Unknown models are assumed to."""

        for entry in MODEL_MAPPINGS.values():
            if entry["model_name"] == self.config.formal_model_name:
                return entry.get("supports_tools", True)
        return True
