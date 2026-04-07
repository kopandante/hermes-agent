"""Minimal providers shim."""
def get_label(provider):
    labels = {"openrouter": "OpenRouter", "openai-codex": "OpenAI Codex",
              "anthropic": "Anthropic", "gemini": "Gemini", "custom": "Custom"}
    return labels.get(provider, provider)

def determine_api_mode(provider=None, **kw):
    if provider == "openai-codex":
        return "codex_responses"
    return "chat"
