import logging
from datetime import datetime, timezone

from src.database import get_connection

logger = logging.getLogger(__name__)


def is_notification_sent(chat_id: int, match_id: str, notification_type: str) -> bool:
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT id FROM sent_notifications WHERE chat_id = ? AND match_id = ? AND notification_type = ?",
            (chat_id, match_id, notification_type),
        ).fetchone()
        conn.close()
        return row is not None
    except Exception:
        logger.exception("Failed to check notification")
        return False


def mark_notification_sent(chat_id: int, match_id: str, notification_type: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO sent_notifications (chat_id, match_id, notification_type, sent_at) VALUES (?, ?, ?, ?)",
            (chat_id, match_id, notification_type, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        logger.exception("Failed to mark notification")
        return False


def get_all_sent_notifications() -> list[dict]:
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT chat_id, match_id, notification_type, sent_at FROM sent_notifications"
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        logger.exception("Failed to get sent notifications")
        return []
