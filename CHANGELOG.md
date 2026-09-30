# Changelog

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
