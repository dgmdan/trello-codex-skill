# Trello Card Fetch Skill

This Codex skill is packaged as `dgmdan/trello-codex-skill`. It runs a helper script that loads the contents of a Trello card so Codex can use the title, description, attachments, comments, and metadata as shared context before making changes.

## Features
- Fetches card metadata plus `commentCard` actions so you can read the conversation around the work.
- Supports Markdown or JSON output for easy pasting or automation.
- Honors optional overrides such as `TRELLO_API_BASE_URL` when you proxy Trello traffic.
- Creates new cards by board and list, returning the new ID and short link so you can confirm placement.

## Prerequisites
1. Python (the helper script is plain Python and has no extra dependencies outside the standard library).
2. Trello credentials available as environment variables (the authentication flow is two-step and not the usual single-token REST pattern):
   - `TRELLO_API_KEY` (you must obtain this first from https://trello.com/app-key and export it immediately; Trello won’t issue a token unless the key is present).
   - `TRELLO_TOKEN` (once the API key is set, run the helper without a token and it will print an authorization link; visit that link, grant access, copy the token Trello returns, and export it so the script can authenticate).
   - `TRELLO_AUTH_SCOPE` (optional, defaults to `read,write`; adjust when operating against a Trello workspace with different scope requirements).
3. Optional: `TRELLO_API_BASE_URL` if you need to proxy the requests.

## Installation
1. Copy or clone the entire `trello-card-fetch` folder (with `SKILL.md`, `scripts/`, etc.) into your own `$CODEX_HOME/skills/` directory.
2. Make sure the helper script is executable by running `chmod +x $CODEX_HOME/skills/trello-card-fetch/scripts/fetch_card.py`.
3. Export the required environment variables in whatever shell Codex uses (`~/.zshrc`, `~/.bash_profile`, etc.).
4. Restart the Codex app so it loads the new skill.

## Usage
Once installed and the credentials are set, invoke the script directly or let the skill trigger when a user asks to load a Trello card. For quick reference, run:

```
python $CODEX_HOME/skills/trello-card-fetch/scripts/fetch_card.py <card-id> [--format markdown|json] [--actions-limit 100]
```

Then paste the markdown summary (or filtered JSON) into your conversation so Codex can see the same information you would get from the card.

### Create a card

```
python $CODEX_HOME/skills/trello-card-fetch/scripts/create_card.py \
  --board <board-shortlink-or-id> \
  --list "<list-name-or-id>" \
  --name "Card title" \
  [--desc "Longer description"] \
  [--due 2026-03-01T12:00:00Z] \
  [--pos top] \
  [--label <label-id> ...] \
  [--member <member-id> ...] \
  [--url-source https://example.com/proposal] \
  [--format summary|json]
```

The new helper requires the same `TRELLO_API_KEY`/`TRELLO_TOKEN` environment that the fetch script uses. The `--list` argument accepts either the Trello list ID or its display name (case-insensitive), and you can repeat `--label` or `--member` to attach multiple IDs. Choose `--format json` when you want the raw card payload and follow-on automation.
