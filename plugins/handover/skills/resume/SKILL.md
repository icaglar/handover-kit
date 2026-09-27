---
name: resume
description: Reads the .claude/HANDOVER.md handover note and continues the work from where it stopped, after checking the note against git state and the files. Use this skill whenever the user asks to pick up where they left off, continue from the handover note, asks "where were we?", or returns to earlier work in a new session. Also use it for equivalent requests in other languages, such as "kaldığımız yerden devam".
---

# Resume from a handover note

The note is a previous session's own summary, not current truth. Code, the branch, or the note itself may have changed or gone stale since. So do not start working before verifying it.

Talk to the user in the language they are using in this conversation.

1. **Read the note.** Read `.claude/HANDOVER.md` at the project root. If it does not exist, say so, mention that `/handover:write` can create one, and stop.
2. **Check it against reality.**
   - Is the current branch the one in the note? If not, stop and ask the user.
   - Do `git status` and recent commits contradict the note? List any contradictions; the current files win.
   - If the note is older than 7 days, say so explicitly.
3. **Load relevant knowledge.** If the project knowledge index (`.claude/knowledge/INDEX.md`, already in your context when it exists) lists topic files related to the first next step, read them before proposing it.
4. **Summarize.** A status summary of at most 5 lines, plus the first next step.
5. **Get confirmation.** If open questions block the first step, ask them first. Otherwise, ask the user to confirm before starting the first step.
