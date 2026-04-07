# Hermes Agent: Gut & Rewrite

Personal DevOps agent. Strip 25K -> 7K LOC, keep what matters.

## What stays

- Agent loop (decomposed from 9371 LOC god file)
- Telegram gateway + API server
- Tools: terminal, files, web, approval, clarify, delegate, mcp, memory, todo, voice transcription, cron, send_message, code_exec, session_search
- Context compression, prompt caching, prompt builder
- Session/state persistence (SQLite FTS5)
- Skills system (local only, no Hub)

## What goes

- CLI TUI (cli.py 8553 LOC) -- gateway-only
- hermes_cli/ (setup wizard, model catalog, etc.) -- replaced by inline buttons
- 14 platform adapters (Discord, Slack, WhatsApp, Signal, Matrix, HomeAssistant, Email, SMS, DingTalk, Feishu, WeChat, Mattermost, Webhook)
- RL environments, batch_runner, trajectory_compressor, rl_cli
- landingpage/, website/
- Tools: voice TTS, browser (camofox, browserbase, providers), homeassistant, mixture_of_agents, image_generation, skills_hub, skills_sync, skills_guard, skill_manager, openrouter_client, url_safety, website_policy, rl_training, osv_check, tirith_security, managed_tool_gateway, tool_backend_helpers, checkpoint_manager, env_passthrough, debug_helpers, fuzzy_match, ansi_strip
- Terminal backends: Modal, Daytona, SSH, Docker, Singularity -- keep only local
- Model pipeline: 8529 LOC across 8 files -> 400 LOC in 2 files

## New structure

```
hermes-agent/
  main.py                    # Entry point: gateway run
  agent/
    core.py                  # AIAgent class (~500)
    conversation.py          # run_conversation loop (~400)
    tools_executor.py        # Sequential + concurrent with locks (~300)
    providers.py             # Provider registry + live model fetch (~300)
    codex_auth.py            # Codex OAuth device flow + refresh (~100)
    prompt_builder.py        # System prompt assembly (from agent/)
    context_compressor.py    # From agent/
    model_metadata.py        # Simplified context lengths
    prompt_caching.py        # From agent/
    display.py               # Spinner, tool preview (from agent/)
    memory_manager.py        # From agent/
    usage_pricing.py         # From agent/
  gateway/
    runner.py                # GatewayRunner (~600)
    session.py               # Session store
    config.py                # Simplified config
    telegram.py              # Telegram adapter + inline keyboards (~800)
    api_server.py            # HTTP API (keep as-is)
  tools/
    registry.py              # Tool registry
    terminal.py              # Terminal + approval (~800)
    files.py                 # File read/write/search/patch
    web.py                   # Web search + extract
    delegate.py              # Subagent delegation
    clarify.py               # Clarify with buttons
    mcp.py                   # MCP client
    memory.py                # Memory tool
    todo.py                  # Todo tool
    voice.py                 # Voice transcription
    cron.py                  # Scheduled tasks
    send_message.py          # Cross-platform send
    code_exec.py             # Python sandbox
    session_search.py        # FTS5 search
  config/
    defaults.yaml            # Default config
    state.py                 # SQLite session/state store
    constants.py             # Constants
  Dockerfile
  pyproject.toml
```

## Model selection rewrite (8529 -> ~400)

### Current problem
8 files, 20+ providers, OAuth flows, credential pools, JWT refresh, models.dev API, pricing tables. `/model openai-codex:openai/gpt-5.3-codex` -- unusable UX.

### New design

**agent/providers.py** (~300 LOC):
- Provider dataclass: name, base_url, api_key, transport
- 5 providers: openai-codex, openrouter, anthropic, gemini, custom
- `resolve_provider(config)` -- config value or first with credentials
- `fetch_models(provider)` -- GET /v1/models, live list
- `create_client(provider)` -- OpenAI SDK

**Telegram `/model` UX** (inline keyboards):
1. `/model` -> buttons: available providers (only those with credentials)
2. Tap provider -> fetch live models -> group by family:
   `[Claude] [GPT] [Gemini] [Open] [All...]`
3. Tap family -> top models in that family as buttons
4. Tap model -> set, done

Config favorites (optional): `providers.openrouter.pinned: [claude-sonnet-4.6, gpt-4.1]` -- shown first.

**agent/codex_auth.py** (~100 LOC):
- Device code OAuth flow
- Token refresh from auth.json
- No credential pools, rotation, exhaustion

## Security fixes (integrated during rewrite)

- threading.Lock on concurrent tool results (tools_executor.py)
- asyncio.Lock on _running_agents (gateway/runner.py)
- int() with try-except in telegram.py
- except Exception: pass -> logger.warning() everywhere
- File blocklist: add ~/.ssh/, ~/.bashrc, ~/.profile, ~/.env
- TOCTOU: os.open() with O_NOFOLLOW for sensitive paths
- time.monotonic() everywhere (no mixed time sources)
- Tool registry: error on name collision with builtins
- force=True: require approval token hash

## Dependencies (stripped)

Core: openai, httpx, pydantic, pyyaml, python-dotenv, rich, tenacity, jinja2
Telegram: python-telegram-bot[webhooks], aiohttp
Web: parallel-web, firecrawl-py
Voice: faster-whisper, sounddevice, numpy
MCP: mcp
Cron: croniter

No: anthropic, fire, prompt_toolkit, exa-py, fal-client, edge-tts, elevenlabs, modal, daytona, discord.py, slack-bolt, matrix-nio, PyJWT, debugpy

## Dockerfile

python:3.11-slim, no Node.js. ~500MB vs ~1.5GB.

## Phases

### Phase 1: Gut
Delete dead files/dirs, strip pyproject.toml, new Dockerfile, gateway-only main.py.
Checkpoint: bot starts and responds in Telegram.

### Phase 2: Decompose
run_agent.py -> agent/core.py + conversation.py + tools_executor.py
gateway/run.py -> gateway/runner.py
Model pipeline -> agent/providers.py + codex_auth.py
Security fixes.
Checkpoint: bot works, code < 7K LOC.

### Phase 3: Polish
Dead imports, logging, AGENTS.md, Docker image, init-tools.sh.
Checkpoint: production-ready.
