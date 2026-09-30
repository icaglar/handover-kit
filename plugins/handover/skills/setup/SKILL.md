---
name: setup
description: One-time setup that connects the plugin to Claude Code's status line so it knows the real context window of the model in use (200K, 1M, or after a /model switch) instead of estimating it. Run by the user with /handover:setup.
disable-model-invocation: true
---

# Connect the status line

The threshold hook cannot see which model, and so which context window, is in use; only the status line receives that. This one-time setup makes the status line record it, so the plugin works with exact figures and follows `/model` switches. Talk to the user in the language they are using.

The setup edits the user's `settings.json` (`statusLine`), so show the plan and get a clear yes before applying anything.

## 1. Show the plan

Run the script in plan mode. It changes nothing.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup_statusline.py" --plan
```

Use `python` if `python3` is not available. If `${CLAUDE_PLUGIN_ROOT}` is not substituted, find the script with `ls ~/.claude/plugins/cache/handover-kit/handover/*/scripts/setup_statusline.py` and use the newest one.

Summarize the plan in two or three lines: whether the user has a status line already (it keeps working: the bridge runs it after recording the numbers), where the backup goes, and that a project's own `statusLine` setting overrides the user-level one inside that project.

## 2. Ask

Use the `AskUserQuestion` tool when available: "Connect the status line?" with the options "Connect (Recommended)" and "Not now". Without the tool, ask in one line.

## 3. Apply

On yes:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup_statusline.py" --apply
```

Report the script's output. If it says it cannot read the settings file, tell the user nothing was changed and show the reason.

Then tell the user: the exact numbers appear after the next response; the status line may show a short "ctx 34% · 340k/1M" if they had none; and to undo everything they can run `/handover:setup` again and ask for removal, which is the same script with `--remove`.

## Removal

If the user asks to disconnect, run the script with `--remove` instead. It restores the previous status line and deletes the bridge files.
