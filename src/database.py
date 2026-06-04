import sqlite3
import logging
from pathlib import Path

from src.config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                timezone TEXT NOT NULL,
                subscription_mode TEXT NOT NULL,
                notify_before_minutes INTEGER DEFAULT 120,
                language TEXT NOT NULL DEFAULT 'es',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                team_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                match_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_at TEXT NOT NULL
            );
        """)
        conn.commit()

        try:
            conn.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'es'")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        logger.info("Database initialized at %s", DB_PATH)
    except Exception:
        logger.exception("Failed to initialize database")
        raise
    finally:
        conn.close()
