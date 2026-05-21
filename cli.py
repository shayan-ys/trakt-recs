"""trakt-recs: Trakt watch-history puller + context emitter for Claude.

Subcommands: auth, pull, context, status.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv

TRAKT_BASE = "https://api.trakt.tv"


class TraktOAuthError(RuntimeError):
    """Raised on terminal OAuth states (denied, expired, unknown)."""


@dataclass(frozen=True)
class DeviceCodeResponse:
    device_code: str
    user_code: str
    verification_url: str
    expires_in: int
    interval: int


def state_dir() -> Path:
    """Resolve the state directory. Honors TRAKT_STATE_DIR env var; defaults next to cli.py."""
    override = os.environ.get("TRAKT_STATE_DIR")
    if override:
        return Path(override)
    return Path(__file__).parent / ".state"


def _tokens_path() -> Path:
    return state_dir() / "tokens.json"


def save_tokens(tokens: dict) -> None:
    d = state_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = _tokens_path()
    p.write_text(json.dumps(tokens, indent=2))
    p.chmod(0o600)


def load_tokens() -> dict:
    p = _tokens_path()
    if not p.exists():
        raise TraktOAuthError(
            "not authenticated — run `python cli.py auth` first (no tokens.json in state dir)"
        )
    return json.loads(p.read_text())


def refresh_access_token() -> dict:
    """Use the stored refresh_token to get a new access+refresh pair. Persists both."""
    cid, csec = _client_creds()
    current = load_tokens()
    r = httpx.post(
        f"{TRAKT_BASE}/oauth/token",
        json={
            "refresh_token": current["refresh_token"],
            "client_id": cid,
            "client_secret": csec,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "refresh_token",
        },
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )
    if r.status_code != 200:
        err = ""
        try:
            err = r.json().get("error", "")
        except Exception:
            err = r.text[:200]
        raise TraktOAuthError(f"refresh failed ({r.status_code}): {err}")
    data = r.json()
    data["expires_at"] = int(data["created_at"]) + int(data["expires_in"])
    save_tokens(data)
    return data


def _client_creds() -> tuple[str, str]:
    cid = os.environ.get("TRAKT_CLIENT_ID")
    csec = os.environ.get("TRAKT_CLIENT_SECRET")
    if not cid or not csec:
        raise TraktOAuthError(
            "TRAKT_CLIENT_ID/TRAKT_CLIENT_SECRET missing. "
            "Copy .env.example to .env and fill in your Trakt app credentials, "
            "or export them in your environment."
        )
    return cid, csec


def request_device_code() -> DeviceCodeResponse:
    """Step 1 of Device Code flow. Returns user-facing code + polling params."""
    cid, _ = _client_creds()
    r = httpx.post(
        f"{TRAKT_BASE}/oauth/device/code",
        json={"client_id": cid},
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )
    r.raise_for_status()
    data = r.json()
    return DeviceCodeResponse(
        device_code=data["device_code"],
        user_code=data["user_code"],
        verification_url=data["verification_url"],
        expires_in=int(data["expires_in"]),
        interval=int(data["interval"]),
    )


_TERMINAL_OAUTH_STATUSES = {404: "not_found", 409: "already_used", 410: "expired", 418: "denied"}


def poll_for_token(device_code: str, interval: int, expires_in: int) -> dict:
    """Step 2 of Device Code flow. Polls until success, terminal error, or timeout.

    Returns a tokens dict augmented with `expires_at` (unix seconds).
    """
    cid, csec = _client_creds()
    start = time.monotonic()
    poll_interval = max(1, interval)

    while True:
        if time.monotonic() - start > expires_in:
            raise TraktOAuthError("device code expired before user authorized")

        r = httpx.post(
            f"{TRAKT_BASE}/oauth/device/token",
            json={"code": device_code, "client_id": cid, "client_secret": csec},
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

        if r.status_code == 200:
            data = r.json()
            data["expires_at"] = int(data["created_at"]) + int(data["expires_in"])
            return data
        if r.status_code == 400:
            # authorization_pending — keep polling
            time.sleep(poll_interval)
            continue
        if r.status_code == 429:
            # slow_down — RFC 8628 says add 5s
            poll_interval += 5
            retry_after = r.headers.get("Retry-After")
            time.sleep(int(retry_after) if retry_after and retry_after.isdigit() else poll_interval)
            continue
        if r.status_code in _TERMINAL_OAUTH_STATUSES:
            raise TraktOAuthError(
                f"OAuth terminal state {r.status_code}: {_TERMINAL_OAUTH_STATUSES[r.status_code]}"
            )
        raise TraktOAuthError(f"unexpected status {r.status_code}: {r.text[:200]}")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="trakt-recs", description=__doc__)
    parser.add_subparsers(dest="cmd", required=True)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
