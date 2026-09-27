#!/usr/bin/env python3
"""UserPromptSubmit hook.

Estimates how full the context window is from the token usage of the last
main-thread assistant message in the transcript. Once the threshold is
crossed (default 70%), prints a note to stdout; Claude Code adds it to the
context. Fires once per fill cycle and re-arms when usage drops below the
re-arm level (for example after /compact).

Settings come from the plugin configuration (/plugin configure): threshold,
window. HANDOVER_THRESHOLD / HANDOVER_WINDOW environment variables override
them. HANDOVER_DISABLED=1 turns the hook off.

On any error the hook exits silently: it must never block the user's prompt.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import NOTE_PATH, disabled, setting, state_path  # noqa: E402

THRESHOLD = setting("THRESHOLD", 0.70)
REARM = setting("REARM", 0.50)
WINDOW = int(setting("WINDOW", 200000))
TAIL_BYTES = 1_000_000  # only the last ~1 MB of the transcript is read


def last_usage(transcript: Path):
    """Total input tokens of the last main-thread assistant message."""
    with transcript.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - TAIL_BYTES))
        lines = f.read().decode("utf-8", errors="ignore").splitlines()

    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("isSidechain"):
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        return sum(
            int(usage.get(field) or 0)
            for field in (
                "input_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
            )
        )
    return None


def read_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"armed": True}


def write_state(path: Path, state: dict) -> None:
    try:
        path.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def main() -> None:
    if disabled():
        return

    payload = json.load(sys.stdin)
    transcript = payload.get("transcript_path")
    if not transcript or not Path(transcript).is_file():
        return

    used = last_usage(Path(transcript))
    if used is None:
        return

    ratio = used / WINDOW
    path = state_path("threshold", payload.get("session_id", ""))
    state = read_state(path)

    if ratio < REARM:
        if not state.get("armed", True):
            write_state(path, {"armed": True})
        return

    if ratio < THRESHOLD or not state.get("armed", True):
        return

    write_state(path, {"armed": False})

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    print(
        f"The context window is about {ratio * 100:.0f}% full "
        f"(estimated {used:,} / {WINDOW:,} tokens). "
        "In this project the handover protocol works like this: the assistant "
        "first answers the user's current request, then offers to write a "
        "handover note and starts the question round from the `/handover:write` "
        "skill: before writing, it asks up to 5 questions about state that is "
        f"not visible in the conversation, then updates {NOTE_PATH} with the answers."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the user's flow
        pass
    sys.exit(0)
