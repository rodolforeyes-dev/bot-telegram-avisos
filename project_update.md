# PROJECT_UPDATE.md

## Persistence

Use SQLite instead of JSON for users and notifications.

Keep the fixture in JSON because it is static.

Structure:

text id="7nycgl"
data/

├── worldcup.ics
├── matches.json
└── bot.db


---

# Database

Use SQLite.

Database file:

text id="d6w19e"
data/bot.db


Create tables automatically at startup.

---

## users

sql id="xjcw9u"
CREATE TABLE users (
    chat_id INTEGER PRIMARY KEY,
    timezone TEXT NOT NULL,
    subscription_mode TEXT NOT NULL,
    notify_before_minutes INTEGER DEFAULT 120,
    created_at TEXT NOT NULL
);


subscription_mode values:

text id="xv6jr3"
ALL
TEAMS


---

## subscriptions

sql id="z09d6w"
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    team_name TEXT NOT NULL
);


---

## sent_notifications

sql id="3u6ccg"
CREATE TABLE sent_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    match_id TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    sent_at TEXT NOT NULL
);


notification_type values:

text id="g72vf7"
DAILY
120M
60M
15M


---

# Subscription Modes

Support two notification modes.

## ALL

User receives notifications for every World Cup match.

Example:

text id="8dv5je"
🌎 All matches


---

## TEAMS

User receives notifications only for selected teams.

Example:

text id="s4n6zj"
🇦🇷 Argentina
🇧🇷 Brazil


---

# Telegram Commands

Add:

## /all

Switch user to ALL mode.

Example response:

text id="i5ivyb"
✅ You will now receive notifications for every World Cup match.


---

## /teamsmode

Switch user to TEAMS mode.

Example response:

text id="4dlut7"
✅ Team subscription mode enabled.
Choose your teams.


---

# User Onboarding

During /start display:

text id="44l4n8"
How would you like to receive notifications?

🌎 All World Cup matches

⭐ Selected teams only


Use Telegram InlineKeyboardButton.

---

# Daily Summary

Implement a second scheduler.

Run every day at 08:00 in the user's configured timezone.

The scheduler must send a summary of all matches scheduled for that day.

Example:

text id="3e06nn"
⚽ FIFA World Cup 2026

Today's matches

13:00 🇯🇵 Japan vs 🇲🇽 Mexico

16:00 🇦🇷 Argentina vs 🇩🇪 Germany

19:00 🇧🇷 Brazil vs 🇪🇸 Spain

22:00 🇫🇷 France vs 🏴 England


The times displayed must be converted to the user's timezone.

---

# Match Reminder Scheduler

Keep existing reminders.

Notification windows:

* 120 minutes
* 60 minutes
* 15 minutes

Examples:

text id="d3rf7h"
⏰ Match starts in 2 hours

🇦🇷 Argentina vs 🇩🇪 Germany

🕒 16:00

🏟️ MetLife Stadium


---

# Notification Logic

If subscription_mode = ALL

Send:

* Daily summary
* All match reminders

If subscription_mode = TEAMS

Send:

* Daily summary only for subscribed teams
* Match reminders only for subscribed teams

---

# Render Deployment

Target platform:

Render Background Worker

Build Command:

bash id="wbrwsh"
pip install -r requirements.txt


Start Command:

bash id="n07f6p"
python src/bot.py


Persistent Disk required.

Mount path:

text id="z4i3kl"
/opt/render/project/data


Store:

text id="n7gvhf"
bot.db
matches.json


inside the persistent disk.

---

# MVP Goal

A Telegram bot that:

* Imports World Cup fixtures from an ICS file.
* Stores users in SQLite.
* Supports ALL matches mode.
* Supports selected teams mode.
* Sends a daily summary.
* Sends reminders 120, 60 and 15 minutes before kickoff.
* Handles user-specific timezones.
* Runs continuously on Render.
* Requires no external sports APIs.