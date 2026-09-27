"""Shared helpers for the handover hooks."""
import os
import re
import tempfile
from pathlib import Path

NOTE_PATH = ".claude/HANDOVER.md"
KNOWLEDGE_INDEX = ".claude/knowledge/INDEX.md"


def setting(key: str, default: float) -> float:
    """Read a numeric setting.

    Order: HANDOVER_<KEY> environment variable (one-off override), then the
    plugin option exported by Claude Code (CLAUDE_PLUGIN_OPTION_<KEY>), then
    the built-in default.
    """
    for name in (f"HANDOVER_{key}", f"CLAUDE_PLUGIN_OPTION_{key}"):
        value = os.environ.get(name)
        if value:
            try:
                return float(value)
            except ValueError:
                pass
    return default


def disabled() -> bool:
    """HANDOVER_DISABLED=1 turns every hook into a no-op (headless / CI runs)."""
    return os.environ.get("HANDOVER_DISABLED") == "1"


def state_path(prefix: str, session_id: str) -> Path:
    """Per-session state file, kept in the plugin data dir when available."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")
    root = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or tempfile.gettempdir())
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{prefix}-{safe}.json"


def project_dir(payload: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
