from __future__ import annotations

from cli import emit_context

SAMPLE_CACHE = {
    "pulled_at": "2026-05-21T12:00:00+00:00",
    "history": [
        {
            "type": "movie",
            "watched_at": "2024-01-10T20:00:00Z",
            "movie": {"title": "Heat", "year": 1995, "ids": {"trakt": 1, "imdb": "tt0113277"}},
        },
        {
            "type": "episode",
            "watched_at": "2024-02-01T20:00:00Z",
            "show": {"title": "The Wire", "year": 2002, "ids": {"trakt": 99}},
            "episode": {"season": 1, "number": 1, "title": "Pilot"},
        },
    ],
    "ratings": [
        {
            "rated_at": "2024-01-11T00:00:00Z",
            "rating": 10,
            "type": "movie",
            "movie": {"title": "Heat", "year": 1995, "ids": {"trakt": 1}},
        },
        {
            "rated_at": "2024-02-01T00:00:00Z",
            "rating": 3,
            "type": "movie",
            "movie": {"title": "Garbage Film", "year": 2010, "ids": {"trakt": 7}},
        },
    ],
    "watchlist": [
        {
            "listed_at": "2024-03-01T00:00:00Z",
            "type": "movie",
            "movie": {"title": "Mishima", "year": 1985, "ids": {"trakt": 22}},
        },
    ],
}


def test_emit_context_includes_pulled_at_header():
    out = emit_context(SAMPLE_CACHE)
    assert "Pulled at: 2026-05-21T12:00:00+00:00" in out


def test_emit_context_lists_movies_and_shows_separately():
    out = emit_context(SAMPLE_CACHE)
    assert "Heat (1995)" in out
    assert "The Wire (2002)" in out
    # Episodes are not enumerated individually.
    assert "Pilot" not in out


def test_emit_context_dedupes_shows_across_episodes():
    cache = {
        "pulled_at": "2026-05-21T12:00:00+00:00",
        "history": [
            {
                "type": "episode",
                "watched_at": f"2024-02-0{i}T20:00:00Z",
                "show": {"title": "The Wire", "year": 2002, "ids": {"trakt": 99}},
                "episode": {"season": 1, "number": i},
            }
            for i in range(1, 6)
        ],
        "ratings": [],
        "watchlist": [],
    }
    out = emit_context(cache)
    assert out.count("The Wire (2002)") == 1


def test_emit_context_highlights_outlier_ratings():
    out = emit_context(SAMPLE_CACHE)
    assert "## Loved (rated 9–10)" in out
    assert "Heat (1995) — 10/10" in out
    assert "## Disliked (rated 1–4)" in out
    assert "Garbage Film (2010) — 3/10" in out


def test_emit_context_includes_watchlist():
    out = emit_context(SAMPLE_CACHE)
    assert "## Watchlist (queued, not yet watched)" in out
    assert "Mishima (1985)" in out


def test_emit_context_includes_counts():
    out = emit_context(SAMPLE_CACHE)
    assert "1 movie" in out
    assert "1 show" in out
