# handover-kit

Context and state management tools for Claude Code. This repository is a Claude Code plugin marketplace and currently contains one plugin:

| Plugin | Description |
|---|---|
| [`handover`](plugins/handover/README.md) | Handover notes and memory management: starts the handover at a context threshold, asks about state before writing, captures rules and durable project knowledge, restores the note after compaction or `/clear`, and audits all memory layers |

## Quick install

```
/plugin marketplace add icaglar/handover-kit
/plugin install handover@handover-kit
```

See the [plugin README](plugins/handover/README.md) for details, settings, and team setup.

## Layout

```text
handover-kit/
├── .claude-plugin/marketplace.json     # marketplace definition
└── plugins/handover/
    ├── .claude-plugin/plugin.json      # plugin manifest and settings (userConfig)
    ├── hooks/hooks.json                # UserPromptSubmit, PreCompact, SessionStart
    ├── scripts/                        # hook scripts (Python, no dependencies)
    └── skills/
        ├── write/SKILL.md              # /handover:write
        ├── rule/SKILL.md               # /handover:rule
        ├── learn/SKILL.md              # /handover:learn
        ├── tidy/SKILL.md               # /handover:tidy
        └── resume/SKILL.md             # /handover:resume
```

Validate after changes:

```bash
claude plugin validate .
claude plugin validate ./plugins/handover
```
