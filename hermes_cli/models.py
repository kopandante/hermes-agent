"""Minimal models shim."""
def copilot_default_headers(model=None):
    return {}

def github_model_reasoning_efforts():
    return {}

def parse_model_input(raw, current_provider=""):
    if ":" in raw:
        provider, model = raw.split(":", 1)
        return model, provider
    return raw, current_provider
