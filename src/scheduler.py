import logging
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from telegram import Bot

from src.i18n import t, reminder_label
from src.match_repository import load_matches
from src.user_repository import get_all_users, get_subscriptions
from src.notification_service import is_notification_sent, mark_notification_sent
from src.config import MATCHES_PATH

logger = logging.getLogger(__name__)

REMINDER_CONFIGS = [
    ("120M", 120),
    ("60M", 60),
    ("15M", 15),
]


async def check_match_reminders(bot: Bot):
    try:
        matches = load_matches(MATCHES_PATH)
    except Exception:
        logger.exception("Failed to load matches for reminders")
        return

    users = get_all_users()
    now_utc = datetime.now(dt_timezone.utc)

    for user in users:
        chat_id = user["chat_id"]
        lang = user.get("language", "es")
        try:
            user_tz = ZoneInfo(user["timezone"])
        except (KeyError, TypeError):
            user_tz = ZoneInfo("UTC")

        if user["subscription_mode"] == "ALL":
            relevant = list(matches)
        else:
            subs = get_subscriptions(chat_id)
            relevant = [m for m in matches if m.home_team in subs or m.away_team in subs]

        for match in relevant:
            try:
                kickoff = datetime.fromisoformat(match.kickoff_utc.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            diff = (kickoff - now_utc).total_seconds()
            if diff < 0:
                continue

            minutes_until = diff / 60.0

            for notif_type, threshold in REMINDER_CONFIGS:
                if minutes_until > threshold:
                    continue
                if is_notification_sent(chat_id, match.id, notif_type):
                    continue

                try:
                    local_time = kickoff.astimezone(user_tz)
                    time_str = local_time.strftime("%H:%M")
                except Exception:
                    time_str = match.kickoff_utc

                label = reminder_label(notif_type, lang)
                text = t(lang, "reminder", label=label,
                         home=match.home_team, away=match.away_team,
                         time=time_str, stadium=match.stadium)
                try:
                    await bot.send_message(chat_id=chat_id, text=text)
                    mark_notification_sent(chat_id, match.id, notif_type)
                    logger.info(
                        "Sent %s reminder to %s for match %s",
                        notif_type, chat_id, match.id,
                    )
                except Exception:
                    logger.exception("Failed to send %s reminder to %s", notif_type, chat_id)
    logger.info("Match reminder check completed")


async def check_daily_summaries(bot: Bot):
    try:
        matches = load_matches(MATCHES_PATH)
    except Exception:
        logger.exception("Failed to load matches for daily summary")
        return

    users = get_all_users()

    for user in users:
        chat_id = user["chat_id"]
        lang = user.get("language", "es")
        try:
            user_tz = ZoneInfo(user["timezone"])
        except (KeyError, TypeError):
            user_tz = ZoneInfo("UTC")

        now_user = datetime.now(user_tz)

        if now_user.hour != 8:
            continue

        day_str = now_user.strftime("%Y-%m-%d")
        if is_notification_sent(chat_id, f"daily_{day_str}", "DAILY"):
            continue

        if user["subscription_mode"] == "ALL":
            relevant = list(matches)
        else:
            subs = get_subscriptions(chat_id)
            relevant = [m for m in matches if m.home_team in subs or m.away_team in subs]

        today_matches = []
        for m in relevant:
            try:
                kickoff = datetime.fromisoformat(m.kickoff_utc.replace("Z", "+00:00"))
                local = kickoff.astimezone(user_tz)
                if local.date() == now_user.date():
                    today_matches.append((local, m))
            except (ValueError, TypeError):
                continue

        if not today_matches:
            continue

        today_matches.sort(key=lambda x: x[0])

        lines = [t(lang, "daily_header")]
        for local, m in today_matches:
            lines.append(f"\n{local.strftime('%H:%M')}  {m.home_team} vs {m.away_team}")

        try:
            await bot.send_message(chat_id=chat_id, text="".join(lines))
            mark_notification_sent(chat_id, f"daily_{day_str}", "DAILY")
            logger.info("Sent daily summary to %s", chat_id)
        except Exception:
            logger.exception("Failed to send daily summary to %s", chat_id)

    logger.info("Daily summary check completed")
