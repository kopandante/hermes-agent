"""Minimal tools config shim."""
from toolsets import get_toolset, resolve_toolset

def _get_platform_tools(user_config, platform_key):
    preset = f"hermes-{platform_key}" if platform_key != "cli" else "hermes-cli"
    try:
        return resolve_toolset(preset)
    except Exception:
        from toolsets import _HERMES_CORE_TOOLS
        return set(_HERMES_CORE_TOOLS)
