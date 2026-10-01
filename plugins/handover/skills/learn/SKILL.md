---
name: learn
description: Saves durable knowledge so it survives compaction and every future session: project knowledge (shared, in .claude/knowledge/), personal knowledge that holds across all the user's projects (a folder outside any repo), and the project overview. Use it when the user asks to record a decision, a fact about how something works, an environment detail or a gotcha, for the project, the team or all their projects, or to create or update the project overview; also for requests like "bunu proje hafızasına ekle", "tüm projelerimde geçerli olsun" or "proje özeti oluştur". Instructions about how to work belong in rules, not here.
---

# Save knowledge

Knowledge is **what is true and why**: decisions and their reasons, how things fit together, environment details, and gotchas someone paid for once. It has two homes and an overview. Talk to the user in the language they are using.

| Scope | Where | Shared? |
|---|---|---|
| **Project** | `.claude/knowledge/` in the repo | Yes, committed: the whole team starts with it |
| **Personal** | `~/.claude/handover/personal/` (under `$CLAUDE_CONFIG_DIR` if set) | No: stays on this machine; applies in every project |
| **Project overview** | `.claude/knowledge/overview.md` | Yes, committed |

## Which layer does this belong to?

Put each item in exactly one layer. If it does not belong here, say where it goes instead.

| It is… | Layer | Where |
|---|---|---|
| Where the current work stands, next steps | State | `.claude/HANDOVER.md` (`/handover:write`) |
| An instruction about how to work ("always…", "never…") | Rule | `.claude/rules/` or `~/.claude/rules/` (`/handover:rule`) |
| A fact or decision about this project, with its reason | **Project knowledge** | `.claude/knowledge/` (this skill) |
| A fact or decision that holds across the user's projects (their stack choices, servers and where credentials live, a vendor's API quirk, a convention of their domain) | **Personal knowledge** | `~/.claude/handover/personal/` (this skill) |
| What the project is: purpose, stack, layout, external services, status | **Project overview** | `.claude/knowledge/overview.md` (this skill) |
| Build, test and run commands; conventions Claude must follow | Instructions | `CLAUDE.md` |
| A personal habit of this user in working with Claude | Auto memory | Claude Code's own memory; do not duplicate it here |

## When to act

- **The user explicitly asks:** that is consent. Save it, then show exactly what was written and where. Ask first only if the content or the reason is unclear.
- **You discover something durable** (a root cause, a non-obvious constraint, an environment quirk): offer in one line. Save nothing unless the user says yes.

**Never store secrets or personal data about other people.** No passwords, API keys, tokens, connection strings with credentials, and no personal data about customers or colleagues. Project knowledge is committed to the repository, and personal knowledge is still plain text on disk. Record *where* a secret lives ("the staging DB password is in the team vault under X"), never the secret itself. If a file you are about to change already contains something that looks like a secret (password, API key, token, private key, credentials in a connection string), tell the user before writing anything, and suggest removing it and rotating the secret; removing it from the file does not remove it from git history.

## 1. Choose the scope

Decide project or personal before anything else.

- **Personal** when the user says it applies everywhere ("in all my projects", "always for me", "genel", "kişisel"), or when the fact is not about this repository at all: their own server or accounts, their stack preferences, a third-party API's behavior that they will meet again elsewhere.
- **Project** when it concerns this repository, its team, its deployment, its data. When in doubt and the fact names something in this repo, choose project.
- **Genuinely unclear:** ask with the `AskUserQuestion` tool when available: "Save for this project (shared with the team) or for all your projects (only on this machine)?" with the options "This project (Recommended)" and "All my projects". Without the tool, ask in one line.

A fact that matters in both places goes where it is *owned*; mention it from the other side in prose only if needed. Never copy the same fact into both.

## 2. Word it

- **Decisions** need the reason; a decision without a why cannot be re-evaluated later. Include rejected alternatives when they were seriously considered.
- **Facts** should be concrete and checkable: names, paths, ports, commands, versions.
- Use absolute dates.
- **Language:** write each entry in the language of the file you add it to; a new file uses the language the user is using.

