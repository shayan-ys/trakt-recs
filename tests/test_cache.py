from __future__ import annotations

from datetime import UTC

from cli import CACHE_STALE_SECONDS, cache_is_fresh, load_cache, save_cache


def test_save_then_load_cache_roundtrip(state_dir):
    payload = {
        "history": [{"id": 1}],
        "ratings": [],
        "watchlist": [],
        "pulled_at": "2026-05-21T00:00:00+00:00",
    }
    save_cache(payload)
    assert load_cache() == payload


def test_load_cache_returns_none_when_missing(state_dir):
    assert load_cache() is None


def test_cache_is_fresh_when_recent(state_dir):
    from datetime import datetime
    payload = {
        "history": [], "ratings": [], "watchlist": [],
        "pulled_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    save_cache(payload)
    assert cache_is_fresh() is True


def test_cache_is_stale_when_old(state_dir):
    from datetime import datetime, timedelta
    payload = {
        "history": [], "ratings": [], "watchlist": [],
        "pulled_at": (datetime.now(UTC) - timedelta(seconds=CACHE_STALE_SECONDS + 10)).isoformat(timespec="seconds"),
    }
    save_cache(payload)
    assert cache_is_fresh() is False
