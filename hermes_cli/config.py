"""Minimal config shim replacing the full hermes_cli.config."""
import os
import yaml
from pathlib import Path

def get_hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

def ensure_hermes_home() -> Path:
    home = get_hermes_home()
    home.mkdir(parents=True, exist_ok=True)
    return home

def load_config() -> dict:
    path = get_hermes_home() / "config.yaml"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(cfg: dict) -> Path:
    path = get_hermes_home() / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    return path

def save_config_value(key: str, value, config: dict = None) -> Path:
    cfg = config or load_config()
    parts = key.split(".")
    d = cfg
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = value
    return save_config(cfg)

def print_config_warnings():
    pass

def _expand_env_vars(val):
    if isinstance(val, str):
        return os.path.expandvars(val)
    return val

def is_managed():
    return False

def format_managed_message():
    return ""

# Constants that other modules expect
DEFAULT_CONFIG = {}
OPTIONAL_ENV_VARS = {}
