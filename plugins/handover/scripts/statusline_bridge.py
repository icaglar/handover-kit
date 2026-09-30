#!/usr/bin/env python3
"""Status line bridge for the handover plugin.

Claude Code pipes a JSON document to the status line command after every
response and on model changes. It is the only place that knows the context
window of the model actually in use (200K, 1M, or whatever /model switched
to) and Claude Code's own used_percentage. Hooks are not given either.

This script saves those two facts to <config dir>/handover/ctx-<session>.json,
where the plugin's threshold hook reads them, and then prints the status line:
the command you used before (see setup_statusline.py) or a short default.

It must be fast and must never fail: on any error it still prints something
and exits 0. Installed by /handover:setup; a copy lives in
<config dir>/handover/statusline_bridge.py so plugin updates cannot break it.
"""
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


def fmt(tokens) -> str:
    if tokens is None:
        return "?"
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M".replace(".0M", "M")
    if tokens >= 1000:
        return f"{tokens / 1000:.0f}k"
    return str(tokens)


def snapshot(data: dict):
    context = data.get("context_window") or {}
    size = context.get("context_window_size")
    session = data.get("session_id")
    if not session or not size:
        return None
    usage = context.get("current_usage") or {}
    tokens = None
    if usage:
        tokens = sum(
            int(usage.get(field) or 0)
            for field in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        )
    return {
        "session_id": session,
        "window": int(size),
        "tokens": tokens,
        "used_pct": context.get("used_percentage"),
        "model": (data.get("model") or {}).get("id"),
        "written_at": time.time(),
    }


def save(snap: dict) -> None:
    folder = config_dir() / "handover"
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", snap["session_id"])
    target = folder / f"ctx-{safe}.json"
    fd, tmp = tempfile.mkstemp(dir=str(folder), prefix=".ctx-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(snap, f)
    os.replace(tmp, target)
    if random.random() < 0.02:  # occasional cleanup of snapshots from old sessions
        cutoff = time.time() - 7 * 86400
        for old in folder.glob("ctx-*.json"):
            try:
                if old.stat().st_mtime < cutoff:
                    old.unlink()
            except OSError:
                pass


def default_line(snap) -> str:
    if not snap:
        return ""
    pct = snap.get("used_pct")
    if pct is None and snap.get("tokens") is not None and snap["window"]:
        pct = 100 * snap["tokens"] / snap["window"]
    if pct is None:
        return f"ctx ?/{fmt(snap['window'])}"
    return f"ctx {pct:.0f}% \u00b7 {fmt(snap.get('tokens'))}/{fmt(snap['window'])}"


def next_command():
    try:
        info = json.loads((config_dir() / "handover" / "next.json").read_text(encoding="utf-8"))
        command = info.get("command")
        return command if isinstance(command, str) and command.strip() else None
    except (OSError, ValueError):
        return None


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except ValueError:
        data = {}
    snap = None
    try:
        snap = snapshot(data)
        if snap:
            save(snap)
    except Exception:
        pass

    command = next_command()
    if command:
        try:
            result = subprocess.run(
                command, shell=True, input=raw, capture_output=True, text=True, timeout=8
            )
            if result.stdout.strip():
                try:
                    sys.stdout.reconfigure(encoding="utf-8")
                except AttributeError:
                    pass
                sys.stdout.write(result.stdout)
                return
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(default_line(snap))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
