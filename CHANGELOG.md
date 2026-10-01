# Changelog

## 0.6.0 — 2026-09-30

- Personal knowledge: facts and decisions that hold across all of the user's projects live in `~/.claude/handover/personal/` (outside any repo, never committed) with their own index, loaded in every project. `/handover:learn` asks for the scope when it is unclear; the handover form labels such items Personal.
- Project overview: `/handover:learn overview` writes a short `.claude/knowledge/overview.md` (purpose, stack, layout, external services, status) that loads in every session; `/handover:write` keeps its Status line current.
- `/handover:tidy` covers both: size caps, scope mix-ups (repo-specific facts in the personal folder and the reverse), duplicates across scopes, a stale or missing overview. Its placement guide no longer sends the project overview to `CLAUDE.md`.
- Includes 0.5.0 (done offer, resume offer), which was not published separately.

## 0.5.0 — 2026-09-30

- Done offer: after substantial work in a session, once, Claude ends its final reply with a one-line offer of a handover note when the job is finished. It never closes the session (Claude Code gives neither Claude nor hooks a way to). New setting `offer_when_done`, on by default.
- Resume offer: when a fresh session starts and a recent handover note exists that the work has not moved past (no code commits since, under 21 days old), Claude offers in its first reply to continue from it, with the user's approval; `/handover:resume` then checks the note against the repository. New setting `offer_resume`, on by default.
- `/handover:write` tells a user who is wrapping up that they can end the session with `/exit`.

## 0.4.1 — 2026-09-30

- `/handover:write` fills every form to the tool's limit of four questions and continues in a second and third form (at most three) when more questions remain, instead of dropping them. New question types: open points, confirmations of things Claude is unsure it remembers, and an off-limits check. Many rule and fact candidates are split over several checkbox questions instead of being cut at four. The most important questions always come first.

## 0.4.0 — 2026-09-30

- New `/handover:setup` (manual only; adds about 60 tokens to every session): connects the plugin to Claude Code's status line so the threshold hook uses the real context window of the model in use and Claude Code's own percentage, including after `/model` switches. An existing status line keeps running and is restored exactly on removal; `settings.json` is backed up first.
- Without the bridge the hook still estimates from the transcript, as before, and its note says so.
- Includes everything from 0.2.1 and 0.3.0.

## 0.3.0 — 2026-09-27

- The question round is now a tap-to-answer form (`AskUserQuestion`): pre-filled recommended answers, checkboxes for what to keep, "Other" for free text; plain-text fallback with lettered choices. `/handover:tidy` uses the same form to pick what to apply.
- Fixed: the threshold hook never fired when the threshold was below 50%, because the re-arm level was fixed at 50%. It is now at most 70% of the threshold.
- The threshold note now carries the figures (usage, window, threshold and where it came from), and Claude quotes them, so a wrong window or threshold is visible immediately. The window is raised to 1,000,000 automatically if the transcript already shows more tokens than the configured window.
- `/handover:write` no longer starts on its own because a conversation feels long; it starts on request or on the plugin's note.

## 0.2.1 — 2026-09-27

Fixes found by a scripted dry run of every skill against a deliberately messy test project.

- Note age no longer resets after `git checkout` or `git pull`: the hooks use the last commit time for a committed, unchanged note.
- `/handover:resume` checks other branches for a newer note before resuming, and judges age by the note's `Updated:` line.
- `/handover:learn`, `/handover:rule`, and `/handover:write` report secrets already present in files they are about to change.
- `/handover:tidy` reports only `paths` frontmatter that actually fails to parse; valid unquoted globs are no longer flagged.
- `/handover:write`: candidates the user declines to keep are no longer marked Unverified; the Git state section is taken after rules and knowledge are saved; the note itself must not contain secrets.
- Entries are written in the language of the file they go into; new files use the user's language.

## 0.2.0 — 2026-09-27

- Project knowledge base in `.claude/knowledge/` with `/handover:learn`; the index loads in every session.
- `/handover:tidy` audits all memory layers.
- `/handover:write` asks which rules and knowledge to keep.

## 0.1.0 — 2026-09-27

- First release: threshold hook, PreCompact guard, note restore, `/handover:write`, `/handover:resume`, `/handover:rule`.
