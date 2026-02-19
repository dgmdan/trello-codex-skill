#!/usr/bin/env python3
"""Fetch Trello card details, comments, and attachments for reuse as a working prompt."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from datetime import datetime
from typing import Any, Dict, Iterable

from trello_client import TrelloError, trello_get


def human_readable_bytes(num: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num)
    for unit in units:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"


def format_datetime(value: str) -> str:
    if not value:
        return "n/a"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.isoformat()
    except ValueError:
        return value


def format_labels(labels: Iterable[Dict[str, Any]]) -> str:
    parts: list[str] = []
    for label in labels:
        name = label.get("name") or label.get("id") or "<label>"
        color = label.get("color")
        if color:
            parts.append(f"{name} ({color})")
        else:
            parts.append(name)
    return ", ".join(parts) if parts else "<none>"


def format_members(members: Iterable[Dict[str, Any]]) -> str:
    parts: list[str] = []
    for member in members:
        name = member.get("fullName") or member.get("username") or member.get("id") or "<member>"
        username = member.get("username")
        if username and username not in name:
            parts.append(f"{name} (@{username})")
        else:
            parts.append(name)
    return ", ".join(parts) if parts else "<none>"


def summarize_badges(badges: Dict[str, Any]) -> str:
    if not badges:
        return ""
    pieces: list[str] = []
    if badges.get("due"):
        pieces.append(f"due {format_datetime(badges.get('due'))}")
    if badges.get("dueComplete"):
        pieces.append("completed")
    if badges.get("subscribed"):
        pieces.append("subscribed")
    if badges.get("attachments"):
        pieces.append(f"{badges['attachments']} attachments")
    if badges.get("checkItems"):
        pieces.append(f"{badges.get('checkItemsChecked', 0)}/{badges['checkItems']} checklist items")
    if badges.get("votes"):
        pieces.append(f"votes: {badges['votes']}")
    return ", ".join(pieces)


def markdown_summary(card: Dict[str, Any]) -> str:
    lines: list[str] = []
    title = card.get("name") or "<unnamed card>"
    url = card.get("shortUrl") or card.get("url")
    lines.append(f"## Trello card: {title}")
    if url:
        lines.append(f"[Open in Trello]({url})")
    lines.append("")

    labels = format_labels(card.get("labels", []))
    due = format_datetime(card.get("due"))
    members = format_members(card.get("members", []))
    badges = summarize_badges(card.get("badges", {}))
    metadata = [
        f"- Short link: {card.get('shortLink', '<n/a>')}",
        f"- Due: {due}",
        f"- Members: {members}",
        f"- Labels: {labels}",
    ]
    if badges:
        metadata.append(f"- Badges: {badges}")
    lines.extend(metadata)
    if card.get("dateLastActivity"):
        lines.append(f"- Last activity: {format_datetime(card['dateLastActivity'])}")
    lines.append("")

    description = card.get("desc", "").strip()
    lines.append("### Description")
    if description:
        lines.append(textwrap.indent(description, "  "))
    else:
        lines.append("<no description>")
    lines.append("")

    attachments = card.get("attachments", [])
    lines.append("### Attachments")
    if attachments:
        for attachment in attachments:
            name = attachment.get("name") or "Attachment"
            att_url = attachment.get("url") or attachment.get("downloadUrl")
            meta: list[str] = []
            size = attachment.get("bytes")
            if isinstance(size, int):
                meta.append(human_readable_bytes(size))
            mime = attachment.get("mimeType")
            if mime:
                meta.append(mime)
            if attachment.get("isUpload"):
                meta.append("uploaded")
            meta_text = f" ({', '.join(meta)})" if meta else ""
            if att_url:
                lines.append(f"- [{name}]({att_url}){meta_text}")
            else:
                lines.append(f"- {name}{meta_text}")
    else:
        lines.append("<no attachments>")
    lines.append("")

    actions = card.get("actions", [])
    lines.append("### Comments")
    if actions:
        for action in actions:
            data = action.get("data", {})
            text = data.get("text") or data.get("comment") or data.get("desc")
            if not text:
                continue
            author = action.get("memberCreator", {})
            author_name = (
                author.get("fullName") or author.get("username") or author.get("id") or "Unknown"
            )
            date = format_datetime(action.get("date"))
            lines.append(f"- {date} by {author_name}: {text}")
    else:
        lines.append("<no comments>")

    return "\n".join(lines)


def load_card(card_id: str, action_limit: int) -> Dict[str, Any]:
    params = {
        "fields": ",".join(
            [
                "name",
                "desc",
                "due",
                "dueComplete",
                "shortUrl",
                "shortLink",
                "dateLastActivity",
                "badges",
                "idBoard",
                "idList",
                "customFieldItems",
            ]
        ),
        "attachments": "true",
        "attachment_fields": ",".join(
            ["name", "url", "downloadUrl", "bytes", "date", "edgeColor", "mimeType", "isUpload"]
        ),
        "labels": "true",
        "label_fields": "name,color",
        "members": "true",
        "member_fields": "fullName,username",
        "actions": "commentCard",
        "actions_limit": str(action_limit),
        "actions_fields": "id,date,memberCreator,data",
    }
    path = f"/cards/{card_id}"
    return trello_get(path, params)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a Trello card with comments and attachments for use as prompt context."
    )
    parser.add_argument("card_id", help="Trello card short link ID or full card ID")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Markdown is human-readable; json is machine-structured.",
    )
    parser.add_argument(
        "--actions-limit",
        type=int,
        default=100,
        help="Maximum number of comment actions to fetch (default: 100)",
    )
    args = parser.parse_args()

    try:
        card = load_card(args.card_id, args.actions_limit)
    except TrelloError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(card, ensure_ascii=False, indent=2))
    else:
        print(markdown_summary(card))


if __name__ == "__main__":
    main()
