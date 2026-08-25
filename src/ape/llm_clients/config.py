"""
LLM Clients Configuration System.
"""

import os
from typing import Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field

class LLMProvider(Enum):
    """LLM provider enumeration."""
    OPENAI = "openai"
    GEMINI = "gemini"

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
    }
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

    model_name: Canonical name that never changes (for example "deepseek_v3.1")
    formal_model_name: Provider-required name (for example "Ark-deepseek-v3.1-0821")
    """

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
    api_key: Optional[str] = None

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
        if provider_type == LLMProvider.OPENAI:
            return os.getenv("OPENAI_API_KEY")
        if provider_type == LLMProvider.GEMINI:
            return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
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
