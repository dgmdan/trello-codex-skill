---
name: trello-card-fetch
description: "Pull a Trello card's title, description, attachments, comments, and metadata so Codex can use the card as a shared working prompt. Trigger when the user asks to load a specific Trello card before changing code, docs, or tickets."
---

# Trello Card Fetch

## When to trigger
- The user says things like “load Trello card ABC123”, “give me the story from Trello”, or “what does the card for this ticket say?” before requesting a new change.
- The deliverable depends on acceptance criteria, attachments, or discussions stored on a Trello card, and you need that context before acting.

## Setup
- Export `TRELLO_API_KEY` so the helper can authenticate requests. Keep that secret in the environment and never commit it.
- If you run the helper without `TRELLO_TOKEN`, it now stops before reaching Trello and prints an authorization link so you can generate a token yourself; copy the returned token, export it as `TRELLO_TOKEN`, and rerun.
- Optionally override `TRELLO_API_BASE_URL` (defaults to `https://api.trello.com/1`) if you proxy Trello traffic.
- Remember the helper you run is `/Users/danmadere/.codex/skills/trello-card-fetch/scripts/fetch_card.py`.
- Optionally override `TRELLO_API_BASE_URL` (defaults to `https://api.trello.com/1`) if you proxy Trello traffic.
- Remember the helper you run is `/Users/danmadere/.codex/skills/trello-card-fetch/scripts/fetch_card.py`.

## Fetch a card
- Run the helper with the card short link or full ID:
  ```
  python /Users/danmadere/.codex/skills/trello-card-fetch/scripts/fetch_card.py <card-id> [--format markdown|json] [--actions-limit 100]
  ```
- The script fetches the card metadata, attachments, and `commentCard` actions so you can capture the full conversation around the work.
- Use `--format markdown` for a quick summary to paste into chat or `--format json` when you need structured data (for filtering or automation).

## Use the card context
- Paste the Markdown summary (or the filtered JSON fields) into the conversation so Codex receives the title, description, most recent comments, attachments, and metadata.
- Identify which attachments should influence the task (design assets, specs, spreadsheets) and note whether comments are approvals, clarifications, or blockers.
- Tie card context back to the change: “Follow the acceptance criteria in this card’s description” or “Use the attachments when drafting the release note.”

## References
- See `references/api-cards.md` for the Trello card endpoint, authentication, supported query parameters, and the fields the helper requests.
