#!/usr/bin/env python3
"""Create a new Trello card on the requested board and list."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from trello_client import TrelloError, trello_get, trello_post


def resolve_list(board_id: str, list_ref: str) -> Dict[str, Any]:
    params = {"fields": "id,name", "filter": "open"}
    candidates = trello_get(f"/boards/{board_id}/lists", params)
    normalized = list_ref.strip().lower()
    for candidate in candidates:
        if candidate.get("id") == list_ref:
            return candidate
        name = (candidate.get("name") or "").strip()
        if name.lower() == normalized:
            return candidate
    raise TrelloError(f"Cannot find list {list_ref!r} on board {board_id}.")


def summarize_card(card: Dict[str, Any], board: Dict[str, Any], list_info: Dict[str, Any]) -> str:
    lines: List[str] = [
        "Created Trello card:",
        f"- Name: {card.get('name')}",
        f"- Board: {board.get('name')} ({board.get('shortLink')})",
        f"- List: {list_info.get('name')}",
        f"- URL: {card.get('shortUrl')}",
        f"- ID: {card.get('id')}",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a Trello card on a board/list and return the card details."
    )
    parser.add_argument("--board", required=True, help="Board short link or full ID.")
    parser.add_argument(
        "--list",
        dest="list_ref",
        required=True,
        help="List name (case-insensitive) or list ID on the board.",
    )
    parser.add_argument("--name", required=True, help="Title for the new card.")
    parser.add_argument("--desc", default="", help="Card description.")
    parser.add_argument("--due", help="ISO 8601 due date/time (optional).")
    parser.add_argument(
        "--pos",
        default="bottom",
        help="Card position (top, bottom, or fractional value). Defaults to bottom.",
    )
    parser.add_argument(
        "--label",
        dest="label_ids",
        action="append",
        metavar="LABEL_ID",
        help="Label ID to attach (repeatable).",
    )
    parser.add_argument(
        "--member",
        dest="member_ids",
        action="append",
        metavar="MEMBER_ID",
        help="Member ID to assign to the card (repeatable).",
    )
    parser.add_argument(
        "--url-source",
        dest="url_source",
        help="Optional URL to attach to the card when creating it.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format for the created card.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        board = trello_get(f"/boards/{args.board}", {"fields": "id,name,shortLink"})
        list_info = resolve_list(board["id"], args.list_ref)
        payload: Dict[str, Any] = {
            "name": args.name.strip(),
            "idList": list_info["id"],
            "desc": args.desc,
            "pos": args.pos,
        }
        if args.due:
            payload["due"] = args.due
        if args.label_ids:
            payload["idLabels"] = ",".join(args.label_ids)
        if args.member_ids:
            payload["idMembers"] = ",".join(args.member_ids)
        if args.url_source:
            payload["urlSource"] = args.url_source

        card = trello_post("/cards", payload)
    except TrelloError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(card, ensure_ascii=False, indent=2))
    else:
        print(summarize_card(card, board, list_info))


if __name__ == "__main__":
    main()
