#!/usr/bin/env python3
"""PreCompact hook (matcher: auto).

Before auto-compaction, checks whether the handover note is fresh. If the
note is missing or older than the freshness window, blocks compaction with
exit code 2 and explains why on stderr.

To avoid deadlocks it blocks only ONCE per session: the next auto-compaction
attempt in the same session is allowed, so a completely full context never
leaves the session stuck. A fresh note re-arms the guard for the next cycle.
Manual /compact is never touched.

Setting comes from the plugin configuration (/plugin configure): fresh_minutes.
HANDOVER_FRESH_MINUTES overrides it. HANDOVER_DISABLED=1 turns the hook off.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import NOTE_PATH, disabled, note_timestamp, project_dir, setting, state_path  # noqa: E402

FRESH_MINUTES = setting("FRESH_MINUTES", 30)


def main() -> int:
    if disabled():
        return 0

    payload = json.load(sys.stdin)
    if payload.get("trigger") != "auto":
        return 0  # never interfere with a manual /compact

    note = project_dir(payload) / NOTE_PATH
    marker = state_path("precompact", payload.get("session_id", ""))

    if note.is_file():
        age_minutes = (time.time() - note_timestamp(note)) / 60
        if age_minutes <= FRESH_MINUTES:
            # Fresh note: clear any old block marker so the next fill cycle
            # can pause once again.
            try:
                marker.unlink()
            except OSError:
                pass
            return 0

    if marker.exists():
        # Already blocked once in this session: allow it now so the session
        # does not get stuck.
        try:
            marker.unlink()
        except OSError:
            pass
        return 0

    try:
        marker.write_text(json.dumps({"blocked_at": time.time()}), encoding="utf-8")
    except OSError:
        return 0  # if we cannot record the block, do not risk blocking

    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.stderr.write(
        f"Auto-compaction paused once: no handover note ({NOTE_PATH}) was updated "
        f"in the last {FRESH_MINUTES:.0f} minutes. Write it with /handover:write, "
        "then run /compact. The next auto-compaction attempt will be allowed.\n"
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # on error, never block compaction
