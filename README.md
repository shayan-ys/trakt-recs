# trakt-recs

Claude-curated movie/TV recommendations from your Trakt watch history.

A small Python CLI plus a Claude Code skill. The differentiator is a human-edited **taste profile** — built once via a structured interview, persisted as a markdown file you can edit any time. The skill pulls fresh Trakt history on demand and returns recommendations that explicitly exclude everything you've already watched.

## Quick start

```bash
# 1. Clone
git clone https://github.com/<you>/trakt-recs.git
cd trakt-recs

# 2. Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# 3. Register a Trakt OAuth app at https://trakt.tv/oauth/applications/new
#    Redirect URI: urn:ietf:wg:oauth:2.0:oob
#    Copy the client_id and client_secret.

# 4. Configure credentials
cp .env.example .env
# Edit .env and paste your client_id / client_secret.

# 5. Authorize (one-time)
uv run python cli.py auth
# Visit the printed URL, enter the user code, click Yes.

# 6. Pull your history
uv run python cli.py pull

# 7. Bootstrap your taste profile (one-time)
# In a fresh Claude Code session at the repo root, paste the contents of
# prompts/interview.md and follow Claude's lead. It will write taste-profile.md.

# 8. Install the Claude Code skill
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/trakt-recs" ~/.claude/skills/trakt-recs
echo "export TRAKT_RECS_REPO=$(pwd)" >> ~/.zshrc   # or ~/.bashrc
# Reload your shell, then in any Claude Code session: /trakt-recs 10
```

## Subcommands

| Command | What it does |
|---------|--------------|
| `auth` | Trakt Device Code OAuth flow. Writes `.state/tokens.json`. |
| `pull` | Fetch history + ratings + watchlist. Writes `.state/cache.json`. |
| `context [--refresh]` | Emit markdown summary of watch history for Claude. |
| `status` | Show token expiry and cache freshness. |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAKT_CLIENT_ID` | _(required)_ | From the Trakt app you registered |
| `TRAKT_CLIENT_SECRET` | _(required)_ | From the Trakt app you registered |
| `TRAKT_STATE_DIR` | `./.state` | Where `tokens.json` and `cache.json` live |
| `TASTE_PROFILE_PATH` | `./taste-profile.md` | Where the taste profile markdown lives |
| `TRAKT_RECS_REPO` | _(none — required for the skill)_ | Absolute path to this cloned repo; used by the bundled SKILL.md |

`cli.py` auto-loads `.env` from the repo root via `python-dotenv`.

## 1Password / Bitwarden / etc.

If you'd rather not put your client secret in a `.env` file, anything that injects env vars works. For example, with the 1Password CLI:

```bash
op run --env-file .env.1p.tpl -- uv run python cli.py pull
```

…where `.env.1p.tpl` contains `op://` references. The CLI doesn't care where its env vars come from.

## License

MIT — see [LICENSE](LICENSE).
