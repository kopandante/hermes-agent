"""Minimal command registry shim."""

GATEWAY_KNOWN_COMMANDS = frozenset({
    "new", "reset", "model", "approve", "deny", "compress",
    "usage", "skills", "cron", "stop", "status", "help",
    "retry", "undo", "personality", "yolo",
})

def resolve_command(text):
    cmd = text.lstrip("/").split()[0].lower() if text else ""
    if cmd in GATEWAY_KNOWN_COMMANDS:
        return cmd, cmd
    return None, None

def gateway_help_lines():
    return [
        "/new -- start fresh session",
        "/model -- switch model (inline buttons)",
        "/approve -- approve dangerous command",
        "/deny -- deny dangerous command",
        "/compress -- compress context",
        "/usage -- token usage stats",
        "/stop -- interrupt agent",
        "/help -- this help",
    ]

def telegram_menu_commands(**kwargs):
    cmds = [(cmd, desc.lstrip("-- ")) for cmd, desc in
            (line.split(" -- ") for line in gateway_help_lines() if " -- " in line)]
    return cmds, 0
