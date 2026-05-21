from __future__ import annotations

import httpx
import pytest
import respx

from cli import (
    DeviceCodeResponse,
    TraktOAuthError,
    poll_for_token,
    request_device_code,
)


@respx.mock
def test_request_device_code_returns_parsed_response(trakt_creds):
    respx.post("https://api.trakt.tv/oauth/device/code").mock(
        return_value=httpx.Response(
            200,
            json={
                "device_code": "dev_abc",
                "user_code": "USER1234",
                "verification_url": "https://trakt.tv/activate",
                "expires_in": 600,
                "interval": 5,
            },
        )
    )

    result = request_device_code()

    assert isinstance(result, DeviceCodeResponse)
    assert result.device_code == "dev_abc"
    assert result.user_code == "USER1234"
    assert result.interval == 5
    assert result.expires_in == 600


@respx.mock
def test_poll_for_token_returns_tokens_on_200(trakt_creds):
    respx.post("https://api.trakt.tv/oauth/device/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "acc_xyz",
                "refresh_token": "ref_xyz",
                "expires_in": 7 * 24 * 3600,
                "created_at": 1_700_000_000,
                "token_type": "bearer",
                "scope": "public",
            },
        )
    )

    tokens = poll_for_token("dev_abc", interval=0, expires_in=10)

    assert tokens["access_token"] == "acc_xyz"
    assert tokens["refresh_token"] == "ref_xyz"
    assert tokens["expires_at"] == 1_700_000_000 + 7 * 24 * 3600


@respx.mock
def test_poll_for_token_keeps_polling_on_400(trakt_creds):
    route = respx.post("https://api.trakt.tv/oauth/device/token")
    route.side_effect = [
        httpx.Response(400, json={"error": "authorization_pending"}),
        httpx.Response(400, json={"error": "authorization_pending"}),
        httpx.Response(
            200,
            json={
                "access_token": "acc_ok",
                "refresh_token": "ref_ok",
                "expires_in": 100,
                "created_at": 1_700_000_000,
                "token_type": "bearer",
                "scope": "public",
            },
        ),
    ]

    tokens = poll_for_token("dev_abc", interval=0, expires_in=10)
    assert tokens["access_token"] == "acc_ok"
    assert route.call_count == 3


@respx.mock
@pytest.mark.parametrize("status,reason", [(404, "not_found"), (409, "already_used"), (410, "expired"), (418, "denied")])
def test_poll_for_token_raises_on_terminal_status(trakt_creds, status, reason):
    respx.post("https://api.trakt.tv/oauth/device/token").mock(
        return_value=httpx.Response(status, json={"error": reason})
    )
    with pytest.raises(TraktOAuthError):
        poll_for_token("dev_abc", interval=0, expires_in=10)


@respx.mock
def test_poll_for_token_times_out_after_expires_in(trakt_creds, monkeypatch):
    respx.post("https://api.trakt.tv/oauth/device/token").mock(
        return_value=httpx.Response(400, json={"error": "authorization_pending"})
    )
    # Force the polling loop to think time has advanced past expires_in immediately.
    calls = iter([0.0, 0.0, 100.0])
    monkeypatch.setattr("cli.time.monotonic", lambda: next(calls))

    with pytest.raises(TraktOAuthError, match="expired"):
        poll_for_token("dev_abc", interval=0, expires_in=10)
