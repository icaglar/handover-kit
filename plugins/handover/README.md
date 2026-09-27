# Handover — a Claude Code plugin

Gets a handover note written before the context fills up, asks you about state before writing it, captures the rules you set during a session into `.claude/rules/`, and restores the note automatically after compaction or `/clear`.

| Part | When it runs | What it does |
|---|---|---|
| `/handover:write` | Manually, or after the threshold note | Asks up to 5 questions about state first (including which of the rules you set should become permanent), then saves confirmed rules and writes `.claude/HANDOVER.md` from a fixed template |
| `/handover:rule` | Whenever you say "make this a rule" | Saves a single rule to `.claude/rules/` right away, after checking for duplicates and conflicts |
| `/handover:resume` | Manually, in a new session | Reads the note, checks it against git state, and asks you to confirm the first step |
| Threshold hook | On every prompt | Once the context passes the threshold (70% by default), adds a note so Claude starts the handover. Fires once per fill cycle |
| PreCompact hook | Before auto-compaction | If there is no fresh note, pauses compaction **once** and allows the next attempt |
| SessionStart hook | After compaction and `/clear` | Loads the handover note, with its age, into the new context |

Hooks add no standing load to the model context; the three skill descriptions add roughly 370 tokens per session. Requirement: Python 3.8+ on PATH as `python3` or `python`. No third-party packages.

## Why

When the context fills up, Claude Code compacts the conversation and early details get lost. Asking for a handover note at 90% usually produces a summary of what is in the context window and nothing else: what you did outside the conversation, open decisions, and priorities that changed never make it in. This plugin moves the handover earlier and adds a question round, because the missing state is by definition something only you know.

## Rules

Rules you state mid-conversation ("always use pnpm", "never touch the generated client") are the first thing lost when the context is compacted. The handover note is the wrong place for them: it is rewritten and pruned at every handover. Claude Code already loads every file in `.claude/rules/` automatically in every session, so the plugin only captures rules and puts them there; no extra hook is involved.

- **During a handover:** `/handover:write` lists the rules you set in the session and asks which should become permanent. Only the ones you confirm are saved; the rest stay in the note as constraints.
- **Mid-session:** say "make this a rule" (or run `/handover:rule`) and it is saved immediately. If you correct the same thing twice, Claude offers to make it a rule but writes nothing without your yes.
- **Duplicates and conflicts:** before saving, the skill reads `CLAUDE.md`, `CLAUDE.local.md`, and existing rule files. Duplicates are skipped; conflicts are shown to you to decide. Files the plugin did not write, such as `CLAUDE.md`, are only edited with your approval.

Where rules go:

| Scope | File |
|---|---|
| This project | `.claude/rules/handover-rules.md` |
| This project, specific files | `.claude/rules/<topic>.md` with a `paths` frontmatter list of quoted globs |
| All your projects | `~/.claude/rules/handover-rules.md` (never path-scoped: Claude Code currently ignores `paths` in user-level rules) |

Rule files are plain markdown; edit or delete rules freely. Commit `.claude/rules/` if the rules should apply to your whole team.

## Install

**Option 1: from GitHub (recommended).** Push this folder as-is to a GitHub repository; a private repo works too. Then in Claude Code:

```
/plugin marketplace add icaglar/handover-kit
/plugin install handover@handover-kit
```

**Option 2: from a local folder.** To use it on your own machine without a repo:

```
/plugin marketplace add /full/path/to/handover-kit
/plugin install handover@handover-kit
```

**Option 3: just to try it.** Loads it for a single session without installing anything:

```bash
claude --plugin-dir /full/path/to/handover-kit/plugins/handover
```

After installing, restart Claude Code and run `/hooks` to check that the handover hooks appear under UserPromptSubmit, PreCompact, and SessionStart.

## Settings

```
/plugin configure handover@handover-kit
```

| Setting | Default | Description |
|---|---|---|
| `threshold` | `0.7` | How full the context must be before a handover is offered |
| `window` | `200000` | The model's context window in tokens. Set to `1000000` for 1M-context models |
| `fresh_minutes` | `30` | How recent the note must be for auto-compaction to proceed without a pause |

If you never configure them, the defaults apply. To override for a single session, use environment variables: `HANDOVER_THRESHOLD=0.5 claude`. `HANDOVER_WINDOW` and `HANDOVER_FRESH_MINUTES` work the same way.

## Headless and automation runs

When the plugin is installed at user level, it also runs in unattended `claude -p` jobs. There is nobody to answer questions there, and a paused compaction can stall the job. Turn the hooks off for those runs:

```bash
HANDOVER_DISABLED=1 claude -p "..."
```

## Sharing with a team

Teammates can install it with the two commands in Option 1. To have Claude Code suggest it to everyone who opens a particular project, add this to that project's `.claude/settings.json` and commit it:

```json
{
  "extraKnownMarketplaces": {
    "handover-kit": {
      "source": { "source": "github", "repo": "icaglar/handover-kit" }
    }
  },
  "enabledPlugins": {
    "handover@handover-kit": true
  }
}
```

If you have a claude.ai organization, an admin can also add the plugin to the organization's plugin catalog so it shows up there alongside other plugins.

## Testing

1. **Threshold:** start with `HANDOVER_THRESHOLD=0.05 claude` and send 2-3 messages. After a reply, Claude should offer a handover and start the question round.
2. **Write:** run `/handover:write`. Questions should come before anything is written. Tell Claude a rule during the session first ("from now on, always ...") and check that the question round asks whether to keep it.
3. **Rule:** say "make this a rule: ...". It should appear in `.claude/rules/handover-rules.md`; run `/memory` in a new session to see it loaded.
4. **Restore:** after the note is written, run `/clear` and ask "what does the handover note say?". The note should be in context.
5. **Resume:** in a new session, run `/handover:resume`. Claude should check git state against the note and ask you to confirm the first step.

## Suggested CLAUDE.md addition

To control what survives auto-compaction, add this to the `CLAUDE.md` at the project root:

```markdown
## Compact Instructions
When summarizing, always keep: decisions and their reasons, approaches that
were tried and dropped, changed files, open questions, the next step, and
rules the user set. See .claude/HANDOVER.md for details.
```

If the handover note is a personal working note, add `.claude/HANDOVER.md` to `.gitignore`. If your team shares it, commit it.

## Known limits

- **Context usage is an estimate.** The threshold hook reads the last `usage` field in the session transcript. That field is not an official API contract; if a Claude Code update changes the format, the hook silently stops firing. It never errors and never blocks your prompt. If it stops triggering, this is the first place to look.
- **PreCompact pauses only once.** This is deliberate: if compaction were blocked every time while the context is completely full, the session would get stuck.
- **Windows.** The hooks look for `python3`, then `python`. The Microsoft Store `python3` shortcut on Windows is not a real Python; if the hooks do nothing, turn that shortcut off under "App execution aliases" in Windows settings.

## Releasing a new version

The `version` field in `plugins/handover/.claude-plugin/plugin.json` pins users to that version. When you make changes, bump it (for example `0.1.0` → `0.2.0`) and push; users update from the `/plugin` interface or with `claude plugin update handover@handover-kit`. Run `claude plugin validate ./plugins/handover` before pushing.

## Uninstall

```
/plugin uninstall handover@handover-kit
```
