"""Minimal runtime provider shim."""
def resolve_runtime_provider(config=None, **kw):
    from agent.providers import resolve_provider
    from hermes_cli.config import load_config
    p = resolve_provider(config or load_config())
    return {"api_key": p.api_key, "base_url": p.base_url, "provider": p.name, "model": ""}

def determine_api_mode(provider=None, **kw):
    return "chat"
