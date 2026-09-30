#!/usr/bin/env python3
"""UserPromptSubmit hook.

Estimates how full the context window is from the token usage of the last
main-thread assistant message in the transcript (input + cache creation +
cache read tokens, the same formula Claude Code uses for its own percentage).
Once the threshold is crossed (default 70%), prints a note to stdout; Claude
Code adds it to the context. Fires once per fill cycle and re-arms when usage
drops well below the threshold (for example after /compact).

Hooks are not told the model's context window; only the status line is. With
the status line bridge connected (/handover:setup) the exact window and Claude
Code's own percentage are used, including after /model switches. Without it,
the window is a setting (default 200,000), and as a safety net it is raised to
1,000,000 if the transcript ever shows more tokens than that.

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
from _common import disabled, read_bridge, setting, setting_with_source, state_path  # noqa: E402

THRESHOLD, THRESHOLD_SRC = setting_with_source("THRESHOLD", 0.70)
# Re-arm well below the threshold, but never above it: with a low threshold
# (for example 0.3 while testing) a fixed re-arm level would sit above the
# threshold and the hook would never fire.
REARM = min(setting("REARM", 0.50), THRESHOLD * 0.7)
WINDOW_CONFIGURED, WINDOW_SRC = setting_with_source("WINDOW", 200000)
BIG_WINDOW = 1_000_000
TAIL_BYTES = 1_000_000  # only the last ~1 MB of the transcript is read


def usage_in_tail(transcript: Path):
    """(last, peak) total input tokens over main-thread assistant messages."""
    with transcript.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - TAIL_BYTES))
        lines = f.read().decode("utf-8", errors="ignore").splitlines()

    last = peak = None
    for line in lines:
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
        total = sum(
            int(usage.get(field) or 0)
            for field in (
                "input_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
            )
        )
        last = total
        peak = total if peak is None else max(peak, total)
    return last, peak


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

    session_id = payload.get("session_id", "")
    exact = read_bridge(session_id, transcript)
    if exact:
        used, window, ratio = exact["tokens"], exact["window"], exact["ratio"]
        figures = f"{used:,} of {window:,} tokens, exact figures from the status line"
    else:
        used, peak = usage_in_tail(Path(transcript))
        if used is None:
            return
        window = int(WINDOW_CONFIGURED)
        window_note = ""
        if peak > window:
            window = BIG_WINDOW
            window_note = "; the window was raised automatically because usage already exceeded the configured size"
        ratio = used / window
        figures = f"estimated {used:,} of {window:,} tokens{window_note}"

    path = state_path("threshold", session_id)
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

    if exact:
        hint = (
            "These figures come straight from Claude Code. If the user's own indicator "
            "shows a different number, it may count what is left rather than what is used."
        )
    else:
        hint = (
            "If the user's own indicator (status line or /context) shows a clearly different "
            f"percentage, tell them this estimate assumes a {window:,}-token window and that "
            "/handover:setup connects the plugin to the status line for exact figures, which "
            "also follow /model switches."
        )
    print(
        f"The context window is about {ratio * 100:.0f}% full ({figures}); "
        f"the handover threshold is {THRESHOLD * 100:.0f}% ({THRESHOLD_SRC}). "
        "In this project the handover protocol works like this: first answer the "
        "user's current request. Then say in one short line where the context "
        "stands, quoting these figures, and start the question round of the "
        "`/handover:write` skill, which is a tap-to-answer form and ends with "
        ".claude/HANDOVER.md being updated. " + hint
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a hook must never break the user's flow
        pass
    sys.exit(0)
