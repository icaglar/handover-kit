#!/usr/bin/env python3
"""SessionStart hook (matcher: startup|resume|clear|compact).

Prints the project knowledge index (.claude/knowledge/INDEX.md) to stdout so
Claude Code adds it to every session, including after compaction and /clear.
Only the short index is loaded; the topic files it links to are read on
demand. The index is capped so a growing file cannot flood the context; when
the cap is hit, a line suggests running /handover:tidy.

HANDOVER_DISABLED=1 turns the hook off.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import KNOWLEDGE_INDEX, disabled, project_dir  # noqa: E402

MAX_LINES = 60
MAX_CHARS = 6_000


def main() -> None:
    if disabled():
        return

    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}

    index = project_dir(payload) / KNOWLEDGE_INDEX
    if not index.is_file():
        return

    content = index.read_text(encoding="utf-8", errors="ignore").strip()
    if not content:
        return

    lines = content.splitlines()
    truncated = len(lines) > MAX_LINES or len(content) > MAX_CHARS
    if truncated:
        content = "\n".join(lines[:MAX_LINES])[:MAX_CHARS]
        content += (
            f"\n\n[Index truncated at {MAX_LINES} lines / {MAX_CHARS:,} characters. "
            "Entries past this point are not loaded; suggest /handover:tidy to the user.]"
        )

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    print(
        f"Project knowledge index ({KNOWLEDGE_INDEX}). It lists durable facts and "
        "decisions for this project; open the linked files under .claude/knowledge/ "
        "when a topic is relevant to the task. If the code contradicts an entry, the "
        "code wins and the entry should be updated.\n\n" + content
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
