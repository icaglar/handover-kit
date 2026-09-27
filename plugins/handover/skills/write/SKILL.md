---
name: write
description: Writes a session handover note to .claude/HANDOVER.md, asking the user about state that is not visible in the conversation before writing, and saves the rules the user set and the durable project knowledge gained during the session (to .claude/rules/ and .claude/knowledge/) once confirmed. Use this skill whenever the user asks for a handover or handoff note, wants to save or snapshot the current state, says they are wrapping up or ending the session, when the context is getting full, or when a context-threshold note appears in the context. Also use it for equivalent requests in other languages, such as "devir notu yaz".
---

# Write a handover note

Write the current state to `.claude/HANDOVER.md` at the project root, and capture what should outlive the session: rules the user set and durable project knowledge. Resuming from the note is `/handover:resume`; mid-session, a single rule is saved with `/handover:rule` and a single fact or decision with `/handover:learn`.

Ask the questions and write the note in the language the user is using in this conversation. If an existing note is written in a different language, keep that language so the note stays consistent.

## Why the question round exists

A summary extracted from the conversation only carries what is visible in this context window. What the user did outside the conversation, decisions they are holding in their head, and priorities that shifted are not here; only the user can supply them. If the question round is skipped, the note looks complete while it is not, and the next session starts from a wrong picture. Also, when the context is nearly full, details from early in the conversation may have faded or been compacted; the question round is the only way to verify them.

## 1. Gather state

Do not say anything to the user in this step; just gather.

- **From the conversation:** the active task, what is done, what is half-done, approaches that were tried and dropped and why, decisions and their reasons, rules and constraints the user set.
- **If there is a repo:** the current branch, `git status --short`, `git diff --stat`, `git log --oneline -5`.
- **Rules the user set:** instructions about *how to work* that should outlive this task: "always/never ...", "use X, not Y", conventions, and anything the user corrected more than once. Leave out one-off instructions that only concern the current task; those belong in the note's constraints section.
- **Existing rules:** read `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, the files under `.claude/rules/`, `~/.claude/CLAUDE.md`, and `~/.claude/rules/` if they exist, so you can drop candidate rules that are already covered and spot conflicts.
- **Knowledge gained:** facts and decisions about the project that will still be true after this task: decisions with lasting effect and their reasons, how something in the architecture or an environment actually works, root causes of bugs, and pitfalls. Leave out anything that only describes the current task's progress; that is state and stays in the note.
- **Existing knowledge:** the index `.claude/knowledge/INDEX.md` is already in your context if it exists; read the topic files your candidates touch, so you can drop duplicates and spot decisions that a new one supersedes.
- **Existing note:** if `.claude/HANDOVER.md` exists, read it. Update it rather than rewriting from scratch; keep what still holds and collapse finished items to a single line.

## 2. Question round

Before writing, ask at most 5 questions in a single message. Each question should be specific to this work and target something you cannot derive from the conversation. Good sources of questions:

- **Changes outside the conversation:** deploys, feedback from customers or the team, changes someone else made, files edited by hand.
- **Open decisions:** decisions not yet made, and which way the user is leaning.
- **Uncertain recollections:** points from early in the conversation you are not sure about. Ask them as confirmations, for example "My understanding is we decided on X — is that right?"
- **Priority:** what should happen first in the next session?
- **Off-limits:** any file, module, or decision that must not be touched?
- **What to keep permanently:** if you found candidate rules or knowledge, list them in one question, rules as R1, R2… and knowledge as K1, K2…, and ask which to keep. Point out any conflict with an existing rule or decision and ask which one wins. This counts as one question toward the 5-question limit.

Do not ask generic questions such as "Anything else to add?". If the user says "don't ask, just write", or leaves some questions unanswered, write the note anyway and mark the unanswered items as **Unverified**. Never save a rule or knowledge item the user did not confirm. Unconfirmed rule candidates go into the note's constraints section and unconfirmed knowledge into its decisions or current-state sections, marked Unverified.

## 3. Save confirmed rules and knowledge

Skip this step if the user confirmed nothing.

**Rules.** For each confirmed rule, follow the same procedure as the `/handover:rule` skill:

- **Wording:** one imperative, specific line, with a short reason when the rule is not self-evident.
- **Destination:** general project rules go to `.claude/rules/handover-rules.md`. Rules for specific files go to `.claude/rules/<topic>.md` with a `paths` frontmatter list of **quoted** globs (unquoted patterns starting with `*` or `{` break the YAML, and the rule then loads everywhere). Rules for all of the user's projects go to `~/.claude/rules/handover-rules.md`, never with `paths`, because path-scoped user-level rules are currently ignored.
- **Format:** append each rule as a list item ending with `(added YYYY-MM-DD)`. A new `handover-rules.md` starts with a `# Project rules` heading and the line "Captured with the handover plugin. Edit freely; delete rules that no longer apply."
- **Conflicts:** update or remove the losing rule instead of adding a contradicting one; ask before editing a file this plugin did not write, such as `CLAUDE.md`.

**Knowledge.** For each confirmed item, follow the same procedure as the `/handover:learn` skill:

- **Never store secrets or personal data**; `.claude/knowledge/` is committed. Record where a secret lives, never the secret.
- **Destination:** decisions go to `.claude/knowledge/decisions.md`; facts go to the topic file that fits (`architecture.md`, `environments.md`, `gotchas.md`, or a new plainly named file).
- **Format:** a decision is a `### <title> — YYYY-MM-DD` block with `Decision`, `Why`, optional `Rejected`, and `Status: active`; a fact is one line ending with `(added YYYY-MM-DD)`.
- **Superseded decisions** are marked `Status: superseded by "<new title>" (YYYY-MM-DD)`, never deleted.
- **Index:** update `.claude/knowledge/INDEX.md` (one line per topic file, under 60 lines; create it with a `# Project knowledge` heading if missing).

## 4. Write the note

Create the `.claude/` directory if it does not exist. Use this template. Do not delete an empty section; write "None" so it is clear the topic was considered and left empty on purpose.

```markdown
# Handover Note
Updated: YYYY-MM-DD HH:MM · Branch: <branch or "no repo">

## Goal
<1-3 sentences: what problem this work solves>

## Current state
<Where we stopped. Concrete: file paths, function names, what works and what doesn't>

## Decisions
- <decision> — reason: <why> (date)

## Tried and dropped
- <approach> — dropped because: <reason>

## From the user
<Answers from the question round; state that is not in the conversation>

## Open questions
- <question> (mark Unverified where applicable)

## Next steps
1. <A concrete first step that can be done right away>
2. ...

## Off-limits and constraints
- ...

## Saved this session
- Rules: <rule> → <file> (or "None")
- Knowledge: <item> → <file> (or "None")

## Git state
<status/diff summary or "no repo">
```

Writing rules:

- **Use absolute dates.** Write the date instead of "yesterday"; the note will be read days later.
- **Be concrete.** Not "fixed the auth part" but "token refresh in `api/auth.py` returned 401; fixed in `refresh_token()`".
- **Separate guesses from facts.** Mark anything you are not sure about as Unverified.
- **Keep it short.** Stay under 150 lines. Summarize finished work in a single line under "Current state" and remove items that no longer apply.

## 5. Close

Tell the user in 2-3 lines where the note is, which rules and knowledge were saved and where (if any), what the next step is, and that the note will be loaded automatically after `/clear` or `/compact`. Saved rules and the knowledge index load automatically in every future session.

## When a context-threshold note appears

If you see a note in the context saying the context window is filling up: first answer the user's current request, then offer to write a handover note and start the question round above. If the user says not now, do not push; continue with the work.
