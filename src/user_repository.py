import logging
from datetime import datetime, timezone as dt_timezone
from typing import Optional

from src.database import get_connection

logger = logging.getLogger(__name__)


def create_user(chat_id: int, tz: str, subscription_mode: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT OR IGNORE INTO users (chat_id, timezone, subscription_mode, created_at) "
            "VALUES (?, ?, ?, ?)",
            (chat_id, tz, subscription_mode, datetime.now(dt_timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to create user %s", chat_id)
        return False


def get_user(chat_id: int) -> Optional[dict]:
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT chat_id, timezone, subscription_mode, notify_before_minutes FROM users WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return dict(row)
    except Exception:
        logger.exception("Failed to get user %s", chat_id)
        return None


def set_timezone(chat_id: int, timezone: str) -> bool:
    try:
        conn = get_connection()
        conn.execute("UPDATE users SET timezone = ? WHERE chat_id = ?", (timezone, chat_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to set timezone for %s", chat_id)
        return False


def set_subscription_mode(chat_id: int, mode: str) -> bool:
    try:
        conn = get_connection()
        conn.execute("UPDATE users SET subscription_mode = ? WHERE chat_id = ?", (mode, chat_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to set subscription mode for %s", chat_id)
        return False


def set_notify_before(chat_id: int, minutes: int) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE users SET notify_before_minutes = ? WHERE chat_id = ?",
            (minutes, chat_id),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to set notify_before for %s", chat_id)
        return False


def subscribe_team(chat_id: int, team_name: str) -> bool:
    try:
        conn = get_connection()
        existing = conn.execute(
            "SELECT id FROM subscriptions WHERE chat_id = ? AND team_name = ?",
            (chat_id, team_name),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO subscriptions (chat_id, team_name) VALUES (?, ?)",
                (chat_id, team_name),
            )
            conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to subscribe %s to %s", chat_id, team_name)
        return False


def unsubscribe_team(chat_id: int, team_name: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "DELETE FROM subscriptions WHERE chat_id = ? AND team_name = ?",
            (chat_id, team_name),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to unsubscribe %s from %s", chat_id, team_name)
        return False


def get_subscriptions(chat_id: int) -> list[str]:
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT team_name FROM subscriptions WHERE chat_id = ?",
            (chat_id,),
        ).fetchall()
        conn.close()
        return [row["team_name"] for row in rows]
    except Exception:
        logger.exception("Failed to get subscriptions for %s", chat_id)
        return []


def get_all_users() -> list[dict]:
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT chat_id, timezone, subscription_mode, notify_before_minutes FROM users"
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        logger.exception("Failed to get all users")
        return []
