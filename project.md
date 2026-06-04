# PROJECT.md

# Telegram World Cup Reminder Bot

## Objective

Build a Telegram bot that sends reminders for FIFA World Cup 2026 matches.

The project must remain extremely simple.

No databases.

No external sports APIs.

The fixture already exists in an ICS file.

The bot must allow users to subscribe to one or more teams and receive reminders before matches.

---

# Technical Stack

## Language

Python 3.12+

## Libraries

* python-telegram-bot
* apscheduler
* icalendar
* zoneinfo
* json
* logging

Avoid unnecessary dependencies.

---

# Project Structure

text
worldcup-bot/

├── data/
│   ├── worldcup.ics
│   ├── matches.json
│   ├── users.json
│   └── notifications.json
│
├── src/
│   ├── bot.py
│   ├── scheduler.py
│   ├── fixture_importer.py
│   ├── user_repository.py
│   ├── match_repository.py
│   ├── notification_service.py
│   ├── command_handlers.py
│   ├── keyboards.py
│   ├── models.py
│   └── config.py
│
├── requirements.txt
├── README.md
└── .env


---

# Persistence

Do not use a database.

Use JSON files only.

## users.json

Store Telegram users.

Example:

json
[
  {
    "chat_id": 123456789,
    "timezone": "America/Argentina/Buenos_Aires",
    "favorite_teams": [
      "Argentina",
      "Brasil"
    ],
    "notify_before_minutes": 120
  }
]


## notifications.json

Used to avoid duplicate notifications.

Example:

json
[
  {
    "chat_id": 123456789,
    "match_id": "match-001",
    "notification_type": "120m"
  }
]


---

# Fixture Import

The file already exists:

text
data/worldcup.ics


Implement a fixture importer.

Requirements:

* Read the ICS file.
* Extract every match.
* Convert matches to JSON.
* Save the result to:

text
data/matches.json


The conversion should run automatically if matches.json does not exist.

---

# Match Model

json
{
  "id": "match-001",
  "home_team": "Argentina",
  "away_team": "Germany",
  "phase": "Group Stage",
  "stadium": "MetLife Stadium",
  "city": "New York",
  "kickoff_utc": "2026-06-11T19:00:00Z"
}


All dates must be stored in UTC.

Never store local times.

---

# Telegram Commands

## /start

Create the user if it does not exist.

Send welcome message.

---

## /help

Display available commands.

---

## /today

Show today's matches using the user's timezone.

---

## /next

Show upcoming matches for subscribed teams.

---

## /teams

Display all available teams.

Use Telegram inline keyboards.

---

## /subscriptions

Display current subscriptions.

Example:

text
Your subscriptions:

🇦🇷 Argentina
🇧🇷 Brazil
🇪🇸 Spain


---

## /subscribe

Allow users to subscribe to teams.

Prefer Telegram InlineKeyboardButton.

The user should not need to type team names manually.

---

## /unsubscribe

Allow users to remove subscriptions.

Use inline buttons.

---

## /timezone

Allow users to configure timezone.

Examples:

text
America/Argentina/Buenos_Aires
Europe/Madrid
America/Mexico_City
America/New_York


Store the selected timezone in users.json.

---

# Team Selection UX

Use Telegram inline keyboards.

Example:

text
Choose a team:

🇦🇷 Argentina
🇧🇷 Brazil
🇪🇸 Spain
🇫🇷 France


Allow multiple subscriptions.

---

# Scheduler

Use APScheduler.

Run every 5 minutes.

python
interval = 5 minutes


Responsibilities:

1. Load users.
2. Load matches.
3. Find upcoming matches.
4. Send notifications.

---

# Notification Rules

Send reminders:

* 120 minutes before kickoff
* 60 minutes before kickoff
* 15 minutes before kickoff

Prevent duplicates using notifications.json.

---

# Timezone Handling

Matches are stored in UTC.

Users have their own timezone.

Convert match times dynamically:

python
kickoff_utc -> user timezone


Use:

python
ZoneInfo(user_timezone)


Never hardcode timezone offsets.

---

# Notification Message

Example:

text
⚽ FIFA World Cup 2026

🇦🇷 Argentina vs 🇩🇪 Germany

🕒 16:00

🏟️ MetLife Stadium

Match starts in 2 hours.


---

# Error Handling

Requirements:

* Log exceptions.
* Handle missing files.
* Handle corrupted JSON.
* Handle invalid timezone values.
* Handle Telegram API failures.

The application must continue running whenever possible.

---

# Configuration

Use environment variables.

Required:

env
TELEGRAM_BOT_TOKEN=


Store secrets only in .env.

---

# Logging

Create application logs.

Minimum levels:

* INFO
* WARNING
* ERROR

---

# Deliverables

Generate:

* Full project structure
* requirements.txt
* README.md
* All source files
* Example JSON files
* Working Telegram bot implementation

The result should be executable with:

bash
pip install -r requirements.txt
python src/bot.py


No placeholders.

Generate production-ready code for the MVP.