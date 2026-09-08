# Taxi Yordamchi

Full project & deployment guide is in **AGENTS.md** — read it first.

@AGENTS.md

## Quick reminders
- User-facing text & communication: **Uzbek**. Code & comments: English/Uzbek mix (match surrounding).
- **Normal workflow: edit → `git push` → CI/CD auto-deploys to the Contabo server in ~15-20s.**
- Do NOT run the bot locally with the production `BOT_TOKEN` (409 conflict with the server).
- Scheduler is a per-user asyncio loop (NOT APScheduler) — see AGENTS.md §8.
- Every user-facing string is an i18n key in `bot/i18n.py` (3 languages).
- Secrets live in `.env` (gitignored) locally and at `/opt/taxi_yordamchi/.env` on the server.
