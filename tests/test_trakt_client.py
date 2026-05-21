from __future__ import annotations

import time

import httpx
import pytest
import respx

from cli import TraktOAuthError, get_authenticated, pull_all, save_tokens


@respx.mock
def test_get_sends_required_trakt_headers(trakt_creds, tokens_file):
    route = respx.get("https://api.trakt.tv/sync/history").mock(
        return_value=httpx.Response(200, json=[], headers={"X-Pagination-Page-Count": "1"})
    )

    response, page_count = get_authenticated("/sync/history")

    assert response == []
    assert page_count == 1
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer test_access_abc"
    assert sent.headers["trakt-api-version"] == "2"
    assert sent.headers["trakt-api-key"] == "test_client_id"


@respx.mock
def test_get_refreshes_when_token_near_expiry(trakt_creds, state_dir):
    # Token expires in 12 hours — within the 1-day refresh window.
    save_tokens({
        "access_token": "stale_acc",
        "refresh_token": "stale_ref",
        "expires_at": int(time.time()) + 12 * 3600,
        "created_at": int(time.time()) - 6 * 24 * 3600,
    })
    refresh_route = respx.post("https://api.trakt.tv/oauth/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "fresh_acc",
                "refresh_token": "fresh_ref",
                "expires_in": 7 * 24 * 3600,
                "created_at": int(time.time()),
                "token_type": "bearer",
                "scope": "public",
            },
        )
    )
    history_route = respx.get("https://api.trakt.tv/sync/history").mock(
        return_value=httpx.Response(200, json=[], headers={"X-Pagination-Page-Count": "1"})
    )

    get_authenticated("/sync/history")

    assert refresh_route.called
    assert history_route.calls.last.request.headers["Authorization"] == "Bearer fresh_acc"


@respx.mock
def test_get_retries_on_429_honoring_retry_after(trakt_creds, tokens_file, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("cli.time.sleep", lambda s: sleeps.append(s))

    route = respx.get("https://api.trakt.tv/sync/history")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "2"}),
        httpx.Response(200, json=[{"id": 1}], headers={"X-Pagination-Page-Count": "1"}),
    ]

    data, _ = get_authenticated("/sync/history")
    assert data == [{"id": 1}]
    assert sleeps == [2.0]


@respx.mock
def test_get_raises_on_401(trakt_creds, tokens_file):
    respx.get("https://api.trakt.tv/sync/history").mock(
        return_value=httpx.Response(401, json={"error": "invalid_token"})
    )
    with pytest.raises(TraktOAuthError, match="401"):
        get_authenticated("/sync/history")


@respx.mock
def test_pull_history_walks_all_pages(trakt_creds, tokens_file):
    history_route = respx.get("https://api.trakt.tv/sync/history")
    history_route.side_effect = [
        httpx.Response(200, json=[{"id": i} for i in range(100)], headers={"X-Pagination-Page-Count": "3"}),
        httpx.Response(200, json=[{"id": i} for i in range(100, 200)], headers={"X-Pagination-Page-Count": "3"}),
        httpx.Response(200, json=[{"id": i} for i in range(200, 230)], headers={"X-Pagination-Page-Count": "3"}),
    ]
    respx.get("https://api.trakt.tv/sync/ratings").mock(
        return_value=httpx.Response(200, json=[{"rating": 9, "rated_at": "2024-01-01T00:00:00Z"}], headers={})
    )
    respx.get("https://api.trakt.tv/sync/watchlist").mock(
        return_value=httpx.Response(200, json=[], headers={})
    )

    result = pull_all()

    assert len(result["history"]) == 230
    assert result["history"][0]["id"] == 0
    assert result["history"][-1]["id"] == 229
    assert result["ratings"] == [{"rating": 9, "rated_at": "2024-01-01T00:00:00Z"}]
    assert result["watchlist"] == []
    assert "pulled_at" in result
    requested_pages = [int(c.request.url.params["page"]) for c in history_route.calls]
    assert requested_pages == [1, 2, 3]
    requested_limits = {int(c.request.url.params["limit"]) for c in history_route.calls}
    assert requested_limits == {100}
