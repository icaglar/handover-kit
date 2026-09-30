"""Shared helpers for the handover hooks."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

NOTE_PATH = ".claude/HANDOVER.md"
KNOWLEDGE_INDEX = ".claude/knowledge/INDEX.md"


def setting_with_source(key: str, default: float):
    """Read a numeric setting and report where it came from.

    Order: HANDOVER_<KEY> environment variable (one-off override), then the
    plugin option exported by Claude Code (CLAUDE_PLUGIN_OPTION_<KEY>), then
    the built-in default.
    """
    for name, label in (
        (f"HANDOVER_{key}", "environment variable"),
        (f"CLAUDE_PLUGIN_OPTION_{key}", "plugin setting"),
    ):
        value = os.environ.get(name)
        if value:
            try:
                return float(value), label
            except ValueError:
                pass
    return default, "default"


def setting(key: str, default: float) -> float:
    return setting_with_source(key, default)[0]


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


def _git(args, cwd: Path):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=5
    )


def note_timestamp(path: Path) -> float:
    """When the note's content was last written, as a Unix timestamp.

    A file's mtime is not enough: `git checkout` or `git pull` rewrites it, so
    an old note looks brand new. If the file is tracked and unchanged since
    its last commit, the content is at most as new as that commit, so the
    earlier of the commit time and the mtime is used. Modified or untracked
    files were written after the checkout, so their mtime is accurate.
    """
    mtime = path.stat().st_mtime
    try:
        cwd = path.parent
        if _git(["ls-files", "--error-unmatch", path.name], cwd).returncode != 0:
            return mtime
        if _git(["diff", "--quiet", "HEAD", "--", path.name], cwd).returncode != 0:
            return mtime
        out = _git(["log", "-1", "--format=%ct", "--", path.name], cwd).stdout.strip()
        if out:
            return min(mtime, float(out))
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return mtime


def config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


def read_bridge(session_id: str, transcript: str):
    """Exact context figures saved by the status line bridge, or None.

    The bridge (statusline_bridge.py, installed by /handover:setup) records the
    real window of the model in use and Claude Code's own used_percentage. The
    snapshot is ignored when it is missing, belongs to another session, or is
    clearly older than the transcript (the status line stopped updating).
    """
    try:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")
        path = config_dir() / "handover" / f"ctx-{safe}.json"
        snap = json.loads(path.read_text(encoding="utf-8"))
        if snap.get("session_id") != session_id:
            return None
        window = int(snap["window"])
        if window <= 0:
            return None
        if transcript and Path(transcript).is_file():
            if Path(transcript).stat().st_mtime - path.stat().st_mtime > 120:
                return None
        tokens, pct = snap.get("tokens"), snap.get("used_pct")
        if tokens is None and pct is None:
            return None
        ratio = float(pct) / 100 if pct is not None else tokens / window
        return {"ratio": ratio, "tokens": int(tokens if tokens is not None else ratio * window), "window": window}
    except (OSError, ValueError, KeyError, TypeError):
        return None
