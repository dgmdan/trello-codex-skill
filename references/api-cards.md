# Trello card endpoint

Source: [GET /cards/{id}](https://developer.atlassian.com/cloud/trello/rest/api-group-cards/#api-cards-id-get) (Trello Cloud REST API reference, February 2026).

## Basics
- **Endpoint:** `GET https://api.trello.com/1/cards/{id}`.
- **Authentication:** Supply `key` and `token` as query parameters (the curl example in the reference shows `?key=APIKey&token=APIToken`).
- **Path parameter:** `id` is the card short link, full ID, or numeric `idShort`.

## Relevant query parameters
- `fields`: comma-separated card fields (name, desc, due, badges, shortLink/Url, dateLastActivity, etc.).
- `actions`: request actions such as `commentCard` when you want comment history.
- `attachments` (true/false) plus `attachment_fields` to fetch attachment metadata (name, url, bytes, mime type, upload flag).
- `labels`: true plus `label_fields=name,color` to include label names and colors.
- `members` / `member_fields`: include assigned members (`fullName`, `username`) for attribution.
- `customFieldItems`: include custom fields when the card uses them.

## Why the helper requests these fields
- The description, badges, and list/members metadata keep the requirements/acceptance criteria visible.
- Fetching `commentCard` actions captures the recorded discussion and decisions for reuse as part of the prompt (the actions request is documented under the same `/cards/{id}` block).
- Attachments frequently contain design assets, spreadsheets, or specs; we request them explicitly so their names, URLs, and sizes can be surfaced for manual review.
