# FIFA World Cup 2026 Telegram Bot

Telegram bot that sends reminders for FIFA World Cup 2026 matches.

## Features

- Import match fixtures from ICS files
- Subscribe to specific teams or all matches
- Match reminders 120, 60, and 15 minutes before kickoff
- Daily summary of today's matches at 08:00 (user timezone)
- Timezone-aware display
- SQLite persistence (no external database required)

## Requirements

- Python 3.12+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Setup

```bash
# Clone the repository
git clone <repo-url> && cd worldcup-bot

# Create .env file
cp .env.example .env
# Edit .env and set your TELEGRAM_BOT_TOKEN

# Install dependencies
pip install -r requirements.txt

# Run the bot
python src/bot.py
```

The bot will automatically import the fixture file (`fifa-world-cup-2026.ics`) on first run.

## Commands

| Command | Description |
|---|---|
| `/start` | Start the bot and choose notification mode |
| `/help` | Show available commands |
| `/today` | Today's matches in your timezone |
| `/next` | Upcoming matches for your subscribed teams |
| `/teams` | List all available teams |
| `/subscribe` | Subscribe to teams (inline keyboard) |
| `/unsubscribe` | Remove team subscriptions |
| `/subscriptions` | Show your current subscriptions |
| `/all` | Receive notifications for all matches |
| `/teamsmode` | Receive notifications for selected teams only |
| `/timezone` | Set your timezone (e.g., `/timezone America/Argentina/Buenos_Aires`) |

## Deployment on Render

1. Create a new **Background Worker** on Render
2. Connect your repository
3. Set the **Build Command**: `pip install -r requirements.txt`
4. Set the **Start Command**: `python src/bot.py`
5. Add environment variable `TELEGRAM_BOT_TOKEN`
6. Add a **Persistent Disk** (1 GB) mounted at `/opt/render/project/data`

The bot stores `bot.db` and `matches.json` in the `data/` directory. On Render, configure the persistent disk mount path accordingly.

## Project Structure

```
├── data/               # Persistent data (matches.json, bot.db)
├── src/
│   ├── bot.py                 # Entry point
│   ├── command_handlers.py    # Telegram command handlers
│   ├── config.py              # Environment configuration
│   ├── database.py            # SQLite initialization
│   ├── fixture_importer.py    # ICS parser
│   ├── keyboards.py           # Inline keyboards
│   ├── match_repository.py    # Match data access
│   ├── models.py              # Data classes
│   ├── notification_service.py # Duplicate prevention
│   ├── scheduler.py           # APScheduler jobs
│   └── user_repository.py     # User data access
├── .env.example
├── fifa-world-cup-2026.ics
├── render.yaml
└── requirements.txt
```
