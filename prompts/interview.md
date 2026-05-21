# Trakt Taste Interview — Prompt

Paste this into a fresh Claude Code session at the repo root, after `uv run python cli.py pull` has been run at least once.

---

You are conducting a one-time taste interview to populate `taste-profile.md` (or wherever `$TASTE_PROFILE_PATH` points).

**Step 1: Load the watch context.** Run:

```
uv run python cli.py context
```

Read everything it prints. That is the user's full Trakt watch history + ratings + watchlist.

**Step 2: Read the current profile.** If `taste-profile.md` exists, open it. If sections are empty (`_(filled by interview)_`), this is a fresh interview. If sections have content, this is a refinement — preserve what's there and offer additive edits only. If the file doesn't exist, copy `taste-profile.example.md` to `taste-profile.md` as your starting structure.

**Step 3: Form hypotheses, then interview.**

Before asking anything, study the data and form 3–5 hypotheses about the user's taste — patterns in genre, era, director, pacing, tone, runtime tolerance. Then ask the user about each hypothesis in turn:

- "I see you've watched a lot of [pattern]. Is that a genuine love or just availability?"
- "You rated [outlier title] [N/10]. What was that about?"
- "You bounce off [pattern]? What specifically?"
- "Hard dislikes — anything I should never recommend?"
- "Contextual rules — anything based on time of day, mood, runtime, who you're with?"

Ask **one question at a time** and wait for an answer. Don't fire off a multi-question questionnaire — the goal is a real conversation that catches nuance.

After 6–10 rounds, if you have enough material, ask: "Anything else I should know about your taste that the data wouldn't reveal?"

**Step 4: Write the profile.**

When the interview is done, write `taste-profile.md` with these sections, populated from the conversation:

- Themes I'm drawn to
- Directors / auteurs
- Eras and traditions
- Pacing and tone
- Hard dislikes
- Contextual rules

Keep the writing tight, declarative, and in the user's voice — quote their phrases verbatim where possible. Avoid hedging.

**Step 5: Confirm.** Print a brief summary of what you wrote, and ask the user to skim the file and tell you if anything is off. Make corrections as requested.
