---
name: learn
description: Saves a durable fact or decision about the project to the repo's shared knowledge base in .claude/knowledge/, so it survives compaction and every future session (and teammate) starts with it. Use this skill when the user asks to record a decision, to note down how something in the project works, an environment detail, or a gotcha "for the project" or "for the team", or equivalent requests in other languages such as "bunu proje hafızasına ekle" or "bu kararı kaydet". Personal preferences are not project knowledge; leave those to Claude Code's own auto memory.
---

# Save project knowledge

Project knowledge is **what is true about this project and why**: decisions and their reasons, how the architecture fits together, environment details, and gotchas someone paid for once. It lives in `.claude/knowledge/`, which is committed, so the whole team shares it. Talk to the user in the language they are using.

## Which layer does this belong to?

Put each item in exactly one layer. If it does not belong here, say where it goes instead.

| It is… | Layer | Where |
|---|---|---|
| Where the current work stands, next steps | State | `.claude/HANDOVER.md` (`/handover:write`) |
| An instruction about how to work ("always…", "never…") | Rule | `.claude/rules/` (`/handover:rule`) |
| A fact or decision about the project, with its reason | **Knowledge** | `.claude/knowledge/` (this skill) |
| A personal preference or habit of this user | Auto memory | Claude Code's own memory; do not duplicate it here |

## When to act

- **The user explicitly asks:** that is consent. Save it, then show exactly what was written and where. Ask first only if the content or the reason is unclear.
- **You discover something durable** (a root cause, a non-obvious constraint, an environment quirk): offer in one line. Save nothing unless the user says yes.

**Never store secrets or personal data.** No passwords, API keys, tokens, connection strings with credentials, or personal data about customers or colleagues: this directory is committed to the repository. Record *where* a secret lives ("the staging DB password is in the team vault under X"), never the secret itself.

## 1. Word it

- **Decisions** need the reason; a decision without a why cannot be re-evaluated later. Include rejected alternatives when they were seriously considered.
- **Facts** should be concrete and checkable: names, paths, ports, commands, versions.
- Use absolute dates.

## 2. Pick the topic file

Use an existing file when one fits. Otherwise create one with a short, plain name. Typical files:

- `decisions.md` — decisions and their reasons
- `architecture.md` — how the parts fit together
- `environments.md` — hosts, ports, deploy flow, external services
- `gotchas.md` — pitfalls and their root causes

## 3. Check for duplicates and conflicts

The index (`.claude/knowledge/INDEX.md`) is already in your context at session start; read the topic file you are about to change.

- **Duplicate:** do not add it; say where it already is.
- **Conflict with a decision:** do not delete the old decision. Mark it `Status: superseded by "<new title>" (YYYY-MM-DD)` and add the new one. The history of why a decision changed is itself knowledge.
- **Conflict with a fact:** replace the old line, and mention the change to the user.
- **Conflict with a rule, `CLAUDE.md`, or auto memory:** point it out and ask which is true; ask before editing files this plugin did not write.

## 4. Write

Decisions in `decisions.md`:

```markdown
### <Short decision title> — YYYY-MM-DD
- Decision: <what was decided>
- Why: <the reason>
- Rejected: <alternatives and why> (optional)
- Status: active
```

Facts in other topic files, one line each:

```markdown
- <Concrete fact>. (added YYYY-MM-DD)
```

## 5. Update the index

`.claude/knowledge/INDEX.md` is loaded into every session, so it must stay short: one line per topic file, naming the most important things inside so Claude knows when to open it. Keep it under 60 lines; lines past that are not loaded. If it does not exist, create it:

```markdown
# Project knowledge

Durable facts and decisions for this project. Open the linked file when a topic is relevant.

- [decisions.md](decisions.md) — <n> active decisions: <the key ones, a few words each>
- [environments.md](environments.md) — <what is covered>
```

Update the line for the file you changed (counts, key items). Add a line for a new file.

## 6. Confirm

Tell the user in 1-2 lines what was saved, in which file, and that it will be available in every future session through the index.
