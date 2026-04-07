"""Minimal env loader."""
from pathlib import Path
from dotenv import load_dotenv

def load_hermes_dotenv(hermes_home=None, project_env=None):
    loaded = []
    if hermes_home:
        p = Path(hermes_home) / ".env"
        if p.exists():
            load_dotenv(p, override=True)
            loaded.append(str(p))
    if project_env and Path(project_env).exists():
        load_dotenv(project_env, override=True)
        loaded.append(str(project_env))
    return loaded
