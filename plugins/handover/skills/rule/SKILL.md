---
name: rule
description: Saves a rule the user just set as a permanent rule in .claude/rules/, so it survives compaction and loads in every future session. Use this skill whenever the user says "make this a rule", "remember this rule", "from now on always/never ...", "add a rule", or equivalent requests in other languages such as "bunu kural yap" or "bundan sonra hep ...". Also use it when the user has corrected the same behavior twice in a session, but only to offer the rule, never to write it unasked.
---

# Save a rule

Rules the user states in the middle of a conversation get lost when the context is compacted. Claude Code already loads every file in `.claude/rules/` automatically, so the job here is only to capture the rule well and put it in the right file. Talk to the user in the language they are using.

## When to act

- **The user explicitly asks** ("make this a rule", "from now on always ..."): that is consent. Write the rule, then show exactly what was written and where. Ask first only if the wording or scope is genuinely unclear.
- **The user corrected the same thing twice:** offer in one line ("Want me to make this a permanent rule?"). Write nothing unless they say yes.
- **A one-off instruction for the current task** ("don't touch the tests in this PR") is not a permanent rule. It belongs in the handover note's constraints section, not here.

## 1. Word the rule

One line, imperative, specific, and actionable without further explanation. Add a short reason when the rule is not self-evident; the reason helps apply it correctly in edge cases.

- Weak: "Be careful with the database."
- Good: "Never run migrations against the production database from a local machine; use the deploy pipeline. (Local runs bypassed the backup step once.)"

## 2. Choose the scope

Default to a general rule for this project. Ask only when the scope is unclear.

| Scope | File | Frontmatter |
|---|---|---|
| This project, everywhere | `.claude/rules/handover-rules.md` | none |
| This project, specific files | `.claude/rules/<topic>.md` (for example `api.md`) | `paths` list |
| All of the user's projects | `~/.claude/rules/handover-rules.md` | none, ever |

For path-specific rules, `paths` must be a YAML list of **quoted** glob patterns. Unquoted patterns starting with `*` or `{` are invalid YAML, and when the frontmatter does not parse, Claude Code silently loads the rule everywhere:

```markdown
---
paths:
  - "src/api/**/*.py"
---
# API rules

- <rule> (added YYYY-MM-DD)
```

Never put `paths` in a user-level rule under `~/.claude/rules/`: path-scoped rules there are currently ignored by Claude Code and would never load. If a personal rule is only relevant to certain files, say so in the rule's wording instead.

## 3. Check for duplicates and conflicts

Before writing, read the rule sources that exist: `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, every file under `.claude/rules/`, `~/.claude/CLAUDE.md`, and `~/.claude/rules/`.

- **Duplicate:** do not add it. Tell the user where the rule already lives.
- **Conflict:** show both rules and ask which one wins. Update or remove the losing rule instead of adding a contradicting one. If the losing rule lives outside the files this plugin writes (for example in `CLAUDE.md`), ask before editing that file.

## 4. Write

- If the target file does not exist, create it. For `handover-rules.md`, start it with:

  ```markdown
  # Project rules

  Captured with the handover plugin. Edit freely; delete rules that no longer apply.
  ```

- Append the rule as a list item ending with `(added YYYY-MM-DD)` using the absolute date.
- Keep rule files short. Files over 200 lines consume more context and reduce adherence. If a rules file passes about 50 rules, suggest consolidating related rules or moving stable, project-wide ones into `CLAUDE.md`.

## 5. Confirm

Tell the user in 1-2 lines: the exact rule text, the file it went into, and that it loads automatically from the next session on. It already applies in this session because it is in the conversation.
