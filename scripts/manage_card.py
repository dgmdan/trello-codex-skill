#!/usr/bin/env python3
"""Add comments, attachments, or completion status to a Trello card."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from trello_client import TrelloError, trello_post, trello_put


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Leave comments, upload attachments, or mark a Trello card as complete."
    )
    parser.add_argument("--card", required=True, help="Card short link or full ID.")
    parser.add_argument("--comment", help="Text to add as a comment on the card.")
    parser.add_argument(
        "--attachment",
        action="append",
        metavar="PATH",
        help="Path to a file to upload (repeatable).",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="Mark the card as complete (sets dueComplete to true).",
    )
    return parser.parse_args()


def validate_attachments(paths: Iterable[str]) -> list[Path]:
    validated: list[Path] = []
    for attachment in paths:
        path = Path(attachment).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Attachment not found or not a file: {attachment}")
        validated.append(path)
    return validated


def add_comment(card_id: str, text: str) -> None:
    trello_post(f"/cards/{card_id}/actions/comments", {"text": text})


def upload_attachment(card_id: str, path: Path) -> None:
    payload = {"name": path.name}
    files = {"file": (path.name, path.read_bytes(), _guess_content_type(path))}
    trello_post(f"/cards/{card_id}/attachments", payload, files=files)


def mark_complete(card_id: str) -> None:
    trello_put(f"/cards/{card_id}", {"dueComplete": "true"})


def _guess_content_type(path: Path) -> str:
    import mimetypes

    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def main() -> None:
    args = parse_args()
    actions_performed: list[str] = []

    if not (args.comment or args.attachment or args.complete):
        print(
            "Specify at least one action: --comment, --attachment, or --complete.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        if args.comment:
            add_comment(args.card, args.comment)
            actions_performed.append("Comment added.")

        if args.attachment:
            paths = validate_attachments(args.attachment)
            for path in paths:
                upload_attachment(args.card, path)
                actions_performed.append(f"Uploaded {path.name}.")

        if args.complete:
            mark_complete(args.card)
            actions_performed.append("Card marked complete.")
    except (TrelloError, FileNotFoundError) as err:
        print(err, file=sys.stderr)
        sys.exit(1)

    for action in actions_performed:
        print(f"- {action}")


if __name__ == "__main__":
    main()
