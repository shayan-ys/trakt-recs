from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


@pytest.fixture
def state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated .state/ for each test. Overrides TRAKT_STATE_DIR env var."""
    d = tmp_path / ".state"
    d.mkdir()
    monkeypatch.setenv("TRAKT_STATE_DIR", str(d))
    return d


@pytest.fixture
def tokens_file(state_dir: Path) -> Path:
    """Pre-populated tokens.json — access valid for 7 days from now."""
    payload = {
        "access_token": "test_access_abc",
        "refresh_token": "test_refresh_xyz",
        "expires_at": int(time.time()) + 7 * 24 * 3600,
        "created_at": int(time.time()),
    }
    p = state_dir / "tokens.json"
    p.write_text(json.dumps(payload))
    return p


@pytest.fixture
def trakt_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAKT_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("TRAKT_CLIENT_SECRET", "test_client_secret")
