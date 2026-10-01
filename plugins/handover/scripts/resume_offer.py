#!/usr/bin/env python3
"""SessionStart hook (matcher: startup).

At the start of a fresh session, if the project has a recent handover note that
the work has not moved past, tells Claude to offer continuing from it with
/handover:resume, with the user's approval. A hook cannot open a session or
start a turn; this only puts a note into the context, so the offer appears in
Claude's first reply. /handover:resume itself checks the note against the
repository and asks before starting anything.

Stays quiet when: there is no note, it is older than 21 days, commits touching
code have been made since it was written (the work already moved on), or the
setting is off. After /clear or /compact the note is loaded by restore_note.py
instead.

Setting: offer_resume (plugin configuration, on by default).
HANDOVER_OFFER_RESUME=0 turns it off for one run; HANDOVER_DISABLED=1 turns
every handover hook off. On any error the hook exits silently.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import NOTE_PATH, _git, disabled, flag, note_timestamp, project_dir  # noqa: E402

MAX_AGE_DAYS = 21


def age_text(seconds: float) -> str:
    minutes = seconds / 60
    if minutes < 60:
        n, unit = round(minutes), "minute"
    elif minutes < 48 * 60:
        n, unit = round(minutes / 60), "hour"
    else:
        n, unit = round(minutes / 1440), "day"
    return f"{n} {unit}{'' if n == 1 else 's'}"


def main() -> None:
    if disabled() or not flag("OFFER_RESUME", True):
        return
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if payload.get("source", "startup") != "startup":
        return

    root = project_dir(payload)
    note = root / NOTE_PATH
    if not note.is_file():
        return
    text = note.read_text(encoding="utf-8", errors="ignore")
    if not text.strip():
        return

    written = note_timestamp(note)
    age = time.time() - written
    if age > MAX_AGE_DAYS * 86400:
        return

    branch_now = None
    try:
        probe = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
        if probe.returncode == 0:
            branch_now = probe.stdout.strip()
            log = _git(["log", "-50", "--format=%ct", "--", ".", ":(exclude).claude"], root)
            if log.returncode == 0:
                newer = [int(x) for x in log.stdout.split() if x.isdigit() and int(x) > written]
                if newer:
                    return  # code was committed after the note: the work moved on
    except Exception:
        pass

    match = re.search(r"Branch:\s*([^\s·|]+)", "\n".join(text.splitlines()[:5]))
    branch_note = match.group(1) if match else None
    branch_info = ""
    if branch_note and branch_now and branch_note != branch_now:
        branch_info = (
            f" The note was written on branch {branch_note} but the current branch is {branch_now}; "
            "mention this in the offer."
        )

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(
        f"A handover note from a previous session exists for this project ({NOTE_PATH}, "
        f"written {age_text(age)} ago).{branch_info} If the user's first message is a greeting, "
        "a question like \"where were we\", or otherwise gives no clear new task, offer in one "
        "line, in their language, to continue from that note. When the AskUserQuestion tool is "
        "available, make it a two-option tap (continue from the note, recommended / start "
        "something new). If they accept, follow the /handover:resume skill: it checks the note "
        "against the repository and asks before starting the first step. If their first message "
        "is a clearly different task, do that task and do not bring the note up. Offer once."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the user's flow
        pass
    sys.exit(0)
