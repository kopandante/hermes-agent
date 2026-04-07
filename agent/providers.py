"""Provider registry and model resolution for Kermit."""

from dataclasses import dataclass, field
from typing import Optional
import os
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class Provider:
    """LLM provider configuration."""
    name: str
    base_url: str
    api_key: str
    transport: str = "chat"  # "chat" or "codex_responses"

@dataclass
class ModelInfo:
    """Model metadata from provider API."""
    id: str
    context_length: int = 128_000
    family: str = "other"  # claude, gpt, gemini, open, other

# Provider factories -- each returns Provider or raises if no credentials
def _openrouter(env) -> Provider:
    key = env("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY not set")
    return Provider("openrouter", "https://openrouter.ai/api/v1", key)

def _codex(env) -> Provider:
    from agent.codex_auth import load_codex_token
    token = load_codex_token()
    if not token:
        raise ValueError("No codex OAuth token. Run: kermit auth codex")
    return Provider("openai-codex", "https://chatgpt.com/backend-api/codex", token, transport="codex_responses")

def _anthropic(env) -> Provider:
    key = env("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return Provider("anthropic", "https://api.anthropic.com/v1", key)

def _gemini(env) -> Provider:
    key = env("GOOGLE_API_KEY") or env("GEMINI_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY not set")
    return Provider("gemini", "https://generativelanguage.googleapis.com/v1beta/openai", key)

def _custom(env) -> Provider:
    base_url = env("CUSTOM_BASE_URL") or env("OPENAI_BASE_URL")
    if not base_url:
        raise ValueError("CUSTOM_BASE_URL not set")
    return Provider("custom", base_url, env("OPENAI_API_KEY") or "")

PROVIDER_FACTORIES = {
    "openrouter": _openrouter,
    "openai-codex": _codex,
    "anthropic": _anthropic,
    "gemini": _gemini,
    "custom": _custom,
}

def _env_getter(name: str, default: str = "") -> str:
    """Get env var value."""
    return os.environ.get(name, default)

def resolve_provider(config: dict) -> Provider:
    """Resolve provider from config. If 'auto', try each until one has credentials."""
    provider_name = config.get("model", {}).get("provider", "auto")
    env = _env_getter

    if provider_name != "auto":
        factory = PROVIDER_FACTORIES.get(provider_name)
        if not factory:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {', '.join(PROVIDER_FACTORIES)}")
        return factory(env)

    # Auto-detect: try each provider, first with credentials wins
    for name, factory in PROVIDER_FACTORIES.items():
        try:
            return factory(env)
        except (ValueError, Exception):
            continue
    raise ValueError("No provider configured. Set model.provider in config.yaml or provide API keys.")

def available_providers() -> list[str]:
    """Return list of providers that have credentials configured."""
    env = _env_getter
    result = []
    for name, factory in PROVIDER_FACTORIES.items():
        try:
            factory(env)
            result.append(name)
        except Exception:
            pass
    return result

def create_client(provider: Provider) -> OpenAI:
    """Create OpenAI client for provider."""
    return OpenAI(api_key=provider.api_key, base_url=provider.base_url)

# --- Model discovery ---

MODEL_FAMILIES = {
    "claude": ["claude"],
    "gpt": ["gpt", "o1", "o3", "o4"],
    "gemini": ["gemini"],
    "deepseek": ["deepseek"],
    "open": ["llama", "qwen", "mistral", "mixtral", "phi", "command"],
}

def _classify_model(model_id: str) -> str:
    """Classify model into family for button grouping."""
    lower = model_id.lower()
    for family, prefixes in MODEL_FAMILIES.items():
        if any(p in lower for p in prefixes):
            return family
    return "other"

CONTEXT_LENGTHS = {
    "claude-opus-4": 1_000_000,
    "claude-sonnet-4": 1_000_000,
    "claude-haiku": 200_000,
    "gpt-5": 1_000_000,
    "gpt-4.1": 1_047_576,
    "gpt-4o": 128_000,
    "gemini": 1_048_576,
    "deepseek": 128_000,
}

def get_context_length(model: str) -> int:
    """Get context length for model. Checks prefixes, falls back to 128K."""
    lower = model.lower()
    for prefix, length in CONTEXT_LENGTHS.items():
        if prefix in lower:
            return length
    return 128_000

async def fetch_models(provider: Provider) -> list[ModelInfo]:
    """Fetch available models from provider's /v1/models endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"Authorization": f"Bearer {provider.api_key}"}
            resp = await client.get(f"{provider.base_url}/models", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("data", []):
                mid = m.get("id", "")
                ctx = m.get("context_length", get_context_length(mid))
                models.append(ModelInfo(id=mid, context_length=ctx, family=_classify_model(mid)))
            return sorted(models, key=lambda m: m.id)
    except Exception as e:
        logger.warning("Failed to fetch models from %s: %s", provider.base_url, e)
        return []

def group_models(models: list[ModelInfo]) -> dict[str, list[ModelInfo]]:
    """Group models by family for button display."""
    groups: dict[str, list[ModelInfo]] = {}
    for m in models:
        groups.setdefault(m.family, []).append(m)
    return groups
