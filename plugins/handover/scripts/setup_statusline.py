#!/usr/bin/env python3
"""Connect (or disconnect) the handover status line bridge.

  setup_statusline.py --plan    show what would change, change nothing
  setup_statusline.py --apply   install the bridge
  setup_statusline.py --remove  restore the previous status line

The bridge script is copied to <config dir>/handover/, so it keeps working
after plugin updates. An existing status line command is not replaced: it is
saved to next.json and the bridge runs it after recording the numbers, so the
status line looks the same as before. Your settings.json is backed up first.
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path


def config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


CFG = config_dir()
SETTINGS = CFG / "settings.json"
FOLDER = CFG / "handover"
BRIDGE = FOLDER / "statusline_bridge.py"
NEXT = FOLDER / "next.json"
SOURCE = Path(__file__).resolve().parent / "statusline_bridge.py"
PY = '"$(command -v python3 || command -v python)"'
COMMAND = f'{PY} "{BRIDGE.as_posix()}"'


def load_settings():
    if not SETTINGS.exists():
        return {}
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def is_ours(status_line) -> bool:
    return isinstance(status_line, dict) and "statusline_bridge.py" in str(status_line.get("command", ""))


def save_settings(data: dict) -> None:
    tmp = SETTINGS.with_suffix(".json.handover-tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, SETTINGS)


def backup_settings() -> None:
    """Copy settings.json aside under a name that never overwrites an earlier backup."""
    if not SETTINGS.exists():
        return
    stamp = time.strftime("%Y%m%d%H%M%S")
    backup = SETTINGS.with_name(f"settings.json.handover-backup-{stamp}")
    counter = 1
    while backup.exists():
        counter += 1
        backup = SETTINGS.with_name(f"settings.json.handover-backup-{stamp}-{counter}")
    shutil.copy2(SETTINGS, backup)
    print(f"Backed up settings to {backup}")


def plan(settings: dict) -> None:
    current = settings.get("statusLine")
    print(f"Settings file: {SETTINGS}")
    if is_ours(current):
        print("The bridge is already connected. --apply refreshes the copied script.")
    elif isinstance(current, dict) and current.get("command"):
        print(f"Your current status line command: {current['command']}")
        print("It will keep running after the bridge; the status line will look the same.")
    else:
        print("You have no status line. The bridge will show a short default: ctx 34% \u00b7 340k/1M")
    print(f"Files written: {BRIDGE}, {NEXT}")
    print("Backup: settings.json.handover-backup-<timestamp> next to your settings file.")
    print("Note: a project's own .claude/settings.json statusLine overrides this one in that project.")


def apply(settings: dict) -> None:
    FOLDER.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, BRIDGE)
    current = settings.get("statusLine")
    if not is_ours(current):
        backup_settings()
        NEXT.write_text(
            json.dumps(
                {
                    "command": current.get("command") if isinstance(current, dict) else None,
                    "original_statusLine": current,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        entry = dict(current) if isinstance(current, dict) else {}
        entry.update({"type": "command", "command": COMMAND})
        settings["statusLine"] = entry
        save_settings(settings)
    print("Bridge connected. The numbers appear after the next response.")


def remove(settings: dict) -> None:
    if not is_ours(settings.get("statusLine")):
        print("The bridge is not connected; nothing to remove.")
        return
    try:
        original = json.loads(NEXT.read_text(encoding="utf-8")).get("original_statusLine")
    except (OSError, ValueError):
        original = None
    backup_settings()
    if original:
        settings["statusLine"] = original
    else:
        settings.pop("statusLine", None)
    save_settings(settings)
    for path in [BRIDGE, NEXT, *FOLDER.glob("ctx-*.json")]:
        try:
            path.unlink()
        except OSError:
            pass
    print("Previous status line restored; bridge files removed.")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--plan"
    if mode not in ("--plan", "--apply", "--remove"):
        print(__doc__)
        return 2
    try:
        settings = load_settings()
    except (OSError, ValueError) as error:
        print(f"Cannot read {SETTINGS} ({error}). Nothing was changed.")
        return 1
    if not isinstance(settings, dict):
        print(f"{SETTINGS} is not a JSON object. Nothing was changed.")
        return 1
    {"--plan": plan, "--apply": apply, "--remove": remove}[mode](settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
