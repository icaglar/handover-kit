#!/usr/bin/env python3
"""SessionStart hook (matcher: startup|resume|clear|compact).

Loads the standing memory into every session, including after compaction and
/clear. Three short pieces, each capped so a growing file cannot flood the
context; when a cap is hit, a line suggests running /handover:tidy:

  1. the project overview            .claude/knowledge/overview.md
  2. the project knowledge index     .claude/knowledge/INDEX.md
  3. the personal knowledge index    <config dir>/handover/personal/INDEX.md
     (facts and decisions that apply to all of the user's projects)

Only the indexes are loaded for knowledge; the topic files they link to are
read on demand.

HANDOVER_DISABLED=1 turns the hook off.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import KNOWLEDGE_INDEX, OVERVIEW_PATH, disabled, personal_dir, project_dir  # noqa: E402


def section(path, max_lines, max_chars, intro, noun):
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not content:
        return None
    lines = content.splitlines()
    if len(lines) > max_lines or len(content) > max_chars:
        content = "\n".join(lines[:max_lines])[:max_chars]
        content += (
            f"\n\n[{noun} truncated at {max_lines} lines / {max_chars:,} characters. "
            "Entries past this point are not loaded; suggest /handover:tidy to the user.]"
        )
    return intro + "\n\n" + content


def main() -> None:
    if disabled():
        return
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    root = project_dir(payload)

    parts = [
        section(
            root / OVERVIEW_PATH, 25, 2_000,
            f"Project overview ({OVERVIEW_PATH}). A short description of what this project is. "
            "If the code contradicts it, the code wins and the overview should be updated.",
            "Overview",
        ),
        section(
            root / KNOWLEDGE_INDEX, 60, 6_000,
            f"Project knowledge index ({KNOWLEDGE_INDEX}). It lists durable facts and decisions "
            "for this project; open the linked files under .claude/knowledge/ when a topic is "
            "relevant. If the code contradicts an entry, the code wins and the entry should be updated.",
            "Index",
        ),
        section(
            personal_dir() / "INDEX.md", 30, 3_000,
            f"Personal knowledge index ({personal_dir() / 'INDEX.md'}). Facts and decisions that "
            "apply to all of this user's projects, kept outside any repository; open the linked "
            "files in that folder when relevant. Anything specific to the current project belongs "
            "in the project knowledge instead.",
            "Index",
        ),
    ]
    parts = [x for x in parts if x]
    if not parts:
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print("\n\n".join(parts))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
