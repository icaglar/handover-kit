#!/usr/bin/env python3
"""SessionStart hook (matcher: compact|clear).

After compaction or /clear, prints the handover note to stdout; Claude Code
adds it to the start of the new context. The note's age is included so an
old note is not mistaken for current state.

HANDOVER_DISABLED=1 turns the hook off.
"""
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import NOTE_PATH, disabled, note_timestamp, project_dir  # noqa: E402

MAX_CHARS = 20_000


def plural(value: float, unit: str) -> str:
    n = round(value)
    return f"{n} {unit}" if n == 1 else f"{n} {unit}s"


def age_text(seconds: float) -> str:
    minutes = seconds / 60
    if minutes < 60:
        return plural(minutes, "minute")
    hours = minutes / 60
    if hours < 48:
        return plural(hours, "hour")
    return plural(hours / 24, "day")


def main() -> None:
    if disabled():
        return

    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}

    note = project_dir(payload) / NOTE_PATH
    if not note.is_file():
        return

    content = note.read_text(encoding="utf-8", errors="ignore").strip()
    if not content:
        return
    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + "\n\n[... note truncated; full text is in the file]"

    mtime = note_timestamp(note)
    when = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    age = age_text(time.time() - mtime)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    print(
        f"Handover note for this project ({NOTE_PATH}, last updated {when}, {age} ago). "
        "It describes the state left by a previous session; if the files or git "
        "state contradict it, the current files win.\n\n" + content
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