## 3. Pick the topic file

Use an existing file when one fits. Otherwise create one with a short, plain name.

- **Project**, typical files: `decisions.md` (decisions and their reasons), `architecture.md`, `environments.md` (hosts, ports, deploy flow, external services), `gotchas.md`.
- **Personal**, typical files: `decisions.md`, `stack.md` (tools and platforms the user chose and why), `hosts-and-accounts.md` (what runs where and where credentials live, never the credentials), `gotchas.md`.

## 4. Check for duplicates and conflicts

Both indexes (`.claude/knowledge/INDEX.md` and the personal one) are already in your context at session start; read the topic file you are about to change.

- **Duplicate:** do not add it; say where it already is. Check the other scope too: a personal fact already in the project knowledge (or the reverse) is a duplicate.
- **Conflict with a decision:** do not delete the old decision. Mark it `Status: superseded by "<new title>" (YYYY-MM-DD)` and add the new one. The history of why a decision changed is itself knowledge.
- **Conflict with a fact:** replace the old line, and mention the change to the user.
- **Conflict between scopes** (a personal decision that the project's knowledge contradicts): point it out and ask which applies in this project; the project's knowledge normally wins inside the project.
- **Conflict with a rule, `CLAUDE.md`, or auto memory:** point it out and ask which is true; ask before editing files this plugin did not write.

## 5. Write

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

Create the personal folder if it does not exist.

## 6. Update the index

Each scope has an `INDEX.md` that is loaded into every session, so it must stay short: one line per topic file, naming the most important things inside so Claude knows when to open it. The project index may have 60 lines, the personal one 30; lines past that are not loaded. If it does not exist, create it:

```markdown
# Project knowledge

Durable facts and decisions for this project. Open the linked file when a topic is relevant.

- [decisions.md](decisions.md) — <n> active decisions: <the key ones, a few words each>
- [environments.md](environments.md) — <what is covered>
```

For the personal index use the heading `# Personal knowledge` and the line "Facts and decisions that hold across all my projects." Update the line for the file you changed (counts, key items). Add a line for a new file. Do not list `overview.md`; it is loaded directly.

## 7. Project overview

When the user asks to create or update the project overview ("proje özeti", "project overview"), write `.claude/knowledge/overview.md`. It is loaded in full at every session start, so it stays **under 25 lines**: it describes, it does not instruct.

1. **Gather.** Read the README, the package or build manifests, the top-level directories, `CLAUDE.md`, and `git log --oneline -5`. Use what you find; do not invent what you cannot see. Ask the user about what the repository cannot tell you (the purpose, who it is for, the current phase) with one `AskUserQuestion` form when available.
2. **Name files by their path** (`.claude/knowledge/gotchas.md`), so nothing in the overview looks like a missing repo file.
3. **Do not duplicate `CLAUDE.md`.** Build, test and run commands and conventions belong there. In the overview, refer to them ("commands: see CLAUDE.md") instead of copying them. If `CLAUDE.md` already covers purpose and stack, keep the overview to what is missing: external services and status.
4. **Write it** in this shape, dropping lines you cannot fill:

```markdown
# <Project name>
- Purpose: <one or two lines: what it does and for whom>
- Stack: <languages, frameworks, datastores>
- Layout: <the main directories, one short phrase each, at most 6>
- External services: <names, and where credentials live; never the values>
- Status: <phase and what is in progress> (updated YYYY-MM-DD)
```

5. **Keep it current.** `/handover:write` refreshes the Status line and anything the session changed. Update it with this skill whenever the stack, layout, or external services change.
6. **Overview already exists?** Update the changed lines and the date; do not rewrite the file.

## 8. Confirm

Tell the user in 1-2 lines what was saved, in which scope and file, and that it will be available in every future session through the index (project knowledge: for the whole team; personal knowledge: in all their projects on this machine).
