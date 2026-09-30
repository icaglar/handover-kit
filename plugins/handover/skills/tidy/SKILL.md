---
name: tidy
description: Audits every memory layer Claude Code loads for this project (CLAUDE.md files, rules, Claude's auto memory, the project knowledge base, and the handover note), reports duplicates, contradictions, stale or misplaced entries, secrets, and size problems, and fixes them only after the user approves. Use this skill when the user asks to clean up, tidy, audit, or review memory, rules, or context files, asks what Claude knows or remembers about the project, when the knowledge index was truncated, or for equivalent requests in other languages such as "hafızayı temizle" or "hafıza bakımı yap".
---

# Tidy memory

Memory fails quietly as it grows: the same fact lives in three places, two files contradict each other, a decision was reversed but the old one still loads, or a file grows past the point where it is loaded at all. This skill audits all layers together, because problems usually sit *between* layers. Talk to the user in the language they are using.

**Change nothing until the user approves.** This skill reports first and edits second.

## 1. Inventory

Read every layer that exists and note its size in lines and approximate tokens (characters ÷ 4) and when it loads:

| Layer | Location | Loads |
|---|---|---|
| Project instructions | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` | every session |
| Personal instructions | `~/.claude/CLAUDE.md` | every session |
| Rules | `.claude/rules/**/*.md`, `~/.claude/rules/*.md` | every session, or on matching files when path-scoped |
| Auto memory | the auto memory directory named in your own system prompt (by default under `~/.claude/projects/<project>/memory/`) | `MEMORY.md`: first 200 lines or 25KB; topic files on demand |
| Project knowledge | `.claude/knowledge/INDEX.md` and topic files | index every session (capped at 60 lines); topic files on demand |
| Handover note | `.claude/HANDOVER.md` | after compaction or `/clear` |

Skip layers that do not exist. If auto memory is disabled or its directory is empty, say so and move on.

## 2. Check

Look for these problems, across layers as well as within them:

- **Size:** `MEMORY.md` past 200 lines or 25KB (the excess is not loaded at session start); `CLAUDE.md` or any rules file past 200 lines (adherence drops); the knowledge index past 60 lines (the excess is not loaded).
- **Duplicates:** the same fact or rule in more than one place. Keep it in the layer where it belongs and remove the others.
- **Contradictions:** two entries that cannot both be true. Do not pick a winner yourself; ask the user.
- **Stale entries:** paths, files, functions, commands, or dependencies the entries mention that no longer exist in the repository (check with file search); decisions that were reversed but are still marked active; handover notes older than 7 days; items still marked Unverified.
- **Misplaced entries:** instructions sitting in the knowledge base (they belong in rules); project facts sitting in rules or auto memory that the team would need (they belong in the knowledge base); current-work state sitting anywhere except the handover note.
- **Secrets and personal data:** anything that looks like a password, API key, token, private key, connection string with credentials, or personal data about customers or colleagues, especially in committed files. Report these first.
- **Broken rules:** `paths` frontmatter that does not parse as YAML (the rule then silently loads everywhere), and `paths` in user-level rules under `~/.claude/rules/` (currently ignored, so the rule never loads). Report only frontmatter that actually fails to parse; check it with a YAML parser when one is available. An unquoted pattern such as `src/**/*.py` is valid. Only unquoted patterns that *start* with a YAML indicator character (`*`, `{`, `[`, `&`, `!`, `?`, `|`, `>`, `%`, `@`, or a backtick) break it; the fix is to quote them.

Use this placement guide when deciding where something belongs:

| It is… | Belongs in |
|---|---|
| Where the current work stands | handover note |
| How to work ("always…", "never…") | rules |
| What is true about the project, and why | project knowledge |
| A personal preference of this user | auto memory or `~/.claude/CLAUDE.md` |
| Project overview, build and test commands | `CLAUDE.md` |

## 3. Report

Present the findings as one numbered list, most important first (secrets, then contradictions, then everything else). For each: the problem, where it is, and the exact proposed change. End with the current always-loaded size and the size after the proposed changes. Then ask what to apply, as a form when the `AskUserQuestion` tool is available (1-4 questions per call, 2-4 options each; it adds "Other" by itself):

- One single-choice question per contradiction, header "Conflict", options = the competing entries. Never pick the winner yourself.
- Then multi-select questions for the remaining fixes, at most 4 options each, header "Apply", labelled with the finding number and a few words, the safe ones marked "(Recommended)".
- More than 4 questions: use follow-up forms.

Without the tool, ask in plain text: "Reply with the numbers to apply, \"all\", or \"none\"; for each conflict, say which entry wins."

If you find nothing worth changing, say so in one line and stop.

## 4. Apply

Apply only the approved changes.

- **Moving between layers** follows each layer's format: rules as in `/handover:rule`, knowledge as in `/handover:learn` (update `INDEX.md` too), decisions are marked superseded rather than deleted.
- **Auto memory** is Claude's personal, machine-local memory. Moving something from it into the knowledge base shares it with the whole team; mention that when proposing the move. When removing an entry from an auto memory topic file, also update its line in `MEMORY.md`.
- **Secrets:** removing a secret from a file does not remove it from git history. Tell the user to rotate the secret if the file was ever committed.

## 5. Summarize

Two or three lines: what changed, and the always-loaded size before and after.
