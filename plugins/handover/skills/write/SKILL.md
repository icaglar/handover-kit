---
name: write
description: Writes a session handover note to .claude/HANDOVER.md, asking the user about state that is not visible in the conversation before writing, and saves the rules the user set and the durable knowledge gained during the session (to .claude/rules/, .claude/knowledge/, or the personal knowledge folder) once confirmed. Use this skill when the user asks for a handover or handoff note, wants to save or snapshot the current state, or says they are wrapping up or ending the session, when a context-threshold note from the plugin is present in the context, or for equivalent requests in other languages such as "devir notu yaz". Do not start it on your own because the conversation feels long: the plugin measures context usage and tells you when it is time.
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

## 2. Question round, as a form

Ask as a form, not as free text: the user should tap an answer or accept your suggestion, not compose a reply. Answering questions at the end of a long session is tiring; a pre-filled form takes seconds.

**Use the `AskUserQuestion` tool when it is available.** One call takes 1-4 questions with 2-4 options each; it adds an "Other" choice for free text by itself, so never add one. Rules for the form:

- **Pre-fill.** Put your best guess first in every question and mark it "(Recommended)", so the user can accept it in one tap. Derive guesses from the conversation and git state.
- **Short labels, details in descriptions.** Labels of 1-5 words; the full wording or reason goes in the option description. `header` is at most 12 characters.
- **Ask only what you cannot derive from the conversation, but then ask all of it.** Drop a question the conversation already answers. When a real question remains, ask it instead of guessing: a tap costs the user seconds, a wrong guess costs the next session.
- **Language.** Write the form in the language the user is using.

**Build the list of questions first, then ask them in as few forms as possible: fill each form to the tool's limit of 4 questions, and when more questions remain, show a second form, then a third.** Say one short line before a follow-up form ("Second form, 3 questions left"). Ask at most 3 forms (12 questions); what does not fit goes into the note as normal content, or as **Unverified** where it is a real open point.

The pool, in priority order. Ask them in this order, so that if anything is cut it is the least important; the first ones decide what gets saved. Include a question only if you cannot answer it from the conversation:

