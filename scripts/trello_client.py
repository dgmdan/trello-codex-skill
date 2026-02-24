#!/usr/bin/env python3
"""Shared helpers for communicating with the Trello REST API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, Optional, Tuple

BASE_URL = os.environ.get("TRELLO_API_BASE_URL", "https://api.trello.com/1").rstrip("/")
AUTHORIZATION_BASE = "https://trello.com/1/authorize"
AUTH_SCOPE = os.environ.get("TRELLO_AUTH_SCOPE", "read,write")
AUTH_EXPIRATION = "never"
AUTH_NAME = "Codex Trello Access"
REQUEST_TIMEOUT = 30


class TrelloError(Exception):
    pass


def authorization_url(key: str) -> str:
    params = {
        "key": key,
        "scope": AUTH_SCOPE,
        "expiration": AUTH_EXPIRATION,
        "name": AUTH_NAME,
        "response_type": "token",
    }
    return f"{AUTHORIZATION_BASE}?{urllib.parse.urlencode(params)}"


def authorization_instructions(key: str) -> str:
    url = authorization_url(key)
    return (
        " To grant access, open the following link while signed in as a board member, "
        "approve the addon, and set TRELLO_TOKEN to the token Trello returns: "
        f"{url}"
    )


def require_api_key() -> str:
    value = os.getenv("TRELLO_API_KEY")
    if not value:
        raise TrelloError("TRELLO_API_KEY is not configured. Export it before running the helper.")
    return value


def require_token(key: str) -> str:
    token = os.getenv("TRELLO_TOKEN")
    if not token:
        raise TrelloError(
            "TRELLO_TOKEN is not configured. The helper can build an authorization link "
            "so you can create one." + authorization_instructions(key)
        )
    return token


def build_auth_params(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    auth: Dict[str, Any] = dict(extra or {})
    key = require_api_key()
    token = require_token(key)
    auth["key"] = key
    auth["token"] = token
    return auth


def _encode_multipart_formdata(
    fields: Dict[str, Any], files: Dict[str, Tuple[str, bytes, str]]
) -> Tuple[str, bytes]:
    boundary = uuid.uuid4().hex
    buffer = bytearray()
    for name, value in fields.items():
        buffer.extend(f"--{boundary}\r\n".encode())
        buffer.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        buffer.extend(str(value).encode())
        buffer.extend(b"\r\n")
    for name, (filename, data, content_type) in files.items():
        buffer.extend(f"--{boundary}\r\n".encode())
        buffer.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode()
        )
        buffer.extend(data)
        buffer.extend(b"\r\n")
    buffer.extend(f"--{boundary}--\r\n".encode())
    return boundary, bytes(buffer)


def trello_request(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET",
    files: Optional[Dict[str, Tuple[str, bytes, str]]] = None,
) -> Any:
    method = method.upper()
    auth_params = build_auth_params(params)
    url = f"{BASE_URL}{path}"
    if method == "GET":
        query = urllib.parse.urlencode(auth_params, doseq=True)
        url = f"{url}?{query}"
        request = urllib.request.Request(url, method=method)
    else:
        if files:
            boundary, body = _encode_multipart_formdata(auth_params, files)
            request = urllib.request.Request(url, data=body, method=method)
            request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        else:
            body = urllib.parse.urlencode(auth_params, doseq=True).encode()
            request = urllib.request.Request(url, data=body, method=method)
            request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        instructions = ""
        if err.code in {401, 403}:
            instructions = authorization_instructions(auth_params.get("key", ""))
        raise TrelloError(
            f"HTTP {err.code} calling {url}: {err.reason}.{instructions}"
        ) from err
    except urllib.error.URLError as err:
        raise TrelloError(f"Unable to reach Trello: {err.reason}") from err


def trello_get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    return trello_request(path, params=params, method="GET")


def trello_post(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Tuple[str, bytes, str]]] = None,
) -> Any:
    return trello_request(path, params=params, method="POST", files=files)


def trello_put(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Tuple[str, bytes, str]]] = None,
) -> Any:
    return trello_request(path, params=params, method="PUT", files=files)
