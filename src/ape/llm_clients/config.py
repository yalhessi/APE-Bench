"""
LLM Clients Configuration System.
"""

import os
from typing import Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class LLMProvider(Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    GEMINI = "gemini"
    #: The University of Edinburgh's OpenAI-compatible gateway. A separate provider rather
    #: than an `llm_config.base_url` override on OPENAI, because `V5RunPlan.model_name` is
    #: the field that says which model produced a run: routing `gpt_5.2` through ELM under
    #: its own name would make two runs against different endpoints read identically there.
    ELM = "elm"


#: Which environment variable holds each provider's key, in the order they are tried.
#:
#: A table rather than a chain of `if`s because two callers need to *name* the variable, not
#: just read it: preflight's remedy text, which was previously the unactionable "export the
#: provider's key", and the worker-boundary check that refuses a YAML-supplied key.
#: ELM gets its own variable rather than reusing `OPENAI_API_KEY`, deliberately: both keys
#: are commonly exported in the same shell, and a shared variable means a misconfigured
#: `base_url` silently sends one provider's credential to the other's endpoint.
PROVIDER_KEY_ENV_VARS: Dict[LLMProvider, tuple] = {
    LLMProvider.OPENAI: ("OPENAI_API_KEY",),
    LLMProvider.GEMINI: ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    LLMProvider.ELM: ("ELM_API_KEY",),
}

MODEL_MAPPINGS = {
    "gemini_3_pro": {
        "model_name": "gemini-3-pro-preview-new",
        "provider": LLMProvider.GEMINI,
        "input_per_1M": 2.00,
        "output_per_1M": 12.00,
        "cached_input_per_1M_usd": 0.3125,
        "cache_creation_per_1M_usd": 0.125
    },
    "gemini_3_flash": {
        "model_name": "gemini-3-flash-preview-priority",
        "provider": LLMProvider.GEMINI,
        "input_per_1M": 0.5,
        "output_per_1M": 3.00,
        "cached_input_per_1M_usd": 0.3125,
        "cache_creation_per_1M_usd": 0.125
    },
    "gemini_2.5_pro": {
        "model_name": "gemini-2.5-pro",
        "provider": LLMProvider.GEMINI,
        "input_per_1M": 1.25,
        "output_per_1M": 10.00,
        "cached_input_per_1M_usd": 0.3125,
        "cache_creation_per_1M_usd": 0.125
    },
    "gemini_2.5_pro_preview_03_25": {
        "model_name": "gemini-2.5-pro-preview-03-25",
        "provider": LLMProvider.GEMINI,
        "input_per_1M": 1.25,
        "output_per_1M": 10.00,
        "cached_input_per_1M_usd": 0.3125,
        "cache_creation_per_1M_usd": 0.125
    },
    "gemini_2.5_pro_preview_05_06": {
        "model_name": "gemini-2.5-pro-preview-05-06",
        "provider": LLMProvider.GEMINI,
        "input_per_1M": 1.25,
        "output_per_1M": 10.00,
        "cached_input_per_1M_usd": 0.3125,
        "cache_creation_per_1M_usd": 0.125
    },
    "gemini_2.5_flash": {
        "model_name": "gemini-2.5-flash-preview-04-17",
        "provider": LLMProvider.GEMINI,
        "input_per_1M": 0.30,
        "output_per_1M": 2.50,
        "cached_input_per_1M_usd": 0.075,
        "cache_creation_per_1M_usd": 0.03
    },
    "gpt_5.4": {
        # Bare alias resolves to the latest gpt-5.4 snapshot; swap to a dated id
        # (e.g. "gpt-5.4-YYYY-MM-DD") if the endpoint requires a pinned snapshot.
        "model_name": "gpt-5.4",
        "provider": LLMProvider.OPENAI,
        # PLACEHOLDER pricing copied from gpt-5.2 — update with real gpt-5.4 rates;
        # only affects cost_usd reporting, not model behavior.
        "input_per_1M": 1.75,
        "output_per_1M": 14.00,
        "cached_input_per_1M_usd": 0.125,
        "cache_creation_per_1M_usd": 1.25
    },
    "gpt_5.2": {
        "model_name": "gpt-5.2-2025-12-11",
        "provider": LLMProvider.OPENAI,
        "input_per_1M": 1.75,
        "output_per_1M": 14.00,
        "cached_input_per_1M_usd": 0.125,
        "cache_creation_per_1M_usd": 1.25
    },
    "gpt_5": {
        "model_name": "gpt-5-2025-08-07",
        "provider": LLMProvider.OPENAI,
        "input_per_1M": 1.25,
        "output_per_1M": 10.00,
        "cached_input_per_1M_usd": 0.125,
        "cache_creation_per_1M_usd": 1.25
    },
    "gpt_5_mini": {
        "model_name": "gpt-5-mini-2025-08-07",
        "provider": LLMProvider.OPENAI,
        "input_per_1M": 0.25,
        "output_per_1M": 2.00,
        "cached_input_per_1M_usd": 0.0625,
        "cache_creation_per_1M_usd": None
    },
    "gpt_5_nano": {
        "model_name": "gpt-5-nano-2025-08-07",
        "provider": LLMProvider.OPENAI,
        "input_per_1M": 0.05,
        "output_per_1M": 0.4,
        "cached_input_per_1M_usd": 0.05,
        "cache_creation_per_1M_usd": None
    },

    # ---------------------------------------------------------------------------------
    # Edinburgh ELM gateway (LLMProvider.ELM). Ids verified against
    # GET https://elm.edina.ac.uk/api/v1/models on 2026-09-22.
    #
    # ELM exposes **bare aliases only** -- no dated snapshots -- so these rows differ from
    # their direct-API counterparts in `model_name`, not just `provider`. Sending
    # `gpt-5-mini-2025-08-07` (what `gpt_5_mini` resolves to) would be rejected. Note also
    # that bare `gpt-5` is not offered by ELM at all, so there is no `elm_gpt_5`.
    #
    # `supports_tools` is a property of how ELM runs each backend, not of the model: the
    # open-weight ones are served by vLLM, and two of those servers were started without
    # `--enable-auto-tool-choice`, which makes any request carrying `tools` a 400.
    # `ElmProvider.build_request_payload` turns that into a named error. Measured per model
    # on 2026-09-22; re-measure before trusting it, since it is a deployment setting ELM can
    # change without notice.
    # ---------------------------------------------------------------------------------

    # OpenAI models proxied by ELM. Rates are OpenAI list price, which is the best available
    # estimate of what the institution is billed -- ELM publishes no tariff. They exist to
    # keep the cost caps binding and the preflight estimate honest, not as an invoice.
    "elm_gpt_5.2": {
        "model_name": "gpt-5.2",
        "provider": LLMProvider.ELM,
        "input_per_1M": 1.75,
        "output_per_1M": 14.00,
        "cached_input_per_1M_usd": 0.125,
        "cache_creation_per_1M_usd": 1.25,
        "supports_tools": True,
    },
    "elm_gpt_5.4": {
        "model_name": "gpt-5.4",
        "provider": LLMProvider.ELM,
        # Same PLACEHOLDER rates as `gpt_5.4`; see the note there.
        "input_per_1M": 1.75,
        "output_per_1M": 14.00,
        "cached_input_per_1M_usd": 0.125,
        "cache_creation_per_1M_usd": 1.25,
        "supports_tools": True,
    },
    "elm_gpt_5_mini": {
        "model_name": "gpt-5-mini",
        "provider": LLMProvider.ELM,
        "input_per_1M": 0.25,
        "output_per_1M": 2.00,
        "cached_input_per_1M_usd": 0.0625,
        "cache_creation_per_1M_usd": None,
        "supports_tools": True,
    },

    # Locally hosted open-weight models. These cost the project nothing per token, and the
    # rates below say so. Do not be tempted to put a fictional rate here to make the dollar
    # caps bite: a made-up number in `input_per_1M` is indistinguishable downstream from a
    # real one, and every cost figure this repo reports -- preflight estimates, the budget
    # ledger, `run_total_cost_cap` -- would silently become a mix of money and metaphor.
    #
    # The consequence is real and must be understood before running one of these:
    # `standard_budget_cap`, `lead_cost_cap`, `per_pr_cost_cap` and `run_total_cost_cap` all
    # bind on billed cost, and `ExecutionLimits` carries only `max_turns` and
    # `billed_cost_limit`. At a true rate of zero every dollar cap is vacuous, and a run on
    # these models is bounded by `max_turns` and `max_delegations` alone.
    #
    # The fix is a token-based limit in `ExecutionLimits`, not a price here. Until that
    # exists, size local-model runs with `max_turns`/`max_delegations` and know that the
    # dollar caps are not protecting you. See docs/todo/README.md.
    #
    # `prompt_tokens_details` comes back null from every one of these, so no cache discount
    # is ever applied and the nominal and billed figures coincide (at zero).
    "elm_qwen_3.5": {
        "model_name": "Qwen/Qwen3.5-397B-A17B-FP8",
        "provider": LLMProvider.ELM,
        "input_per_1M": 0.0,
        "output_per_1M": 0.0,
        "cached_input_per_1M_usd": None,
        "cache_creation_per_1M_usd": None,
        # Verified: emits well-formed tool_calls under both tool_choice=auto and =required.
        "supports_tools": True,
        #: Measured 2026-09-22; see `LLMConfig.reasoning_effort`. Reasoning is ON when
        #: nothing is sent, and `none` is the only way to turn it off.
        "reasoning_efforts": ("none", "high"),
    },
    "elm_mistral_small_4": {
        "model_name": "mistralai/Mistral-Small-4-119B-2603",
        "provider": LLMProvider.ELM,
        "input_per_1M": 0.0,
        "output_per_1M": 0.0,
        "cached_input_per_1M_usd": None,
        "cache_creation_per_1M_usd": None,
        "supports_tools": True,
        #: Reasoning is OFF when nothing is sent -- the opposite of Qwen's default, so
        #: "the ELM default" is not one setting and a run has to say which it used.
        "reasoning_efforts": ("none", "high"),
    },
    "elm_llama_3.3": {
        "model_name": "meta-llama/Llama-3.3-70B-Instruct",
        "provider": LLMProvider.ELM,
        "input_per_1M": 0.0,
        "output_per_1M": 0.0,
        "cached_input_per_1M_usd": None,
        "cache_creation_per_1M_usd": None,
        # 400: '"auto" tool choice requires --enable-auto-tool-choice ... to be set'.
        "supports_tools": False,
        #: No reasoning mode. The gateway ACCEPTS every effort value for this model and
        #: honours none of them -- 2 completion tokens in all six cells -- so an empty tuple
        #: means "refuse the knob" rather than "untested".
        "reasoning_efforts": (),
    },
    "elm_eurollm_22b": {
        "model_name": "utter-project/EuroLLM-22B-Instruct-2512",
        "provider": LLMProvider.ELM,
        "input_per_1M": 0.0,
        "output_per_1M": 0.0,
        "cached_input_per_1M_usd": None,
        "cache_creation_per_1M_usd": None,
        "supports_tools": False,
        #: No reasoning mode; accepted and ignored, like Llama above.
        "reasoning_efforts": (),
    },
}

#: How to read a provider's token accounting when pricing a call.
#:
#: The two models disagree about exactly one thing: whether `cache_read_input_tokens` is a
#: **subset of** `prompt_tokens` or **disjoint from** it. Every other difference follows.
#:
#: * ``prompt_inclusive`` — cached tokens are part of the reported prompt. This is OpenAI's
#:   documented behaviour (`prompt_tokens_details.cached_tokens` counts a portion of
#:   `prompt_tokens`, and `total_tokens = prompt_tokens + completion_tokens`), and it is what
#:   this repo's own logs show: for one 9-turn conversation, `sum(total_tokens)` was 334,970
#:   and `sum(input) + sum(output)` was 334,970 exactly, while `input + cached + output`
#:   would have been 620,794. Reported prompt sizes also grow monotonically across turns,
#:   which only makes sense if they are cumulative totals rather than per-turn new tokens.
#:
#: * ``prompt_exclusive`` — the original APE assumption: the prompt count excludes cached
#:   tokens, so the two are added. Retained because the evidence above is this project's own
#:   measurement rather than a vendor invoice; if a bill says otherwise, switch back with
#:   `llm_config.cost_model=prompt_exclusive` and every historical figure reproduces.
#:
#: Under `prompt_exclusive`, cached tokens are counted twice — once at full price inside
#: `prompt_tokens` and once more at the cache rate — inflating both the nominal and the
#: discounted figure. Measured on the conversation above: $1.164 nominal and $0.700
#: "discounted" against a true cost of $0.200.
COST_MODELS = ("prompt_inclusive", "prompt_exclusive")
DEFAULT_COST_MODEL = "prompt_inclusive"


class LLMConfig(BaseModel):
    """LLM configuration class with a consistent model naming scheme.

    model_name: Canonical name that never changes (for example "gpt_5.2")
    formal_model_name: Provider-required name (for example "gpt-5.2-2025-12-11")
    """

    #: `extra='forbid'`, like `BaseScaffoldConfig` and `BaseToolsConfig` -- this was the one
    #: block in the config tree that silently swallowed a typo. Pydantic's default is
    #: `ignore`, so `llm_config: {base_rul: ...}` validated cleanly and dropped the key, and
    #: the run went to the default endpoint with no warning. That is the failure `extra`
    #: exists to prevent, and it matters most for exactly the keys nothing else checks:
    #: `base_url`, `api_key`, `cost_model`.
    model_config = ConfigDict(extra='forbid')

    # Basic configuration
    model_name: Optional[str] = None  # Canonical name provided by the user that always stays the same. None means use official models.
    max_tokens: int = 32000
    thinking_budget_tokens: int = 30000
    temperature: float = 1.0
    streaming: bool = True  # Whether to use streaming (default True to avoid socket read timeouts)
    timeout: int = 3600  # Total timeout in seconds for the entire request
    connect_timeout: int = 300  # Connection setup timeout in seconds

    # Connection settings
    base_url: Optional[str] = None

    #: Never serialized. `model_dump` feeds four consumers and only one of them wants a
    #: credential: the on-disk run snapshot (`save_orchestrator_config`), the container
    #: runtime's `--scaffold-config-json` *argv* (world-readable through /proc), the
    #: `scaffold_config_sha256` provenance hash, and the worker-process handoff. Including
    #: the key wrote it to 640 files under `.ape/runs/` across 289 runs, and made an
    #: otherwise-identical pair of runs hash differently after a key rotation.
    #:
    #: The worker does not lose it: `model_post_init` re-resolves from the environment
    #: whenever `api_key` is falsy, and worker processes inherit the launching environment.
    #: A key supplied as `llm_config.api_key` in YAML has no such fallback and therefore does
    #: not survive the process boundary -- `preflight._check_model_credential` refuses that
    #: case up front rather than letting it fail inside a worker.
    api_key: Optional[str] = Field(default=None, exclude=True)

    # Retry configuration
    retry_max_attempts: int = 100
    retry_min_wait: float = 1.0
    retry_max_wait: float = 60.0

    # Relay mode: disable error checks (empty responses, malformed data, etc.) and return directly
    relay_mode: bool = False

    # Metadata
    meta_info: Dict[str, Any] = Field(default_factory=dict)

    # Internal fields automatically populated by model_post_init
    formal_model_name: str = Field(default="", description="Formal model name required by the provider API")
    provider_type: Optional[LLMProvider] = Field(default=None, description="Provider type")

    #: Which token-accounting model to price this call under. See `COST_MODELS`.
    cost_model: Literal["prompt_inclusive", "prompt_exclusive"] = DEFAULT_COST_MODEL

    #: How much the model may think before answering. `None` sends nothing and takes the
    #: provider's default, which is what every run before this field did.
    #:
    #: It belongs in the config rather than being left to the endpoint because it moves token
    #: consumption by two orders of magnitude and therefore moves every token ceiling with it.
    #: Measured on the ELM gateway 2026-09-22, 3 samples per cell on one arithmetic prompt,
    #: completion tokens:
    #:
    #:     elm_qwen_3.5          none 4    absent 451   high 395    (default: ON)
    #:     elm_mistral_small_4   none 4    absent 4     high 143    (default: OFF)
    #:     elm_llama_3.3         2 in every cell -- no reasoning mode
    #:     elm_eurollm_22b       4 in every cell -- no reasoning mode
    #:
    #: Two things that table is worth stating out loud. The two agent-capable open-weight
    #: models have OPPOSITE defaults, so "the ELM default" is not one setting. And the
    #: parameter is `reasoning_effort`: a payload carrying `reasoning: null` returns HTTP 200,
    #: leaves reasoning ON (321 completion tokens against 4 when it is actually off) and says
    #: nothing -- so a config written that way would buy a hundredfold token bill believing it
    #: had bought none.
    #:
    #: `low` and `medium` are refused by name by both models that have a reasoning mode, and
    #: accepted-and-ignored by both that do not; `ElmProvider` therefore checks the value
    #: against the measured row rather than letting either outcome happen at runtime.
    reasoning_effort: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """Auto-configure immediately after initialization."""
        # If model_name is None, skip auto-configuration (use official models)
        if self.model_name is None:
            self.formal_model_name = ""
            self.provider_type = None
            return

        # model_name always stores the canonical label and does not change
        # Compute the formal model name
        self.formal_model_name = self.normalize_model_name(self.model_name)
        self.provider_type = self.detect_provider_type(self.model_name)
        if not self.api_key:
            self.api_key = self._resolve_api_key_from_environment(self.provider_type)
    
    @staticmethod
    def detect_provider_type(model_name: str) -> LLMProvider:
        """Detect the provider type for the supplied model name.

        Strategy:
        1. Look up MODEL_MAPPINGS for a known model.
        2. If nothing matches, raise an error.
        """
        model_config = MODEL_MAPPINGS.get(model_name)
        if model_config:
            return model_config["provider"]

        raise ConfigurationError(
            f"Unknown model name: {model_name}. "
            f"Supported models: {', '.join(MODEL_MAPPINGS.keys())}"
        )
    
    @staticmethod
    def normalize_model_name(model_name: str) -> str:
        """Normalize a canonical model name into a provider model name."""
        if model_name in MODEL_MAPPINGS:
            return MODEL_MAPPINGS[model_name]["model_name"]

        # Already in provider format, return as-is
        for key, config in MODEL_MAPPINGS.items():
            if config["model_name"] == model_name:
                return model_name

        raise ConfigurationError(
            f"Unknown model name: {model_name}. "
            f"Supported models: {', '.join(MODEL_MAPPINGS.keys())}"
        )

    @staticmethod
    def _resolve_api_key_from_environment(provider_type: Optional[LLMProvider]) -> Optional[str]:
        """Resolve provider API key from standard environment variables."""
        for name in PROVIDER_KEY_ENV_VARS.get(provider_type, ()):
            value = os.getenv(name)
            if value:
                return value
        return None

# Exception classes
class LLMError(Exception):
    """Base exception for LLM usage."""
    pass


class ConfigurationError(LLMError):
    """Configuration error."""
    pass


class ProviderError(LLMError):
    """Provider error."""
    pass


class ContextLengthExceededError(LLMError):
    """Context length exceeded error."""
    pass


class StreamingError(LLMError):
    """Streaming error."""
    pass


class MalformedResponseError(LLMError):
    """
    Response format error caused by model limitations.

    Indicates that the model failed to produce a valid response.
    Runners should not retry and must treat it as CONVERSATION_STOPPED.
    """
    pass


class CostExhaustedError(LLMError):
    """
    Cost limit exhausted.

    Raised when total conversation cost exceeds the budget; runners must not retry.
    """
    pass


class TokenBudgetExhaustedError(LLMError):
    """
    Token ceiling exhausted.

    The same event as `CostExhaustedError` against the other denomination, raised at the same
    checkpoint in the same loop. It is a separate class only so the record says which ceiling
    stopped the task: on a zero-priced model the cost ceiling cannot fire, and on a paid one
    either can, so "paused on budget" without saying which budget is not actionable.
    """
    pass
