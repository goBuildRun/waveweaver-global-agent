#!/usr/bin/env python3
"""Create the Twitch EventSub webhook subscriptions used by the live overlay.

The script uses only :mod:`urllib` and is intentionally separate from
``twitch_codex.py``.  It can resolve a broadcaster login, then creates chat,
cheer, and raid subscriptions against the Helix API.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional


HELIX_BASE = "https://api.twitch.tv/helix"
SUBSCRIPTION_TYPES = ("channel.chat.message", "channel.cheer", "channel.raid")


def _required(value: Optional[str], name: str) -> str:
    clean = (value or "").strip()
    if not clean:
        raise ValueError(f"{name} is required")
    return clean


def _helix_request(
    method: str,
    path: str,
    *,
    client_id: str,
    token: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 15.0,
) -> Dict[str, Any]:
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"Client-Id": client_id, "Authorization": "Bearer " + token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(HELIX_BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return {"status": response.status, "body": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"message": raw[:300]}
        return {"status": exc.code, "body": body}
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Helix request failed: {exc.reason}") from exc


def resolve_broadcaster_id(
    *,
    client_id: str,
    token: str,
    broadcaster_id: Optional[str] = None,
    login: Optional[str] = None,
    timeout: float = 15.0,
) -> str:
    if broadcaster_id and broadcaster_id.strip():
        return broadcaster_id.strip()
    clean_login = _required(login, "TWITCH_BROADCASTER_LOGIN or --login")
    path = "/users?login=" + urllib.parse.quote(clean_login, safe="")
    result = _helix_request("GET", path, client_id=client_id, token=token, timeout=timeout)
    if result["status"] != 200:
        raise RuntimeError(f"Helix user lookup failed with HTTP {result['status']}")
    users = result["body"].get("data") or []
    if not users or not users[0].get("id"):
        raise RuntimeError("Helix user lookup returned no broadcaster")
    return str(users[0]["id"])


def subscription_payloads(
    *,
    broadcaster_id: str,
    callback_url: str,
    secret: str,
    chat_user_id: Optional[str] = None,
) -> Iterable[Dict[str, Any]]:
    user_id = (chat_user_id or broadcaster_id).strip()
    transport = {"method": "webhook", "callback": callback_url, "secret": secret}
    yield {
        "type": "channel.chat.message",
        "version": "1",
        "condition": {"broadcaster_user_id": broadcaster_id, "user_id": user_id},
        "transport": dict(transport),
    }
    yield {
        "type": "channel.cheer",
        "version": "1",
        "condition": {"broadcaster_user_id": broadcaster_id},
        "transport": dict(transport),
    }
    yield {
        "type": "channel.raid",
        "version": "1",
        "condition": {"to_broadcaster_user_id": broadcaster_id},
        "transport": dict(transport),
    }


def create_subscriptions(
    *,
    client_id: str,
    token: str,
    broadcaster_id: str,
    callback_url: str,
    secret: str,
    chat_user_id: Optional[str] = None,
    timeout: float = 15.0,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for payload in subscription_payloads(
        broadcaster_id=broadcaster_id,
        callback_url=callback_url,
        secret=secret,
        chat_user_id=chat_user_id,
    ):
        result = _helix_request(
            "POST",
            "/eventsub/subscriptions",
            client_id=client_id,
            token=token,
            payload=payload,
            timeout=timeout,
        )
        subscription = (result["body"].get("data") or [{}])[0]
        results.append(
            {
                "type": payload["type"],
                "status": result["status"],
                "subscription_id": subscription.get("id"),
                "subscription_status": subscription.get("status"),
                "message": result["body"].get("message"),
            }
        )
    return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create channel.chat.message, channel.cheer, and channel.raid webhook subscriptions.",
        epilog=(
            "Local tunnel: start `python3 server.py --port 8767`, then run "
            "`cloudflared tunnel --url http://127.0.0.1:8767` or `ngrok http 8767`. "
            "Pass the resulting HTTPS URL with /eventsub as --callback."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--callback", default=os.environ.get("TWITCH_EVENTSUB_CALLBACK"), help="Public HTTPS callback ending in /eventsub")
    parser.add_argument(
        "--broadcaster-id",
        default=os.environ.get("TWITCH_BROADCASTER_USER_ID") or os.environ.get("TWITCH_BROADCASTER_ID"),
    )
    parser.add_argument("--login", default=os.environ.get("TWITCH_BROADCASTER_LOGIN"), help="Broadcaster login, used when an ID is not supplied")
    parser.add_argument(
        "--chat-user-id",
        default=os.environ.get("TWITCH_EVENTSUB_USER_ID") or os.environ.get("TWITCH_USER_ID"),
        help="User ID for channel.chat.message; defaults to broadcaster ID",
    )
    parser.add_argument("--client-id", default=os.environ.get("TWITCH_CLIENT_ID"))
    parser.add_argument("--token", default=os.environ.get("TWITCH_USER_TOKEN"))
    parser.add_argument("--secret", default=os.environ.get("TWITCH_EVENTSUB_SECRET"))
    parser.add_argument("--dry-run", action="store_true", help="Print subscription types and callback without calling Helix")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        client_id = _required(args.client_id, "TWITCH_CLIENT_ID or --client-id")
        token = _required(args.token, "TWITCH_USER_TOKEN or --token")
        callback = _required(args.callback, "TWITCH_EVENTSUB_CALLBACK or --callback")
        secret = _required(args.secret, "TWITCH_EVENTSUB_SECRET or --secret")
        if not callback.startswith("https://") or not callback.rstrip("/").endswith("/eventsub"):
            raise ValueError("callback must be an HTTPS URL ending in /eventsub")
        if not 10 <= len(secret) <= 100:
            raise ValueError("EventSub secret must be 10-100 characters")
        if args.dry_run and not (args.broadcaster_id or "").strip():
            broadcaster_id = "BROADCASTER_ID_FROM_LOGIN"
            print("Broadcaster user id: resolved by Helix when run without --dry-run")
        else:
            broadcaster_id = resolve_broadcaster_id(
                client_id=client_id,
                token=token,
                broadcaster_id=args.broadcaster_id,
                login=args.login,
            )
        payloads = list(
            subscription_payloads(
                broadcaster_id=broadcaster_id,
                callback_url=callback,
                secret=secret,
                chat_user_id=args.chat_user_id,
            )
        )
        print("Callback:", callback)
        if not (args.dry_run and not (args.broadcaster_id or "").strip()):
            print("Broadcaster user id:", broadcaster_id)
        print("Requested subscriptions:", ", ".join(item["type"] for item in payloads))
        if args.dry_run:
            return 0
        for result in create_subscriptions(
            client_id=client_id,
            token=token,
            broadcaster_id=broadcaster_id,
            callback_url=callback,
            secret=secret,
            chat_user_id=args.chat_user_id,
        ):
            status = result["subscription_status"] or result["message"] or "request_failed"
            print(f"{result['type']}: HTTP {result['status']} ({status})")
            if result["status"] != 202:
                return 1
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

