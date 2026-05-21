---
name: trakt-recs
description: Return personalized movie/TV recommendations from Trakt watch history, excluding everything already watched. Use when the user asks for movie or show recommendations, "what should I watch", "recommend me a film", "suggest something to watch", or invokes /trakt-recs.
when_to_use: Triggers on "what should I watch tonight", "movie recs", "show suggestions", "give me something to watch", "I need a movie", "recommend me a documentary", or direct /trakt-recs invocation. Default count is 10.
argument-hint: "[N]"
allowed-tools: Bash(uv run *) Bash(cat *) Read
---

## Watch context (refreshed live)

!`cd "$TRAKT_RECS_REPO" && uv run python cli.py context 2>&1`

## Taste profile

!`cat "${TASTE_PROFILE_PATH:-$TRAKT_RECS_REPO/taste-profile.md}"`

## Instructions

Return **N = $ARGUMENTS** recommendations (default to 10 if no number was given).

Rules:

1. **Exclude every title in the watch context above.** No exceptions — if it appears under "Watched movies" or "Watched shows", do not recommend it. Treat watchlist items as "already considered" — only suggest one if you have a strong reason to push it up the queue.
2. **Match the taste profile.** Lean into themes/directors/eras the user calls out; respect hard dislikes and contextual rules.
3. **Diversify.** Don't return ten films from the same director or decade unless the profile explicitly asks for that.
4. **Format the output** as a numbered list. Each line: `Title (Year) — one-sentence reason tied to the profile.` Group movies before TV if both are returned.
5. **If the `context` command output above contains an error** (e.g. "not authenticated", "TRAKT_CLIENT_ID missing", a stack trace), stop and report the error. Do NOT fabricate recommendations from training data alone.
6. **Be opinionated.** This isn't a popular-films list — it's a curated nudge.

After the list, add one line: `_Refresh the cache anytime with `python cli.py pull`._`
