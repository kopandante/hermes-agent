"""Minimal auth shim -- delegates to agent/providers.py."""
PROVIDER_REGISTRY = {}

def resolve_provider(*a, **kw):
    from agent.providers import resolve_provider as _rp
    from hermes_cli.config import load_config
    p = _rp(load_config())
    return p.name

def resolve_api_key_provider_credentials(provider_id):
    return {"api_key": "", "base_url": ""}

def resolve_codex_runtime_credentials():
    from agent.codex_auth import load_codex_token
    token = load_codex_token()
    return {"api_key": token or "", "base_url": "https://chatgpt.com/backend-api/codex"}

def resolve_nous_runtime_credentials():
    return {"api_key": "", "base_url": ""}

def _read_codex_tokens():
    from agent.codex_auth import load_codex_token
    return {"access_token": load_codex_token() or ""}
