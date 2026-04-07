"""OpenAI Codex OAuth -- device code flow + token refresh."""

import json
import time
import logging
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
AUTH_BASE = "https://auth.openai.com"
TOKEN_URL = f"{AUTH_BASE}/oauth/token"
DEVICE_CODE_URL = f"{AUTH_BASE}/api/accounts/deviceauth/usercode"
TOKEN_EXCHANGE_URL = f"{AUTH_BASE}/oauth/token"

def _auth_path() -> Path:
    """Path to auth.json in HERMES_HOME."""
    import os
    home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    return home / "auth.json"

def _load_auth() -> dict:
    path = _auth_path()
    if path.exists():
        return json.loads(path.read_text())
    return {}

def _save_auth(data: dict) -> None:
    path = _auth_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)

def load_codex_token() -> str | None:
    """Load and refresh codex access token. Returns None if not logged in."""
    auth = _load_auth()
    # Support both formats:
    # 1. Simple: {"tokens": {"access_token": ..., "refresh_token": ...}}
    # 2. Credential pool: {"credential_pool": {"openai-codex": [{"access_token": ..., "refresh_token": ...}]}}
    tokens = auth.get("tokens", {})
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    last_refresh = auth.get("last_refresh", 0)
    if not refresh:
        # Try credential_pool format
        pool = auth.get("credential_pool", {})
        entries = pool.get("openai-codex", [])
        if isinstance(entries, list) and entries:
            entry = entries[0]
            access = entry.get("access_token")
            refresh = entry.get("refresh_token")
            last_refresh = entry.get("last_refresh", 0)
    if not refresh:
        return None
    # Check if access token needs refresh (2 min skew)
    if time.time() - last_refresh > 3300:  # refresh every ~55 min
        access = _refresh_token(refresh)
        if access:
            # Update whichever format we found
            pool = auth.get("credential_pool", {})
            entries = pool.get("openai-codex", [])
            if isinstance(entries, list) and entries:
                entries[0]["access_token"] = access
                entries[0]["last_refresh"] = time.time()
            else:
                auth.setdefault("tokens", {})["access_token"] = access
                auth["last_refresh"] = time.time()
            _save_auth(auth)
    return access

def _refresh_token(refresh_token: str) -> str | None:
    """Refresh access token using refresh token."""
    try:
        resp = httpx.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CODEX_CLIENT_ID,
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("access_token")
    except Exception as e:
        logger.warning("Codex token refresh failed: %s", e)
        return None

def device_code_login() -> bool:
    """Interactive device code login. Returns True on success."""
    # Step 1: Get device code
    resp = httpx.post(DEVICE_CODE_URL, json={"client_id": CODEX_CLIENT_ID}, timeout=15)
    if resp.status_code != 200:
        print(f"Device code request failed: {resp.status_code}")
        return False
    data = resp.json()
    user_code = data["user_code"]
    device_auth_id = data["device_auth_id"]
    interval = data.get("interval", 5)

    print(f"\nOpen: https://auth.openai.com/codex/device")
    print(f"Code: {user_code}\n")
    print("Waiting for authorization...")

    # Step 2: Poll for authorization
    for _ in range(180):  # 15 min max
        time.sleep(interval)
        resp = httpx.post(f"{AUTH_BASE}/api/accounts/deviceauth/token", json={
            "client_id": CODEX_CLIENT_ID,
            "device_auth_id": device_auth_id,
        }, timeout=15)
        if resp.status_code == 200:
            token_data = resp.json()
            auth_code = token_data.get("authorization_code")
            code_verifier = token_data.get("code_verifier")
            if auth_code:
                # Step 3: Exchange for tokens
                return _exchange_code(auth_code, code_verifier)
        elif resp.status_code == 400:
            continue  # still pending
        else:
            print(f"Polling error: {resp.status_code}")
            return False
    print("Timeout waiting for authorization")
    return False

def _exchange_code(auth_code: str, code_verifier: str) -> bool:
    """Exchange authorization code for access + refresh tokens."""
    try:
        resp = httpx.post(TOKEN_EXCHANGE_URL, data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "code_verifier": code_verifier,
            "client_id": CODEX_CLIENT_ID,
            "redirect_uri": "https://chatgpt.com",
        }, timeout=15)
        resp.raise_for_status()
        tokens = resp.json()
        auth = {
            "auth_mode": "chatgpt",
            "tokens": {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
            },
            "last_refresh": time.time(),
        }
        _save_auth(auth)
        print("Logged in successfully!")
        return True
    except Exception as e:
        print(f"Token exchange failed: {e}")
        return False
