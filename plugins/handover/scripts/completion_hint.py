#!/usr/bin/env python3
"""UserPromptSubmit hook: offer a handover when the job is done.

Claude Code cannot be told to close a session, and a hook cannot judge whether
a job is finished. Claude can. So after substantial work in a session (about a
dozen tool calls), this hook adds one note to the context, once per session:
when the user's request is complete, end the final reply with a one-line offer
of a handover note. It never fires on short question-and-answer sessions, and
stays quiet when a fresh handover note exists or when the context threshold
note already started a handover.

Setting: offer_when_done (plugin configuration, on by default).
HANDOVER_OFFER_WHEN_DONE=0 turns it off for one run; HANDOVER_DISABLED=1 turns
every handover hook off. On any error the hook exits silently.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    NOTE_PATH, disabled, flag, note_timestamp, project_dir, setting, state_path,
)

MIN_TOOL_CALLS = int(setting("DONE_MIN_TOOLS", 12))
FRESH_MINUTES = setting("FRESH_MINUTES", 30)
TAIL_BYTES = 1_000_000


def count_tool_calls(transcript: Path) -> int:
    """Distinct tool calls made by the main conversation in the transcript tail."""
    with transcript.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - TAIL_BYTES))
        lines = f.read().decode("utf-8", errors="ignore").splitlines()
    seen = set()
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("isSidechain"):
            continue
        message = entry.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                seen.add(block.get("id") or f"line-{len(seen)}")
    return len(seen)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main() -> None:
    if disabled() or not flag("OFFER_WHEN_DONE", True):
        return

    payload = json.load(sys.stdin)
    transcript = payload.get("transcript_path")
    if not transcript or not Path(transcript).is_file():
        return

    session = payload.get("session_id", "")
    marker = state_path("donehint", session)
    if marker.exists():
        return  # already offered (or deliberately skipped) in this session

    calls = count_tool_calls(Path(transcript))
    if calls < MIN_TOOL_CALLS:
        return

    def done_with_session() -> None:
        try:
            marker.write_text(json.dumps({"at": time.time()}), encoding="utf-8")
        except OSError:
            pass

    # The context threshold note already started a handover in this cycle.
    threshold = read_json(state_path("threshold", session))
    if isinstance(threshold, dict) and threshold.get("armed") is False:
        return done_with_session()

    # A fresh handover note exists: the user already handed over.
    note = project_dir(payload) / NOTE_PATH
    if note.is_file() and (time.time() - note_timestamp(note)) / 60 <= FRESH_MINUTES:
        return done_with_session()

    done_with_session()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(
        f"This session has had substantial work (about {calls} tool calls). When you have "
        "finished what the user asked and nothing is left open (results delivered, tests "
        "pass, changes committed or deliberately left uncommitted), end your final reply "
        "with one short line, in the user's language, offering a handover note with "
        "/handover:write. Offer it once. Never offer in the middle of work or while the user "
        "is still iterating, and do not start the form unless they accept. If the user says "
        "they are done, wrapping up, or leaving, offer right away. Only the user can close "
        "the session (/exit); after a handover you may remind them they can. If a "
        "context-threshold note is also present, follow that one instead."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the user's flow
        pass
    sys.exit(0)