1. **Keep**: the candidate rules and project knowledge worth making permanent (knowledge = decisions with their reason, gotchas, environment details). Leave out what `CLAUDE.md`, the rules, or the knowledge base already hold, and anything that only concerns the current task. The tool needs 2-4 options per question, so shape it by the number of candidates:
   - **none:** skip.
   - **one:** a single-choice question with the options "Save it (Recommended)" and "Only in the note".
   - **2-4:** one `multiSelect` question, one option per candidate. Label with a prefix and 1-3 words ("Rule: pytest -x", "Fact: ERP pageSize", "Personal: Hetzner host" for knowledge that holds across all the user's projects); the full wording or reason goes in the description. If a candidate conflicts with or replaces an existing rule or decision, say so in its description ("replaces the active Celery and RQ decisions").
   - **more than 4:** several Keep questions, splitting the candidates as evenly as possible into groups of 2-4 (5 becomes 3+2, 9 becomes 3+3+3), the most durable first. Never leave a group of one.
2. **Next step** (single choice): the most likely first task for the next session, from the conversation and git state, recommended option first.
3. **Outside chat** (single choice): "Did anything change outside this conversation (deploys, feedback, edits by hand)?" Options "Nothing changed (Recommended)" and "Not sure". Say in the question text that "Other" lets the user type details. This cannot be pre-filled, so it stays a one-tap question.
4. **Open points**: one single-choice question for each point still open in the conversation (a decision not made yet, a question that blocks the first next step, scope such as "is X part of this PR?"). Options are the plausible answers, recommended first, and "Not decided yet" last. An answer goes into Decisions (with the user's reason if they gave one); "Not decided yet" stays under Open questions.
5. **Confirmations**: one single-choice question for each point from early in the conversation you are not sure you remember correctly (a decision, a dropped approach, a number). Options "Right (Recommended)" and "Not sure"; "Other" lets the user correct it. Anything left unconfirmed is marked Unverified in the note.
6. **Off-limits check**: "Anything to leave alone besides what we discussed?" Options "Only what we discussed (Recommended)" and "Not sure"; "Other" for details. Ask it only if the work touches shared or sensitive areas (migrations, deploys, other people's code).

Constraints the user stated ("don't touch migrations/") need no question: write them into the note directly.

**Without `AskUserQuestion`** (a subagent, another client, or the tool is unavailable or returns no answer): ask the same pool in plain text, in the same batches of four, one message per batch: a numbered list, each question with lettered choices and your recommendation marked, so the user can reply "1a 3a" or "all recommended".

**If the user dismisses a form or says "don't ask, just write":** stop asking, do not show the next form, and write the note anyway. Text typed under "Other" goes into the note's "From the user" section. Only save rules and knowledge the user confirmed. A candidate the user *declined* to make permanent still goes into the note if it matters for the current work, written normally: the user did not doubt it, they just did not want to keep it beyond this task. Mark **Unverified** only what the user left unanswered and you could not confirm from the conversation.

## 3. Save confirmed rules and knowledge

Skip this step if the user confirmed nothing.

**Rules.** For each confirmed rule, follow the same procedure as the `/handover:rule` skill:

- **Wording:** one imperative, specific line, with a short reason when the rule is not self-evident.
- **Destination:** general project rules go to `.claude/rules/handover-rules.md`. Rules for specific files go to `.claude/rules/<topic>.md` with a `paths` frontmatter list of **quoted** globs (unquoted patterns starting with `*` or `{` break the YAML, and the rule then loads everywhere). Rules for all of the user's projects go to `~/.claude/rules/handover-rules.md`, never with `paths`, because path-scoped user-level rules are currently ignored.
- **Format:** append each rule as a list item ending with `(added YYYY-MM-DD)`. A new `handover-rules.md` starts with a `# Project rules` heading and the line "Captured with the handover plugin. Edit freely; delete rules that no longer apply."
- **Conflicts:** update or remove the losing rule instead of adding a contradicting one; ask before editing a file this plugin did not write, such as `CLAUDE.md`.
- **Language:** write each entry in the language of the file you add it to; a new file uses the language the user is using.

**Knowledge.** For each confirmed item, follow the same procedure as the `/handover:learn` skill:

- **Never store secrets or personal data**; `.claude/knowledge/` is committed. Record where a secret lives, never the secret. If a file you are about to change already contains something that looks like a secret (password, API key, token, private key, credentials in a connection string), tell the user before writing anything, and suggest removing it and rotating the secret; removing it from the file does not remove it from git history.
- **Destination:** decisions go to `.claude/knowledge/decisions.md`; facts go to the topic file that fits (`architecture.md`, `environments.md`, `gotchas.md`, or a new plainly named file). Items labelled Personal go to `~/.claude/handover/personal/` (under `$CLAUDE_CONFIG_DIR` if set) with its own `INDEX.md` of at most 30 lines, as in `/handover:learn`; never copy a fact into both scopes.
- **Format:** a decision is a `### <title> — YYYY-MM-DD` block with `Decision`, `Why`, optional `Rejected`, and `Status: active`; a fact is one line ending with `(added YYYY-MM-DD)`.
- **Superseded decisions** are marked `Status: superseded by "<new title>" (YYYY-MM-DD)`, never deleted.
- **Index:** update `.claude/knowledge/INDEX.md` (one line per topic file, under 60 lines; create it with a `# Project knowledge` heading if missing).
- **Overview:** if `.claude/knowledge/overview.md` exists and this session changed what it describes (stack, layout, external services, status), update only the affected lines and the date, and say so in the closing lines. Do not create an overview here; that is `/handover:learn`.

## 4. Write the note

Re-run `git status --short` right before writing, so the Git state section also lists the rule and knowledge files you changed in step 3. Create the `.claude/` directory if it does not exist. Use this template. Do not delete an empty section; write "None" so it is clear the topic was considered and left empty on purpose.

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
- **No secrets or personal data.** The note may be committed. If a password, key, or token came up in the conversation, write where it is stored, never the value.
- **Keep it short.** Stay under 150 lines. Summarize finished work in a single line under "Current state" and remove items that no longer apply.

## 5. Close

Tell the user in 2-3 lines where the note is, which rules and knowledge were saved and where (if any), what the next step is, and that the note will be loaded automatically after `/clear` or `/compact`. Saved rules and the knowledge index load automatically in every future session. If the user is wrapping up, add that they can end the session now with `/exit` (you cannot close it yourself) and pick the work up later: in a fresh session Claude sees the note and offers to continue from it (you can also run `/handover:resume`). After `/clear` or `/compact` the note is loaded on its own.

## When to start

Start only when (a) the user asked for a handover or to save state, or (b) a context-threshold note from the plugin is in the context. Do not start because the conversation feels long or you guess the context is filling up; the plugin measures usage, and asking too early interrupts the work.

When the threshold note is present: first answer the user's current request, then say in one short line where the context stands, quoting the figures from the note (for example "Context is at about 72% (144k of 200k tokens, threshold 70%)"), then show the form. Follow the note's hint if the user says their own indicator shows a different figure. If the user dismisses the form, treat that as "not now" and continue with the work; do not ask again until the plugin adds a new note.
